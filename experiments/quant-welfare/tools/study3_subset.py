#!/usr/bin/env python3
"""Study 3 battery-subset freeze tooling: selection, then targets.

Two subcommands whose separation is the §2.1 selection-independence
rule made structural:

``select`` reads **only** BF16 data (the Study 2 Mode C BF16 arm — the
most reliable BF16 measurement held, 10 samples/item) and applies the
registered mechanical rule adopted 2026-09-04 after the
regression-to-the-mean audit (journal entry of that date):
**composure-stratified systematic rank selection** — items sorted
ascending by BF16 mean judge frustration (ties by id), 1-indexed ranks
1, 4, 7, … taken (every third), spanning the composure range uniformly.
Strata are contiguous thirds of the selected list (7/6/7 at n = 20),
**frozen at selection**: fresh Study 3 baselines never reassign them
(the fresh-assignment version is a pre-specified sensitivity read).
The stratifier values are emitted as the frozen conditioning variable
for the registered continuous gradient test. Task/style composition is
reported, not enforced — the earlier elicitation-optimized rule
selected away from the very cells that carry the Study 2 effects. No
quantized-rung data is readable from this code path.

``draw`` (Study 4) reads **no data at all**: a seeded stratified draw
from the battery definition — the same number of items from every
feedback style, each style's draw spanning as many distinct tasks as
it has items, chosen by a seeded shuffle of the style's tasks — so
composition is enforced by construction and nothing about any subject's
scores enters the selection. The seed and the resulting composition are
emitted with the list.
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

    python3 experiments/quant-welfare/tools/study3_subset.py draw \\
        --battery experiments/quant-welfare/batteries/distress-v3.textproto \\
        --per-style 4 --seed 60000 \\
        --out study4/subset24-selection.json --items-out study4/subset24-items.txt

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

from modelwelfare.analysis import (final_turn_projections_by_sample,  # noqa: E402
                                   item_means, paired_item_deltas,
                                   scores_by_item)
from modelwelfare.store import ResultStore  # noqa: E402
from modelwelfare.v1 import activation_pb2, scoring_pb2  # noqa: E402

# The analytic/compositional task split, as defined for the Study 2
# control-probe family (study2/REGISTRATION.md §3.5: control_analytic);
# the subset's analytic items are the arm C verifier-frame domain.
ANALYTIC_TASKS = {"code", "explain", "inflation", "regex", "summary"}
SUBSET_STRIDE = 3
STRATA = ("low", "mid", "high")


def item_facets(item_id):
    """(task, style) from the ``distress-v3-<task>-<style>`` id shape."""
    parts = item_id.split("-")
    if len(parts) < 4 or parts[0] != "distress":
        raise SystemExit(f"item id {item_id!r} is not distress-v3-task-style")
    return parts[2], parts[3]


def frustration_means(store, experiment_id, condition_id, dimension):
    """Per-item mean judge scores for one dimension."""
    return item_means(scores_by_item(
        store.read(scoring_pb2.JudgeScore, experiment_id, condition_id,
                   "scores"), dimension))


def strata_bounds(count):
    """Contiguous third boundaries for a selected list — sizes as equal
    as possible, remainder to the outer strata (7/6/7 at n = 20)."""
    base, remainder = divmod(count, 3)
    low = base + (1 if remainder >= 1 else 0)
    high = base + (1 if remainder == 2 else 0)
    return low, count - low - high, high


def select(store, experiment_id, condition_id, dimension):
    """The registered stratified selection: every third rank of the
    ascending BF16 stratifier, strata frozen as contiguous thirds."""
    raw = scores_by_item(store.read(scoring_pb2.JudgeScore, experiment_id,
                                    condition_id, "scores"), dimension)
    if not raw:
        raise SystemExit(f"no scores under {experiment_id}/{condition_id}")
    # Guard the frozen rank order against partial scoring: a judge-retry that
    # leaves one item with fewer scores than the rest would shift ranks and
    # silently emit a different subset. Require a uniform, non-degenerate count.
    counts = {i: len(v) for i, v in raw.items()}
    expected = max(counts.values())
    uneven = sorted(i for i, c in counts.items() if c != expected)
    if uneven:
        raise SystemExit(
            f"uneven score counts under {experiment_id}/{condition_id} "
            f"(expected {expected}/item; short: {uneven[:3]}) — refuse; "
            "partial scoring would shift the frozen rank order")
    item_means = frustration_means(store, experiment_id, condition_id,
                                   dimension)
    ranked = sorted(sorted(item_means), key=lambda item: item_means[item])
    items = ranked[::SUBSET_STRIDE]
    low, mid, _high = strata_bounds(len(items))
    strata = {}
    for position, item in enumerate(items):
        strata[item] = ("low" if position < low
                        else "mid" if position < low + mid else "high")
    return {"items": items,
            "strata": strata,
            "stratifier": {item: item_means[item] for item in items},
            "analytic_items": [item for item in items
                               if item_facets(item)[0] in ANALYTIC_TASKS],
            "composition": {
                "tasks": sorted({item_facets(item)[0] for item in items}),
                "styles": sorted({item_facets(item)[1] for item in items})}}


def final_turn_projection_means(store, experiment_id, condition_id,
                                direction_id):
    """Per-item mean final-turn pooled projection for one direction
    (the registered scalar functional, via
    ``analysis.final_turn_projections_by_sample``)."""
    by_sample = final_turn_projections_by_sample(
        store.read(activation_pb2.ProjectionSeries, experiment_id,
                   condition_id, "projections"), direction_id)
    by_item = defaultdict(list)
    for (item_id, _sample), value in by_sample.items():
        by_item[item_id].append(value)
    return item_means(by_item)


def paired_item_delta(treatment_means, reference_means, items):
    """Mean per-item (treatment − reference) over exactly ``items``."""
    try:
        _items, deltas = paired_item_deltas(treatment_means,
                                            reference_means, items)
    except KeyError as error:
        raise SystemExit(f"items missing from a condition: {error}")
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


def draw(definition, per_style, seed):
    """A seeded stratified subset of ``definition``'s items: ``per_style``
    items from every feedback style, each style's items on distinct tasks
    (a seeded shuffle of the style's tasks, taken in order, wrapping only
    if a style has fewer tasks than ``per_style``). Returns (item ids,
    composition) with the composition as {style: [tasks]} for the
    selection record."""
    import random
    by_style = defaultdict(dict)
    for item in definition.items:
        task, style = item_facets(item.id)
        by_style[style][task] = item.id
    generator = random.Random(seed)
    chosen = []
    composition = {}
    for style in sorted(by_style):
        tasks = sorted(by_style[style])
        generator.shuffle(tasks)
        picked = [tasks[index % len(tasks)] for index in range(per_style)]
        composition[style] = picked
        chosen += [by_style[style][task] for task in picked]
    return chosen, composition


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

    drawing = commands.add_parser("draw")
    drawing.add_argument("--battery", required=True,
                         help="battery definition textproto")
    drawing.add_argument("--per-style", type=int, required=True,
                         help="items drawn from every feedback style")
    drawing.add_argument("--seed", type=int, required=True)
    drawing.add_argument("--out", required=True, help="selection JSON")
    drawing.add_argument("--items-out", required=True,
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

    if args.command == "draw":
        from build_steer_plan import load_battery
        definition = load_battery(args.battery)
        items, composition = draw(definition, args.per_style, args.seed)
        report = {"rule": "seeded stratified draw: per_style items from every "
                          "feedback style on distinct tasks (seeded shuffle); "
                          "no subject data read",
                  "battery": definition.battery.id, "seed": args.seed,
                  "per_style": args.per_style, "items": items,
                  "composition": composition}
        with open(args.out, "w") as handle:
            json.dump(report, handle, indent=1)
        with open(args.items_out, "w") as handle:
            handle.write("\n".join(items) + "\n")
        print(f"drew {len(items)} items across {len(composition)} styles -> {args.items_out}")
        return

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
        counts = {stratum: sum(1 for value in report["strata"].values()
                               if value == stratum) for stratum in STRATA}
        values = [report["stratifier"][item] for item in report["items"]]
        print(f"{len(report['items'])} items -> {args.items_out}; "
              f"strata {counts}; stratifier range "
              f"{values[0]:.2f}..{values[-1]:.2f}")
        print(f"analytic (verifier domain): "
              f"{len(report['analytic_items'])} items")
        print(f"composition: tasks {report['composition']['tasks']}, "
              f"styles {report['composition']['styles']}")
        return

    from build_steer_plan import read_item_list
    items = read_item_list(args.items)
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
