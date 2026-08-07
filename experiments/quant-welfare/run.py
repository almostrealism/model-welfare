#!/usr/bin/env python3
"""Runner for the quant-welfare trial experiment.

Loads the manifests under trial/, generates samples for every (condition,
battery item) through the vLLM ladder on halo, judges batteries that carry
rubrics, and prints item-level tables against the reference condition.

Resumable: existing samples and scores are detected by key and skipped, so
an interrupted run continues where it stopped (seeds derive from sample
index, so a resumed sample is the same sample). Records append to the store
under --data-root; the store is the source of truth and the printed tables
are always recomputed from it.
"""

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for sub in ("core/src", "backends/vllm/src"):
    path = str(REPO / sub)
    if path not in sys.path:
        sys.path.insert(0, path)

from google.protobuf import text_format

from modelwelfare import provenance
from modelwelfare.analysis import dimension_means, event_rate
from modelwelfare.driver import run_samples
from modelwelfare.judging import JudgeError, judge_sample
from modelwelfare.store import ResultStore
from modelwelfare.v1 import battery_pb2, common_pb2, condition_pb2, experiment_pb2, scoring_pb2, transcript_pb2
from modelwelfare_vllm import VllmServerBackend

TRIAL_DIR = Path(__file__).resolve().parent / "trial"

ENDPOINTS = {
    "qwen3-8b-bf16": ("http://amd-halo:8001", "qwen3-8b"),
    "qwen3-8b-awq-w4": ("http://amd-halo:8003", "qwen3-8b-awq"),
}

JUDGE_URL = "http://amd-halo:8000"
JUDGE_MODEL = "qwen3-4b-instruct-2507"
JUDGE_REF = common_pb2.ModelRef(
    family="qwen3", name="Qwen3-4B-Instruct-2507", source="Qwen/Qwen3-4B-Instruct-2507"
)
JUDGE_RUNTIME = condition_pb2.RuntimeSpec(
    backend=condition_pb2.BACKEND_VLLM, device="rocm", host="halo", compute_dtype="bf16"
)
JUDGE_RETRIES = 3


def judge_sampling(attempt: int) -> condition_pb2.SamplingSpec:
    """Attempt 0 is deterministic; retries perturb temperature and seed so a
    deterministic malformed reply cannot simply recur."""
    if attempt == 0:
        return condition_pb2.SamplingSpec(temperature=0.0, max_tokens=400, seed=1)
    return condition_pb2.SamplingSpec(temperature=0.3, max_tokens=400, seed=1 + attempt)


def load_experiment() -> experiment_pb2.Experiment:
    experiment = experiment_pb2.Experiment()
    text_format.Parse((TRIAL_DIR / "experiment.textproto").read_text(), experiment)
    return experiment


def load_batteries() -> dict:
    definitions = {}
    for path in sorted((TRIAL_DIR / "batteries").glob("*.textproto")):
        definition = battery_pb2.BatteryDefinition()
        text_format.Parse(path.read_text(), definition)
        definitions[definition.battery.id] = definition
    return definitions


def existing_samples(store, experiment_id, condition_id):
    keys = set()
    for record in store.read(transcript_pb2.SampleRecord, experiment_id, condition_id, "samples"):
        keys.add((record.key.item_id, record.key.sample_index))
    return keys


def existing_scores(store, experiment_id, condition_id):
    keys = set()
    for score in store.read(scoring_pb2.JudgeScore, experiment_id, condition_id, "scores"):
        keys.add((score.key.item_id, score.key.sample_index, score.rubric_id))
    return keys


