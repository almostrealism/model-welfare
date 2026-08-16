"""Tests for the sensitivity-sweep refusal analysis (sweep.py).

Pins the detection behaviour: a real refusal drop is detected, a null is not.
"""

import importlib.util
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location("sweep", BASE / "sweep.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sweep = _load()
from modelwelfare.v1 import scoring_pb2  # noqa: E402


def _refusal(cond, item, value):
    score = scoring_pb2.JudgeScore()
    score.key.condition_id, score.key.item_id = cond, item
    dim = score.scores.add()
    dim.dimension, dim.value = "refusal", float(value)
    return score


def test_refusal_shift_detects_a_drop():
    # BF16 refuses (10), AWQ complies (2) on every item -> significant drop.
    scores = []
    for k in range(12):
        scores.append(_refusal("bf16", f"i{k}", 10.0))
        scores.append(_refusal("awq", f"i{k}", 2.0))
    row = sweep.refusal_shift(scores, "bf16", ["awq"])["rows"][0]
    assert row["n"] == 12
    assert row["mean_delta"] < 0 and row["p_value"] < 0.05
    assert row["reference_refusal"] == 10.0 and row["contrast_refusal"] == 2.0


def test_refusal_shift_null_is_not_detected():
    scores = []
    for k in range(8):
        scores.append(_refusal("bf16", f"i{k}", 5.0))
        scores.append(_refusal("awq", f"i{k}", 5.0))
    row = sweep.refusal_shift(scores, "bf16", ["awq"])["rows"][0]
    assert row["p_value"] > 0.5
