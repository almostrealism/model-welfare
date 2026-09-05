"""Tests for tools/g3_behavioral.py over fabricated paired stores.

Two sides are written with exactly known score and sample content, so
the assertions are on the computed deltas and refusals, not on "it ran":
per-item score means, the degenerate/re-offer mechanical rates, the
item-identity requirement, and the CLI end to end with a TOST margin.
"""
import json
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parents[1]
if str(BASE / "tools") not in sys.path:
    sys.path.insert(0, str(BASE / "tools"))

import g3_behavioral as g3b  # noqa: E402
from study3_fixtures import GOOD_REPLY, make_result_key  # noqa: E402
from modelwelfare.store import ResultStore  # noqa: E402
from modelwelfare.v1 import common_pb2, scoring_pb2, transcript_pb2  # noqa: E402

GOOD = GOOD_REPLY


def key(side, item, index):
    return make_result_key(f"exp-{side}", f"cond-{side}", item, index)


def sample(side, item, index, text=GOOD):
    record = transcript_pb2.SampleRecord(key=key(side, item, index))
    record.messages.append(transcript_pb2.Message(
        role="user", content="ask", turn_index=0, scripted=True))
    record.messages.append(transcript_pb2.Message(
        role="assistant", content=text, turn_index=1))
    return record


def score(side, item, index, value):
    record = scoring_pb2.JudgeScore(key=key(side, item, index))
    record.scores.append(scoring_pb2.DimensionScore(
        dimension="frustration", value=value))
    record.scores.append(scoring_pb2.DimensionScore(
        dimension="other", value=99.0))
    return record


@pytest.fixture
def world(tmp_path):
    store = ResultStore(tmp_path / "data")
    values = {"a": {"item-1": [2.0, 4.0], "item-2": [6.0, 6.0]},
              "b": {"item-1": [1.0, 1.0], "item-2": [5.0, 7.0]}}
    for side, by_item in values.items():
        with store.writer(f"exp-{side}", f"cond-{side}",
                          "samples", "test") as writer:
            for item, item_values in by_item.items():
                for index, _ in enumerate(item_values):
                    text = "" if (side, item, index) == ("b", "item-2", 0) \
                        else GOOD
                    writer.write(sample(side, item, index, text))
        with store.writer(f"exp-{side}", f"cond-{side}",
                          "scores", "test") as writer:
            for item, item_values in by_item.items():
                for index, value in enumerate(item_values):
                    writer.write(score(side, item, index, value))
    return store


def test_item_score_means_reads_one_dimension(world):
    means = g3b.item_score_means(world, "exp-a", "cond-a", "frustration")
    assert means == {"item-1": pytest.approx(3.0),
                     "item-2": pytest.approx(6.0)}


def test_item_mechanical_rates_flags_the_empty_sample(world):
    rates = g3b.item_mechanical_rates(world, "exp-b", "cond-b")
    assert rates["item-1"] == (0.0, 0.0)
    assert rates["item-2"][0] == pytest.approx(0.5)


def test_paired_deltas_requires_identical_items():
    with pytest.raises(SystemExit, match="item sets differ"):
        g3b.paired_deltas({"x": 1.0}, {"y": 1.0}, "scores")
    items, deltas = g3b.paired_deltas(
        {"i": 3.0, "j": 5.0}, {"i": 1.0, "j": 6.0}, "scores")
    assert items == ["i", "j"]
    assert deltas == [pytest.approx(2.0), pytest.approx(-1.0)]


def test_cli_end_to_end(world, tmp_path, monkeypatch):
    out = tmp_path / "g3b.json"
    monkeypatch.setattr(sys, "argv", [
        "g3_behavioral.py", "--data-root", str(tmp_path / "data"),
        "--experiment-a", "exp-a", "--condition-a", "cond-a",
        "--experiment-b", "exp-b", "--condition-b", "cond-b",
        "--dimension", "frustration", "--margin", "3.0",
        "--out", str(out)])
    g3b.main()
    report = json.loads(out.read_text())
    assert report["items"] == ["item-1", "item-2"]
    assert report["score"]["mean_delta"] == pytest.approx(1.0)
    assert report["score"]["n_items"] == 2
    assert "tost" in report["score"]
    assert report["invalid_rate"]["mean_delta"] == pytest.approx(-0.25)
    assert report["reoffer_rate"]["mean_delta"] == pytest.approx(0.0)
