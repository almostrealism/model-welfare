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

    report = ev.verdict(store, exp, "ref", ["treat"], ["r0", "r1", "r2"],
                        treatment_doses={"treat": 1.0}, envelope_dose_declared=1.0)
    assert report["envelope_dose"] == 1.0
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


def test_condition_dose_parsing():
    assert ev.condition_dose("qwen3.6-27b-bf16-torch-graderL36-a20") == 20.0
    assert ev.condition_dose("qwen3-4b-bf16-torch-randL18-a1.039-r07") == 1.039
    assert ev.condition_dose("qwen3-4b-bf16-torch-alpha1039") is None
    assert ev.condition_dose("ref") is None
    assert ev.envelope_dose(["x-randL36-a20-r00", "x-randL36-a20-r01"]) == 20.0
    assert ev.envelope_dose(["r0", "r1"]) is None
    with pytest.raises(ValueError, match="mixes doses"):
        ev.envelope_dose(["x-randL36-a20-r00", "x-randL36-a40-r01"])


def test_treatment_at_another_dose_gets_no_placement(tmp_path):
    store = ResultStore(str(tmp_path))
    exp = "e"
    _write(store, exp, "ref", {"i1": 2.0, "i2": 4.0}, samples=2)
    _write(store, exp, "m-graderL36-a20", {"i1": 3.0, "i2": 5.0}, samples=2)
    _write(store, exp, "m-graderL36-a40", {"i1": 4.0, "i2": 6.0}, samples=2)
    _write(store, exp, "m-alpha", {"i1": 3.5, "i2": 5.5}, samples=2)
    env = ["m-randL36-a20-r00", "m-randL36-a20-r01"]
    _write(store, exp, env[0], {"i1": 2.5, "i2": 4.0})
    _write(store, exp, env[1], {"i1": 2.0, "i2": 4.5})
    report = ev.verdict(store, exp, "ref", ["m-graderL36-a20", "m-graderL36-a40"], env)
    assert report["envelope_dose"] == 20.0
    same = report["dimensions"]["frustration"]["treatments"]["m-graderL36-a20"]
    other = report["dimensions"]["frustration"]["treatments"]["m-graderL36-a40"]
    assert same["dose"] == 20.0 and "percentile" in same
    assert other["dose"] == 40.0 and other["envelope"] is None
    assert "differs from the envelope dose 20.0" in other["note"]
    assert other["effect"] == pytest.approx(2.0) and "permutation" in other
    # a treatment whose id names no dose must be given one
    with pytest.raises(ValueError, match="no dose in the id"):
        ev.verdict(store, exp, "ref", ["m-alpha"], env)
    placed = ev.verdict(store, exp, "ref", ["m-alpha"], env, treatment_doses={"m-alpha": 20})
    assert placed["dimensions"]["frustration"]["treatments"]["m-alpha"]["dose"] == 20.0
    assert "percentile" in placed["dimensions"]["frustration"]["treatments"]["m-alpha"]


def test_verdict_explicit_items_refuse_missing(tmp_path):
    store = ResultStore(str(tmp_path))
    _write(store, "e", "ref", {"i1": 1.0})
    _write(store, "e", "treat", {"i1": 2.0})
    _write(store, "e", "r0", {"i1": 1.5})
    with pytest.raises(KeyError):
        ev.verdict(store, "e", "ref", ["treat"], ["r0"], items=["i1", "i9"],
                   treatment_doses={"treat": 1.0}, envelope_dose_declared=1.0)


def test_envelope_dose_must_be_known_and_consistent(tmp_path):
    store = ResultStore(str(tmp_path))
    _write(store, "e", "ref", {"i1": 1.0})
    _write(store, "e", "treat", {"i1": 2.0})
    _write(store, "e", "r0", {"i1": 1.5})
    # ids that name no dose: the envelope's dose must be declared
    with pytest.raises(ValueError, match="name no dose and none was given"):
        ev.verdict(store, "e", "ref", ["treat"], ["r0"], treatment_doses={"treat": 1.0})
    # a declared dose that contradicts the ids is refused
    with pytest.raises(ValueError, match="name dose 20.0 but --envelope-dose says 40"):
        ev.resolve_envelope_dose(["x-randL36-a20-r00"], declared=40)
    assert ev.resolve_envelope_dose(["x-randL36-a20-r00"], declared=20) == 20.0
    assert ev.resolve_envelope_dose(["r0"], declared=2.5) == 2.5
