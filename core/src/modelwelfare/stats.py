"""Registered confirmatory statistics for Study 1 (see PREREGISTRATION.md §4).

Pure-numpy implementations of exactly the tests the pre-registration commits
to, so the confirmatory analysis is fixed as tested code before any data:

  - paired sign-flip permutation test (primary), with a paired-t companion;
  - Holm step-down correction over the full primary family;
  - Page's L trend test for the repeated-measures ordered ladder (H3);
  - the H1 flip-fraction test against a within-condition sampling null.

These operate on plain arrays and dicts, decoupled from the protobuf records:
aggregation to (condition, item) lives in ``analysis`` and the runner; the
statistics are the caller's to assemble and are unit-tested in isolation. No
scipy dependency — the normal CDF is via ``math.erf`` and the only large-sample
approximations (paired-t p-value, Page's L z) are documented at their use and
are negligible at the study's item counts (N ≈ 150).
"""
from __future__ import annotations

import math
from typing import Optional

import numpy as np


def _normal_cdf(z: float) -> float:
    """Standard-normal CDF via the error function (no scipy)."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def rankdata_average(values: np.ndarray) -> np.ndarray:
    """Ranks (1-based) with ties resolved to the average rank, matching the
    convention Page's L assumes. Small-array helper; avoids a scipy import."""
    values = np.asarray(values, float)
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(len(values), float)
    sorted_vals = values[order]
    i = 0
    n = len(values)
    while i < n:
        j = i
        while j + 1 < n and sorted_vals[j + 1] == sorted_vals[i]:
            j += 1
        average = (i + j) / 2.0 + 1.0  # 1-based average of the tied block
        for k in range(i, j + 1):
            ranks[order[k]] = average
        i = j + 1
    return ranks


def paired_permutation_test(deltas, n_perm: int = 10000, seed: int = 0) -> dict:
    """Sign-flip permutation test on item-level paired differences (primary).

    Under H0 each item's delta is symmetric about zero, so the exact test
    flips signs; we sample ``n_perm`` sign vectors. The two-sided p-value
    includes the observed statistic in the count (the standard +1 correction),
    so it is never exactly zero.
    """
    deltas = np.asarray(deltas, float)
    deltas = deltas[~np.isnan(deltas)]
    n = len(deltas)
    if n == 0:
        return {"mean": float("nan"), "p_value": float("nan"), "n": 0}
    observed = float(deltas.mean())
    rng = np.random.default_rng(seed)
    signs = rng.choice(np.array([-1.0, 1.0]), size=(n_perm, n))
    perm_means = (signs * deltas).mean(axis=1)
    extreme = int(np.sum(np.abs(perm_means) >= abs(observed) - 1e-12))
    p_value = (extreme + 1) / (n_perm + 1)
    return {"mean": observed, "p_value": float(p_value), "n": n}


def paired_t_test(deltas) -> dict:
    """Paired t on item-level differences — the descriptive companion to the
    permutation test. The two-sided p-value uses the normal approximation to
    Student's t, which is negligible at the study's item counts; the
    permutation test is the primary inference regardless."""
    deltas = np.asarray(deltas, float)
    deltas = deltas[~np.isnan(deltas)]
    n = len(deltas)
    if n < 2:
        return {"t": float("nan"), "p_value": float("nan"), "n": n}
    mean = float(deltas.mean())
    sd = float(deltas.std(ddof=1))
    if sd == 0.0:
        t = 0.0 if mean == 0.0 else math.inf
        p_value = 1.0 if mean == 0.0 else 0.0
        return {"t": t, "p_value": p_value, "n": n}
    t = mean / (sd / math.sqrt(n))
    p_value = 2.0 * (1.0 - _normal_cdf(abs(t)))
    return {"t": float(t), "p_value": float(p_value), "n": n}


def holm(pvalues) -> list:
    """Holm–Bonferroni step-down adjusted p-values, returned in input order.

    Adjusted p_(i) = max over the sorted prefix of min(1, (m - rank) * p),
    enforcing monotonicity. Compare each adjusted value to alpha directly to
    control the family-wise error rate over the full primary family."""
    pvalues = list(pvalues)
    m = len(pvalues)
    if m == 0:
        return []
    order = sorted(range(m), key=lambda i: pvalues[i])
    adjusted = [0.0] * m
    running = 0.0
    for rank, idx in enumerate(order):
        value = min(1.0, (m - rank) * pvalues[idx])
        running = max(running, value)
        adjusted[idx] = running
    return adjusted


