"""Activation record ingest: capture pair -> store streams -> bundle.

A fabricated capture with known vectors proves the whole §6 item 6 chain:
TensorRef content-addressing, span fields, pooled projections against
known directions, per-producer streams, bundle round-trip, and the
tensors directory staying out of the record-kind accounting.
"""
import json

import numpy as np
import pytest
from safetensors.numpy import save_file

from modelwelfare import activations, bundle
from modelwelfare.store import ResultStore
from modelwelfare.v1 import activation_pb2

HIDDEN = 4
LAYER = 18
E0 = np.eye(HIDDEN, dtype=np.float32)[0]
E1 = np.eye(HIDDEN, dtype=np.float32)[1]


def write_capture(path, conversations):
    """conversations: {conversation_id: {message_index: vector}}"""
    tensors = {}
    manifest = {"point": "residual_post", "layers": [LAYER],
                "conversations": []}
    for conversation_id, turns in conversations.items():
        spans = []
        for index, (message_index, vector) in enumerate(sorted(turns.items())):
            tensors[f"{conversation_id}|t{message_index}|L{LAYER}"] = vector
            spans.append({"message_index": message_index,
                          "start": 10 * index, "end": 10 * index + 5})
        manifest["conversations"].append(
            {"id": conversation_id, "n_tokens": 64, "assistant_spans": spans})
    save_file(tensors, str(path))
    path.with_name(path.name + ".manifest.json").write_text(
        json.dumps(manifest))
    return path


def write_vectors(path):
    save_file({f"dir-a|L{LAYER}": E0, f"dir-b|L{LAYER}": E1,
               "dir-a|L6": E1}, str(path))
    return path


@pytest.fixture
def capture(tmp_path):
    return write_capture(tmp_path / "cap.safetensors", {
        "item-x|s0": {1: E0 * 2.0, 3: E0 * 3.0 + E1},
        "item-y|s1": {1: E1 * 5.0},
    })


def test_capture_records_fields_and_projections(capture, tmp_path):
    directions = activations.layer_directions(
        write_vectors(tmp_path / "vec.safetensors"), LAYER)
    assert set(directions) == {"dir-a", "dir-b"}

    slices, projections = activations.capture_records(
        capture, "exp", "cond", LAYER, "exp/cond/tensors/cap.safetensors",
        directions=directions)
    assert len(slices) == 3 and len(projections) == 6

    first = slices[0]
    assert (first.key.experiment_id, first.key.condition_id,
            first.key.item_id, first.key.sample_index) == (
        "exp", "cond", "item-x", 0)
    assert (first.turn_index, first.token_start, first.token_end) == (1, 0, 5)
    assert (first.hook.layer, first.hook.point) == (LAYER, "residual_post")
    assert first.tensor.tensor_name == f"item-x|s0|t1|L{LAYER}"
    assert first.tensor.uri == "exp/cond/tensors/cap.safetensors"
    assert list(first.tensor.shape) == [HIDDEN]
    assert first.tensor.dtype == "float32"
    assert first.tensor.file_digest == activations.file_sha256(capture)

    by_key = {(p.key.item_id, p.key.sample_index, p.turn_index,
               p.direction_id): list(p.values) for p in projections}
    assert by_key[("item-x", 0, 1, "dir-a")] == [pytest.approx(2.0)]
    assert by_key[("item-x", 0, 3, "dir-a")] == [pytest.approx(3.0)]
    assert by_key[("item-x", 0, 3, "dir-b")] == [pytest.approx(1.0)]
    assert by_key[("item-y", 1, 1, "dir-b")] == [pytest.approx(5.0)]


