#!/usr/bin/env python3
"""Direction-specificity read of a steered effect against a matched-norm
random-direction envelope (the Study 3 grader/random-envelope verdicts,
Study 4 Gate 1).

Reads one experiment's judge scores from the store and, per rubric
dimension, computes the item-paired effect of each treatment cell (a
steered direction at some alpha) against the alpha = 0 reference cell,
then places that effect in the envelope of the same statistic over K
random directions of the same norm and alpha: the signed percentile
(share of random effects at or below the treatment effect) and the
two-sided exceedance count (random effects at least as large in
magnitude). A treatment effect that a random direction of the same size
matches is generic perturbation, not evidence about the direction.

Effects are means over items of (treatment item mean − reference item
mean), so cells with different samples per item pair cleanly; the
report records each cell's samples per item because the envelope cells
are typically one sample per item and hence noisier than the treatment
cells. A sign-flip permutation p-value over the paired item deltas is
reported alongside as a within-cell reference — it answers "is the
effect nonzero," not "is it direction-specific," which is the
envelope's question.

    python3 experiments/quant-welfare/tools/envelope_verdict.py \\
        --data-root data --experiment s4-gate1-welfare-1 \\
        --reference qwen3-14b-bf16-torch \\
        --treatments qwen3-14b-bf16-torch-graderL24-a40,qwen3-14b-bf16-torch-graderL24-a80 \\
        --envelope-prefix qwen3-14b-bf16-torch-randL24-a80- \\
        --out experiments/quant-welfare/study4/gate1-welfare-verdict.json
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
REPO = BASE.parents[1]
for path in (str(REPO / "core/src"),):
    if path not in sys.path:
        sys.path.insert(0, path)

from modelwelfare import stats  # noqa: E402
from modelwelfare.analysis import dimension_means, paired_item_deltas  # noqa: E402
from modelwelfare.store import ResultStore  # noqa: E402
from modelwelfare.v1 import scoring_pb2, transcript_pb2  # noqa: E402


def envelope_summary(effect: float, envelope_effects: dict) -> dict:
    """Place one effect in a random-direction envelope.

    ``percentile`` is the share (0–100) of envelope effects at or below
    the signed effect; ``n_exceed`` counts envelope effects whose
    magnitude is at least the effect's magnitude, and ``p_two_sided`` is
    the corresponding (n_exceed + 1) / (K + 1) exceedance probability —
    the same +1 convention as the permutation tests, so it is never
    exactly zero."""
    values = list(envelope_effects.values())
    k = len(values)
    if k == 0:
        raise ValueError("empty envelope")
    mean = sum(values) / k
    var = sum((v - mean) ** 2 for v in values) / (k - 1) if k > 1 else 0.0
    ordered = sorted(abs(v) for v in values)
    at_or_below = sum(1 for v in values if v <= effect)
    n_exceed = sum(1 for v in values if abs(v) >= abs(effect))
    return {
        "effect": effect,
        "envelope_n": k,
        "envelope_mean": mean,
        "envelope_sd": var ** 0.5,
        "envelope_absmax": ordered[-1],
        "envelope_abs95": ordered[max(0, int(round(0.95 * (k - 1))))],
        "percentile": 100.0 * at_or_below / k,
        "n_exceed": n_exceed,
        "p_two_sided": (n_exceed + 1) / (k + 1),
    }


def condition_effect(means: dict, treatment: str, reference: str, items) -> tuple:
    """(mean paired effect, {item: delta}) of ``treatment`` over ``reference``
    for one dimension's (condition, item) means, over an explicit item list."""
    treatment_means = {item: v for (c, item), v in means.items() if c == treatment}
    reference_means = {item: v for (c, item), v in means.items() if c == reference}
    paired_items, deltas = paired_item_deltas(treatment_means, reference_means, items)
    return sum(deltas) / len(deltas), dict(zip(paired_items, deltas))


def shared_items(means: dict, conditions) -> list:
    """Items scored in every one of ``conditions`` (sorted), so every
    effect in the report is over one item list."""
    per_condition = defaultdict(set)
    for condition, item in means:
        per_condition[condition].add(item)
    common = None
    for condition in conditions:
        items = per_condition.get(condition, set())
        common = items if common is None else common & items
    return sorted(common or [])


