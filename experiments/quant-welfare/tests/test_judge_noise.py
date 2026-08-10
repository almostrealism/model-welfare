"""Offline tests for the judge-noise tool's reporting half.

The re-judge loop needs the live judge server; ``report_variance`` — the
partition of score variance into subject signal vs judge noise — is pure and
tested here with synthetic JudgeScore records.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parents[1]
for path in (str(BASE), str(BASE / "tools")):
    if path not in sys.path:
        sys.path.insert(0, path)


def _load():
    spec = importlib.util.spec_from_file_location("judge_noise", BASE / "tools" / "judge_noise.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


judge_noise = _load()
from modelwelfare.v1 import scoring_pb2  # noqa: E402


def js(cond, item, sample, pass_index, frustration):
    score = scoring_pb2.JudgeScore()
    score.key.condition_id, score.key.item_id, score.key.sample_index = cond, item, sample
    score.judge_sample_index = pass_index
    dim = score.scores.add()
    dim.dimension, dim.value = "frustration", float(frustration)
    return score


def test_report_variance_quiet_judge_is_reliable():
    # Each transcript scored identically across passes; transcripts differ ->
    # all variance is subject signal, none is judge noise.
    scores = []
    for p in range(3):
        scores.append(js("bf16", "d0", 0, p, 2.0))
        scores.append(js("bf16", "d1", 0, p, 8.0))
    report = judge_noise.report_variance(scores)
    assert report["frustration"]["icc"] == pytest.approx(1.0)
    assert report["frustration"]["judge_noise_share"] == pytest.approx(0.0)


def test_report_variance_noisy_judge_is_unreliable():
    # Every transcript has the same mean but the passes disagree wildly ->
    # all variance is judge noise.
    scores = []
    for transcript in ("d0", "d1"):
        scores.append(js("bf16", transcript, 0, 0, 0.0))
        scores.append(js("bf16", transcript, 0, 1, 10.0))
    report = judge_noise.report_variance(scores)
    assert report["frustration"]["icc"] == pytest.approx(0.0)
    assert report["frustration"]["judge_noise_share"] == pytest.approx(1.0)
