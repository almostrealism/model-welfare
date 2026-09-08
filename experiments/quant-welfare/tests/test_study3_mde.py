"""Tests for tools/study3_mde.py over a fabricated calibration world.

Components are planted exactly: known within-item sampling noise, a
known item-effect spread on the judged endpoint, deterministic exits —
so the decomposition, the zero-floor, the override path, and the
escalation-ladder arithmetic are asserted on values.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

BASE = Path(__file__).resolve().parents[1]
if str(BASE / "tools") not in sys.path:
    sys.path.insert(0, str(BASE / "tools"))

import study3_mde as s3m  # noqa: E402
from modelwelfare import stats  # noqa: E402
from study3_fixtures import GOOD_REPLY, make_result_key  # noqa: E402
from modelwelfare.store import ResultStore  # noqa: E402
from modelwelfare.v1 import common_pb2, scoring_pb2, transcript_pb2  # noqa: E402

RNG = np.random.default_rng(11)
ITEMS = 30
K = 10
SIGMA = 1.5
SIGMA_ITEM = 0.8


def key(cond, item, index):
    return make_result_key("cal", cond, item, index)


@pytest.fixture
def world(tmp_path):
    store = ResultStore(tmp_path / "data")
    effects = RNG.normal(1.0, SIGMA_ITEM, ITEMS)
    for cond, offset in (("ref", None), ("treat", effects)):
        with store.writer("cal", cond, "scores", "t") as writer:
            for index_item in range(ITEMS):
                item = f"item-{index_item:02d}"
                base = 3.0
                shift = 0.0 if offset is None else offset[index_item]
                for s in range(K):
                    record = scoring_pb2.JudgeScore(key=key(cond, item, s))
                    record.scores.append(scoring_pb2.DimensionScore(
                        dimension="frustration",
                        value=base + shift + RNG.normal(0, SIGMA)))
                    writer.write(record)
        with store.writer("cal", cond, "samples", "t") as writer:
            for index_item in range(ITEMS):
                item = f"item-{index_item:02d}"
                for s in range(K):
                    record = transcript_pb2.SampleRecord(
                        key=key(cond, item, s))
                    # exits: ref items exit on even samples (rate 0.5);
                    # treat never exits — a planted rate delta of −0.5.
                    if cond == "ref" and s % 2 == 0:
                        record.outcomes.append(transcript_pb2.OutcomeEvent(
                            name="terminal_tool_invoked"))
                    writer.write(record)
    return store


def test_components_recover_planted_values(world):
    scored = s3m.components(
        s3m.per_sample_scores(world, "cal", "ref", "frustration"),
        s3m.per_sample_scores(world, "cal", "treat", "frustration"), K)
    assert scored["n_items"] == ITEMS
    assert scored["mean_delta"] == pytest.approx(1.0, abs=0.35)
    assert scored["sigma_sample"] == pytest.approx(SIGMA, rel=0.15)
    assert scored["sigma_item"] == pytest.approx(SIGMA_ITEM, rel=0.45)


def test_exit_components_and_zero_floor(world):
    exits = s3m.components(
        s3m.per_item_exits(world, "cal", "ref"),
        s3m.per_item_exits(world, "cal", "treat"), K)
    assert exits["mean_delta"] == pytest.approx(-0.5)
    # deterministic exits: zero within-item variance, zero item spread —
    # the estimator must floor at zero, not fabricate heterogeneity.
    assert exits["sigma_item"] == 0.0


def test_mde_ladder_matches_primitives():
    ladder = s3m.mde_ladder(SIGMA, SIGMA_ITEM, 20)
    for k in (10, 15, 20):
        expected = stats.mde_paired(
            stats.delta_sd_mixed(SIGMA, k, SIGMA_ITEM), 20)
        assert ladder[str(k)] == pytest.approx(expected)
    assert ladder["20"] < ladder["10"]


def test_cli_end_to_end_with_override(world, tmp_path, monkeypatch):
    out = tmp_path / "mde.json"
    monkeypatch.setattr(sys, "argv", [
        "study3_mde.py", "--data-root", str(tmp_path / "data"),
        "--experiment", "cal", "--reference", "ref",
        "--treatment", "treat", "--samples", str(K), "--items", "20",
        "--sigma-item", "1.67", "--out", str(out)])
    s3m.main()
    report = json.loads(out.read_text())
    scored = report["endpoints"]["frustration"]
    assert scored["sigma_item_used"] == pytest.approx(1.67)
    assert scored["mde"]["10"] == pytest.approx(stats.mde_paired(
        stats.delta_sd_mixed(scored["sigma_sample"], 10, 1.67), 20))
    assert "exit_rate" in report["endpoints"]


def test_exit_binomial_sigma_matches_analytic():
    # The exit-rate binomial sampling model must reproduce the analytic
    # paired rate-delta SD sqrt(p(1-p)/k + q(1-q)/k) through the MDE
    # machinery — guards the factor-of-sqrt(2) the concatenation form
    # obscured. Deterministic rates: ref exits half its k samples
    # (p=0.5), treat exits none (q=0.0), so item-effect variance is 0.
    from modelwelfare import stats
    K = 10
    ref = {f"i{n}": {s: (1.0 if s % 2 == 0 else 0.0) for s in range(K)}
           for n in range(30)}
    treat = {f"i{n}": {s: 0.0 for s in range(K)} for n in range(30)}
    comp = s3m.exit_components(ref, treat, K)
    # p(1-p)+q(1-q) = 0.25 + 0 = 0.25 per item; analytic delta SD:
    analytic = (0.5 * 0.5 / K + 0.0) ** 0.5
    assert stats.null_delta_sd_mean(
        comp["binomial_sigma_sample"], K) == pytest.approx(analytic)
    assert comp["sigma_item"] == 0.0  # no item heterogeneity planted