def samples_per_item(store, experiment_id, condition_id) -> dict:
    counts = defaultdict(int)
    for record in store.read(transcript_pb2.SampleRecord, experiment_id, condition_id, "samples"):
        counts[record.key.item_id] += 1
    return dict(counts)


_DOSE = re.compile(r"-a(\d+(?:\.\d+)?)(?:-|$)")


def condition_dose(condition_id: str):
    """The steering dose a condition id carries under the ``…-a<dose>``
    naming (``-graderL36-a20``, ``-randL18-a1.039-r07``), as a float, or
    None when the id does not name one."""
    match = _DOSE.search(condition_id)
    return float(match.group(1)) if match else None


def envelope_dose(envelope, treatment_doses=None):
    """The one dose every envelope cell was generated at, or None when the
    ids do not name a dose. An envelope mixing doses is refused: a
    specificity read is a same-size comparison by definition."""
    doses = {condition_dose(c) for c in envelope}
    doses.discard(None)
    if len(doses) > 1:
        raise ValueError(f"the envelope mixes doses {sorted(doses)}; one envelope per dose")
    return doses.pop() if doses else None


def treatment_dose(treatment, treatment_doses=None):
    override = (treatment_doses or {}).get(treatment)
    return float(override) if override is not None else condition_dose(treatment)


def resolve_envelope_dose(envelope, declared=None):
    """The dose the envelope was generated at: from the ids, or from
    ``declared`` when the ids name none. Both known and different is a
    contradiction; neither known is refused — a placement is a same-size
    comparison and cannot be made against an envelope of unknown size."""
    named = envelope_dose(envelope)
    if named is not None and declared is not None and float(declared) != named:
        raise ValueError(
            f"the envelope ids name dose {named} but --envelope-dose says {declared}")
    if named is None and declared is None:
        raise ValueError(
            "the envelope ids name no dose and none was given (--envelope-dose); "
            "a specificity read needs the envelope's dose to be a same-size comparison")
    return named if named is not None else float(declared)


