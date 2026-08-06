"""Result store framing and layout tests."""

import pytest

from modelwelfare.store import ResultStore, read_records
from modelwelfare.v1 import common_pb2, transcript_pb2


def sample(item_id, sample_index=0, content="x"):
    return transcript_pb2.SampleRecord(
        key=common_pb2.ResultKey(
            experiment_id="exp", condition_id="cond", item_id=item_id, sample_index=sample_index
        ),
        messages=[transcript_pb2.Message(role="assistant", content=content)],
    )


def test_roundtrip_and_append_across_sessions(tmp_path):
    store = ResultStore(tmp_path)
    with store.writer("exp", "cond", "samples", "mini-1") as writer:
        writer.write(sample("item-a"))
        writer.write(sample("item-b"))
    with store.writer("exp", "cond", "samples", "mini-1") as writer:
        writer.write(sample("item-c"))

    records = list(store.read(transcript_pb2.SampleRecord, "exp", "cond", "samples"))
    assert [r.key.item_id for r in records] == ["item-a", "item-b", "item-c"]


def test_multi_producer_merge(tmp_path):
    store = ResultStore(tmp_path)
    with store.writer("exp", "cond", "samples", "mini-2") as writer:
        writer.write(sample("from-mini-2"))
    with store.writer("exp", "cond", "samples", "mini-1") as writer:
        writer.write(sample("from-mini-1"))

    records = list(store.read(transcript_pb2.SampleRecord, "exp", "cond", "samples"))
    assert [r.key.item_id for r in records] == ["from-mini-1", "from-mini-2"]


def test_large_record_crosses_varint_width(tmp_path):
    store = ResultStore(tmp_path)
    big = sample("big", content="word " * 5000)
    with store.writer("exp", "cond", "samples", "p") as writer:
        writer.write(sample("small"))
        writer.write(big)
        writer.write(sample("after"))

    records = list(store.read(transcript_pb2.SampleRecord, "exp", "cond", "samples"))
    assert [r.key.item_id for r in records] == ["small", "big", "after"]
    assert records[1].messages[0].content == big.messages[0].content


def test_truncated_tail_raises(tmp_path):
    store = ResultStore(tmp_path)
    path = store.path("exp", "cond", "samples", "p")
    with store.writer("exp", "cond", "samples", "p") as writer:
        writer.write(sample("ok"))
        writer.write(sample("doomed", content="word " * 100))

    data = path.read_bytes()
    path.write_bytes(data[:-20])

    reader = read_records(path, transcript_pb2.SampleRecord)
    assert next(reader).key.item_id == "ok"
    with pytest.raises(ValueError, match="truncated"):
        next(reader)


def test_missing_condition_reads_empty(tmp_path):
    store = ResultStore(tmp_path)
    assert list(store.read(transcript_pb2.SampleRecord, "exp", "nope", "samples")) == []


def test_layout_paths(tmp_path):
    store = ResultStore(tmp_path)
    path = store.path("exp-1", "qwen3-8b-gptq-w4", "samples", "mini-1")
    assert path == tmp_path / "exp-1" / "qwen3-8b-gptq-w4" / "samples" / "mini-1.pb"
