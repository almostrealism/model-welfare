#!/usr/bin/env python3
"""Regression-to-the-mean audit for select-on-baseline delta claims.

Built for the 2026-09-04 composure-concentration finding (journal:
docs/journal/study3-steering.md, entry of that date) and kept as a tool
because the failure shape is general: whenever items are selected by
their baseline mean and a delta is then quoted against that same
baseline, part of the quoted delta is the selection's own sampling
noise flowing back (and, where two instruments share conversations,
the bias transmits across instruments). The audit:

- **split-half**: selection on one sample-index-parity half of the
  baseline, deltas measured against the held-out half (treatment uses
  all its samples — its noise is independent of any baseline
  selection); both parities run and averaged;
- **pure-noise gauge**: held-half minus selection-half baseline
  pseudo-delta on the selected items — the direct, simulation-free
  measurement of the noise pull (compare it to naive − clean);
- **continuous read**: rank correlation of the selection-half baseline
  with the held-half-cleaned delta, alongside the extreme-k bins;
- **variance decomposition**: between-item variance of baseline means
  against the mean sampling variance of those means (the signal share
  of the selector).

Selection is on judge scores (one dimension); audited endpoints are
that dimension plus any frozen-direction final-turn projections.
Everything reads the streaming store; nothing is written but the JSON
report.

    python3 experiments/quant-welfare/tools/composure_audit.py \\
        --data-root data --experiment quant-welfare-s2-modec-1 \\
        --reference qwen3-4b-bf16 --treatment qwen3-4b-rtn-w4 \\
        --direction distress-contrast --direction assistant-axis-contrast \\
        --subset-size 20 --out audit.json
"""

import argparse
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
REPO = BASE.parents[1]
for path in (str(REPO / "core/src"), str(BASE / "tools")):
    if path not in sys.path:
        sys.path.insert(0, path)

import numpy as np  # noqa: E402

from modelwelfare import stats  # noqa: E402
from modelwelfare.store import ResultStore  # noqa: E402
from modelwelfare.v1 import activation_pb2, scoring_pb2  # noqa: E402


def per_sample_scores(store, experiment_id, condition_id, dimension):
    """{item: {sample_index: value}} for one judged dimension
    (noise-measurement passes excluded)."""
    values = {}
    for score in store.read(scoring_pb2.JudgeScore, experiment_id,
                            condition_id, "scores"):
        if score.judge_sample_index:
            continue
        for entry in score.scores:
            if entry.dimension == dimension:
                values.setdefault(score.key.item_id, {})[
                    score.key.sample_index] = entry.value
    return values


def per_sample_projections(store, experiment_id, condition_id, direction_id):
    """{item: {sample_index: final-turn pooled projection}} — the
    registered scalar functional (highest-turn length-1 series)."""
    latest = {}
    for record in store.read(activation_pb2.ProjectionSeries, experiment_id,
                             condition_id, "projections"):
        if record.direction_id != direction_id or len(record.values) != 1:
            continue
        key = (record.key.item_id, record.key.sample_index)
        if key not in latest or record.turn_index > latest[key][0]:
            latest[key] = (record.turn_index, record.values[0])
    values = {}
    for (item, sample), (_turn, value) in latest.items():
        values.setdefault(item, {})[sample] = value
    return values


def half_mean(samples, parity):
    chosen = [value for sample, value in samples.items()
              if sample % 2 == parity]
    if not chosen:
        raise SystemExit("a sample half is empty; parity split needs ≥ 2 "
                         "samples per item")
    return sum(chosen) / len(chosen)


def full_mean(samples):
    return sum(samples.values()) / len(samples)


def variance_decomposition(selector_values, items):
    means = np.array([full_mean(selector_values[item]) for item in items])
    sampling = float(np.mean(
        [np.var(list(selector_values[item].values()), ddof=1)
         / len(selector_values[item]) for item in items]))
    between = float(means.var(ddof=1))
    return {"between_item_variance": between,
            "mean_sampling_variance": sampling,
            "signal_share": 1.0 - sampling / between if between > 0 else 0.0}


