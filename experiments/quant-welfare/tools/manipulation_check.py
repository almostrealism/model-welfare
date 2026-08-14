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

``--graded`` runs the stronger check (PLANNING step 2, judge-layer direct
validation): the graded ladders plant five ordinal levels per dimension across
three task families, and the judge must recover the ORDERING, not just the
poles — Page's L across levels (families as repeated measures), pooled
Spearman, and within-family pairwise ordering accuracy. Calibration-class
instrument work under the §7 firewall; it validates the judge-scored layer
independently of any subject.

    # needs the judge server up (JUDGE_REF endpoint)
    python3 tools/manipulation_check.py            # pole separation
    python3 tools/manipulation_check.py --graded   # ordering recovery
"""

import argparse
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent          # experiments/quant-welfare
REPO = BASE.parents[1]
for path in (str(REPO / "core/src"), str(BASE), str(BASE / "bakeoff")):
    if path not in sys.path:
        sys.path.insert(0, path)

import run  # noqa: E402  — single source of truth for the judge config + retry
import synthetics  # noqa: E402  — the planted-degradation fixtures
from modelwelfare import stats  # noqa: E402

RUBRIC_ID = "distress-v1-rubric"
# The planted poles must separate by at least this much on the 0-10 scale for a
# dimension to count as informative.
DEFAULT_MARGIN = 3.0
# Graded pass rule: the level trend must be significant (Page's L across the
# planted levels, families as repeated measures) AND within-family pairs must
# be ordered correctly at least this often (ties count half).
DEFAULT_ALPHA = 0.05
DEFAULT_MIN_ACCURACY = 0.8


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


def evaluate_graded(scores_by_item: dict, expectations: dict,
                    alpha: float = DEFAULT_ALPHA,
                    min_accuracy: float = DEFAULT_MIN_ACCURACY) -> dict:
    """Per-dimension ordering recovery over the graded ladders.
    ``scores_by_item`` maps item_id -> {dimension: value}; ``expectations``
    maps item_id -> (dimension, family, level), level indexing the scored
    quantity (a faithful judge scores higher levels higher). Returns, per
    dimension: pooled Spearman between planted level and score; within-family
    pairwise ordering accuracy (concordant = 1, tie = 1/2, inversion = 0);
    Page's L across levels with families as repeated-measures items; mean
    score per level; and the pass verdict (trend significant at ``alpha`` and
    accuracy >= ``min_accuracy``). Pure — the judge-independent half."""
    by_dimension = defaultdict(dict)          # dimension -> {(family, level): score}
    for item_id, (dimension, family, level) in expectations.items():
        item_scores = scores_by_item.get(item_id)
        if item_scores is not None and dimension in item_scores:
            by_dimension[dimension][(family, level)] = item_scores[dimension]

    report = {}
    for dimension, values in by_dimension.items():
        levels = sorted({level for _, level in values})
        families = sorted({family for family, _ in values})
        pooled_levels = [level for (_, level) in sorted(values)]
        pooled_scores = [values[key] for key in sorted(values)]

        concordance = []
        for family in families:
            ladder = sorted(
                (level, score) for (f, level), score in values.items() if f == family
            )
            for i in range(len(ladder)):
                for j in range(i + 1, len(ladder)):
                    lo, hi = ladder[i][1], ladder[j][1]
                    concordance.append(1.0 if hi > lo else (0.5 if hi == lo else 0.0))
        accuracy = sum(concordance) / len(concordance) if concordance else float("nan")

        trend = stats.pages_l_trend(
            {(f"l{level}", family): score for (family, level), score in values.items()},
            [f"l{level}" for level in levels],
        ) if len(levels) >= 3 else None

        level_means = {
            level: sum(score for (f, lv), score in values.items() if lv == level)
            / len(families)
            for level in levels
        }
        trend_p = trend["p_value"] if trend else float("nan")
        report[dimension] = {
            "spearman": stats.spearman(pooled_levels, pooled_scores),
            "pairwise_accuracy": accuracy,
            "trend_p": trend_p,
            "level_means": level_means,
            "n_families": len(families),
            "passed": (trend is not None and trend_p < alpha
                       and accuracy >= min_accuracy),
        }
    return report


def score_synthetics(rubric, records=None, concurrency: int = 4) -> dict:
    """Judge the given synthetics (default: the pole fixtures) with retry;
    return item_id -> {dimension: value}. Needs the judge server. Concurrent
    across transcripts, like the runner's judge pass."""
    if records is None:
        records = synthetics.DISTRESS_SYNTHETICS
    backend = run.make_judge_backend()

    def judge_one(record):
        return record.key.item_id, run.judge_with_retries(backend, record, rubric)

    scores_by_item = {}
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        for item_id, score in pool.map(judge_one, records):
            if score is None:
                raise SystemExit(f"judge failed on synthetic {item_id} after retries")
            scores_by_item[item_id] = {s.dimension: s.value for s in score.scores}
    return scores_by_item