def verdict(store, experiment_id, reference, treatments, envelope, dimensions=None,
            items=None, treatment_doses=None, envelope_dose_declared=None) -> dict:
    """The full report: per dimension, each treatment's paired effect,
    permutation p, per-item deltas, and its envelope placement, plus the
    envelope's per-direction effects and every cell's samples per item.

    The envelope is a same-size null: its dose must be known (from its
    ids or ``envelope_dose_declared``), every treatment's dose must be
    known (from its id or ``treatment_doses``), and a treatment is placed
    in the envelope only when the two are equal. A treatment at another
    dose gets its effect and permutation test but no placement
    (``envelope`` None, with a note)."""
    conditions = [reference] + list(treatments) + list(envelope)
    env_dose = resolve_envelope_dose(envelope, envelope_dose_declared)
    doses = {}
    for treatment in treatments:
        dose = treatment_dose(treatment, treatment_doses)
        if dose is None:
            raise ValueError(
                f"{treatment}: no dose in the id and none given (--treatment-dose) "
                f"while the envelope is at dose {env_dose}; cannot decide whether "
                "the specificity read is same-size")
        doses[treatment] = dose
    scores = []
    for condition in conditions:
        scores += list(store.read(scoring_pb2.JudgeScore, experiment_id, condition, "scores"))
    if not scores:
        raise SystemExit(f"no scores under {experiment_id} for {conditions}")
    if dimensions is None:
        dimensions = sorted({entry.dimension for score in scores for entry in score.scores})

    report = {
        "experiment": experiment_id,
        "reference": reference,
        "treatments": list(treatments),
        "treatment_doses": doses,
        "envelope": list(envelope),
        "envelope_dose": env_dose,
        "samples_per_item": {c: samples_per_item(store, experiment_id, c) for c in conditions},
        "dimensions": {},
    }
    for dimension in dimensions:
        means = dimension_means(scores, dimension)
        paired_items = list(items) if items else shared_items(means, conditions)
        if not paired_items:
            raise SystemExit(f"no item scored in every condition for {dimension!r}")
        envelope_effects = {
            direction: condition_effect(means, direction, reference, paired_items)[0]
            for direction in envelope
        }
        entry = {"items": paired_items, "envelope_per_direction": envelope_effects,
                 "treatments": {}}
        for treatment in treatments:
            effect, per_item = condition_effect(means, treatment, reference, paired_items)
            if doses[treatment] == env_dose:
                summary = envelope_summary(effect, envelope_effects)
            else:
                summary = {"effect": effect, "envelope": None,
                           "note": (f"treatment dose {doses[treatment]} differs from the "
                                    f"envelope dose {env_dose}; no specificity read — "
                                    "the envelope is a same-size null")}
            summary["dose"] = doses[treatment]
            summary["permutation"] = stats.paired_permutation_test(list(per_item.values()))
            summary["per_item_delta"] = per_item
            entry["treatments"][treatment] = summary
        report["dimensions"][dimension] = entry
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--reference", required=True, help="alpha = 0 condition id")
    parser.add_argument("--treatments", required=True,
                        help="comma-separated steered condition ids")
    parser.add_argument("--envelope", default="",
                        help="comma-separated random-direction condition ids")
    parser.add_argument("--envelope-prefix", default="",
                        help="alternatively, every condition id under the "
                             "experiment starting with this prefix")
    parser.add_argument("--dimensions", default="",
                        help="comma-separated rubric dimensions (default: all scored)")
    parser.add_argument("--items", default="",
                        help="file of item ids, one per line (default: items "
                             "scored in every cell)")
    parser.add_argument("--treatment-dose", action="append", default=[],
                        metavar="CONDITION=DOSE",
                        help="the dose of a treatment whose id does not name "
                             "one (repeatable); a treatment is placed in the "
                             "envelope only at the envelope's dose")
    parser.add_argument("--envelope-dose", type=float, default=None,
                        help="the dose the envelope was generated at, when its "
                             "condition ids do not name one")
    parser.add_argument("--out", default="", help="write the JSON report here")
    args = parser.parse_args()
    treatment_doses = {}
    for spec in args.treatment_dose:
        condition, _, dose = spec.rpartition("=")
        if not condition or not dose:
            raise SystemExit(f"--treatment-dose {spec!r} is not CONDITION=DOSE")
        treatment_doses[condition] = float(dose)

    store = ResultStore(args.data_root)
    envelope = [c for c in args.envelope.split(",") if c]
    if args.envelope_prefix:
        root = Path(args.data_root) / args.experiment
        envelope += sorted(p.name for p in root.iterdir()
                           if p.is_dir() and p.name.startswith(args.envelope_prefix))
    if not envelope:
        raise SystemExit("no envelope conditions given")
    dimensions = [d for d in args.dimensions.split(",") if d] or None
    items = None
    if args.items:
        items = [line.strip() for line in Path(args.items).read_text().splitlines()
                 if line.strip()]

    try:
        report = verdict(store, args.experiment, args.reference,
                         [c for c in args.treatments.split(",") if c],
                         envelope, dimensions, items, treatment_doses,
                         envelope_dose_declared=args.envelope_dose)
    except ValueError as error:
        raise SystemExit(str(error))
    for dimension, entry in report["dimensions"].items():
        print(f"== {dimension} ({len(entry['items'])} items, "
              f"K={len(entry['envelope_per_direction'])} random directions) ==")
        for treatment, summary in entry["treatments"].items():
            if summary.get("envelope", "") is None:
                print(f"  {treatment}: effect {summary['effect']:+.3f} "
                      f"(perm p={summary['permutation']['p_value']:.3f}); "
                      f"no envelope placement — {summary['note']}")
                continue
            print(f"  {treatment}: effect {summary['effect']:+.3f} "
                  f"(perm p={summary['permutation']['p_value']:.3f}); "
                  f"envelope mean {summary['envelope_mean']:+.3f} sd {summary['envelope_sd']:.3f} "
                  f"abs95 {summary['envelope_abs95']:.3f}; "
                  f"percentile {summary['percentile']:.1f}, "
                  f"{summary['n_exceed']}/{summary['envelope_n']} random >= |effect| "
                  f"(p={summary['p_two_sided']:.3f})")
    if args.out:
        Path(args.out).write_text(json.dumps(report, indent=1))
        print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
