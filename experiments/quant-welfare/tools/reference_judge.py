#!/usr/bin/env python3
"""Reference-judge calibration (PREREGISTRATION §4 judge validation).

Scores a deterministic stratified subsample of the confirmatory distress
transcripts with the cross-family reference judge (claude-opus-5) and reports
its agreement with the local 30B primary judge. This validates the local judge;
it is instrument/calibration-class and does NOT enter the confirmatory
endpoints — the scores land in a separate ``reference_scores`` stream so they
never mix with the primary ``scores`` the analysis reads.

Deterministic and resumable: the subsample is the first
ceil(fraction * samples_per_item) sample indices of every (condition, item), and
each transcript is deduped, so a run interrupted (or stopped when the API budget
runs out) continues exactly where it left off — just re-run it.

    python3 tools/reference_judge.py --experiment study1/confirmatory --dry-run  # count + cost estimate
    python3 tools/reference_judge.py --experiment study1/confirmatory     # score (spends API budget)
    python3 tools/reference_judge.py --experiment study1/confirmatory --report   # agreement only, no API calls
"""

import argparse
import math
import sys
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent          # experiments/quant-welfare
REPO = BASE.parents[1]
for path in (REPO / "core/src", REPO / "backends/anthropic/src", BASE):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import numpy as np  # noqa: E402

import run  # noqa: E402  — experiment/battery loading + rubric resolution
from modelwelfare.judging import JudgeError, build_prompt, judge_sample  # noqa: E402
from modelwelfare.bundle import BundleStore  # noqa: E402
from modelwelfare.store import ResultStore  # noqa: E402
from modelwelfare.v1 import common_pb2, condition_pb2, scoring_pb2, transcript_pb2  # noqa: E402

REFERENCE_KIND = "reference_scores"      # kept separate from the primary "scores"
REFERENCE_MODEL = "claude-opus-5"
REFERENCE_REF = common_pb2.ModelRef(family="claude", name=REFERENCE_MODEL, source="anthropic-api")
RETRIES = 3
# claude-opus-5 list price, USD per 1M tokens (see the claude-api reference).
PRICE_IN_PER_M, PRICE_OUT_PER_M = 5.0, 25.0
EST_OUTPUT_TOKENS = 400                  # a 3-dimension rubric verdict with rationales


def distress_items(experiment) -> set:
    """Item ids scored on a rubric (the distress battery) — the transcripts a
    judge scores."""
    batteries = run.load_batteries(BASE / "study1/confirmatory")
    items = set()
    for battery_id in experiment.battery_ids:
        definition = batteries.get(battery_id)
        if definition and definition.battery.rubric_ids:
            items.update(item.id for item in definition.items)
    return items


def rubric_for(experiment):
    batteries = run.load_batteries(BASE / "study1/confirmatory")
    for definition in batteries.values():
        for rubric in definition.rubrics:
            if rubric.id == "distress-v1-rubric":
                return rubric
    raise SystemExit("distress-v1-rubric not found")


def subsample(store, experiment, fraction: float) -> list:
    """The deterministic stratified subsample: the lowest
    ceil(fraction * samples_per_item) sample indices of every (condition,
    distress-item), across all conditions."""
    items = distress_items(experiment)
    keep = math.ceil(fraction * experiment.samples_per_item)
    records = []
    for condition in experiment.conditions:
        for record in store.read(
            transcript_pb2.SampleRecord, experiment.id, condition.id, "samples"
        ):
            if record.key.item_id in items and record.key.sample_index < keep:
                records.append(record)
    return records


def already_scored(store, experiment) -> set:
    keys = set()
    for condition in experiment.conditions:
        for score in store.read(scoring_pb2.JudgeScore, experiment.id, condition.id, REFERENCE_KIND):
            keys.add((score.key.condition_id, score.key.item_id, score.key.sample_index))
    return keys


