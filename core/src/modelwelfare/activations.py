"""Activation records over capture output (REGISTRATION §3.4; §6 item 6).

Capture backends write pooled turn vectors to safetensors with a JSON
manifest — the workbench form. The store's registered at-rest form is two
record kinds: ``activations`` — one ActivationSlice per captured assistant
turn, content-addressing its pooled vector inside the safetensors file —
and ``projections`` — ProjectionSeries per (turn, frozen direction), where
a length-1 series is the pooled-turn scalar functional (a longer series is
a token-level drift read). The streaming store keeps tensors in the
safetensors workbench form; the release form embeds each record's tensor
inline (``TensorRef.data``, via :func:`embed_tensor_data`) so a bundle is
one self-contained file, and :func:`condition_capture` reads either form.

Ingest is numpy-only, so any host can convert any capture regardless of
where it was produced. In two-host collection each producer ingests its
own conditions under its own producer name, and the per-producer streams
merge on read — the same convention as every other record kind. Ingest
appends; running it twice for the same (capture, producer) duplicates
records, so a re-ingest belongs in a fresh store or a new producer name.
"""

import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
from safetensors.numpy import load_file

from modelwelfare.replay import split_conversation_id
from modelwelfare.v1 import activation_pb2, common_pb2

# Sub-directory of a condition holding capture tensors. Not a record kind:
# consolidation packs the record streams and leaves tensors as assets.
TENSOR_DIRECTORY = "tensors"


def file_sha256(path) -> str:
    """SHA-256 of a file's bytes — the TensorRef content address."""
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_capture(path):
    """(tensors, manifest) for a capture backend's output pair."""
    with open(str(path) + ".manifest.json") as handle:
        manifest = json.load(handle)
    return load_file(str(path)), manifest


def layer_directions(vectors_path, layer: int) -> dict:
    """Frozen direction vectors at one layer, keyed by direction name."""
    vectors = load_file(str(vectors_path))
    suffix = f"|L{layer}"
    return {name[: -len(suffix)]: vector
            for name, vector in vectors.items() if name.endswith(suffix)}


def encode_tensor(array) -> tuple:
    """(dtype_name, bytes) for one float32 array, little-endian.

    Activations computed by a bfloat16 model and upcast to float32 have an
    all-zero mantissa tail; those round-trip losslessly as 2-byte bfloat16
    (the high half of each float32 word), halving the payload. Anything
    else — pooled means are true float32 arithmetic — stays float32.
    """
    array = np.ascontiguousarray(array, dtype="<f4")
    words = array.view("<u4")
    if array.size and not (words & np.uint32(0xFFFF)).any():
        return "bfloat16", (words >> np.uint32(16)).astype("<u2").tobytes()
    return "float32", array.tobytes()


def decode_tensor(ref):
    """The float32 array a TensorRef carries inline (exact inverse of
    :func:`encode_tensor`)."""
    shape = tuple(ref.shape)
    if ref.dtype == "bfloat16":
        words = np.frombuffer(ref.data, dtype="<u2").astype("<u4")
        return (words << np.uint32(16)).view("<f4").reshape(shape)
    if ref.dtype == "float32":
        return np.frombuffer(ref.data, dtype="<f4").reshape(shape).copy()
    raise ValueError(f"inline tensor dtype {ref.dtype!r} not supported")


def record_conversation_id(record) -> str:
    """The capture conversation id an ActivationSlice belongs to, recovered
    from its tensor name (authoritative — ids outside the ``item|sN``
    convention, e.g. direction-extraction prompts, stay exact) with the
    record key as the fallback."""
    name = record.tensor.tensor_name
    if name:
        base = name.removesuffix("|tokens")
        suffix = f"|t{record.turn_index}|L{record.hook.layer}"
        if base.endswith(suffix):
            return base.removesuffix(suffix)
    return f"{record.key.item_id}|s{record.key.sample_index}"


