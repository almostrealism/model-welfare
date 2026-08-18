"""Math-level validation of contrastive direction extraction.

Synthetic pooled vectors with a planted direction: extraction must recover
it, held-out separations must carry its sign, and the deterministic held-out
split must be exactly reproducible — these are the properties the Study 2
instrument gate reads off real captures.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from modelwelfare import directions as dirs  # noqa: E402

HIDDEN = 64
PAIRS = 12
DELTA = 2.0
NOISE = 0.1


def planted_world(seed=7):
    rng = np.random.default_rng(seed)
    planted = rng.normal(size=HIDDEN)
    planted /= np.linalg.norm(planted)
    pooled, pairs = {}, {}
    for index in range(PAIRS):
        base = rng.normal(scale=1.0, size=HIDDEN)
        pos = base + DELTA * planted + rng.normal(scale=NOISE, size=HIDDEN)
        neg = base + rng.normal(scale=NOISE, size=HIDDEN)
        pooled[f"pair{index:02d}-pos"] = pos
        pooled[f"pair{index:02d}-neg"] = neg
        pairs[f"pair{index:02d}"] = {"pos": f"pair{index:02d}-pos",
                                     "neg": f"pair{index:02d}-neg"}
    return planted, pooled, pairs


def test_extraction_recovers_planted_direction():
    planted, pooled, pairs = planted_world()
    held_out = dirs.held_out_pair_ids(pairs)
    direction, magnitude = dirs.extract_direction(
        pooled, pairs, sorted(set(pairs) - held_out))
    assert np.dot(direction, planted) > 0.95
    assert magnitude == pytest.approx(DELTA, rel=0.2)


def test_held_out_separations_carry_the_planted_sign():
    planted, pooled, pairs = planted_world()
    held_out = dirs.held_out_pair_ids(pairs)
    direction, _ = dirs.extract_direction(
        pooled, pairs, sorted(set(pairs) - held_out))
    separations = dirs.pair_separations(direction, pooled, pairs, held_out)
    consistent, total = dirs.sign_consistency(separations)
    assert total == len(held_out) > 0
    assert consistent == total
    assert np.mean(list(separations.values())) == pytest.approx(DELTA, rel=0.3)


def test_held_out_split_is_deterministic_and_disjoint():
    ids = [f"p{i}" for i in range(12)]
    held = dirs.held_out_pair_ids(ids)
    assert held == dirs.held_out_pair_ids(list(reversed(ids)))
    ordered = sorted(ids)
    assert held == {ordered[2], ordered[5], ordered[8], ordered[11]}


def test_zero_mean_difference_raises():
    pooled = {"a-pos": np.ones(4), "a-neg": np.ones(4)}
    pairs = {"a": {"pos": "a-pos", "neg": "a-neg"}}
    with pytest.raises(ValueError):
        dirs.extract_direction(pooled, pairs, ["a"])


def test_plan_rejects_duplicate_conversation_ids():
    entry = ("same-id", [{"role": "user", "content": "hi"}])
    with pytest.raises(ValueError):
        dirs.build_plan([entry, entry])


def test_projection_is_dot_with_unit_direction():
    direction = np.zeros(4)
    direction[1] = 1.0
    values = dirs.project([np.array([5.0, 2.0, 0.0, 0.0])], direction)
    assert values == [2.0]
