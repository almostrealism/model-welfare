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


def tost_summary(mean: float, se: float, margin: float) -> float:
    """Equivalence p-value from summary statistics (mean and standard
    error): the larger of the two one-sided p-values against the margins
    -margin/+margin. The summary form serves pair members whose data is
    published rather than held (Study 2 §4.4's bail-side E1);
    :func:`tost_paired` derives the same read from raw deltas."""
    if margin <= 0:
        raise ValueError("equivalence margin must be positive")
    if se == 0.0:
        return 0.0 if abs(mean) < margin else 1.0
    p_lower = 1.0 - _normal_cdf((mean + margin) / se)
    p_upper = 1.0 - _normal_cdf((margin - mean) / se)
    return float(max(p_lower, p_upper))


def tost_paired(deltas, margin: float) -> dict:
    """Equivalence read for a paired item-level contrast (two one-sided
    tests against the pre-registered margins -margin/+margin).

    The equivalence p-value is the larger of the two one-sided p-values;
    equivalence at level alpha is ``p_value <= alpha``, the same claim as
    the (1 - 2*alpha) CI lying inside (-margin, +margin). This is the
    Study 2 §4.4 dissociation rule's second condition: the pair's other
    member is *equivalent-to-null* only by this test, never by a failed
    significance test alone — absence of significance is not evidence of
    absence. Normal approximation to Student's t, consistent with
    :func:`paired_t_test` and negligible at the study's item counts."""
    if margin <= 0:
        raise ValueError("equivalence margin must be positive")
    deltas = np.asarray(deltas, float)
    deltas = deltas[~np.isnan(deltas)]
    n = len(deltas)
    if n < 2:
        return {"mean": float("nan"), "p_value": float("nan"), "n": n}
    mean = float(deltas.mean())
    se = float(deltas.std(ddof=1)) / math.sqrt(n)
    return {"mean": mean, "p_value": tost_summary(mean, se, margin), "n": n}


