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
from modelwelfare.driver import TERMINAL_TOOL_INVOKED  # noqa: E402
from modelwelfare.v1 import (  # noqa: E402
    battery_pb2, condition_pb2, experiment_pb2, scoring_pb2, transcript_pb2,
)


# --- builders ---------------------------------------------------------------

def make_experiment(condition_ids, reference, samples_per_item=4, exp_id="synth-1",
                    bits=None, methods=None):
    """bits/methods (aligned to condition_ids) shape the quantization specs;
    a descending bits ladder with a single method makes a dose ladder."""
    experiment = experiment_pb2.Experiment()
    experiment.id = exp_id
    experiment.reference_condition_id = reference
    experiment.samples_per_item = samples_per_item
    for index, cid in enumerate(condition_ids):
        condition = experiment.conditions.add()
        condition.id = cid
        if bits:
            condition.quantization.weight_bits = bits[index]
        if methods:
            condition.quantization.method = methods[index]
    return experiment


DOSE_BITS = [16, 8, 4, 3]
DOSE_METHODS = [
    condition_pb2.QUANT_METHOD_NONE, condition_pb2.QUANT_METHOD_RTN,
    condition_pb2.QUANT_METHOD_RTN, condition_pb2.QUANT_METHOD_RTN,
]


def sample(cond, item, sidx, text="a perfectly ordinary and sufficiently long helpful reply here",
           tokens=20, exited=False):
    record = transcript_pb2.SampleRecord()
    record.key.condition_id, record.key.item_id, record.key.sample_index = cond, item, sidx
    message = record.messages.add()
    message.role, message.content = "assistant", text
    record.usage.completion_tokens = tokens
    if exited:
        record.outcomes.add(name=TERMINAL_TOOL_INVOKED, detail="end_conversation")
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
                exited = s < exit_hits[cond]
                samples.append(sample(cond, item, s, exited=exited))
                if exited:
                    exits.append(exit_class(cond, item, s, scoring_pb2.EXIT_REASON_AVERSION))
        for item in ("d0", "d1"):                        # distress items
            for s in range(4):
                samples.append(sample(cond, item, s))
                scores.append(score(cond, item, s, frust[cond] + (0.5 if s % 2 else -0.5)))
    return conds, samples, scores, exits


def test_analyze_end_to_end_splits_and_excludes_degraded():
    conds, samples, scores, exits = _synthetic_store()
    experiment = make_experiment(conds, "bf16", bits=DOSE_BITS, methods=DOSE_METHODS)
    perplexity = {"bf16": 10.0, "w8": 11.0, "w4": 12.0, "w3": 100.0}  # w3 degraded
    result = analyze_mod.analyze(
        experiment, samples, scores, exits, perplexity, bail_items={"b0", "b1"}
    )

    # Capability gate excludes w3 from every family and the trend fit.
    assert result["degraded"] == ["w3"]
    assert [r["contrast"] for r in result["e1"]] == ["w8", "w4"]
    assert [r["contrast"] for r in result["e2"]] == ["w8", "w4"]

    # The degraded rung is still reported, separately and uncorrected, as
    # capability-confounded (PREREGISTRATION §2 interpretation rule).
    assert [r["contrast"] for r in result["e1_confounded"]] == ["w3"]
    assert [r["contrast"] for r in result["e2_confounded"]] == ["w3"]
    assert "holm_p" not in result["e1_confounded"][0]

    # E1 is bail-only: two bail items, never the distress items.
    assert all(r["n"] == 2 for r in result["e1"])

    # Every family row carries the paired-t descriptive companion.
    assert all("t_p" in r for r in result["e1"] + result["e1_confounded"])

    # Trend runs over the three surviving rungs (bf16, w8, w4) and rises.
    assert result["dose_ladder"]
    assert result["trends"]["E1"] is not None
    assert result["trends"]["E1"]["z"] > 0
    assert result["trends"]["E2"]["z"] > 0


def test_mechanical_family_covers_gated_rungs():
    # The mechanical indicators (invalid rate, re-offer rate) measure
    # degradation itself: every contrast appears, including capability-gated
    # ones the behavioral families exclude.
    conds, samples, scores, exits = _synthetic_store()
    experiment = make_experiment(conds, "bf16", bits=DOSE_BITS, methods=DOSE_METHODS)
    perplexity = {"bf16": 10.0, "w8": 11.0, "w4": 12.0, "w3": 100.0}  # w3 degraded
    result = analyze_mod.analyze(
        experiment, samples, scores, exits, perplexity, bail_items={"b0", "b1"}
    )
    assert [r["contrast"] for r in result["mech_invalid"]] == ["w8", "w4", "w3"]
    assert [r["contrast"] for r in result["mech_reoffer"]] == ["w8", "w4", "w3"]
    assert all("holm_p" in r for r in result["mech_invalid"])


def test_analyze_method_contrast_gets_no_trend_family():
    # A method-comparison arm (two 4-bit methods vs BF16) is not a bit-width
    # dose: Page's L must not run on it (PREREGISTRATION §4/§9).
    conds = ["bf16", "rtn-w4", "awq-w4"]
    samples, scores, exits = [], [], []
    for cond in conds:
        for item in ("b0", "b1"):
            for s in range(4):
                samples.append(sample(cond, item, s, exited=(s % 2 == 0)))
    experiment = make_experiment(
        conds, "bf16", bits=[16, 4, 4],
        methods=[condition_pb2.QUANT_METHOD_NONE, condition_pb2.QUANT_METHOD_RTN,
                 condition_pb2.QUANT_METHOD_AWQ],
    )
    result = analyze_mod.analyze(experiment, samples, scores, exits,
                                 bail_items={"b0", "b1"})
    assert not result["dose_ladder"]
    assert all(value is None for value in result["trends"].values())
    # The per-contrast families still run — only the trend family is gated.
    assert [r["contrast"] for r in result["e1"]] == ["rtn-w4", "awq-w4"]