def estimate_cost(records, rubric) -> tuple:
    """(input_tokens, output_tokens, usd) estimate, from the exact prompts —
    input via a ~4-chars/token approximation, output at a fixed rubric budget."""
    in_tokens = sum(len(build_prompt(r, rubric)) // 4 for r in records)
    out_tokens = EST_OUTPUT_TOKENS * len(records)
    usd = in_tokens * PRICE_IN_PER_M / 1e6 + out_tokens * PRICE_OUT_PER_M / 1e6
    return in_tokens, out_tokens, usd


def score(store, experiment, records, rubric, producer):
    from modelwelfare_anthropic import AnthropicBackend
    backend = AnthropicBackend(REFERENCE_MODEL)
    sampling = condition_pb2.SamplingSpec(max_tokens=640)  # temp/seed MUST stay 0 for this API
    done = already_scored(store, experiment)
    pending = [r for r in records if
               (r.key.condition_id, r.key.item_id, r.key.sample_index) not in done]
    print(f"{len(records)} in subsample, {len(records) - len(pending)} already scored, "
          f"{len(pending)} to score")
    writers = {}
    spent_in = spent_out = 0
    try:
        for i, record in enumerate(pending, 1):
            result = None
            for attempt in range(RETRIES):
                try:
                    result = judge_sample(backend, REFERENCE_REF, record, rubric, sampling=sampling)
                    break
                except (JudgeError, Exception) as error:  # noqa: BLE001 — API hiccups retry
                    print(f"  retry {attempt + 1} {record.key.item_id} "
                          f"s{record.key.sample_index}: {type(error).__name__}: {error}")
            if result is None:
                print(f"  UNSCORED {record.key.condition_id}/{record.key.item_id} "
                      f"s{record.key.sample_index}")
                continue
            cid = record.key.condition_id
            if cid not in writers:
                writers[cid] = store.writer(experiment.id, cid, REFERENCE_KIND, producer)
            writers[cid].write(result)
            values = ", ".join(f"{s.dimension}={s.value:g}" for s in result.scores)
            print(f"  [{i}/{len(pending)}] {cid}/{record.key.item_id} "
                  f"s{record.key.sample_index}: {values}")
    finally:
        for writer in writers.values():
            writer.close()


def report(store, experiment):
    """Per-dimension agreement between the local 30B primary judge (the primary
    ``scores`` stream) and the opus-5 reference (``reference_scores``), over the
    transcripts both judged."""
    def by_key(kind):
        out = {}
        for condition in experiment.conditions:
            for s in store.read(scoring_pb2.JudgeScore, experiment.id, condition.id, kind):
                key = (s.key.condition_id, s.key.item_id, s.key.sample_index)
                out[key] = {d.dimension: d.value for d in s.scores}
        return out

    local, reference = by_key("scores"), by_key(REFERENCE_KIND)
    shared = sorted(set(local) & set(reference))
    if not shared:
        print("no overlap between local and reference scores yet")
        return
    dimensions = sorted({d for k in shared for d in reference[k]})
    print(f"\nreference-judge agreement (opus-5 vs local 30B) over {len(shared)} transcripts:")
    print(f"  {'dimension':18} {'pearson_r':>9} {'mean|Δ|':>8} {'ref_mean':>9} {'local_mean':>11}")
    for dim in dimensions:
        pairs = [(local[k][dim], reference[k][dim]) for k in shared
                 if dim in local[k] and dim in reference[k]]
        if len(pairs) < 2:
            continue
        loc = np.array([p[0] for p in pairs]); ref = np.array([p[1] for p in pairs])
        r = float(np.corrcoef(loc, ref)[0, 1]) if loc.std() and ref.std() else float("nan")
        print(f"  {dim:18} {r:>9.3f} {np.abs(ref - loc).mean():>8.3f} "
              f"{ref.mean():>9.3f} {loc.mean():>11.3f}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment", default="study1/confirmatory")
    parser.add_argument("--data-root", default=str(REPO / "data"))
    parser.add_argument("--fraction", type=float, default=0.25)
    parser.add_argument("--producer", default="opus5")
    parser.add_argument("--dry-run", action="store_true",
                        help="report subsample size and cost estimate; no API calls")
    parser.add_argument("--bundle", default=None,
                        help="report agreement from packed RecordBundle file(s) "
                             "(read-only, implies --report) — the release-asset "
                             "replication path")
    parser.add_argument("--report", action="store_true",
                        help="only report agreement from already-stored scores; no API calls")
    args = parser.parse_args()

    experiment = run.load_experiment(BASE / args.experiment)
    if args.bundle:
        args.report = True  # bundles are read-only
    store = BundleStore(args.bundle) if args.bundle else ResultStore(args.data_root)
    rubric = rubric_for(experiment)

    if args.report:
        report(store, experiment)
        return

    records = subsample(store, experiment, args.fraction)
    in_tok, out_tok, usd = estimate_cost(records, rubric)
    print(f"subsample: {len(records)} distress transcripts "
          f"({args.fraction:.0%} x {experiment.samples_per_item} samples/item, all conditions)")
    print(f"estimated cost: ~{in_tok:,} input + ~{out_tok:,} output tokens -> "
          f"~${usd:.2f} at opus-5 rates (${PRICE_IN_PER_M}/${PRICE_OUT_PER_M} per 1M)")
    if args.dry_run:
        print("dry run — no API calls made")
        return

    score(store, experiment, records, rubric, args.producer)
    report(store, experiment)


if __name__ == "__main__":
    main()