def embed_tensor_data(records, root) -> int:
    """Fill each ActivationSlice's ``tensor.data`` from its referenced
    capture file under ``root`` — the streaming-form -> release-form step.
    The uri/tensor_name/file_digest stay as write-time provenance; records
    already carrying data are left alone. Each referenced file's digest is
    verified before its tensors are trusted, exactly as the read bridge
    verifies. Returns the number of records embedded."""
    by_uri = {}
    for record in records:
        if not record.tensor.data:
            by_uri.setdefault(record.tensor.uri, []).append(record)
    embedded = 0
    for uri, uri_records in by_uri.items():
        path = Path(root) / uri
        digest = file_sha256(path)
        recorded = {record.tensor.file_digest for record in uri_records}
        if recorded != {digest}:
            raise ValueError(
                f"{uri}: file digest {digest} does not match the recorded "
                f"digest(s) {sorted(recorded)} — capture asset corrupt or "
                "substituted")
        tensors = load_file(str(path))
        for record in uri_records:
            array = tensors[record.tensor.tensor_name]
            dtype, data = encode_tensor(array)
            record.tensor.dtype = dtype
            record.tensor.data = data
            del record.tensor.shape[:]
            record.tensor.shape.extend(array.shape)
            embedded += 1
    return embedded


def capture_records(capture_path, experiment_id: str, condition_id: str,
                    layer: int, uri: str, directions=None, provenance=None,
                    token_series=False):
    """Build the record streams for one capture pair at one layer.

    Returns (slices, projections): one ActivationSlice per pooled assistant
    turn found at ``layer``, and — when ``directions`` (name -> unit
    vector) is given — one length-1 ProjectionSeries per (turn, direction),
    the pooled-turn scalar functional. With ``token_series`` a capture's
    per-token span arrays (the ``|tokens`` entries a retention pass saves)
    become slices too, so a token capture consolidates like any other.
    ``uri`` is the capture file's path relative to the data root the
    records will live under; token indices are the capture manifest's
    spans (into the conversation's tokenization).
    """
    tensors, manifest = load_capture(capture_path)
    digest = file_sha256(capture_path)
    point = manifest.get("point", "residual_post")
    slices, projections = [], []
    for conversation in manifest["conversations"]:
        try:
            item_id, sample_index = split_conversation_id(conversation["id"])
        except ValueError:
            # Captures outside the experiment convention (e.g. the
            # direction-extraction prompt set) use bare ids; the exact id
            # stays recoverable from the tensor name.
            item_id, sample_index = conversation["id"], 0
        key = common_pb2.ResultKey(
            experiment_id=experiment_id, condition_id=condition_id,
            item_id=item_id, sample_index=sample_index)
        for span in conversation["assistant_spans"]:
            base = f"{conversation['id']}|t{span['message_index']}|L{layer}"
            names = [base] + ([f"{base}|tokens"] if token_series else [])
            for name in names:
                vector = tensors.get(name)
                if vector is None:
                    continue
                record = activation_pb2.ActivationSlice(
                    key=key, turn_index=span["message_index"],
                    token_start=span["start"], token_end=span["end"],
                    hook=activation_pb2.HookPoint(layer=layer, point=point),
                    tensor=activation_pb2.TensorRef(
                        uri=uri, tensor_name=name, shape=list(vector.shape),
                        dtype=str(vector.dtype), file_digest=digest))
                if provenance is not None:
                    record.provenance.CopyFrom(provenance)
                slices.append(record)
                if name != base:
                    continue
                for direction_name, direction in sorted(
                        (directions or {}).items()):
                    series = activation_pb2.ProjectionSeries(
                        key=key, direction_id=direction_name,
                        turn_index=span["message_index"],
                        values=[float(np.dot(vector, direction))])
                    if provenance is not None:
                        series.provenance.CopyFrom(provenance)
                    projections.append(series)
    return slices, projections


def probe_scores(weights, group: str, features: dict) -> dict:
    """Standardized linear probe score for each feature vector.

    ``weights`` is a trained-probe safetensors dict (train_probe.py's
    output): per group a weight vector, bias, and the train-split feature
    mean/std the weights assume.
    """
    mean = weights[f"{group}|feature_mean"]
    std = weights[f"{group}|feature_std"]
    w = weights[f"{group}|weight"]
    b = weights[f"{group}|bias"][0]
    return {cid: float(np.dot((vector - mean) / std, w) + b)
            for cid, vector in features.items()}


