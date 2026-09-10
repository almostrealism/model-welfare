"""The sign-flip permutation test's directional alternatives."""
import pytest

from modelwelfare import stats


def test_directional_alternatives_bracket_the_two_sided_p():
    deltas = [-1.5, -2.0, -0.5, -1.0, -1.2, 0.3, -0.8, -1.7]
    two = stats.paired_permutation_test(deltas, n_perm=4000, seed=1)
    less = stats.paired_permutation_test(deltas, n_perm=4000, seed=1, alternative="less")
    greater = stats.paired_permutation_test(deltas, n_perm=4000, seed=1, alternative="greater")
    assert two["alternative"] == "two-sided" and less["alternative"] == "less"
    assert less["p_value"] < two["p_value"] < greater["p_value"]
    # the two one-sided counts overlap only on exact ties, and each carries
    # the +1 correction, so they sum to 1 up to those terms
    assert less["p_value"] + greater["p_value"] == pytest.approx(1.0, abs=0.01)
    assert less["mean"] == two["mean"]


def test_unknown_alternative_is_refused():
    with pytest.raises(ValueError):
        stats.paired_permutation_test([1.0, -1.0], alternative="sideways")
