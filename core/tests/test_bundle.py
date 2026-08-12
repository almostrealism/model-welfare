"""Tests for the portable RecordBundle format (modelwelfare.bundle).

Pin the property that matters for a shareable format: packing the streaming
store and reading it back through BundleStore reproduces exactly the same records
(lossless round trip), and BundleStore's read filters by condition and kind like
the streaming store it stands in for.
"""

from modelwelfare import bundle
from modelwelfare.store import ResultStore
from modelwelfare.v1 import scoring_pb2, transcript_pb2


def _sample(cond, item, sidx, exp="exp"):
    r = transcript_pb2.SampleRecord()
    r.key.experiment_id, r.key.condition_id = exp, cond
    r.key.item_id, r.key.sample_index = item, sidx
    m = r.messages.add()
    m.role, m.content = "assistant", f"reply {item} {sidx}"
    r.provenance.host = "h"
    return r


def _score(cond, item, sidx, value):
    s = scoring_pb2.JudgeScore()
    s.key.experiment_id, s.key.condition_id = "exp", cond
    s.key.item_id, s.key.sample_index = item, sidx
    d = s.scores.add()
    d.dimension, d.value = "frustration", value
    return s


def _exit(cond, item, sidx):
    e = scoring_pb2.ExitClassification()
    e.key.experiment_id, e.key.condition_id = "exp", cond
    e.key.item_id, e.key.sample_index = item, sidx
    e.reason = scoring_pb2.EXIT_REASON_AVERSION
    return e


def _write_streaming_store(root):
    store = ResultStore(root)
    for cond in ("bf16", "w4"):
        with store.writer("exp", cond, "samples", "p") as w:
            for k in range(3):
                w.write(_sample(cond, f"i{k}", 0))
        with store.writer("exp", cond, "scores", "p") as w:
            w.write(_score(cond, "d0", 0, 5.0))
        with store.writer("exp", cond, "exit_reasons", "p") as w:
            w.write(_exit(cond, "i0", 0))
    return store


def _serialized_multiset(records):
    return sorted(r.SerializeToString(deterministic=True) for r in records)


def test_pack_round_trip_is_lossless(tmp_path):
    store = _write_streaming_store(tmp_path / "streaming")
    packed = bundle.pack_condition(store, "exp", "bf16")
    path = tmp_path / "bf16.pb"
    bundle.write_bundle(packed, path)

    reloaded = bundle.BundleStore(path)
    for kind, (_field, mtype) in bundle.KINDS.items():
        original = list(store.read(mtype, "exp", "bf16", kind))
        via_bundle = list(reloaded.read(mtype, "exp", "bf16", kind))
        assert _serialized_multiset(original) == _serialized_multiset(via_bundle), kind


def test_bundle_metadata_counts(tmp_path):
    store = _write_streaming_store(tmp_path / "streaming")
    packed = bundle.pack_condition(store, "exp", "bf16")
    assert dict(packed.metadata.record_counts) == {"samples": 3, "scores": 1, "exit_reasons": 1}
    assert packed.metadata.condition_id == "bf16"


def test_bundle_store_filters_by_condition(tmp_path):
    store = _write_streaming_store(tmp_path / "streaming")
    bundle.pack(store, _Experiment(["bf16", "w4"]), tmp_path / "bundles")
    reader = bundle.BundleStore(tmp_path / "bundles")
    bf16 = list(reader.read(transcript_pb2.SampleRecord, "exp", "bf16", "samples"))
    w4 = list(reader.read(transcript_pb2.SampleRecord, "exp", "w4", "samples"))
    assert len(bf16) == 3 and len(w4) == 3
    assert all(r.key.condition_id == "bf16" for r in bf16)


class _Experiment:
    """Minimal stand-in for the manifest object bundle.pack iterates."""
    def __init__(self, condition_ids):
        self.id = "exp"
        self.conditions = [type("C", (), {"id": cid}) for cid in condition_ids]


def test_whole_experiment_bundle_digest_matches_store(tmp_path):
    from modelwelfare import signature
    store = _write_streaming_store(tmp_path / "streaming")
    whole = bundle.pack_experiment(store, _Experiment(["bf16", "w4"]))
    expected = signature.store_digest(store, "exp", ["bf16", "w4"])["digest"]
    assert whole.metadata.data_digest == expected != ""


def test_bundle_store_scopes_by_experiment(tmp_path):
    # Two experiments share condition "bf16"; a merged directory must not leak
    # one experiment's records into a read scoped to the other.
    counts = {"A": 2, "B": 3}
    for exp, n in counts.items():
        store = ResultStore(tmp_path / exp)
        with store.writer(exp, "bf16", "samples", "p") as w:
            for k in range(n):
                w.write(_sample("bf16", f"i{k}", 0, exp=exp))
        bundle.write_bundle(bundle.pack_condition(store, exp, "bf16"), tmp_path / "merged" / f"{exp}.pb")

    reader = bundle.BundleStore(tmp_path / "merged")
    a = list(reader.read(transcript_pb2.SampleRecord, "A", "bf16", "samples"))
    b = list(reader.read(transcript_pb2.SampleRecord, "B", "bf16", "samples"))
    assert len(a) == 2 and len(b) == 3
    assert all(r.key.experiment_id == "A" for r in a)
    assert all(r.key.experiment_id == "B" for r in b)
