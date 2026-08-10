"""Tests for the confirmatory analysis driver (analyze.py).

The driver is a thin wiring over the tested stats primitives, so these tests
pin the wiring the primitives cannot: the hierarchical family assembly, the
bail/distress endpoint split, and the capability-gate exclusion of degraded
rungs. The end-to-end correctness against a real store is exercised separately
by running analyze.py against the ladder-calibration store.
"""

import importlib.util
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parents[1]


def _load_analyze():
    spec = importlib.util.spec_from_file_location("analyze", BASE / "analyze.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


analyze_mod = _load_analyze()
from modelwelfare.v1 import experiment_pb2, scoring_pb2, transcript_pb2  # noqa: E402


# --- builders ---------------------------------------------------------------

def make_experiment(condition_ids, reference, samples_per_item=4, exp_id="synth-1"):
    experiment = experiment_pb2.Experiment()
    experiment.id = exp_id
    experiment.reference_condition_id = reference
    experiment.samples_per_item = samples_per_item
    for cid in condition_ids:
        experiment.conditions.add().id = cid
    return experiment


def sample(cond, item, sidx, text="a perfectly ordinary and sufficiently long helpful reply here",
           tokens=20):
    record = transcript_pb2.SampleRecord()
    record.key.condition_id, record.key.item_id, record.key.sample_index = cond, item, sidx
    message = record.messages.add()
    message.role, message.content = "assistant", text
    record.usage.completion_tokens = tokens
    return record


def score(cond, item, sidx, frustration):
    js = scoring_pb2.JudgeScore()
    js.key.condition_id, js.key.item_id, js.key.sample_index = cond, item, sidx
    dim = js.scores.add()
    dim.dimension, dim.value = "frustration", float(frustration)
    return js


def exit_class(cond, item, sidx, reason):
    ec = scoring_pb2.ExitClassification()
    ec.key.condition_id, ec.key.item_id, ec.key.sample_index = cond, item, sidx
    ec.reason = reason
    return ec


# --- dict-level wiring ------------------------------------------------------

def test_paired_deltas_only_over_shared_items():
    ref = {"a": 1.0, "b": 2.0, "c": 3.0}
    cond = {"a": 2.0, "b": 2.0}  # c missing -> dropped
    assert analyze_mod.paired_deltas(ref, cond) == [1.0, 0.0]


def test_run_family_holm_corrects_within_family():
    # Two contrasts: one all-positive (significant), one symmetric (null).
    value_by_condition = {
        "ref": {f"i{k}": 0.0 for k in range(8)},
        "up": {f"i{k}": 1.0 for k in range(8)},
        "flat": {f"i{k}": (1.0 if k % 2 else -1.0) for k in range(8)},
    }
    rows = analyze_mod.run_family(value_by_condition, "ref", ["up", "flat"])
    up = next(r for r in rows if r["contrast"] == "up")
    flat = next(r for r in rows if r["contrast"] == "flat")
    assert up["holm_p"] >= up["p"]          # Holm never shrinks a p-value
    assert up["holm_p"] < 0.05              # the real effect survives correction
    assert flat["p"] > 0.5                  # the null contrast is not significant


def test_trend_requires_three_rungs():
    values = {("bf16", "i"): 1.0, ("w4", "i"): 2.0}
    assert analyze_mod.trend(values, ["bf16", "w4"]) is None
    three = {("bf16", "i"): 1.0, ("w8", "i"): 2.0, ("w4", "i"): 3.0}
    result = analyze_mod.trend(three, ["bf16", "w8", "w4"])
    assert result is not None and result["n"] == 1


# --- end-to-end wiring ------------------------------------------------------

def _synthetic_store():
    """Two bail items and two distress items across a four-rung ladder, with a
    clear E1 signal on the quantized rungs and frustration rising with bit-width
    reduction."""
    conds = ["bf16", "w8", "w4", "w3"]
    exit_hits = {"bf16": 0, "w8": 1, "w4": 2, "w3": 3}   # aversion exits / 4 samples
    frust = {"bf16": 2.0, "w8": 3.0, "w4": 5.0, "w3": 7.0}
    samples, scores, exits = [], [], []
    for cond in conds:
        for item in ("b0", "b1"):                        # bail items
            for s in range(4):
                samples.append(sample(cond, item, s))
                if s < exit_hits[cond]:
                    exits.append(exit_class(cond, item, s, scoring_pb2.EXIT_REASON_AVERSION))
        for item in ("d0", "d1"):                        # distress items
            for s in range(4):
                samples.append(sample(cond, item, s))
                scores.append(score(cond, item, s, frust[cond] + (0.5 if s % 2 else -0.5)))
    return conds, samples, scores, exits


def test_analyze_end_to_end_splits_and_excludes_degraded():
    conds, samples, scores, exits = _synthetic_store()
    experiment = make_experiment(conds, "bf16")
    perplexity = {"bf16": 10.0, "w8": 11.0, "w4": 12.0, "w3": 100.0}  # w3 degraded
    result = analyze_mod.analyze(
        experiment, samples, scores, exits, perplexity, bail_items={"b0", "b1"}
    )

    # Capability gate excludes w3 from every family and the trend fit.
    assert result["degraded"] == ["w3"]
    assert [r["contrast"] for r in result["e1"]] == ["w8", "w4"]
    assert [r["contrast"] for r in result["e2"]] == ["w8", "w4"]

    # E1 is bail-only: two bail items, never the distress items.
    assert all(r["n"] == 2 for r in result["e1"])

    # Trend runs over the three surviving rungs (bf16, w8, w4) and rises.
    assert result["trends"]["E1"] is not None
    assert result["trends"]["E1"]["z"] > 0
    assert result["trends"]["E2"]["z"] > 0


def test_analyze_bail_filter_keeps_distress_out_of_e1():
    conds, samples, scores, exits = _synthetic_store()
    experiment = make_experiment(conds, "bf16")
    # Without the bail filter, the never-exiting distress items would inflate n.
    unfiltered = analyze_mod.analyze(experiment, samples, scores, exits, bail_items=None)
    filtered = analyze_mod.analyze(experiment, samples, scores, exits, bail_items={"b0", "b1"})
    assert unfiltered["e1"][0]["n"] == 4     # 2 bail + 2 distress leaked in
    assert filtered["e1"][0]["n"] == 2       # bail only