def test_analyze_bail_filter_keeps_distress_out_of_e1():
    conds, samples, scores, exits = _synthetic_store()
    experiment = make_experiment(conds, "bf16")
    # Without the bail filter, the never-exiting distress items would inflate n.
    unfiltered = analyze_mod.analyze(experiment, samples, scores, exits, bail_items=None)
    filtered = analyze_mod.analyze(experiment, samples, scores, exits, bail_items={"b0", "b1"})
    assert unfiltered["e1"][0]["n"] == 4     # 2 bail + 2 distress leaked in
    assert filtered["e1"][0]["n"] == 2       # bail only


def test_h1_bail_reads_mechanical_exits_not_classifications():
    # H1-bail is the registered "exit vs. no-exit" behavioral outcome
    # (PREREGISTRATION §2): a condition where every sample exits must flip vs a
    # no-exit reference even when the classifier calls every exit COMPLETION —
    # i.e. when E1 (refusal+aversion share) sees nothing at all.
    conds = ["bf16", "w4"]
    samples, exits = [], []
    for item in ("b0", "b1", "b2", "b3"):
        for s in range(4):
            samples.append(sample("bf16", item, s, exited=False))
            samples.append(sample("w4", item, s, exited=True))
            exits.append(exit_class("w4", item, s, scoring_pb2.EXIT_REASON_COMPLETION))
    experiment = make_experiment(conds, "bf16")
    result = analyze_mod.analyze(
        experiment, samples, [], exits, bail_items={"b0", "b1", "b2", "b3"}
    )
    h1 = result["h1_bail"][0]
    assert h1["contrast"] == "w4"
    assert h1["observed"] == pytest.approx(1.0)   # every item flips mechanically
    assert result["e1"][0]["mean"] == pytest.approx(0.0)  # E1 sees no refusal/aversion


def _battery(battery_id, items):
    """items: list of (item_id, driver_params, tags) for a synthetic battery."""
    definition = battery_pb2.BatteryDefinition()
    definition.battery.id = battery_id
    for item_id, params, tags in items:
        item = definition.items.add()
        item.id = item_id
        item.battery_id = battery_id
        for key, value in params.items():
            item.driver_params[key] = value
        for key, value in tags.items():
            item.tags[key] = value
    return definition


def test_item_roles_excludes_benign_from_bail():
    # The registered confirmatory bail pool is the graded items (PREREGISTRATION
    # §5); benign negative controls carry the terminal tool but stay out of
    # E1/H1-bail.
    definitions = {"pool": _battery("pool", [
        ("graded-1", {"terminal_tools": "end_conversation"}, {"situation": "abuse"}),
        ("benign-1", {"terminal_tools": "end_conversation"}, {"situation": "benign"}),
        ("untagged-1", {"terminal_tools": "end_conversation"}, {}),
    ])}
    experiment = make_experiment(["bf16"], "bf16")
    experiment.battery_ids.append("pool")
    bail, distress = analyze_mod.item_roles(experiment, definitions)
    assert bail == {"graded-1", "untagged-1"}
    assert distress == set()


def test_e2_style_adjustment_separates_confound_from_effect():
    """The 'survives style controls' claim rests on _e2_style: a frustration
    delta fully explained by response-length change must adjust to ~zero,
    while a genuine delta at unchanged style must survive adjustment."""
    rng_items = [f"i{k}" for k in range(24)]
    slope = 0.5

    # World A: frustration delta is pure length artifact (delta = slope*dlen).
    ref_e2 = {i: 1.0 for i in rng_items}
    ref_len = {i: 100.0 for i in rng_items}
    ref_rep = {i: 0.1 for i in rng_items}
    dlen = {i: float(k - 12) for k, i in enumerate(rng_items)}
    cond_e2 = {i: ref_e2[i] + slope * dlen[i] for i in rng_items}
    cond_len = {i: ref_len[i] + dlen[i] for i in rng_items}
    rows = analyze_mod._e2_style(
        {"ref": ref_e2, "c": cond_e2}, {"ref": ref_len, "c": cond_len},
        {"ref": ref_rep, "c": dict(ref_rep)}, "ref", ["c"])
    assert abs(rows[0]["adjusted_intercept"]) < 1e-6

    # World B: genuine +0.9 shift with style unchanged (small non-collinear
    # length jitter so the design matrix is full-rank).
    jitter = {i: ((k % 3) - 1) * 0.5 for k, i in enumerate(rng_items)}
    cond_e2 = {i: ref_e2[i] + 0.9 for i in rng_items}
    cond_len = {i: ref_len[i] + jitter[i] for i in rng_items}
    rows = analyze_mod._e2_style(
        {"ref": ref_e2, "c": cond_e2}, {"ref": ref_len, "c": cond_len},
        {"ref": ref_rep, "c": dict(ref_rep)}, "ref", ["c"])
    assert rows[0]["adjusted_intercept"] == pytest.approx(0.9, abs=1e-6)