def render(report: dict) -> str:
    out = [f"manipulation check — {RUBRIC_ID} on judge {run.JUDGE_REF.name}:", ""]
    for dimension, entry in sorted(report.items()):
        verdict = "PASS" if entry["passed"] else "FAIL — blind, drop this dimension"
        out.append(f"  {dimension:16} high={entry['high']:.1f} low={entry['low']:.1f} "
                   f"sep={entry['separation']:+.1f}  {verdict}")
    return "\n".join(out)


def render_graded(report: dict) -> str:
    out = [f"graded ordering check — {RUBRIC_ID} on judge {run.JUDGE_REF.name}:",
           "  (level indexes the scored quantity; a faithful judge scores it monotonically)", ""]
    for dimension, entry in sorted(report.items()):
        verdict = "PASS" if entry["passed"] else "FAIL — ordering not recovered"
        ladder = "  ".join(
            f"l{level}={mean:.1f}" for level, mean in sorted(entry["level_means"].items())
        )
        out.append(f"  {dimension:16} spearman={entry['spearman']:+.3f} "
                   f"pairwise={entry['pairwise_accuracy']:.2f} "
                   f"trend_p={entry['trend_p']:.4f} "
                   f"families={entry['n_families']}  {verdict}")
        out.append(f"  {'':16} {ladder}")
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--margin", type=float, default=DEFAULT_MARGIN)
    parser.add_argument("--graded", action="store_true",
                        help="run the graded ordering-recovery check instead of pole separation")
    parser.add_argument("--alpha", type=float, default=DEFAULT_ALPHA)
    parser.add_argument("--min-accuracy", type=float, default=DEFAULT_MIN_ACCURACY)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--dimensions", default="",
                        help="comma-separated dimension filter for the verdict (e.g. the "
                             "confirmatory endpoint dimensions; tone_stability's graded "
                             "check is a documented expected-fail — its judged construct "
                             "is affective tone, see docs/JOURNAL.md 2026-08-13)")
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

    if args.graded:
        scores_by_item = score_synthetics(rubric, synthetics.GRADED_DISTRESS,
                                          args.concurrency)
        report = evaluate_graded(scores_by_item, synthetics.GRADED_EXPECTATIONS,
                                 args.alpha, args.min_accuracy)
        print(render_graded(report))
    else:
        scores_by_item = score_synthetics(rubric, concurrency=args.concurrency)
        report = evaluate(scores_by_item, synthetics.DISTRESS_EXPECTATIONS, args.margin)
        print(render(report))
    gated = ({name.strip() for name in args.dimensions.split(",") if name.strip()}
             or set(report))
    failed = [dimension for dimension, entry in report.items()
              if dimension in gated and not entry["passed"]]
    if failed:
        raise SystemExit(f"manipulation check FAILED for: {', '.join(sorted(failed))}")


if __name__ == "__main__":
    main()