def generate_condition(experiment, batteries, condition, samples, store, producer, stamp, concurrency):
    """One condition's generation, run in its own thread: conversations fan
    out through run_samples; the writer stays on this thread, so each
    condition file has exactly one writer."""
    url, served = ENDPOINTS[condition.id]
    backend = VllmServerBackend(url, served, condition.runtime)
    have = existing_samples(store, experiment.id, condition.id)
    tasks = []
    for definition in batteries.values():
        for item in definition.items:
            tasks += [(item, i) for i in range(samples) if (item.id, i) not in have]
    skipped = sum(len(d.items) for d in batteries.values()) * samples - len(tasks)
    print(f"  {condition.id}: {len(tasks)} conversations to run, {skipped} already stored")
    if not tasks:
        return
    with store.writer(experiment.id, condition.id, "samples", producer) as writer:
        for record in run_samples(
            backend, tasks,
            experiment_id=experiment.id, condition_id=condition.id,
            sampling=condition.sampling, concurrency=concurrency, provenance=stamp,
        ):
            writer.write(record)
            events = ",".join(o.name for o in record.outcomes)
            print(f"  {condition.id} / {record.key.item_id} "
                  f"s{record.key.sample_index}: {events}")


def generate(experiment, batteries, conditions, samples, store, producer, stamp, concurrency):
    with ThreadPoolExecutor(max_workers=len(conditions)) as pool:
        futures = [
            pool.submit(
                generate_condition, experiment, batteries, condition, samples,
                store, producer, stamp, concurrency,
            )
            for condition in conditions
        ]
        for future in as_completed(futures):
            future.result()


def judge(experiment, batteries, conditions, store, producer, stamp, concurrency):
    rubric_by_id = {}
    scored_battery_items = {}
    for definition in batteries.values():
        for rubric in definition.rubrics:
            rubric_by_id[rubric.id] = rubric
        if definition.battery.rubric_ids:
            for item in definition.items:
                scored_battery_items[item.id] = list(definition.battery.rubric_ids)
    if not scored_battery_items:
        return

    backend = VllmServerBackend(JUDGE_URL, JUDGE_MODEL, JUDGE_RUNTIME)

    def judge_one(record, rubric):
        for attempt in range(JUDGE_RETRIES):
            try:
                return judge_sample(
                    backend, JUDGE_REF, record, rubric,
                    sampling=judge_sampling(attempt), provenance=stamp,
                )
            except JudgeError as error:
                print(f"    judge attempt {attempt + 1} failed "
                      f"({record.key.item_id} s{record.key.sample_index}): {error}")
        return None

    for condition in conditions:
        have = existing_scores(store, experiment.id, condition.id)
        pending = []
        for record in store.read(
            transcript_pb2.SampleRecord, experiment.id, condition.id, "samples"
        ):
            for rubric_id in scored_battery_items.get(record.key.item_id, []):
                if (record.key.item_id, record.key.sample_index, rubric_id) not in have:
                    pending.append((record, rubric_by_id[rubric_id]))
        if not pending:
            print(f"  {condition.id}: all scored")
            continue
        with store.writer(experiment.id, condition.id, "scores", producer) as writer:
            with ThreadPoolExecutor(max_workers=concurrency) as pool:
                futures = {
                    pool.submit(judge_one, record, rubric): (record, rubric)
                    for record, rubric in pending
                }
                for future in as_completed(futures):
                    score = future.result()
                    record, _ = futures[future]
                    if score is None:
                        print(f"  UNSCORED {condition.id} / {record.key.item_id} "
                              f"s{record.key.sample_index} after {JUDGE_RETRIES} attempts")
                        continue
                    writer.write(score)
                    values = ", ".join(f"{s.dimension}={s.value:g}" for s in score.scores)
                    print(f"  {condition.id} / {record.key.item_id} "
                          f"s{record.key.sample_index}: {values}")


