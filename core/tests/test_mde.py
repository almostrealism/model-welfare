"""The §5 MDE analytic forms: null-based paired-delta SDs and the
alpha/power multiplier — pinned numerically so a silent formula edit cannot
change registered values."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from modelwelfare.stats import (MDE_MULTIPLIER, mde_paired,  # noqa: E402
                                null_delta_sd_dispersion, null_delta_sd_mean,
                                null_delta_sd_rate)


def test_multiplier_is_the_alpha05_power80_constant():
    assert MDE_MULTIPLIER == pytest.approx(2.801585, abs=1e-6)


def test_paired_mean_form():
    # sigma=1, k=10 -> delta SD sqrt(0.2); n=60 items.
    assert null_delta_sd_mean(1.0, 10) == pytest.approx(np.sqrt(0.2))
    assert mde_paired(null_delta_sd_mean(1.0, 10), 60) == pytest.approx(
        2.801585 * np.sqrt(0.2) / np.sqrt(60), rel=1e-6)


def test_dispersion_form_is_sigma_over_sqrt_k_minus_1():
    assert null_delta_sd_dispersion(3.0, 10) == pytest.approx(1.0)


def test_rate_form_averages_binomial_variance():
    # p=0.5 everywhere, k=10: delta SD = sqrt(2*0.25/10).
    assert null_delta_sd_rate([0.5, 0.5], 10) == pytest.approx(np.sqrt(0.05))
    # Degenerate rates contribute zero variance.
    assert null_delta_sd_rate([1.0, 0.0], 10) == 0.0


def test_monte_carlo_agreement_for_the_mean_form():
    rng = np.random.default_rng(3)
    k, trials = 10, 4000
    deltas = (rng.normal(size=(trials, k)).mean(axis=1)
              - rng.normal(size=(trials, k)).mean(axis=1))
    assert deltas.std() == pytest.approx(null_delta_sd_mean(1.0, k), rel=0.05)
