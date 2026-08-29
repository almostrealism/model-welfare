"""Activation records over capture output (REGISTRATION §3.4; §6 item 6).

Capture backends write pooled turn vectors to safetensors with a JSON
manifest — the workbench form. The store's registered at-rest form is two
record kinds: ``activations`` — one ActivationSlice per captured assistant
turn, content-addressing its pooled vector inside the safetensors file —
and ``projections`` — ProjectionSeries per (turn, frozen direction), where
a length-1 series is the pooled-turn scalar functional (a longer series is
a token-level drift read). Tensors never enter protobuf: bundles carry the
records, the safetensors file travels beside them as a sha-listed asset.

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


def capture_records(capture_path, experiment_id: str, condition_id: str,
                    layer: int, uri: str, directions=None, provenance=None):
    """Build the record streams for one capture pair at one layer.

    Returns (slices, projections): one ActivationSlice per pooled assistant
    turn found at ``layer``, and — when ``directions`` (name -> unit
    vector) is given — one length-1 ProjectionSeries per (turn, direction),
    the pooled-turn scalar functional. ``uri`` is the capture file's path
    relative to the data root the records will live under; token indices
    are the capture manifest's spans (into the conversation's
    tokenization).
    """
    tensors, manifest = load_capture(capture_path)
    digest = file_sha256(capture_path)
    point = manifest.get("point", "residual_post")
    slices, projections = [], []
    for conversation in manifest["conversations"]:
        item_id, sample_index = split_conversation_id(conversation["id"])
        key = common_pb2.ResultKey(
            experiment_id=experiment_id, condition_id=condition_id,
            item_id=item_id, sample_index=sample_index)
        for span in conversation["assistant_spans"]:
            name = f"{conversation['id']}|t{span['message_index']}|L{layer}"
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
            for direction_name, direction in sorted((directions or {}).items()):
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
    """(tensors, manifest) merged over every capture file the condition's
    activation records reference — the read-side bridge back to the
    ``replay`` feature functionals, so analysis pools exactly as
    calibration did. Each referenced file's digest is verified before its
    tensors are trusted."""
    from modelwelfare.v1 import activation_pb2
    recorded_by_uri = {}
    for record in store.read(activation_pb2.ActivationSlice,
                             experiment_id, condition_id, "activations"):
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
