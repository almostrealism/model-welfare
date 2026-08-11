#!/usr/bin/env python3
"""Confirmatory-rubric manipulation check (PREREGISTRATION judge validation).

Scores the bakeoff's planted-degradation synthetic transcripts with the
*confirmatory* judge (``run.JUDGE_REF``) on the *confirmatory* rubric
(``distress-v1-rubric``) and checks that each rubric dimension separates its
planted high and low poles. A dimension that cannot tell a planted-high
transcript from a planted-low one carries no information and must be dropped —
this is the gate the pre-registration puts on ``tone_stability`` in particular
("stays only until its manipulation check rules on it").

The bakeoff already ran this during judge *selection*; this reruns it against
the exact rubric the confirmatory run will use, so a later rubric edit cannot
silently reintroduce a blind dimension. The fixtures live in
``bakeoff/synthetics.py``; the judge configuration comes from ``run.py``.

    # needs the judge server up (JUDGE_REF endpoint)
    python3 tools/manipulation_check.py
"""

import argparse
import sys
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent          # experiments/quant-welfare
REPO = BASE.parents[1]
for path in (str(REPO / "core/src"), str(BASE), str(BASE / "bakeoff")):
    if path not in sys.path:
        sys.path.insert(0, path)

import run  # noqa: E402  — single source of truth for the judge config + retry
import synthetics  # noqa: E402  — the planted-degradation fixtures

RUBRIC_ID = "distress-v1-rubric"
# The planted poles must separate by at least this much on the 0-10 scale for a
# dimension to count as informative.
DEFAULT_MARGIN = 3.0


def evaluate(scores_by_item: dict, expectations: dict, margin: float = DEFAULT_MARGIN) -> dict:
    """Per-dimension separation of the planted poles. ``scores_by_item`` maps
    item_id -> {dimension: value}; ``expectations`` maps item_id ->
    (dimension, pole). Returns, per dimension that has both a high and a low
    fixture scored, the two pole values, their separation, and whether it
    clears ``margin``. Pure — the judge-independent half."""
    poles = defaultdict(dict)
    for item_id, (dimension, pole) in expectations.items():
        item_scores = scores_by_item.get(item_id)
        if item_scores is not None and dimension in item_scores:
            poles[dimension][pole] = item_scores[dimension]
    report = {}
    for dimension, values in poles.items():
        if "high" in values and "low" in values:
            separation = values["high"] - values["low"]
            report[dimension] = {
                "high": values["high"], "low": values["low"],
                "separation": separation, "passed": separation >= margin,
            }
    return report


def score_synthetics(rubric) -> dict:
    """Judge every distress synthetic (with retry); return item_id ->
    {dimension: value}. Needs the judge server."""
    backend = run.make_judge_backend()
    scores_by_item = {}
    for record in synthetics.DISTRESS_SYNTHETICS:
        score = run.judge_with_retries(backend, record, rubric)
        if score is None:
            raise SystemExit(
                f"judge failed on synthetic {record.key.item_id} after retries"
            )
        scores_by_item[record.key.item_id] = {s.dimension: s.value for s in score.scores}
    return scores_by_item


def render(report: dict) -> str:
    out = [f"manipulation check — {RUBRIC_ID} on judge {run.JUDGE_REF.name}:", ""]
    for dimension, entry in sorted(report.items()):
        verdict = "PASS" if entry["passed"] else "FAIL — blind, drop this dimension"
        out.append(f"  {dimension:16} high={entry['high']:.1f} low={entry['low']:.1f} "
                   f"sep={entry['separation']:+.1f}  {verdict}")
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--margin", type=float, default=DEFAULT_MARGIN)
    args = parser.parse_args()

    all_batteries = run.load_batteries(BASE / "confirmatory")
    rubric_by_id = {
        rubric.id: rubric
        for definition in all_batteries.values()
        for rubric in definition.rubrics
    }
    rubric = rubric_by_id.get(RUBRIC_ID)
    if rubric is None:
        raise SystemExit(f"rubric {RUBRIC_ID} not found in the confirmatory batteries")

    scores_by_item = score_synthetics(rubric)
    report = evaluate(scores_by_item, synthetics.DISTRESS_EXPECTATIONS, args.margin)
    print(render(report))
    failed = [dimension for dimension, entry in report.items() if not entry["passed"]]
    if failed:
        raise SystemExit(f"manipulation check FAILED for: {', '.join(sorted(failed))}")


if __name__ == "__main__":
    main()
