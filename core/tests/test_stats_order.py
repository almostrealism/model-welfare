"""The seeded permutation tests must not depend on the order their inputs
arrive in: the sign matrix (paired) and the pooled shuffles (two-sample)
are assigned by position, so the inputs are put in a canonical order
before the draw. A registered p-value therefore cannot move with the
order of a frozen item list (PLANNING, opened 2026-09-12)."""
import numpy as np

from modelwelfare import stats


def test_paired_permutation_ignores_item_order():
    rng = np.random.default_rng(3)
    deltas = rng.normal(-0.4, 1.0, size=30)
    reference = stats.paired_permutation_test(deltas, n_perm=4000, seed=7, alternative="less")
    for trial in range(5):
        shuffled = rng.permutation(deltas)
        result = stats.paired_permutation_test(shuffled, n_perm=4000, seed=7, alternative="less")
        assert result["p_value"] == reference["p_value"], trial
        assert result["mean"] == reference["mean"]
    reversed_result = stats.paired_permutation_test(deltas[::-1], n_perm=4000, seed=7)
    assert reversed_result["p_value"] == stats.paired_permutation_test(deltas, n_perm=4000, seed=7)["p_value"]


def test_paired_permutation_drops_nan_before_ordering():
    deltas = [0.5, float("nan"), -0.2, 0.9]
    assert stats.paired_permutation_test(deltas, n_perm=500, seed=1)["n"] == 3
    assert (stats.paired_permutation_test(deltas, n_perm=500, seed=1)["p_value"]
            == stats.paired_permutation_test(deltas[::-1], n_perm=500, seed=1)["p_value"])


def test_two_sample_permutation_ignores_group_order():
    rng = np.random.default_rng(5)
    a = rng.normal(0.3, 1.0, size=12)
    b = rng.normal(0.0, 1.0, size=15)
    reference = stats.two_sample_permutation_test(a, b, n_perm=2000, seed=11)
    result = stats.two_sample_permutation_test(rng.permutation(a), rng.permutation(b), n_perm=2000, seed=11)
    assert result["p_value"] == reference["p_value"]
    assert result["difference"] == reference["difference"]
