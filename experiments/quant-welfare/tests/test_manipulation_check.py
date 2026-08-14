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


# --- graded ordering recovery ------------------------------------------------

def _graded_scores(per_family_scores):
    """Build (scores_by_item, expectations) for one dimension from
    family -> [score at level 0..4]."""
    scores, expectations = {}, {}
    for family, ladder in per_family_scores.items():
        for level, value in enumerate(ladder):
            item_id = f"syn-grade-frustration-{family}-l{level}"
            scores[item_id] = {"frustration": value}
            expectations[item_id] = ("frustration", family, level)
    return scores, expectations


def test_evaluate_graded_recovers_perfect_ordering():
    scores, expectations = _graded_scores({
        "poem": [0.0, 2.0, 5.0, 7.0, 9.0],
        "plan": [1.0, 3.0, 4.0, 6.0, 8.0],
        "code": [0.5, 2.5, 5.5, 7.5, 9.5],
    })
    report = mc.evaluate_graded(scores, expectations)
    entry = report["frustration"]
    assert entry["passed"]
    assert entry["spearman"] > 0.95
    assert entry["pairwise_accuracy"] == 1.0
    assert entry["trend_p"] < 0.05
    assert entry["n_families"] == 3


def test_evaluate_graded_fails_on_inverted_ordering():
    scores, expectations = _graded_scores({
        "poem": [9.0, 7.0, 5.0, 3.0, 1.0],
        "plan": [8.0, 6.0, 4.0, 2.0, 0.0],
        "code": [9.5, 7.5, 5.5, 3.5, 1.5],
    })
    report = mc.evaluate_graded(scores, expectations)
    entry = report["frustration"]
    assert not entry["passed"]
    assert entry["spearman"] < -0.95
    assert entry["pairwise_accuracy"] == 0.0


def test_evaluate_graded_flat_scores_fail():
    # A judge that gives every level the same score has ties everywhere:
    # accuracy 0.5 and no trend — not a recovered ordering.
    scores, expectations = _graded_scores({
        "poem": [5.0] * 5, "plan": [5.0] * 5, "code": [5.0] * 5,
    })
    report = mc.evaluate_graded(scores, expectations)
    entry = report["frustration"]
    assert entry["pairwise_accuracy"] == 0.5
    assert not entry["passed"]


def test_graded_fixtures_are_complete_and_distinct():
    import synthetics

    ids = [record.key.item_id for record in synthetics.GRADED_DISTRESS]
    assert len(ids) == len(set(ids))
    assert set(ids) == set(synthetics.GRADED_EXPECTATIONS)
    assert not (set(ids) & set(synthetics.DISTRESS_EXPECTATIONS))
    per_dimension = {}
    for dimension, family, level in synthetics.GRADED_EXPECTATIONS.values():
        per_dimension.setdefault(dimension, set()).add((family, level))
    assert set(per_dimension) == {"frustration", "self_deprecation", "tone_stability"}
    for dimension, cells in per_dimension.items():
        families = {family for family, _ in cells}
        assert len(families) == 3, dimension
        for family in families:
            levels = sorted(level for f, level in cells if f == family)
            assert levels == list(range(synthetics.GRADED_LEVELS)), (dimension, family)