def condition_capture(store, experiment_id: str, condition_id: str):
    """(tensors, manifest) over the condition's activation records — the
    read-side bridge back to the ``replay`` feature functionals, so
    analysis pools exactly as calibration did. Records carrying their
    tensor inline (the release form) decode directly; records referencing
    a capture file (the streaming form) merge that file after its digest
    is verified."""
    from modelwelfare.v1 import activation_pb2
    recorded_by_uri = {}
    inline = []
    for record in store.read(activation_pb2.ActivationSlice,
                             experiment_id, condition_id, "activations"):
        if record.tensor.data:
            inline.append(record)
        else:
            recorded_by_uri.setdefault(record.tensor.uri, set()).add(
                record.tensor.file_digest)
    tensors = {}
    manifest = {"layers": [], "conversations": []}
    for uri, recorded in recorded_by_uri.items():
        path = Path(store.root) / uri
        digest = file_sha256(path)
        if recorded != {digest}:
            raise ValueError(
                f"{uri}: file digest {digest} does not match the recorded "
                f"digest(s) {sorted(recorded)} — capture asset corrupt or "
                "substituted")
        file_tensors, file_manifest = load_capture(path)
        tensors.update(file_tensors)
        for layer in file_manifest["layers"]:
            if layer not in manifest["layers"]:
                manifest["layers"].append(layer)
        manifest.setdefault("point", file_manifest.get("point"))
        manifest["conversations"].extend(file_manifest["conversations"])
    if inline:
        spans_by_conversation = {}
        for record in inline:
            tensors[record.tensor.tensor_name] = decode_tensor(record.tensor)
            if record.hook.layer not in manifest["layers"]:
                manifest["layers"].append(record.hook.layer)
            manifest.setdefault("point", record.hook.point)
            if record.tensor.tensor_name.endswith("|tokens"):
                continue
            cid = record_conversation_id(record)
            spans_by_conversation.setdefault(cid, {})[record.turn_index] = {
                "message_index": record.turn_index,
                "start": record.token_start, "end": record.token_end}
        for cid, spans in spans_by_conversation.items():
            manifest["conversations"].append({
                "id": cid,
                "assistant_spans": [span for _turn, span
                                    in sorted(spans.items())]})
    return tensors, manifest


def ingest_capture(store, experiment_id: str, condition_id: str,
                   capture_path, layer: int, producer: str,
                   vectors_path=None, provenance=None):
    """Place a capture pair under the store root and write its records.

    The tensors (and their manifest) are copied to
    ``<root>/<experiment>/<condition>/tensors/`` — the TensorRef uri is
    that path relative to the root — and the ``activations`` /
    ``projections`` streams append under ``producer``. Returns
    (slice_count, projection_count).
    """
    capture_path = Path(capture_path)
    with open(str(capture_path) + ".manifest.json") as handle:
        rejected = json.load(handle).get("rejected", [])
    if rejected:
        # The backend rejects per conversation so one unstable rendering
        # cannot kill a batch, but an incomplete capture must never enter
        # the record store looking complete: every registered conversation
        # is accounted for, or the ingest fails loudly.
        raise ValueError(
            f"{capture_path.name}: manifest records {len(rejected)} rejected "
            f"conversation(s) (first: {rejected[0]['id']}) — the capture is "
            "incomplete for its plan; re-capture before ingesting")
    destination_dir = (Path(store.root) / experiment_id / condition_id
                       / TENSOR_DIRECTORY)
    destination = destination_dir / capture_path.name
    if destination != capture_path:
        destination_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(capture_path, destination)
        shutil.copy2(str(capture_path) + ".manifest.json",
                     str(destination) + ".manifest.json")
    uri = destination.relative_to(store.root).as_posix()

    directions = (layer_directions(vectors_path, layer)
                  if vectors_path else None)
    slices, projections = capture_records(
        destination, experiment_id, condition_id, layer, uri,
        directions=directions, provenance=provenance)
    with store.writer(experiment_id, condition_id, "activations",
                      producer) as writer:
        for record in slices:
            writer.write(record)
    if projections:
        with store.writer(experiment_id, condition_id, "projections",
                          producer) as writer:
            for record in projections:
                writer.write(record)
    return len(slices), len(projections)
