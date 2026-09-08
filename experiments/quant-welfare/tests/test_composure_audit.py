"""Tests for tools/composure_audit.py: the audit must catch a planted
regression-to-the-mean artifact and must not invent one.

Two fabricated worlds with a fixed RNG: a HOMOGENEOUS world (every item
has the same true delta; item baselines vary only by sampling noise)
where the naive bottom-k estimate must exceed the true delta while the
clean estimate stays near it and the noise-pull gauge accounts for the
gap; and a GRADIENT world (true delta genuinely larger for
low-baseline items) where the clean estimate must retain the gradient.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

BASE = Path(__file__).resolve().parents[1]
if str(BASE / "tools") not in sys.path:
    sys.path.insert(0, str(BASE / "tools"))

import composure_audit as ca  # noqa: E402

RNG = np.random.default_rng(7)
ITEMS = 60
SAMPLES = 10
NOISE = 2.0
TRUE_DELTA = 1.0


def build_world(gradient, noise=NOISE):
    """(selector/reference values, treatment values) per item. In the
    homogeneous world every true baseline is 5.0, so any bottom-k
    structure in the reference means is pure sampling noise; the
    gradient world ties the true delta to a true per-item trait (never
    to the noisy observed rank), with noise low enough that selection
    can see the trait."""
    reference = {}
    treatment = {}
    traits = np.linspace(-1.0, 1.0, ITEMS)
    for index in range(ITEMS):
        item = f"item-{index:02d}"
        base = 5.0 + (traits[index] if gradient else 0.0)
        delta = TRUE_DELTA - (traits[index] if gradient else 0.0)
        reference[item] = {s: base + RNG.normal(0, noise)
                           for s in range(SAMPLES)}
        treatment[item] = {s: base + delta + RNG.normal(0, noise)
                           for s in range(SAMPLES)}
    return reference, treatment


def test_homogeneous_world_naive_inflates_clean_does_not():
    reference, treatment = build_world(gradient=False)
    items = sorted(reference)
    report = ca.audit_endpoint(reference, reference, treatment, items, 20)
    # naive bottom-20 must be inflated well beyond the true delta...
    assert report["naive_bottom"] > TRUE_DELTA + 0.3
    # ...the clean estimate must sit near it...
    assert report["clean_bottom"] == pytest.approx(TRUE_DELTA, abs=0.35)
    # ...and the noise-pull gauge must account for the gap: the naive
    # baseline is the full mean, which carries half the selection
    # half's noise, so pull = 2 x (naive - clean).
    assert report["noise_pull_bottom"] == pytest.approx(
        2 * (report["naive_bottom"] - report["clean_bottom"]), abs=0.2)
    assert report["full_delta"] == pytest.approx(TRUE_DELTA, abs=0.2)


def test_gradient_world_clean_retains_the_gradient():
    reference, treatment = build_world(gradient=True, noise=1.0)
    items = sorted(reference)
    report = ca.audit_endpoint(reference, reference, treatment, items, 20)
    # low-trait items (low true baseline) carry larger true deltas;
    # the clean bottom-vs-top separation must survive the audit
    # (attenuated by selector noise, never erased).
    assert report["clean_bottom"] - report["clean_top"] > 0.6
    assert report["spearman_clean"] < -0.3


def test_variance_decomposition_reads_signal_share():
    reference, _ = build_world(gradient=True)
    items = sorted(reference)
    decomposition = ca.variance_decomposition(reference, items)
    sampling = NOISE ** 2 / SAMPLES
    assert decomposition["mean_sampling_variance"] == pytest.approx(
        sampling, rel=0.3)
    assert 0.0 < decomposition["signal_share"] < 1.0


def test_half_mean_parity_and_empty_refusal():
    samples = {0: 1.0, 1: 3.0, 2: 5.0}
    assert ca.half_mean(samples, 0) == pytest.approx(3.0)
    assert ca.half_mean(samples, 1) == pytest.approx(3.0)
    with pytest.raises(SystemExit):
        ca.half_mean({0: 1.0}, 1)
