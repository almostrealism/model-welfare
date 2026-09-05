#!/usr/bin/env python3
"""Study 3 MDE pinning under the item-random-effect error model.

Reads calibration data (two conditions of one experiment — for the
freeze, the G3b pilot's paired fresh baselines) and produces the §5
components and MDE table: pooled within-item across-sample SD, the
observed per-item delta spread, the implied item-effect SD (the
variance component the 2026-09-04 audit showed the seed-only model
omits), and MDEs at the frozen item count across the power-floor
escalation ladder (10 → 15 → 20 samples/item). Two endpoint families:

- a judged dimension (mean per-item score deltas; the SB2/CB2/FB2
  scale), components estimated from the data;
- the exit rate (SB1/CB1/FB1): binomial sampling noise from the
  observed per-item rates plus the same item-effect decomposition.

For contrasts whose treatment cells do not exist yet (the steered
arms), the two "conditions" are the paired fresh baselines — their
delta spread estimates the no-effect heterogeneity floor; the
registered convention seeds the effect-heterogeneity component from
the Study 2 per-item delta spread until fresh steered cells
re-estimate it, and ``--sigma-item`` lets the pinned value carry that
override explicitly.

    python3 experiments/quant-welfare/tools/study3_mde.py \\
        --data-root data --experiment s3-g3b-pilot-2 \\
        --reference qwen3-4b-bf16 --treatment qwen3-4b-bf16-torch \\
        --dimension frustration --items 20 --out mde-components.json
"""

import argparse
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
REPO = BASE.parents[1]
for path in (str(REPO / "core/src"),):
    if path not in sys.path:
        sys.path.insert(0, path)

import numpy as np  # noqa: E402

from modelwelfare import stats  # noqa: E402
from modelwelfare.analysis import exit_flags_by_item, scores_by_item  # noqa: E402
from modelwelfare.store import ResultStore  # noqa: E402
from modelwelfare.v1 import scoring_pb2, transcript_pb2  # noqa: E402

LADDER = (10, 15, 20)


def per_sample_scores(store, experiment_id, condition_id, dimension):
    return scores_by_item(
        store.read(scoring_pb2.JudgeScore, experiment_id, condition_id,
                   "scores"), dimension)


def per_item_exits(store, experiment_id, condition_id):
    return exit_flags_by_item(
        store.read(transcript_pb2.SampleRecord, experiment_id, condition_id,
                   "samples"))


def components(reference, treatment, k):
    """(sigma_sample, observed delta SD, sigma_item estimate) over the
    shared item set at k samples per condition. Inputs are the
    sample-indexed per-item dicts of ``analysis.scores_by_item`` /
    ``exit_flags_by_item`` (plain lists also accepted)."""
    def samples(side, item):
        values = side[item]
        return list(values.values()) if isinstance(values, dict) else values
    items = sorted(set(reference) & set(treatment))
    deltas = [float(np.mean(samples(treatment, i))
                    - np.mean(samples(reference, i))) for i in items]
    sigma_sample = float(np.sqrt(np.mean(
        [np.var(samples(reference, i), ddof=1) for i in items]
        + [np.var(samples(treatment, i), ddof=1) for i in items])))
    observed_sd = float(np.std(deltas, ddof=1))
    sigma_item = stats.sigma_item_estimate(observed_sd, sigma_sample, k)
    return {"n_items": len(items), "mean_delta": float(np.mean(deltas)),
            "sigma_sample": sigma_sample, "observed_delta_sd": observed_sd,
            "sigma_item": sigma_item}


def mde_ladder(sigma_sample, sigma_item, n_items):
    return {str(k): float(stats.mde_paired(
        stats.delta_sd_mixed(sigma_sample, k, sigma_item), n_items))
        for k in LADDER}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--reference", required=True)
    parser.add_argument("--treatment", required=True)
    parser.add_argument("--dimension", default="frustration")
    parser.add_argument("--samples", type=int, default=10,
                        help="samples/item in the calibration data")
    parser.add_argument("--items", type=int, default=20,
                        help="item count the MDEs are pinned at")
    parser.add_argument("--sigma-item", type=float, default=None,
                        help="override the item-effect SD (the registered "
                             "Study 2 seeding for not-yet-run contrasts)")
    parser.add_argument("--out", required=True, help="JSON report path")
    args = parser.parse_args()

    store = ResultStore(args.data_root)
    report = {"experiment": args.experiment,
              "reference": args.reference, "treatment": args.treatment,
              "calibration_samples": args.samples,
              "pinned_items": args.items, "endpoints": {}}

    scored = components(
        per_sample_scores(store, args.experiment, args.reference,
                          args.dimension),
        per_sample_scores(store, args.experiment, args.treatment,
                          args.dimension),
        args.samples)
    sigma_item = (args.sigma_item if args.sigma_item is not None
                  else scored["sigma_item"])
    scored["sigma_item_used"] = sigma_item
    scored["mde"] = mde_ladder(scored["sigma_sample"], sigma_item, args.items)
    report["endpoints"][args.dimension] = scored

    ref_exits = per_item_exits(store, args.experiment, args.reference)
    treat_exits = per_item_exits(store, args.experiment, args.treatment)
    exits = components(ref_exits, treat_exits, args.samples)
    rates = [float(np.mean(list(values.values()))) for values in ref_exits.values()]
    exits["binomial_sigma_sample"] = float(np.sqrt(
        np.mean([r * (1 - r) for r in rates])))
    exits["mde"] = mde_ladder(exits["binomial_sigma_sample"],
                              exits["sigma_item"], args.items)
    report["endpoints"]["exit_rate"] = exits

    with open(args.out, "w") as handle:
        json.dump(report, handle, indent=1)
    for name, entry in report["endpoints"].items():
        ladder = ", ".join(f"k={k}: {v:.3f}"
                           for k, v in entry["mde"].items())
        print(f"{name}: sigma_sample {entry.get('binomial_sigma_sample', entry['sigma_sample']):.3f}, "
              f"sigma_item {entry['sigma_item']:.3f} "
              f"(delta spread {entry['observed_delta_sd']:.3f}) | MDE {ladder}")


if __name__ == "__main__":
    main()