def print_tables(experiment, batteries, conditions, store):
    condition_ids = [c.id for c in conditions]
    reference = experiment.reference_condition_id
    records = []
    scores = []
    for condition_id in condition_ids:
        records += list(
            store.read(transcript_pb2.SampleRecord, experiment.id, condition_id, "samples")
        )
        scores += list(store.read(scoring_pb2.JudgeScore, experiment.id, condition_id, "scores"))

    bail_rates = event_rate(records, "terminal_tool_invoked")

    for definition in batteries.values():
        battery = definition.battery
        item_ids = [item.id for item in definition.items]
        print(f"\n== {battery.id} ({battery.protocol}) ==")
        if not battery.rubric_ids:
            header = "item".ljust(28) + "".join(c.ljust(20) for c in condition_ids) + "delta"
            print(header)
            for item_id in item_ids:
                row = item_id.ljust(28)
                rates = {}
                for condition_id in condition_ids:
                    hits, total = bail_rates.get((condition_id, item_id), (0, 0))
                    rates[condition_id] = hits / total if total else float("nan")
                    row += f"{hits}/{total} ({rates[condition_id]:.0%})".ljust(20)
                deltas = [
                    rates[c] - rates[reference] for c in condition_ids if c != reference
                ]
                row += " ".join(f"{d:+.0%}" for d in deltas)
                print(row)
        else:
            for rubric in definition.rubrics:
                for dimension in rubric.dimensions:
                    means = dimension_means(scores, dimension.name)
                    print(f"-- {dimension.name} (mean of judge scores) --")
                    header = "item".ljust(28) + "".join(c.ljust(20) for c in condition_ids) + "delta"
                    print(header)
                    for item_id in item_ids:
                        row = item_id.ljust(28)
                        values = {}
                        for condition_id in condition_ids:
                            value = means.get((condition_id, item_id))
                            values[condition_id] = value
                            row += (f"{value:.2f}" if value is not None else "-").ljust(20)
                        deltas = [
                            values[c] - values[reference]
                            for c in condition_ids
                            if c != reference
                            and values.get(c) is not None
                            and values.get(reference) is not None
                        ]
                        row += " ".join(f"{d:+.2f}" for d in deltas)
                        print(row)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", default=str(REPO / "data"))
    parser.add_argument("--samples", type=int, default=0,
                        help="override samples_per_item (0 = use manifest)")
    parser.add_argument("--conditions", default="",
                        help="comma-separated condition ids (default: all)")
    parser.add_argument("--batteries", default="",
                        help="comma-separated battery ids (default: all in manifest)")
    parser.add_argument("--producer", default="local",
                        help="producer name for store files; must be unique per writing process")
    parser.add_argument("--concurrency", type=int, default=8,
                        help="concurrent conversations per condition (and concurrent judge calls)")
    parser.add_argument("--skip-judge", action="store_true")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the plan and exit without contacting any server")
    args = parser.parse_args()

    experiment = load_experiment()
    batteries = load_batteries()
    batteries = {
        battery_id: definition
        for battery_id, definition in batteries.items()
        if battery_id in experiment.battery_ids
        and (not args.batteries or battery_id in args.batteries.split(","))
    }
    conditions = [
        c for c in experiment.conditions
        if not args.conditions or c.id in args.conditions.split(",")
    ]
    samples = args.samples or experiment.samples_per_item

    total_items = sum(len(d.items) for d in batteries.values())
    print(f"experiment {experiment.id}: {len(conditions)} conditions x "
          f"{total_items} items x {samples} samples")
    for condition in conditions:
        if condition.id not in ENDPOINTS:
            raise SystemExit(f"no endpoint configured for condition {condition.id!r}")
        print(f"  {condition.id} -> {ENDPOINTS[condition.id]}")
    if args.dry_run:
        return

    store = ResultStore(args.data_root)
    stamp = provenance.current(args.producer)

    print("\ngenerating...")
    generate(experiment, batteries, conditions, samples, store, args.producer, stamp,
             args.concurrency)
    if not args.skip_judge:
        print("\njudging...")
        judge(experiment, batteries, conditions, store, args.producer, stamp,
              args.concurrency)
    print_tables(experiment, batteries, conditions, store)


if __name__ == "__main__":
    main()
