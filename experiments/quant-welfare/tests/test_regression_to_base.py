"""Tests for the regression-toward-base stats core (tools/regression_to_base.py).

The conditional-logprob scoring needs live servers; the per-item shift statistic
is pure and tested here.
"""

import importlib.util
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location(
        "regression_to_base", BASE / "tools" / "regression_to_base.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rtb = _load()


def test_base_affinity_shift_detects_regression():
    # Every item more base-like under awq -> significant positive shift.
    means = {"bf16": {f"i{k}": 0.0 for k in range(10)},
             "awq": {f"i{k}": 1.0 for k in range(10)}}
    row = rtb.base_affinity_shift(means, "bf16", ["awq"])["rows"][0]
    assert row["n"] == 10 and row["mean_delta"] > 0 and row["p_value"] < 0.05


def test_base_affinity_shift_null_is_not_detected():
    means = {"bf16": {f"i{k}": 0.5 for k in range(8)},
             "awq": {f"i{k}": 0.5 for k in range(8)}}
    assert rtb.base_affinity_shift(means, "bf16", ["awq"])["rows"][0]["p_value"] > 0.5