def audit_endpoint(selector_values, reference_values, treatment_values,
                   items, subset_size):
    """Split-half audit rows for one endpoint, averaged over parities."""
    rows = {"naive_bottom": [], "clean_bottom": [], "clean_top": [],
            "noise_pull_bottom": [], "spearman_clean": []}
    for parity in (0, 1):
        held = 1 - parity
        selector = {item: half_mean(selector_values[item], parity)
                    for item in items}
        ranked = sorted(sorted(items), key=lambda item: selector[item])
        bottom, top = ranked[:subset_size], ranked[-subset_size:]
        rows["naive_bottom"].append(float(np.mean(
            [full_mean(treatment_values[i]) - full_mean(reference_values[i])
             for i in bottom])))
        rows["clean_bottom"].append(float(np.mean(
            [full_mean(treatment_values[i])
             - half_mean(reference_values[i], held) for i in bottom])))
        rows["clean_top"].append(float(np.mean(
            [full_mean(treatment_values[i])
             - half_mean(reference_values[i], held) for i in top])))
        rows["noise_pull_bottom"].append(float(np.mean(
            [half_mean(reference_values[i], held)
             - half_mean(reference_values[i], parity) for i in bottom])))
        clean_deltas = [full_mean(treatment_values[i])
                        - half_mean(reference_values[i], held)
                        for i in items]
        rows["spearman_clean"].append(stats.spearman(
            [selector[i] for i in items], clean_deltas))
    per_item = [full_mean(treatment_values[i]) - full_mean(reference_values[i])
                for i in items]
    report = {key: sum(values) / 2 for key, values in rows.items()}
    report["full_delta"] = float(np.mean(per_item))
    report["subset_mean_se"] = float(np.std(per_item, ddof=1)
                                     / np.sqrt(subset_size))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--reference", required=True)
    parser.add_argument("--treatment", required=True)
    parser.add_argument("--dimension", default="frustration",
                        help="the judged selection dimension (also audited)")
    parser.add_argument("--direction", action="append", default=[],
                        help="frozen direction id to audit (repeatable)")
    parser.add_argument("--subset-size", type=int, default=20)
    parser.add_argument("--out", required=True, help="JSON report path")
    args = parser.parse_args()

    store = ResultStore(args.data_root)
    selector = per_sample_scores(store, args.experiment, args.reference,
                                 args.dimension)
    items = sorted(selector)
    if not items:
        raise SystemExit("no reference scores found")
    report = {"selector": variance_decomposition(selector, items),
              "endpoints": {}}
    endpoints = {args.dimension: (
        selector, per_sample_scores(store, args.experiment, args.treatment,
                                    args.dimension))}
    for direction in args.direction:
        endpoints[direction] = (
            per_sample_projections(store, args.experiment, args.reference,
                                   direction),
            per_sample_projections(store, args.experiment, args.treatment,
                                   direction))
    for name, (reference_values, treatment_values) in endpoints.items():
        report["endpoints"][name] = audit_endpoint(
            selector, reference_values, treatment_values, items,
            args.subset_size)
    with open(args.out, "w") as handle:
        json.dump(report, handle, indent=1)
    print(f"selector signal share: "
          f"{report['selector']['signal_share']:.2f}")
    for name, entry in report["endpoints"].items():
        print(f"{name}: full {entry['full_delta']:+.4f} | bottom naive "
              f"{entry['naive_bottom']:+.4f} clean "
              f"{entry['clean_bottom']:+.4f} (noise pull "
              f"{entry['noise_pull_bottom']:+.4f}) | top clean "
              f"{entry['clean_top']:+.4f} | rho "
              f"{entry['spearman_clean']:+.3f}")


if __name__ == "__main__":
    main()