def test_ingest_round_trips_through_store_and_bundle(capture, tmp_path):
    store = ResultStore(tmp_path / "data")
    slices, projections = activations.ingest_capture(
        store, "exp", "cond", capture, LAYER, "host-a",
        vectors_path=write_vectors(tmp_path / "vec.safetensors"))
    assert (slices, projections) == (3, 6)

    copied = (store.root / "exp" / "cond" / activations.TENSOR_DIRECTORY
              / "cap.safetensors")
    assert copied.is_file()
    assert copied.with_name(copied.name + ".manifest.json").is_file()

    stored = list(store.read(activation_pb2.ActivationSlice,
                             "exp", "cond", "activations"))
    assert len(stored) == 3
    assert stored[0].tensor.uri == "exp/cond/tensors/cap.safetensors"
    assert store.path("exp", "cond", "activations", "host-a").is_file()

    # The tensors directory is layout, not a record kind: packing must
    # accept it and carry the two record streams.
    packed = bundle.pack_experiment_store(store, "exp")
    assert packed.metadata.record_counts["activations"] == 3
    assert packed.metadata.record_counts["projections"] == 6
    path = tmp_path / "exp.pb"
    bundle.write_bundle(packed, path)
    reread = bundle.BundleStore(path)
    assert len(list(reread.read(activation_pb2.ProjectionSeries,
                                "exp", "cond", "projections"))) == 6


def test_ingest_refuses_a_capture_with_rejections(capture, tmp_path):
    # The backend rejects per conversation so one unstable rendering cannot
    # kill a batch, but the resulting capture is incomplete for its plan:
    # ingest must refuse it, or a rejection would silently survive every
    # resume as a permanently accepted partial capture.
    manifest_path = capture.with_name(capture.name + ".manifest.json")
    manifest = json.loads(manifest_path.read_text())
    manifest["rejected"] = [{"id": "item-z|s0", "reason": "unstable prefix"}]
    manifest_path.write_text(json.dumps(manifest))
    store = ResultStore(tmp_path / "data")
    with pytest.raises(ValueError, match="rejected"):
        activations.ingest_capture(store, "exp", "cond", capture, LAYER,
                                   "host-a")
    assert not list(store.read(activation_pb2.ActivationSlice,
                               "exp", "cond", "activations"))


def test_two_producers_merge_without_contention(capture, tmp_path):
    second = write_capture(tmp_path / "cap2.safetensors",
                           {"item-z|s0": {1: E0 * 7.0}})
    store = ResultStore(tmp_path / "data")
    activations.ingest_capture(store, "exp", "cond", capture, LAYER, "host-a")
    activations.ingest_capture(store, "exp", "cond", second, LAYER, "host-b")
    stored = list(store.read(activation_pb2.ActivationSlice,
                             "exp", "cond", "activations"))
    assert len(stored) == 4
    assert {record.key.item_id for record in stored} == {
        "item-x", "item-y", "item-z"}
    digests = {record.tensor.file_digest for record in stored}
    assert len(digests) == 2


def test_tensor_encoding_is_exact_in_both_regimes():
    # A bfloat16-computing model's float32 activations have a zero mantissa
    # tail: they must take the 2-byte path and round-trip bit-exactly. True
    # float32 arithmetic (pooled means) must stay float32, also bit-exact.
    clean = ((np.arange(12, dtype=np.uint32) << 16).view(np.float32)
             .reshape(3, 4))
    dtype, data = activations.encode_tensor(clean)
    assert dtype == "bfloat16" and len(data) == clean.size * 2
    ref = activation_pb2.TensorRef(dtype=dtype, data=data,
                                   shape=list(clean.shape))
    assert (activations.decode_tensor(ref) == clean).all()

    pooled = np.array([1.0, 1.0 / 3.0, np.pi], dtype=np.float32)
    dtype, data = activations.encode_tensor(pooled)
    assert dtype == "float32" and len(data) == pooled.size * 4
    ref = activation_pb2.TensorRef(dtype=dtype, data=data,
                                   shape=list(pooled.shape))
    assert (activations.decode_tensor(ref) == pooled).all()


def test_token_series_entries_become_records(tmp_path):
    path = tmp_path / "tok.safetensors"
    tensors = {
        f"item-x|s0|t1|L{LAYER}": E0 * 2.0,
        f"item-x|s0|t1|L{LAYER}|tokens": np.stack([E0, E0 * 3.0]),
    }
    manifest = {"point": "residual_post", "layers": [LAYER],
                "conversations": [{"id": "item-x|s0", "n_tokens": 8,
                                   "assistant_spans": [
                                       {"message_index": 1,
                                        "start": 0, "end": 2}]}]}
    save_file(tensors, str(path))
    path.with_name(path.name + ".manifest.json").write_text(
        json.dumps(manifest))
    slices, _ = activations.capture_records(
        path, "exp", "cond", LAYER, path.name, token_series=True)
    names = {record.tensor.tensor_name: record for record in slices}
    assert set(names) == set(tensors)
    assert list(names[f"item-x|s0|t1|L{LAYER}|tokens"].tensor.shape) == [2, 4]
    # Without the flag the |tokens entry stays out (the ingest default).
    pooled_only, _ = activations.capture_records(
        path, "exp", "cond", LAYER, path.name)
    assert len(pooled_only) == 1


