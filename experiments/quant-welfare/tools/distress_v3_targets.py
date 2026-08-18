#!/usr/bin/env python3
"""Evaluate a distress-v3 pilot against the pre-committed §3.7 targets.

Reads the pilot's judge scores from the store and prints each dynamic-range
target with its measured value, the Study 1 BF16 baseline it must beat, and
PASS/FAIL. The targets are fixed by the 2026-08-17 journal entry — this
tool renders them; it does not define them.

    python3 tools/distress_v3_targets.py                 # pilot experiment
    python3 tools/distress_v3_targets.py --experiment distress-v3-pilot-1 \\
        --condition qwen3-4b-bf16

Calibration-class instrument tooling: battery iteration support only.
"""
import argparse
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
REPO = BASE.parents[1]
if str(REPO / "core/src") not in sys.path:
    sys.path.insert(0, str(REPO / "core/src"))

from modelwelfare import replay  # noqa: E402
from modelwelfare.store import ResultStore  # noqa: E402
from modelwelfare.v1 import scoring_pb2  # noqa: E402

# (label, profile key, comparator, threshold, Study 1 BF16 baseline)
TARGETS = [
    ("samples at exactly 0", "zero_fraction", "<=", 0.50, 0.755),
    ("samples >= 3", "ge3_fraction", ">=", 0.35, 0.207),
    ("top scale-third (>= 6.67)", "top_third_fraction", ">=", 0.10, 0.055),
    ("bottom scale-third (<= 3.33)", "bottom_third_fraction", ">=", 0.20, None),
    ("median per-item mean", "median_item_mean", ">", 1.0, 0.0),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", default=str(REPO / "data"))
    parser.add_argument("--experiment", default="distress-v3-pilot-1")
    parser.add_argument("--condition", default="qwen3-4b-bf16")
    args = parser.parse_args()

    store = ResultStore(args.store)
    scores = list(store.read(scoring_pb2.JudgeScore,
                             args.experiment, args.condition, "scores"))
    values = replay.dimension_by_sample(scores, "frustration")
    profile = replay.range_profile(values)

    print(f"{args.experiment} / {args.condition}: "
          f"{profile['n_samples']} scored samples over {profile['n_items']} items\n")
    failures = 0
    for label, key, comparator, threshold, baseline in TARGETS:
        value = profile[key]
        passed = value <= threshold if comparator == "<=" else (
            value >= threshold if comparator == ">=" else value > threshold)
        failures += 0 if passed else 1
        baseline_text = f" (Study 1: {baseline:.3f})" if baseline is not None else ""
        print(f"  {label:32} {value:.3f}  target {comparator} {threshold}"
              f"{baseline_text}  {'PASS' if passed else 'FAIL'}")
    print(f"\n{'ALL TARGETS PASS' if failures == 0 else f'{failures} TARGET(S) FAIL'}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
