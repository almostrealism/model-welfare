"""Tests for tools/pack_bundles.py's experiment selection over a fabricated
store: the ``--exclude`` globs keep a later study's collection out of a
release, the excluded experiments leave no trace in the combined bundle's
digest map, and a selection that empties the store is refused."""
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parents[1]
if str(BASE / "tools") not in sys.path:
    sys.path.insert(0, str(BASE / "tools"))

import pack_bundles  # noqa: E402
from modelwelfare import bundle  # noqa: E402
from modelwelfare.store import ResultStore  # noqa: E402
from modelwelfare.v1 import transcript_pb2  # noqa: E402


def _write_samples(store, experiment_id, condition_id, count):
    with store.writer(experiment_id, condition_id, "samples", "t") as writer:
        for index in range(count):
            record = transcript_pb2.SampleRecord()
            record.key.experiment_id = experiment_id
            record.key.condition_id = condition_id
            record.key.item_id, record.key.sample_index = "item-a", index
            record.messages.add(role="assistant", turn_index=1,
                                content="a reply " * 8)
            writer.write(record)


@pytest.fixture
def store(tmp_path):
    store = ResultStore(str(tmp_path / "data"))
    _write_samples(store, "s3-pilot-1", "bf16", 2)
    _write_samples(store, "s3-pilot-2", "bf16", 3)
    _write_samples(store, "s4-gate1-1", "bf16", 4)
    return store


def test_select_without_exclusions_is_the_whole_store(store):
    assert set(pack_bundles.select_experiments(store)) == {
        "s3-pilot-1", "s3-pilot-2", "s4-gate1-1"}


def test_exclude_glob_drops_matching_experiments(store):
    selected = pack_bundles.select_experiments(store, ["s4-*"])
    assert set(selected) == {"s3-pilot-1", "s3-pilot-2"}


def test_exclude_globs_accumulate(store):
    selected = pack_bundles.select_experiments(store, ["s4-*", "*-pilot-2"])
    assert selected == ["s3-pilot-1"]


def test_excluding_everything_is_refused(store):
    with pytest.raises(ValueError, match="no experiment to pack"):
        pack_bundles.select_experiments(store, ["s3-*", "s4-*"])


def test_empty_store_is_refused(tmp_path):
    with pytest.raises(ValueError, match="no experiments"):
        pack_bundles.select_experiments(ResultStore(str(tmp_path / "empty")))


def test_release_layout_carries_only_selected_digests(store, tmp_path):
    selected = pack_bundles.select_experiments(store, ["s4-*"])
    paths = pack_bundles.pack_release(store, selected, tmp_path / "release",
                                      "records", bundle.VOLUME_BYTES)
    assert [path.name for path in paths] == ["records.pb"]
    metadata = bundle.read_bundle(paths[0]).metadata
    assert set(metadata.experiment_digests) == {"s3-pilot-1", "s3-pilot-2"}
    assert metadata.record_counts["samples"] == 5