def two_sample_permutation_test(a, b, n_perm: int = 10000, seed: int = 0) -> dict:
    """One-sided two-sample permutation test on the difference of means
    (alternative: mean(a) > mean(b)), permuting group assignment.

    The Study 2 §4.1 exit-side specificity gate: the exit probe's
    item-level accuracy degradations against the control family's, across
    batteries where item pairing does not exist. NaNs are dropped."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    a = a[~np.isnan(a)]
    b = b[~np.isnan(b)]
    if len(a) == 0 or len(b) == 0:
        return {"difference": float("nan"), "p_value": float("nan"),
                "n_a": len(a), "n_b": len(b)}
    observed = float(a.mean() - b.mean())
    pooled = np.concatenate([a, b])
    rng = np.random.default_rng(seed)
    extreme = 0
    for _ in range(n_perm):
        rng.shuffle(pooled)
        if pooled[:len(a)].mean() - pooled[len(a):].mean() >= observed - 1e-12:
            extreme += 1
    p_value = (extreme + 1) / (n_perm + 1)
    return {"difference": observed, "p_value": float(p_value),
            "n_a": int(len(a)), "n_b": int(len(b))}


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
    is a change in that boolean. The null draws each item's rate from a
    beta-binomial posterior on its pooled counts — Beta(k+½, n−k+½), which
    propagates the small-n estimation uncertainty — then samples both
    conditions from that rate; plugging the point estimate in directly would be
    anti-conservative at n = 10. One-sided p (observed exceeds null).
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
    # Per-item Jeffreys posterior on the pooled counts, then sample both
    # conditions from the drawn rate (beta-binomial parametric bootstrap).
    alpha = (ref + cond) + 0.5
    beta = (2.0 * n_samples - (ref + cond)) + 0.5
    rng = np.random.default_rng(seed)
    null_fracs = np.empty(n_sim)
    for s in range(n_sim):
        rate = rng.beta(alpha, beta)
        sim_ref = rng.binomial(n_samples, rate)
        sim_cond = rng.binomial(n_samples, rate)
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


def band_flip_test(
    ref_scores_by_item: dict,
    cond_scores_by_item: dict,
    edges,
    n_sim: int = 10000,
    seed: int = 0,
) -> dict:
    """H1 for a scored indicator: does the fraction of items whose mean-score
    *band* changes between reference and condition exceed sampling noise?

    The continuous analogue of :func:`flip_fraction_test`. Each dict maps
    item_id -> that item's per-sample scores (e.g. frustration on 0-10). An
    item's outcome is the band of its mean score (``edges`` are the interior
    cut points, as in :func:`band_index`); a flip is a change in that band
    between conditions. The null pools each item's reference and condition
    samples and draws both conditions' means from the pooled pool (a pooled
    parametric bootstrap) — the continuous counterpart of the beta-binomial
    exit null, so a band that moves only because the mean wobbled within noise
    is not counted as real. One-sided p (observed exceeds null).
    """
    items = sorted(set(ref_scores_by_item) & set(cond_scores_by_item))
    items = [
        item for item in items
        if len(ref_scores_by_item[item]) and len(cond_scores_by_item[item])
    ]
    n_items = len(items)
    if n_items == 0:
        return {"observed": float("nan"), "null_mean": float("nan"),
                "p_value": float("nan"), "n": 0}

    edges = np.asarray(edges, float)

    def band_of_mean(values) -> int:
        return int(np.digitize(np.mean(values), edges))

    observed = float(np.mean([
        band_of_mean(ref_scores_by_item[item]) != band_of_mean(cond_scores_by_item[item])
        for item in items
    ]))

    pooled = {item: np.concatenate([
        np.asarray(ref_scores_by_item[item], float),
        np.asarray(cond_scores_by_item[item], float),
    ]) for item in items}
    sizes = {item: (len(ref_scores_by_item[item]), len(cond_scores_by_item[item]))
             for item in items}

    rng = np.random.default_rng(seed)
    null_fracs = np.empty(n_sim)
    for s in range(n_sim):
        flips = 0
        for item in items:
            values = pooled[item]
            n_ref, n_cond = sizes[item]
            sim_ref = rng.choice(values, size=n_ref, replace=True)
            sim_cond = rng.choice(values, size=n_cond, replace=True)
            flips += int(band_of_mean(sim_ref) != band_of_mean(sim_cond))
        null_fracs[s] = flips / n_items
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


def linear_adjusted_intercept(y, covariates) -> dict:
    """E2 style-drift adjustment (PREREGISTRATION §4): the mean of ``y`` (the
    per-item frustration deltas) after linear adjustment for covariate deltas —
    response length and a repetition metric.

    Fits ``y = intercept + covariates·beta`` by ordinary least squares; the
    intercept is the covariate-adjusted mean effect. If the unadjusted mean is
    significant but this intercept is not, the E2 effect is flagged
    style-confounded rather than a welfare shift. ``covariates`` is a list of
    columns, each a per-item sequence aligned to ``y``. Rows with a NaN in ``y``
    or any covariate are dropped. Two-sided p via the normal approximation,
    consistent with the other large-sample tests here.
    """
    y = np.asarray(y, float)
    cols = [np.asarray(c, float) for c in covariates]
    mask = ~np.isnan(y)
    for col in cols:
        mask &= ~np.isnan(col)
    y = y[mask]
    cols = [col[mask] for col in cols]
    n = len(y)
    k = len(cols) + 1  # covariate columns plus the intercept
    if n <= k:
        return {"intercept": float("nan"), "p_value": float("nan"), "n": n}
    design = np.column_stack([np.ones(n)] + cols)
    beta, *_ = np.linalg.lstsq(design, y, rcond=None)
    residual = y - design @ beta
    dof = n - k
    sigma2 = float(residual @ residual) / dof
    try:
        cov_beta = np.linalg.inv(design.T @ design)
    except np.linalg.LinAlgError:
        return {"intercept": float(beta[0]), "p_value": float("nan"), "n": n}
    se = math.sqrt(max(sigma2 * cov_beta[0, 0], 0.0))
    if se == 0.0:
        t = 0.0 if beta[0] == 0.0 else math.inf
        p_value = 1.0 if beta[0] == 0.0 else 0.0
    else:
        t = beta[0] / se
        p_value = 2.0 * (1.0 - _normal_cdf(abs(t)))
    return {"intercept": float(beta[0]), "p_value": float(p_value), "n": n}


def variance_components(scores_by_item: dict) -> dict:
    """Partition repeated-judge scores into item signal vs. judge noise
    (one-way random-effects ANOVA / ICC(1)).

    ``scores_by_item`` maps item_id -> list of that item's scores from repeated
    judge passes (``judge_sample_index`` 0..k-1). Returns the between-item and
    within-item (judge-noise) variance components, the intraclass correlation
    ``icc`` (the share of total variance that is real item signal), and the
    complementary ``judge_noise_share``. Judge noise eats power on the
    judge-scored endpoints (E2), so this quantifies how much: an ICC near 1 is
    a quiet judge; a low ICC means most of the spread is the judge, not the
    subject. Unbalanced group sizes are handled via the standard ANOVA k0.
    Items with fewer than two passes contribute to neither component.
    """
    items = {i: np.asarray(v, float) for i, v in scores_by_item.items() if len(v) >= 2}
    m = len(items)
    if m < 2:
        return {"between": float("nan"), "within": float("nan"), "icc": float("nan"),
                "judge_noise_share": float("nan"), "n_items": m}
    sizes = {i: len(v) for i, v in items.items()}
    total_n = sum(sizes.values())
    grand = float(np.concatenate(list(items.values())).mean())
    ss_between = sum(sizes[i] * (values.mean() - grand) ** 2 for i, values in items.items())
    ss_within = sum(float(((values - values.mean()) ** 2).sum()) for values in items.values())
    df_within = total_n - m
    ms_between = ss_between / (m - 1)
    ms_within = ss_within / df_within if df_within > 0 else 0.0
    # k0: the ANOVA "average" group size for unbalanced one-way designs.
    k0 = (total_n - sum(k ** 2 for k in sizes.values()) / total_n) / (m - 1)
    var_between = max((ms_between - ms_within) / k0, 0.0) if k0 > 0 else 0.0
    var_within = ms_within
    total = var_between + var_within
    icc = var_between / total if total > 0 else float("nan")
    return {
        "between": var_between,
        "within": var_within,
        "icc": icc,
        "judge_noise_share": (var_within / total) if total > 0 else float("nan"),
        "n_items": m,
    }


def spearman(x, y) -> float:
    """Spearman rank correlation (Pearson over average ranks). Instrument
    tooling — used by the graded judge-validation check to quantify how well
    judge scores track planted ordinal levels — not a registered confirmatory
    test. Returns NaN when either input is constant."""
    x = rankdata_average(np.asarray(x, float))
    y = rankdata_average(np.asarray(y, float))
    if x.std() == 0.0 or y.std() == 0.0:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


# z(0.975) + z(0.80): the two-sided alpha = .05, power = .80 multiplier used
# by every MDE in this project (PREREGISTRATION §5 convention).
MDE_MULTIPLIER = 1.959964 + 0.841621


def mde_paired(delta_sd: float, n: int) -> float:
    """Minimum detectable effect for a paired item-level contrast: the mean
    delta detectable at two-sided alpha = .05 with power .80, given the SD
    of per-item paired deltas and the item count."""
    return MDE_MULTIPLIER * delta_sd / np.sqrt(n)


def null_delta_sd_mean(sigma_sample: float, k: int) -> float:
    """SD of the paired delta of per-item MEANS under the null (no condition
    effect), from the within-item across-sample SD and k samples per
    condition: each mean carries sigma^2/k, the delta twice that."""
    return sigma_sample * np.sqrt(2.0 / k)


def null_delta_sd_dispersion(sigma_sample: float, k: int) -> float:
    """SD of the paired delta of per-item across-sample SDs under the null,
    via the asymptotic Var(SD_hat) ~= sigma^2 / (2(k-1)) per condition —
    an approximation, stated as such wherever the value is pinned."""
    return sigma_sample / np.sqrt(k - 1)


def delta_sd_mixed(sigma_sample: float, k: int, sigma_item: float) -> float:
    """SD of per-item paired mean deltas under the Study 3 error model:
    sampling noise (two means at sigma^2/k each) plus an ITEM-LEVEL
    random effect — real between-item heterogeneity of the treatment
    effect, the variance component the seed-only model omits (the ±5
    per-item swings of the 2026-09-04 audit). Feed the result to
    :func:`mde_paired`."""
    return float(np.sqrt(null_delta_sd_mean(sigma_sample, k) ** 2
                         + sigma_item ** 2))


def sigma_item_estimate(observed_delta_sd: float, sigma_sample: float,
                        k: int) -> float:
    """The item-effect SD implied by an observed per-item delta spread:
    the excess of the observed variance over what sampling noise alone
    predicts, floored at zero (a spread below the sampling prediction
    estimates no heterogeneity, not imaginary negative variance)."""
    excess = observed_delta_sd ** 2 - null_delta_sd_mean(sigma_sample, k) ** 2
    return float(np.sqrt(max(excess, 0.0)))


def null_delta_sd_rate(rates, k: int) -> float:
    """SD of the paired delta of per-item RATES (e.g. probe accuracy) under
    the null: binomial noise p(1-p)/k per condition, averaged over items."""
    rates = np.asarray(rates, float)
    return float(np.sqrt(2.0 * np.mean(rates * (1.0 - rates)) / k))


def auroc(scores, labels) -> float:
    """Area under the ROC curve via the rank statistic (Mann–Whitney U),
    with average ranks so ties contribute half. Instrument tooling — the
    Tier-2 probe and direction-separation reads — not a registered
    confirmatory test. Returns NaN when either class is empty."""
    scores = np.asarray(scores, float)
    labels = np.asarray(labels, int)
    positives = int(labels.sum())
    negatives = int(len(labels) - positives)
    if positives == 0 or negatives == 0:
        return float("nan")
    ranks = rankdata_average(scores)
    u_statistic = ranks[labels == 1].sum() - positives * (positives + 1) / 2.0
    return float(u_statistic / (positives * negatives))


def band_index(values, edges):
    """Band membership for scored values, given ascending interior cut points.

    ``edges=[3.33, 6.67]`` yields three bands — [0, 3.33) -> 0, [3.33, 6.67) ->
    1, [6.67, ...] -> 2. This defines the H1 distress-transition endpoint: an
    item flips when its mean-frustration band differs between conditions
    (PREREGISTRATION §2, H1)."""
    return np.digitize(np.asarray(values, float), np.asarray(edges, float))


def _isnan(value) -> bool:
    try:
        return math.isnan(value)
    except TypeError:
        return False