def test_embedded_bundle_reads_like_the_file_backed_store(capture, tmp_path):
    # The single-file release form: embed the tensors into the bundle, delete
    # every side file, and the read bridge must reproduce the same features.
    from modelwelfare import bundle as bundle_module

    store = ResultStore(tmp_path / "data")
    activations.ingest_capture(store, "exp", "cond", capture, LAYER, "host-a")
    file_tensors, file_manifest = activations.condition_capture(
        store, "exp", "cond")

    packed = bundle_module.pack_experiment_store(store, "exp")
    assert bundle_module.embed_bundle(packed, store.root) == 3
    path = tmp_path / "release" / "exp.pb"
    bundle_module.write_bundle(packed, path)

    reader = bundle_module.BundleStore(path)
    inline_tensors, inline_manifest = activations.condition_capture(
        reader, "exp", "cond")
    assert set(inline_tensors) == set(file_tensors)
    for name in file_tensors:
        assert (inline_tensors[name] == file_tensors[name]).all(), name
    spans = {conv["id"]: conv["assistant_spans"]
             for conv in inline_manifest["conversations"]}
    assert spans == {conv["id"]: conv["assistant_spans"]
                     for conv in file_manifest["conversations"]}
    assert inline_manifest["layers"] == [LAYER]


def test_bundle_cli_inspect_and_extract_round_trip(capture, tmp_path, capsys):
    from modelwelfare import bundle as bundle_module

    store = ResultStore(tmp_path / "data")
    activations.ingest_capture(store, "exp", "cond", capture, LAYER, "host-a")
    packed = bundle_module.pack_experiment_store(store, "exp")
    bundle_module.embed_bundle(packed, store.root)
    path = tmp_path / "exp.pb"
    bundle_module.write_bundle(packed, path)

    bundle_module.main(["inspect", str(path)])
    listing = capsys.readouterr().out
    assert "exp/cond/activations: 3" in listing
    assert "embedded" in listing

    out = tmp_path / "restored"
    bundle_module.main(["extract", str(path), "--out", str(out),
                        "--uri", "cap"])
    restored, manifest = activations.load_capture(out / "cap.safetensors")
    original, _ = activations.load_capture(capture)
    assert set(restored) == set(original)
    for name in original:
        assert (restored[name] == original[name]).all(), name
    assert {conv["id"] for conv in manifest["conversations"]} == \
        {"item-x|s0", "item-y|s1"}


def test_bare_conversation_ids_survive_pack_and_extract(tmp_path, capsys):
    # Direction-extraction captures name conversations without the |sN
    # suffix; packing and extracting must reproduce the exact ids, because
    # the read functionals key tensors by them.
    from modelwelfare import bundle as bundle_module

    path = write_capture(tmp_path / "fixture.safetensors",
                         {"dir-axis-bread-neg": {1: E0 * 2.0}})
    slices, _ = activations.capture_records(
        path, "calibration", "fixture", LAYER, path.name)
    assert slices[0].key.item_id == "dir-axis-bread-neg"
    assert activations.record_conversation_id(slices[0]) == \
        "dir-axis-bread-neg"
    activations.embed_tensor_data(slices, tmp_path)
    packed = bundle_module.bundle_pb2.RecordBundle()
    packed.activations.extend(slices)
    bundle_path = tmp_path / "fixture.pb"
    bundle_module.write_bundle(packed, bundle_path)
    out = tmp_path / "restored"
    bundle_module.main(["extract", str(bundle_path), "--out", str(out)])
    restored, manifest = activations.load_capture(out / "fixture.safetensors")
    assert set(restored) == {f"dir-axis-bread-neg|t1|L{LAYER}"}
    assert manifest["conversations"][0]["id"] == "dir-axis-bread-neg"
