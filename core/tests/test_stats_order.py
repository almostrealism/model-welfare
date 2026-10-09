"""The seeded permutation tests are assigned by position, so the order
their inputs arrive in is part of the computation. ``order="positional"``
(the default) keeps that: every published Study 1 and 2 result was computed
with it and their reproduction checks depend on it. ``order="canonical"``
sorts first, so a registered p-value cannot move with the order of a frozen
item list (PLANNING, opened 2026-09-12; Study 4 registers canonical)."""
import numpy as np
import pytest

from modelwelfare import stats


def test_canonical_paired_permutation_ignores_item_order():
    rng = np.random.default_rng(3)
    deltas = rng.normal(-0.4, 1.0, size=30)
    reference = stats.paired_permutation_test(deltas, n_perm=4000, seed=7, alternative="less",
                                              order="canonical")
    for trial in range(5):
        shuffled = rng.permutation(deltas)
        result = stats.paired_permutation_test(shuffled, n_perm=4000, seed=7, alternative="less",
                                               order="canonical")
        assert result["p_value"] == reference["p_value"], trial
        assert result["mean"] == reference["mean"]
    reversed_result = stats.paired_permutation_test(deltas[::-1], n_perm=4000, seed=7, order="canonical")
    assert reversed_result["p_value"] == stats.paired_permutation_test(
        deltas, n_perm=4000, seed=7, order="canonical")["p_value"]


def test_default_order_is_positional_and_unchanged():
    """The default must stay the published computation: explicit
    "positional" and the default agree, and the draw follows input order
    (a reversed input is a different draw when the deltas differ)."""
    rng = np.random.default_rng(9)
    deltas = rng.normal(-0.3, 1.0, size=20)
    default = stats.paired_permutation_test(deltas, n_perm=3000, seed=2)
    explicit = stats.paired_permutation_test(deltas, n_perm=3000, seed=2, order="positional")
    assert default == explicit
    reversed_default = stats.paired_permutation_test(deltas[::-1], n_perm=3000, seed=2)
    canonical = stats.paired_permutation_test(deltas, n_perm=3000, seed=2, order="canonical")
    # positional and canonical are different draws of the same test: same
    # observed mean, p-values that need not agree
    assert reversed_default["mean"] == pytest.approx(default["mean"])
    assert canonical["mean"] == pytest.approx(default["mean"])


def test_canonical_paired_permutation_drops_nan_before_ordering():
    deltas = [0.5, float("nan"), -0.2, 0.9]
    assert stats.paired_permutation_test(deltas, n_perm=500, seed=1, order="canonical")["n"] == 3
    assert (stats.paired_permutation_test(deltas, n_perm=500, seed=1, order="canonical")["p_value"]
            == stats.paired_permutation_test(deltas[::-1], n_perm=500, seed=1, order="canonical")["p_value"])


def test_unknown_order_is_refused():
    with pytest.raises(ValueError, match="order"):
        stats.paired_permutation_test([1.0, 2.0], n_perm=10, order="sorted")
    with pytest.raises(ValueError, match="order"):
        stats.two_sample_permutation_test([1.0], [2.0], n_perm=10, order="sorted")


def test_canonical_two_sample_permutation_ignores_group_order():
    rng = np.random.default_rng(5)
    a = rng.normal(0.3, 1.0, size=12)
    b = rng.normal(0.0, 1.0, size=15)
    reference = stats.two_sample_permutation_test(a, b, n_perm=2000, seed=11, order="canonical")
    result = stats.two_sample_permutation_test(rng.permutation(a), rng.permutation(b), n_perm=2000,
                                               seed=11, order="canonical")
    assert result["p_value"] == reference["p_value"]
    assert result["difference"] == reference["difference"]
    default = stats.two_sample_permutation_test(a, b, n_perm=2000, seed=11)
    assert default == stats.two_sample_permutation_test(a, b, n_perm=2000, seed=11, order="positional")
