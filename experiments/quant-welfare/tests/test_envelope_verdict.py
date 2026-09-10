"""Tests for tools/envelope_verdict.py — the random-envelope specificity read.

The envelope placement is pinned on values (percentile, two-sided
exceedance, +1 exceedance probability, envelope spread) and the store
path is exercised end-to-end over fabricated judge scores so the item
pairing, the shared-item rule, and the per-cell sample counts are the
ones the verdict reports.
"""
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parents[1]
if str(BASE / "tools") not in sys.path:
    sys.path.insert(0, str(BASE / "tools"))

import envelope_verdict as ev  # noqa: E402
from modelwelfare.store import ResultStore  # noqa: E402
from modelwelfare.v1 import scoring_pb2, transcript_pb2  # noqa: E402


def test_envelope_summary_values():
    envelope = {f"r{k}": v for k, v in enumerate([-0.5, -0.2, 0.0, 0.1, 0.3, 0.6, 0.9, 1.4])}
    summary = ev.envelope_summary(0.35, envelope)
    assert summary["envelope_n"] == 8
    assert summary["percentile"] == pytest.approx(100 * 5 / 8)
    assert summary["n_exceed"] == 4  # -0.5, 0.6, 0.9, 1.4
    assert summary["p_two_sided"] == pytest.approx(5 / 9)
    assert summary["envelope_absmax"] == pytest.approx(1.4)
    assert summary["envelope_mean"] == pytest.approx(sum(envelope.values()) / 8)


def test_envelope_summary_negative_effect_is_two_sided():
    envelope = {"a": 0.2, "b": -0.1, "c": 0.05}
    summary = ev.envelope_summary(-0.15, envelope)
    assert summary["percentile"] == pytest.approx(0.0)
    assert summary["n_exceed"] == 1


def test_envelope_summary_refuses_empty():
    with pytest.raises(ValueError):
        ev.envelope_summary(0.1, {})


def _write(store, experiment, condition, item_scores, samples=1):
    with store.writer(experiment, condition, "samples", "t") as writer:
        for item in item_scores:
            for index in range(samples):
                record = transcript_pb2.SampleRecord()
                record.key.experiment_id = experiment
                record.key.condition_id = condition
                record.key.item_id = item
                record.key.sample_index = index
                writer.write(record)
    with store.writer(experiment, condition, "scores", "t") as writer:
        for item, value in item_scores.items():
            for index in range(samples):
                score = scoring_pb2.JudgeScore()
                score.key.experiment_id = experiment
                score.key.condition_id = condition
                score.key.item_id = item
                score.key.sample_index = index
                score.rubric_id = "r"
                score.scores.add(dimension="frustration", value=value)
                score.scores.add(dimension="tone", value=10 - value)
                writer.write(score)


def test_verdict_over_store(tmp_path):
    store = ResultStore(str(tmp_path))
    exp = "e"
    _write(store, exp, "ref", {"i1": 2.0, "i2": 4.0, "i3": 3.0}, samples=2)
    _write(store, exp, "treat", {"i1": 3.0, "i2": 6.0, "i3": 3.0}, samples=2)
    _write(store, exp, "r0", {"i1": 2.0, "i2": 4.0, "i3": 3.5})
    _write(store, exp, "r1", {"i1": 2.5, "i2": 3.5, "i3": 3.0})
    _write(store, exp, "r2", {"i1": 1.0, "i2": 4.0, "i3": 2.0, "extra": 9.0})

    report = ev.verdict(store, exp, "ref", ["treat"], ["r0", "r1", "r2"])
    assert report["samples_per_item"]["ref"] == {"i1": 2, "i2": 2, "i3": 2}
    frustration = report["dimensions"]["frustration"]
    assert frustration["items"] == ["i1", "i2", "i3"]  # 'extra' is not shared
    treat = frustration["treatments"]["treat"]
    assert treat["effect"] == pytest.approx(1.0)
    assert treat["per_item_delta"] == {"i1": 1.0, "i2": 2.0, "i3": 0.0}
    assert frustration["envelope_per_direction"] == pytest.approx(
        {"r0": 0.5 / 3, "r1": 0.0, "r2": -2.0 / 3})
    assert treat["n_exceed"] == 0
    assert treat["percentile"] == pytest.approx(100.0)
    assert treat["p_two_sided"] == pytest.approx(1 / 4)
    assert treat["permutation"]["n"] == 3
    tone = report["dimensions"]["tone"]["treatments"]["treat"]
    assert tone["effect"] == pytest.approx(-1.0)


def test_verdict_explicit_items_refuse_missing(tmp_path):
    store = ResultStore(str(tmp_path))
    _write(store, "e", "ref", {"i1": 1.0})
    _write(store, "e", "treat", {"i1": 2.0})
    _write(store, "e", "r0", {"i1": 1.5})
    with pytest.raises(KeyError):
        ev.verdict(store, "e", "ref", ["treat"], ["r0"], items=["i1", "i9"])
