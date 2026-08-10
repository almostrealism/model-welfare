#!/usr/bin/env python3
"""Judge-noise measurement (PREREGISTRATION power story).

Re-judges a subsample of stored transcripts ``k`` times — same transcript,
distinct ``judge_sample_index`` and perturbed judge sampling — and partitions
each rubric dimension's score variance into subject signal (between transcripts)
and judge noise (within a transcript across passes) via
:func:`modelwelfare.stats.variance_components`. Judge noise eats power on the
judge-scored endpoint E2, so this quantifies how much before the confirmatory
run commits to a sample size: an ICC near 1 is a quiet judge; a low ICC means
the judge is adding most of the spread.

The extra passes are written to a separate store ``judge_noise_scores`` stream
so they never mix into the confirmatory ``scores`` that E2/E3 read. Pass 0 is
reused from the existing ``scores`` stream; only passes 1..k-1 are generated.
The judge configuration (identity, endpoint, rubric, sampling) is imported from
``run.py`` so there is one source of truth.

    # needs the judge server up (JUDGE_REF endpoint)
    python3 tools/judge_noise.py --experiment ladder-calibration --k 4 --transcripts 40
    # analysis only, from already-stored passes:
    python3 tools/judge_noise.py --experiment ladder-calibration --report-only
"""

import argparse
import random
import sys
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent          # experiments/quant-welfare
REPO = BASE.parents[1]
for path in (str(REPO / "core/src"), str(BASE)):
    if path not in sys.path:
        sys.path.insert(0, path)

import run  # noqa: E402  — single source of truth for the judge config + retry

from modelwelfare import stats  # noqa: E402
from modelwelfare.store import ResultStore  # noqa: E402
from modelwelfare.v1 import scoring_pb2, transcript_pb2  # noqa: E402

NOISE_KIND = "judge_noise_scores"


def scored_rubrics(batteries) -> dict:
    """item_id -> rubric object list, for the rubric-scored (distress) items."""
    result = {}
    for definition in batteries.values():
        if not definition.battery.rubric_ids:
            continue
        for item in definition.items:
            result[item.id] = list(definition.battery.rubric_ids)
    return result


def report_variance(scores) -> dict:
    """Variance components per rubric dimension. A "unit" is one transcript
    (condition, item, sample); its repeated values are the judge passes, so the
    within-unit component is pure judge noise. Pure function — the reporting
    half, independent of any server."""
    per_dimension = defaultdict(lambda: defaultdict(list))
    for score in scores:
        transcript = (score.key.condition_id, score.key.item_id, score.key.sample_index)
        for entry in score.scores:
            per_dimension[entry.dimension][transcript].append(entry.value)
    return {
        dimension: stats.variance_components(by_transcript)
        for dimension, by_transcript in per_dimension.items()
    }


def read_all_passes(store, experiment):
    """Pass 0 from the main ``scores`` stream plus every extra pass from
    ``judge_noise_scores``, merged."""
    scores = []
    for condition in experiment.conditions:
        for kind in ("scores", NOISE_KIND):
            scores += list(store.read(scoring_pb2.JudgeScore, experiment.id, condition.id, kind))
    return scores


def rejudge(store, experiment, batteries, rubric_by_id, k, n_transcripts, seed, producer):
    """Generate passes 1..k-1 for a deterministic subsample of scored
    transcripts, writing them to the ``judge_noise_scores`` stream. Resumable:
    a (condition, item, sample, rubric, pass) already present is skipped."""
    rubrics_for = scored_rubrics(batteries)
    backend = run.make_judge_backend()
    rng = random.Random(seed)

    for condition in experiment.conditions:
        transcripts = [
            record
            for record in store.read(
                transcript_pb2.SampleRecord, experiment.id, condition.id, "samples"
            )
            if record.key.item_id in rubrics_for
        ]
        rng.shuffle(transcripts)
        chosen = transcripts[:n_transcripts]
        have = {
            (s.key.item_id, s.key.sample_index, s.rubric_id, s.judge_sample_index)
            for s in store.read(scoring_pb2.JudgeScore, experiment.id, condition.id, NOISE_KIND)
        }
        if not chosen:
            continue
        with store.writer(experiment.id, condition.id, NOISE_KIND, producer) as writer:
            for record in chosen:
                for rubric_id in rubrics_for[record.key.item_id]:
                    rubric = rubric_by_id[rubric_id]
                    for pass_index in range(1, k):
                        if (record.key.item_id, record.key.sample_index, rubric_id,
                                pass_index) in have:
                            continue
                        score = run.judge_with_retries(
                            backend, record, rubric, judge_sample_index=pass_index
                        )
                        if score is None:
                            print(f"  UNSCORED {condition.id}/{record.key.item_id} "
                                  f"s{record.key.sample_index} pass{pass_index}")
                            continue
                        writer.write(score)
                        print(f"  {condition.id}/{record.key.item_id} "
                              f"s{record.key.sample_index} pass{pass_index}: "
                              + ", ".join(f"{d.dimension}={d.value:g}" for d in score.scores))


def render(report: dict) -> str:
    out = ["judge-noise variance components (unit = one transcript across passes):", ""]
    out.append(f"  {'dimension':18} {'ICC':>6} {'judge_noise':>12} "
               f"{'between':>9} {'within':>9} {'n':>5}")
    for dimension, components in sorted(report.items()):
        out.append(
            f"  {dimension:18} {components['icc']:>6.3f} "
            f"{components['judge_noise_share']:>12.3f} "
            f"{components['between']:>9.3f} {components['within']:>9.3f} "
            f"{components['n_items']:>5}"
        )
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment", default="confirmatory")
    parser.add_argument("--data-root", default=str(REPO / "data"))
    parser.add_argument("--k", type=int, default=4, help="total judge passes per transcript")
    parser.add_argument("--transcripts", type=int, default=40,
                        help="transcripts per condition to re-judge")
    parser.add_argument("--seed", type=int, default=20260810)
    parser.add_argument("--producer", default=None, help="unique writer name (default: host)")
    parser.add_argument("--report-only", action="store_true",
                        help="skip re-judging; report from already-stored passes")
    args = parser.parse_args()

    experiment_dir = BASE / args.experiment
    experiment = run.load_experiment(experiment_dir)
    all_batteries = run.load_batteries(experiment_dir)
    rubric_by_id = {
        rubric.id: rubric
        for definition in all_batteries.values()
        for rubric in definition.rubrics
    }
    batteries = {bid: all_batteries[bid] for bid in experiment.battery_ids if bid in all_batteries}
    store = ResultStore(args.data_root)

    if not args.report_only:
        import socket
        producer = args.producer or socket.gethostname()
        rejudge(store, experiment, batteries, rubric_by_id,
                args.k, args.transcripts, args.seed, producer)

    report = report_variance(read_all_passes(store, experiment))
    if not report:
        raise SystemExit("no judge scores found; run without --report-only first")
    print(render(report))


if __name__ == "__main__":
    main()
