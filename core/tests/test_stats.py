"""Unit tests for the registered confirmatory statistics (modelwelfare.stats).

Each test pins a hand-computable property or a closed-form value, so the tests
double as a specification of what the pre-registration commits to.
"""
import math

import numpy as np
import pytest

from modelwelfare import stats


# --- permutation + paired t -------------------------------------------------

def test_permutation_all_positive_is_significant():
    result = stats.paired_permutation_test([1.0] * 8, n_perm=2000, seed=1)
    assert result["mean"] == pytest.approx(1.0)
    assert result["p_value"] < 0.05  # only all-same sign flips are as extreme


def test_permutation_symmetric_is_null():
    result = stats.paired_permutation_test([1.0, -1.0, 1.0, -1.0, 1.0, -1.0], seed=1)
    assert result["mean"] == pytest.approx(0.0)
    assert result["p_value"] > 0.5


def test_permutation_ignores_nan_and_reports_n():
    result = stats.paired_permutation_test([1.0, float("nan"), 1.0], n_perm=500, seed=0)
    assert result["n"] == 2


def test_paired_t_matches_closed_form():
    result = stats.paired_t_test([1.0, 2.0, 3.0, 4.0, 5.0])
    # mean 3, sd 1.5811, n 5 -> t = 3 / (1.5811/sqrt(5)) = 4.2426
    assert result["t"] == pytest.approx(4.2426, abs=1e-3)
    assert result["p_value"] < 0.001


def test_paired_t_zero_variance():
    result = stats.paired_t_test([2.0, 2.0, 2.0])
    assert math.isinf(result["t"]) and result["p_value"] == 0.0


# --- Holm -------------------------------------------------------------------

def test_holm_step_down_known_case():
    adjusted = stats.holm([0.01, 0.04, 0.03])
    assert adjusted == pytest.approx([0.03, 0.06, 0.06])


def test_holm_enforces_monotonicity_and_caps_at_one():
    adjusted = stats.holm([0.5, 0.5, 0.5])
    assert adjusted == pytest.approx([1.0, 1.0, 1.0])
    assert all(0.0 <= a <= 1.0 for a in adjusted)


def test_holm_empty():
    assert stats.holm([]) == []


# --- Page's L ---------------------------------------------------------------

def test_pages_l_perfect_increasing_trend():
    # Two items, three ordered conditions, perfectly increasing within each.
    values = {
        ("A", "i1"): 1.0, ("B", "i1"): 2.0, ("C", "i1"): 3.0,
        ("A", "i2"): 1.0, ("B", "i2"): 2.0, ("C", "i2"): 3.0,
    }
    result = stats.pages_l_trend(values, ["A", "B", "C"])
    assert result["L"] == pytest.approx(28.0)   # 1*2 + 2*4 + 3*6
    assert result["z"] == pytest.approx(2.0)     # (28-24)/2
    assert result["n"] == 2
    assert result["p_value"] < 0.05


def test_pages_l_reversed_trend_not_significant():
    values = {
        ("A", "i1"): 3.0, ("B", "i1"): 2.0, ("C", "i1"): 1.0,
        ("A", "i2"): 3.0, ("B", "i2"): 2.0, ("C", "i2"): 1.0,
    }
    result = stats.pages_l_trend(values, ["A", "B", "C"])
    assert result["z"] < 0 and result["p_value"] > 0.95


def test_pages_l_only_uses_items_present_in_all_conditions():
    values = {
        ("A", "i1"): 1.0, ("B", "i1"): 2.0, ("C", "i1"): 3.0,
        ("A", "i2"): 1.0, ("B", "i2"): 2.0,  # i2 missing under C -> dropped
    }
    result = stats.pages_l_trend(values, ["A", "B", "C"])
    assert result["n"] == 1


def test_pages_l_requires_three_conditions():
    with pytest.raises(ValueError):
        stats.pages_l_trend({}, ["A", "B"])


# --- flip-fraction (H1) -----------------------------------------------------

def test_flip_fraction_strong_effect_is_significant():
    # Every item flat-off in ref, flat-on in cond -> all flip.
    result = stats.flip_fraction_test([0] * 20, [10] * 20, n_samples=10,
                                      n_sim=2000, seed=1)
    assert result["observed"] == pytest.approx(1.0)
    assert result["p_value"] < 0.05


def test_flip_fraction_no_effect_is_null():
    # Identical, deterministic counts -> zero observed flips, pooled rate 0/1.
    result = stats.flip_fraction_test([0] * 10, [0] * 10, n_samples=10,
                                      n_sim=1000, seed=1)
    assert result["observed"] == 0.0
    assert result["p_value"] > 0.5


def test_flip_fraction_length_mismatch():
    with pytest.raises(ValueError):
        stats.flip_fraction_test([0, 1], [0], n_samples=10)


def test_flip_fraction_beta_binomial_null_is_not_anticonservative():
    # Items near p=0.5 flip readily by chance; the beta-binomial null must
    # produce a substantial baseline flip fraction (not ~0), or it would call
    # noise "real". 20 items observed at exactly 5/10 both ways -> observed 0.
    result = stats.flip_fraction_test([5] * 20, [5] * 20, n_samples=10,
                                      n_sim=2000, seed=1)
    assert result["null_mean"] > 0.2  # sampling noise alone flips many items
    assert result["p_value"] > 0.5    # observed (0) is not extreme


def test_band_index_edges():
    idx = stats.band_index([0.0, 3.32, 3.33, 6.66, 6.67, 10.0], [3.33, 6.67])
    assert list(idx) == [0, 0, 1, 1, 2, 2]


# --- E3 across-sample SD delta ---------------------------------------------

def test_across_sample_sd_delta_known():
    ref = {"i1": [1.0, 1.0, 1.0]}          # sd 0
    cond = {"i1": [0.0, 2.0, 4.0]}         # sd(ddof=1) = 2.0
    assert stats.across_sample_sd_delta(ref, cond) == pytest.approx([2.0])


def test_across_sample_sd_delta_skips_singletons():
    ref = {"i1": [1.0]}
    cond = {"i1": [0.0, 2.0]}
    assert stats.across_sample_sd_delta(ref, cond) == []


# --- helpers ----------------------------------------------------------------

def test_rankdata_average_ties():
    ranks = stats.rankdata_average(np.array([10.0, 20.0, 20.0, 40.0]))
    assert list(ranks) == pytest.approx([1.0, 2.5, 2.5, 4.0])
