"""Tests for the replication signature (modelwelfare.signature).

Pin the two properties that make the digest a usable replication check: it is
independent of record order (and therefore file layout) and of provenance, but
sensitive to any change in report-determining content.
"""

from modelwelfare import signature
from modelwelfare.v1 import transcript_pb2


def sample(item, sidx, text="hello", host="host-a", tokens=10):
    record = transcript_pb2.SampleRecord()
    record.key.experiment_id, record.key.condition_id = "exp", "cond"
    record.key.item_id, record.key.sample_index = item, sidx
    message = record.messages.add()
    message.role, message.content = "assistant", text
    record.usage.completion_tokens = tokens
    record.provenance.host = host
    return record


def test_kind_digest_is_order_independent():
    records = [sample(f"i{k}", 0) for k in range(6)]
    assert signature.kind_digest(records) == signature.kind_digest(list(reversed(records)))


def test_kind_digest_ignores_provenance():
    a = [sample("i0", 0, host="machine-a")]
    b = [sample("i0", 0, host="machine-b")]  # identical content, different provenance
    assert signature.kind_digest(a) == signature.kind_digest(b)


def test_kind_digest_detects_content_change():
    base = [sample("i0", 0, text="original")]
    changed = [sample("i0", 0, text="tampered")]
    assert signature.kind_digest(base) != signature.kind_digest(changed)


def test_kind_digest_detects_missing_or_extra_record():
    two = [sample("i0", 0), sample("i1", 0)]
    one = [sample("i0", 0)]
    assert signature.kind_digest(two) != signature.kind_digest(one)
