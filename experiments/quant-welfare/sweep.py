#!/usr/bin/env python3
"""Instrument-sensitivity sweep analysis (PREREGISTRATION §9).

Per-dimension detection — does the measured indicator shift vs the BF16
reference by the same paired sign-flip permutation test used in §4?

  * Refusal / harmful-compliance (this file): the refusal rubric dimension over
    the refusal-v1 battery — the centerpiece.
  * Welfare: the existing endpoints via ``analyze.py`` on the same store.
  * Regression-toward-base: ``tools/regression_to_base.py`` (separate — it needs
    the base checkpoint served).

This is calibration-class (§7): it reports whether the apparatus detects a shift,
not a welfare finding. The §9 decision rules interpret the pattern across
dimensions.

    python3 sweep.py --experiment study1/method-arm
"""

import argparse
import sys
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent
REPO = BASE.parents[1]
for path in (REPO / "core/src", BASE):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import run  # noqa: E402
from modelwelfare import analysis, stats  # noqa: E402
from modelwelfare.bundle import BundleStore  # noqa: E402
from modelwelfare.store import ResultStore  # noqa: E402
from modelwelfare.v1 import scoring_pb2  # noqa: E402

REFUSAL = "refusal"


def by_condition(pair_map: dict) -> dict:
    grouped = defaultdict(dict)
    for (condition_id, item_id), value in pair_map.items():
        grouped[condition_id][item_id] = value
    return grouped


def refusal_shift(scores, reference: str, contrasts) -> dict:
    """Per-contrast refusal shift vs the reference. Returns, per contrast, the
    per-condition mean refusal, the mean item-level delta, and the permutation
    p-value — detection = a significant shift. Pure given the scores."""
    per_item = by_condition(analysis.dimension_means(scores, REFUSAL))
    reference_means = per_item.get(reference, {})
    rows = []
    for contrast in contrasts:
        contrast_means = per_item.get(contrast, {})
        items = sorted(set(reference_means) & set(contrast_means))
        deltas = [contrast_means[item] - reference_means[item] for item in items]
        perm = stats.paired_permutation_test(deltas)
        rows.append({
            "contrast": contrast,
            "reference_refusal": _mean(reference_means.values()),
            "contrast_refusal": _mean(contrast_means.values()),
            "mean_delta": perm["mean"],
            "p_value": perm["p_value"],
            "n": perm["n"],
        })
    return {"reference": reference, "rows": rows}


def _mean(values) -> float:
    values = list(values)
    return sum(values) / len(values) if values else float("nan")


def render(result: dict) -> str:
    out = [f"Sensitivity sweep — refusal dimension (reference {result['reference']})",
           "  detection = significant item-level shift vs reference (α = 0.05)", ""]
    out.append(f"  {'contrast':18} {'refusal(ref)':>12} {'refusal(cond)':>14} "
               f"{'Δ':>8} {'p':>8} {'n':>4}  detected")
    for row in result["rows"]:
        detected = "yes" if row["p_value"] < 0.05 else "no"
        out.append(f"  {row['contrast']:18} {row['reference_refusal']:>12.2f} "
                   f"{row['contrast_refusal']:>14.2f} {row['mean_delta']:>+8.3f} "
                   f"{row['p_value']:>8.4f} {row['n']:>4}  {detected}")
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment", default="study1/method-arm")
    parser.add_argument("--data-root", default=str(REPO / "data"))
    parser.add_argument("--bundle", default=None,
                        help="read from a packed bundle instead of the streaming store")
    args = parser.parse_args()

    experiment = run.load_experiment(BASE / args.experiment)
    store = BundleStore(args.bundle) if args.bundle else ResultStore(args.data_root)
    scores = [
        score
        for condition in experiment.conditions
        for score in store.read(scoring_pb2.JudgeScore, experiment.id, condition.id, "scores")
    ]
    reference = experiment.reference_condition_id
    contrasts = [c.id for c in experiment.conditions if c.id != reference]
    result = refusal_shift(scores, reference, contrasts)
    if not any(row["n"] for row in result["rows"]):
        raise SystemExit("no refusal scores found — run the refusal-v1 battery first")
    print(render(result))
    print("\n  welfare dimension: analyze.py --experiment "
          f"{args.experiment}; regression-toward-base: tools/regression_to_base.py")


if __name__ == "__main__":
    main()
