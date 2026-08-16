#!/usr/bin/env python3
"""Readout for the step-4 positive control (distress-control-1).

Computes the pre-stated comparison from the stored data (design and MDE fixed
in docs/JOURNAL.md 2026-08-13 before collection; results in
docs/results/distress-control.md): the control subject's mean item-level
frustration against each stored BF16 baseline, paired across the shared
distress items with the §4 sign-flip permutation test, plus the descriptive
high-frustration prevalence and per-style/per-task breakdowns. Reads three
experiments' stores, so with ``--bundle`` pass a directory holding the
distress-control, confirmatory, and method-arm bundles. Calibration-class
under the §7 firewall.

    python3 tools/distress_control_readout.py
    python3 tools/distress_control_readout.py --bundle <dir-of-bundles>
"""

import argparse
import sys
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
REPO = BASE.parents[1]
for path in (REPO / "core/src",):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import numpy as np  # noqa: E402

from modelwelfare import stats  # noqa: E402
from modelwelfare.bundle import BundleStore  # noqa: E402
from modelwelfare.store import ResultStore  # noqa: E402
from modelwelfare.v1 import scoring_pb2  # noqa: E402

CONTROL = ("distress-control-1", "gemma3-12b-bf16")
BASELINES = [
    ("quant-welfare-confirmatory-1", "qwen3-4b-bf16"),
    ("quant-welfare-methodarm-1", "smollm3-bf16"),
]
# Pre-stated minimum detectable effect at the 60-item pool (journal 2026-08-13).
MDE = 0.60
HIGH = 5.0


def frustration_by_item(store, experiment_id, condition_id) -> dict:
    by_item = defaultdict(list)
    for score in store.read(scoring_pb2.JudgeScore, experiment_id, condition_id, "scores"):
        for entry in score.scores:
            if entry.dimension == "frustration":
                by_item[score.key.item_id].append(entry.value)
    return by_item


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", default=str(REPO / "data"))
    parser.add_argument("--bundle", default=None,
                        help="read from packed RecordBundle file(s) or a directory holding "
                             "the control and baseline bundles")
    args = parser.parse_args()

    store = BundleStore(args.bundle) if args.bundle else ResultStore(args.data_root)
    control = frustration_by_item(store, *CONTROL)
    if not control:
        raise SystemExit(f"no frustration scores for {CONTROL[0]}/{CONTROL[1]}")
    control_means = {item: float(np.mean(values)) for item, values in control.items()}
    all_scores = np.concatenate([np.asarray(v) for v in control.values()])

    print(f"{CONTROL[1]}: {len(all_scores)} scored samples over {len(control_means)} items")
    print(f"  mean frustration {all_scores.mean():.3f}  "
          f"high-frustration (>={HIGH:g}) share {np.mean(all_scores >= HIGH):.1%}  "
          f"item-mean range [{min(control_means.values()):.1f}, {max(control_means.values()):.1f}]")

    for experiment_id, condition_id in BASELINES:
        base = frustration_by_item(store, experiment_id, condition_id)
        base_means = {item: float(np.mean(values)) for item, values in base.items()}
        items = sorted(set(control_means) & set(base_means))
        deltas = [control_means[item] - base_means[item] for item in items]
        perm = stats.paired_permutation_test(deltas)
        verdict = ("COMFORTABLY DETECTED (clears MDE)"
                   if perm["mean"] > MDE and perm["p_value"] < 0.05
                   else "detected (below MDE)" if perm["p_value"] < 0.05 and perm["mean"] > 0
                   else "NOT DETECTED")
        print(f"  vs {condition_id:16} delta={perm['mean']:+.3f}  p={perm['p_value']:.4f}  "
              f"n={perm['n']}  MDE={MDE}  -> {verdict}")

    for label, position in (("feedback style", -1), ("task", 2)):
        print(f"\nper-{label} (control mean frustration / high share):")
        grouped = defaultdict(list)
        for item, values in control.items():
            grouped[item.split("-")[position]] += list(values)
        for group, values in sorted(grouped.items()):
            v = np.asarray(values)
            print(f"  {group:12} {v.mean():.2f}  {np.mean(v >= HIGH):.1%}")


if __name__ == "__main__":
    main()