def pages_l_trend(value_by_condition_item: dict, ordered_conditions: list) -> dict:
    """Page's L trend test for ordered alternatives (H3), repeated measures.

    ``value_by_condition_item`` maps (condition_id, item_id) -> value;
    ``ordered_conditions`` lists the conditions in increasing predicted-value
    order (e.g. BF16, RTN-w8, RTN-w4, RTN-w3 for an endpoint expected to rise
    as precision drops). Only items present in every ordered condition are
    used. Within each item the conditions are ranked (ties averaged); L sums
    predicted_rank * rank_total per condition. The z-standardization is the
    large-sample normal approximation (exact at the study's item counts). The
    p-value is one-sided for the predicted increasing trend.
    """
    k = len(ordered_conditions)
    if k < 3:
        raise ValueError("Page's L needs at least 3 ordered conditions")
    items = None
    for condition in ordered_conditions:
        present = {
            item
            for (cond, item) in value_by_condition_item
            if cond == condition and not _isnan(value_by_condition_item[(cond, item)])
        }
        items = present if items is None else (items & present)
    items = sorted(items or [])
    n = len(items)
    if n == 0:
        return {"L": float("nan"), "z": float("nan"), "p_value": float("nan"), "n": 0}

    rank_totals = np.zeros(k)
    for item in items:
        row = np.array(
            [value_by_condition_item[(cond, item)] for cond in ordered_conditions],
            float,
        )
        rank_totals += rankdata_average(row)

    predicted = np.arange(1, k + 1)
    L = float(np.sum(predicted * rank_totals))
    mean_L = n * k * (k + 1) ** 2 / 4.0
    var_L = n * k ** 2 * (k + 1) * (k ** 2 - 1) / 144.0
    if var_L <= 0:
        return {"L": L, "z": float("nan"), "p_value": float("nan"), "n": n}
    z = (L - mean_L) / math.sqrt(var_L)
    p_value = 1.0 - _normal_cdf(z)  # one-sided, predicted increasing trend
    return {"L": L, "z": float(z), "p_value": float(p_value), "n": n}


def flip_fraction_test(
    ref_counts, cond_counts, n_samples: int, n_sim: int = 10000, seed: int = 0
) -> dict:
    """H1 for a binary indicator: does the fraction of items that flip their
    majority outcome between reference and condition exceed sampling noise?

    ``ref_counts``/``cond_counts`` are per-item exit counts out of
    ``n_samples``. An item's outcome is majority-exit (count/n > 0.5); a flip
    is a change in that boolean. The null draws both conditions from each
    item's pooled rate (no true effect) and simulates the flip fraction from
    sampling variation alone. One-sided p (observed exceeds null).
    """
    ref = np.asarray(ref_counts, float)
    cond = np.asarray(cond_counts, float)
    if len(ref) != len(cond):
        raise ValueError("ref_counts and cond_counts must align by item")
    n_items = len(ref)
    if n_items == 0:
        return {"observed": float("nan"), "null_mean": float("nan"),
                "p_value": float("nan"), "n": 0}

    def majority(counts):
        return (counts / n_samples) > 0.5

    observed = float(np.mean(majority(ref) != majority(cond)))
    pooled = (ref + cond) / (2.0 * n_samples)
    rng = np.random.default_rng(seed)
    null_fracs = np.empty(n_sim)
    for s in range(n_sim):
        sim_ref = rng.binomial(n_samples, pooled)
        sim_cond = rng.binomial(n_samples, pooled)
        null_fracs[s] = np.mean(
            ((sim_ref / n_samples) > 0.5) != ((sim_cond / n_samples) > 0.5)
        )
    extreme = int(np.sum(null_fracs >= observed - 1e-12))
    p_value = (extreme + 1) / (n_sim + 1)
    return {
        "observed": observed,
        "null_mean": float(null_fracs.mean()),
        "p_value": float(p_value),
        "n": n_items,
    }


def across_sample_sd_delta(ref_values_by_item: dict, cond_values_by_item: dict) -> list:
    """Per-item across-sample SD deltas for E3 (continuous indicators only).

    Each dict maps item_id -> list of that item's per-sample values in the
    reference / condition. Returns cond_SD - ref_SD for every item present in
    both with at least two samples. E3/H4 is not defined for binary indicators
    (see PREREGISTRATION §4, amended 2026-08-09), so callers pass scored
    indicators only.
    """
    deltas = []
    for item in sorted(set(ref_values_by_item) & set(cond_values_by_item)):
        ref = np.asarray(ref_values_by_item[item], float)
        cond = np.asarray(cond_values_by_item[item], float)
        if len(ref) < 2 or len(cond) < 2:
            continue
        deltas.append(float(cond.std(ddof=1) - ref.std(ddof=1)))
    return deltas


def _isnan(value) -> bool:
    try:
        return math.isnan(value)
    except TypeError:
        return False
