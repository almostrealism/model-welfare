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
