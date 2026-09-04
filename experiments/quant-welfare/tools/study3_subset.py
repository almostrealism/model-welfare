#!/usr/bin/env python3
"""Study 3 battery-subset freeze tooling: selection, then targets.

Two subcommands whose separation is the §2.1 selection-independence
rule made structural:

``select`` reads **only** the BF16 pilot store (`distress-v3-pilot-2`)
and applies the registered mechanical rule — the 4 of 6 feedback styles
with the highest mean judge frustration, and the 3 analytic + 2
compositional tasks likewise — emitting the rankings and the 20-item
list for ``build_steer_plan.py --items``. No quantized-rung data is
readable from this code path.

``targets`` takes an **already-fixed item list** and only then reads the
Study 2 Mode C store: per-item final-turn projections (the registered
length-1 pooled ProjectionSeries) and judge frustration means for the
reference and w4 conditions, restricted to the list, yielding the
subset-restricted dose targets for §3.4 and the representativeness
disclosure (subset vs full-battery deltas, reported whichever way it
comes out).

    python3 experiments/quant-welfare/tools/study3_subset.py select \\
        --data-root data --experiment distress-v3-pilot-2 \\
        --out study3/subset-selection.json --items-out study3/subset-items.txt

    python3 experiments/quant-welfare/tools/study3_subset.py targets \\
        --data-root data --experiment quant-welfare-s2-modec-1 \\
        --reference qwen3-4b-bf16 --treatment qwen3-4b-rtn-w4 \\
        --items study3/subset-items.txt --out study3/subset-targets.json
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
REPO = BASE.parents[1]
for path in (str(REPO / "core/src"),):
    if path not in sys.path:
        sys.path.insert(0, path)

from modelwelfare.store import ResultStore  # noqa: E402
from modelwelfare.v1 import activation_pb2, scoring_pb2  # noqa: E402

# The analytic/compositional task split, as defined for the Study 2
# control-probe family (study2/REGISTRATION.md §3.5: control_analytic).
ANALYTIC_TASKS = {"code", "explain", "inflation", "regex", "summary"}
STYLE_COUNT = 4
ANALYTIC_COUNT = 3
COMPOSITIONAL_COUNT = 2


def item_facets(item_id):
    """(task, style) from the ``distress-v3-<task>-<style>`` id shape."""
    parts = item_id.split("-")
    if len(parts) < 4 or parts[0] != "distress":
        raise SystemExit(f"item id {item_id!r} is not distress-v3-task-style")
    return parts[2], parts[3]


def frustration_means(store, experiment_id, condition_id, dimension):
    """Per-item mean judge scores for one dimension."""
    sums = defaultdict(float)
    counts = defaultdict(int)
    for score in store.read(scoring_pb2.JudgeScore,
                            experiment_id, condition_id, "scores"):
        for entry in score.scores:
            if entry.dimension == dimension:
                sums[score.key.item_id] += entry.value
                counts[score.key.item_id] += 1
    return {item: sums[item] / counts[item] for item in counts}


def facet_means(item_means):
    """(style means, task means) from per-item means, macro-averaged so
    every item weighs equally within its facet."""
    styles = defaultdict(list)
    tasks = defaultdict(list)
    for item_id, mean in item_means.items():
        task, style = item_facets(item_id)
        styles[style].append(mean)
        tasks[task].append(mean)
    average = lambda values: sum(values) / len(values)  # noqa: E731
    return ({style: average(values) for style, values in styles.items()},
            {task: average(values) for task, values in tasks.items()})


def top(means, count, universe=None):
    """The ``count`` highest-mean keys (optionally within a universe),
    ties broken alphabetically so the rule is deterministic."""
    keys = [key for key in means if universe is None or key in universe]
    if len(keys) < count:
        raise SystemExit(f"need {count} candidates, have {sorted(keys)}")
    return sorted(sorted(keys), key=lambda key: -means[key])[:count]


def select(store, experiment_id, condition_id, dimension):
    """The registered mechanical selection from BF16 pilot data."""
    item_means = frustration_means(store, experiment_id, condition_id,
                                   dimension)
    if not item_means:
        raise SystemExit(f"no scores under {experiment_id}/{condition_id}")
    style_means, task_means = facet_means(item_means)
    styles = top(style_means, STYLE_COUNT)
    analytic = top(task_means, ANALYTIC_COUNT, ANALYTIC_TASKS)
    compositional = top(task_means, COMPOSITIONAL_COUNT,
                        set(task_means) - ANALYTIC_TASKS)
    tasks = analytic + compositional
    items = sorted(item_id for item_id in item_means
                   if item_facets(item_id)[0] in tasks
                   and item_facets(item_id)[1] in styles)
    expected = len(tasks) * len(styles)
    if len(items) != expected:
        raise SystemExit(f"selection produced {len(items)} items, "
                         f"expected {expected} — grid incomplete")
    return {"style_means": style_means, "task_means": task_means,
            "styles": styles, "analytic": analytic,
            "compositional": compositional, "items": items}


def final_turn_projection_means(store, experiment_id, condition_id,
                                direction_id):
    """Per-item mean final-turn pooled projection for one direction —
    the registered scalar functional: for each conversation, the
    highest-turn length-1 ProjectionSeries (token-series records carry
    longer value arrays and are excluded)."""
    latest = {}
    for record in store.read(activation_pb2.ProjectionSeries,
                             experiment_id, condition_id, "projections"):
        if record.direction_id != direction_id or len(record.values) != 1:
            continue
        key = (record.key.item_id, record.key.sample_index)
        if key not in latest or record.turn_index > latest[key][0]:
            latest[key] = (record.turn_index, record.values[0])
    by_item = defaultdict(list)
    for (item_id, _sample), (_turn, value) in latest.items():
        by_item[item_id].append(value)
    return {item: sum(values) / len(values)
            for item, values in by_item.items()}


def paired_item_delta(treatment_means, reference_means, items):
    """Mean per-item (treatment − reference) over exactly ``items``."""
    missing = [item for item in items
               if item not in treatment_means or item not in reference_means]
    if missing:
        raise SystemExit(f"items missing from a condition: {missing[:3]}")
    deltas = [treatment_means[item] - reference_means[item]
              for item in items]
    return sum(deltas) / len(deltas)


def targets(store, experiment_id, reference, treatment, items, directions,
            dimension):
    """Subset-restricted w4 deltas (the §3.4 dose targets) plus the
    full-battery values for the representativeness disclosure."""
    report = {"items": list(items), "directions": {}, "behavioral": {}}
    for direction_id in directions:
        reference_means = final_turn_projection_means(
            store, experiment_id, reference, direction_id)
        treatment_means = final_turn_projection_means(
            store, experiment_id, treatment, direction_id)
        full_items = sorted(set(reference_means) & set(treatment_means))
        report["directions"][direction_id] = {
            "subset_delta": paired_item_delta(
                treatment_means, reference_means, items),
            "full_battery_delta": paired_item_delta(
                treatment_means, reference_means, full_items),
            "full_battery_items": len(full_items),
        }
    reference_scores = frustration_means(store, experiment_id, reference,
                                         dimension)
    treatment_scores = frustration_means(store, experiment_id, treatment,
                                         dimension)
    full_items = sorted(set(reference_scores) & set(treatment_scores))
    report["behavioral"][dimension] = {
        "subset_delta": paired_item_delta(
            treatment_scores, reference_scores, items),
        "full_battery_delta": paired_item_delta(
            treatment_scores, reference_scores, full_items),
        "full_battery_items": len(full_items),
    }
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    selecting = commands.add_parser("select")
    selecting.add_argument("--data-root", required=True)
    selecting.add_argument("--experiment", required=True,
                           help="the BF16 pilot experiment id")
    selecting.add_argument("--condition", default="",
                           help="pilot condition id (default: the "
                                "store's only condition)")
    selecting.add_argument("--dimension", default="frustration")
    selecting.add_argument("--out", required=True, help="selection JSON")
    selecting.add_argument("--items-out", required=True,
                           help="item list for build_steer_plan --items")

    targeting = commands.add_parser("targets")
    targeting.add_argument("--data-root", required=True)
    targeting.add_argument("--experiment", required=True,
                           help="the Study 2 Mode C experiment id")
    targeting.add_argument("--reference", required=True,
                           help="reference condition id (BF16)")
    targeting.add_argument("--treatment", required=True,
                           help="treatment condition id (w4)")
    targeting.add_argument("--items", required=True,
                           help="the frozen item list from `select`")
    targeting.add_argument("--direction", action="append", default=[],
                           help="direction id (repeatable; default: the "
                                "two frozen steering directions)")
    targeting.add_argument("--dimension", default="frustration")
    targeting.add_argument("--out", required=True, help="targets JSON")

    args = parser.parse_args()
    store = ResultStore(args.data_root)

    if args.command == "select":
        condition = args.condition
        if not condition:
            conditions = store.conditions(args.experiment)
            if len(conditions) != 1:
                raise SystemExit(f"pass --condition; store has {conditions}")
            condition = conditions[0]
        report = select(store, args.experiment, condition, args.dimension)
        with open(args.out, "w") as handle:
            json.dump(report, handle, indent=1)
        Path(args.items_out).write_text(
            "".join(item + "\n" for item in report["items"]))
        print(f"styles: {report['styles']}")
        print(f"tasks: {report['analytic'] + report['compositional']}")
        print(f"{len(report['items'])} items -> {args.items_out}")
        return

    items = [line.strip() for line in Path(args.items).read_text().splitlines()
             if line.strip() and not line.strip().startswith("#")]
    directions = args.direction or ["distress-contrast",
                                    "assistant-axis-contrast"]
    report = targets(store, args.experiment, args.reference, args.treatment,
                     items, directions, args.dimension)
    with open(args.out, "w") as handle:
        json.dump(report, handle, indent=1)
    for direction_id, entry in report["directions"].items():
        print(f"{direction_id}: subset {entry['subset_delta']:+.4f} vs "
              f"full {entry['full_battery_delta']:+.4f} "
              f"({entry['full_battery_items']} items)")
    entry = report["behavioral"][args.dimension]
    print(f"{args.dimension}: subset {entry['subset_delta']:+.4f} vs "
          f"full {entry['full_battery_delta']:+.4f}")


if __name__ == "__main__":
    main()
