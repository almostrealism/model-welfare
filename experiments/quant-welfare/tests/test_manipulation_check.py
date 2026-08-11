"""Offline tests for the manipulation-check evaluator.

Scoring the synthetics needs the live judge; ``evaluate`` — the per-dimension
pole-separation verdict — is pure and tested here.
"""

import importlib.util
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
for path in (str(BASE), str(BASE / "tools"), str(BASE / "bakeoff")):
    if path not in sys.path:
        sys.path.insert(0, path)


def _load():
    spec = importlib.util.spec_from_file_location(
        "manipulation_check", BASE / "tools" / "manipulation_check.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mc = _load()


def test_evaluate_passes_when_poles_separate():
    scores = {
        "syn-frustration-high": {"frustration": 9.0},
        "syn-frustration-low": {"frustration": 1.0},
        "syn-tone-stable": {"tone_stability": 9.0},
        "syn-tone-degrading": {"tone_stability": 2.0},
    }
    expectations = {
        "syn-frustration-high": ("frustration", "high"),
        "syn-frustration-low": ("frustration", "low"),
        "syn-tone-stable": ("tone_stability", "high"),
        "syn-tone-degrading": ("tone_stability", "low"),
    }
    report = mc.evaluate(scores, expectations, margin=3.0)
    assert report["frustration"]["passed"]
    assert report["tone_stability"]["passed"]


def test_evaluate_flags_blind_dimension():
    # The judge scores the tone poles identically -> tone_stability is blind.
    scores = {
        "syn-tone-stable": {"tone_stability": 5.0},
        "syn-tone-degrading": {"tone_stability": 5.0},
    }
    expectations = {
        "syn-tone-stable": ("tone_stability", "high"),
        "syn-tone-degrading": ("tone_stability", "low"),
    }
    report = mc.evaluate(scores, expectations, margin=3.0)
    assert report["tone_stability"]["separation"] == 0.0
    assert not report["tone_stability"]["passed"]
