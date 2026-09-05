#!/usr/bin/env python3
"""Runner for the quant-welfare trial experiment.

Loads the manifests under study1/trial/, generates samples for every (condition,
battery item) through the vLLM ladder on halo, judges batteries that carry
rubrics, and prints item-level tables against the reference condition.

Resumable: existing samples and scores are detected by key and skipped, so
an interrupted run continues where it stopped (seeds derive from sample
index, so a resumed sample is the same sample). Records append to the store
under --data-root; the store is the source of truth and the printed tables
are always recomputed from it.
"""

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for sub in ("core/src", "backends/vllm/src", "backends/llamacpp/src"):
    path = str(REPO / sub)
    if path not in sys.path:
        sys.path.insert(0, path)

from google.protobuf import text_format

from modelwelfare import provenance
from modelwelfare.analysis import dimension_means, event_rate, exit_reason_rate
from modelwelfare.driver import FramedPolicy, TERMINAL_TOOL_INVOKED, run_samples
from modelwelfare.judging import JudgeError, classify_exit, judge_sample
from modelwelfare.store import ResultStore
from modelwelfare.v1 import battery_pb2, common_pb2, condition_pb2, experiment_pb2, scoring_pb2, transcript_pb2
from modelwelfare_llamacpp import LlamaCppServerBackend
from modelwelfare_vllm import VllmServerBackend

BASE_DIR = Path(__file__).resolve().parent
SHARED_BATTERIES = BASE_DIR / "batteries"

with open(BASE_DIR / "endpoints.json") as handle:
    ENDPOINTS = {
        condition: entry
        for condition, entry in json.load(handle).items()
        if not condition.startswith("_")
    }

BACKEND_KINDS = {
    "vllm": condition_pb2.BACKEND_VLLM,
    "llamacpp": condition_pb2.BACKEND_LLAMACPP,
}

# Per-request backend timeout. The 120s default keeps a stalled response on a
# flaky link tripping in ~2 min so the driver's per-sample retry recovers; a
# 512-token completion from the small subjects is well under it. Larger
# subjects on halo's bandwidth-bound APU (e.g. a 12B at ~9 tok/s single-stream)
# need --backend-timeout raised, or every request times out under batching.
BACKEND_TIMEOUT = 120.0


def make_backend(condition):
    entry = ENDPOINTS.get(condition.id)
    if entry is None:
        raise SystemExit(f"no endpoint configured for condition {condition.id!r}")
    if condition.runtime.backend != BACKEND_KINDS[entry["kind"]]:
        raise SystemExit(
            f"{condition.id}: endpoint kind {entry['kind']!r} does not match "
            f"the manifest's runtime backend"
        )
    if entry["kind"] == "vllm":
        return VllmServerBackend(entry["url"], entry["model"], condition.runtime,
                                 timeout=BACKEND_TIMEOUT)
    return LlamaCppServerBackend(entry["url"], condition.runtime, timeout=BACKEND_TIMEOUT)

# The distress primary judge selected by the bakeoff (docs/JOURNAL.md
# 2026-08-07): Qwen3-30B-A3B served as a local llama.cpp rung. It is
# hybrid-thinking-free (2507 line) and needs no thinking pin.
JUDGE_URL = "http://127.0.0.1:8095"
JUDGE_REF = common_pb2.ModelRef(
    family="qwen3", name="Qwen3-30B-A3B-Instruct-2507-Q4",
    source="bartowski/Qwen_Qwen3-30B-A3B-Instruct-2507-GGUF",
    weights_digest="382b4f5a164d200f93790ee0e339fae12852896d23485cfb203ce868fea33a95",
)
JUDGE_RUNTIME = condition_pb2.RuntimeSpec(
    backend=condition_pb2.BACKEND_LLAMACPP, device="metal", host="studio",
    compute_dtype="f16",
)
JUDGE_RETRIES = 3


def make_judge_backend():
    return LlamaCppServerBackend(JUDGE_URL, JUDGE_RUNTIME, timeout=600.0)


# The exit-reason classifier selected by the bakeoff (docs/JOURNAL.md): Qwen3-8B
# served as a local llama.cpp rung (services/llamacpp/rungs.sh qwen3-8b-q8:8092,
# pinned non-thinking there). It classifies each residual terminal exit into the
# pre-registered taxonomy so E1 (aversion+refusal share) can be computed.
EXIT_CLASSIFIER_URL = "http://127.0.0.1:8092"
# Source hash-verified 2026-08-13 (PREREGISTRATION §11.2): the served file is
# the OFFICIAL Qwen GGUF — its SHA-256 matches Qwen/Qwen3-8B-GGUF's published
# LFS digest exactly and does not match bartowski's. Classifications stored
# before this date carry the earlier, incorrect "bartowski/Qwen3-8B-GGUF"
# source string; the weights_digest identifies the file authoritatively.
EXIT_CLASSIFIER_REF = common_pb2.ModelRef(
    family="qwen3", name="Qwen3-8B-Q8",
    source="Qwen/Qwen3-8B-GGUF",
    weights_digest="408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6",
)
EXIT_CLASSIFIER_RUNTIME = condition_pb2.RuntimeSpec(
    backend=condition_pb2.BACKEND_LLAMACPP, device="metal", host="studio",
    compute_dtype="f16",
)
# The outcome name generation records when a conversation-ending tool fired.
TERMINAL_EXIT_OUTCOME = TERMINAL_TOOL_INVOKED


def make_exit_classifier_backend():
    return LlamaCppServerBackend(EXIT_CLASSIFIER_URL, EXIT_CLASSIFIER_RUNTIME, timeout=600.0)


def judge_sampling(attempt: int, judge_sample_index: int = 0) -> condition_pb2.SamplingSpec:
    """Sampling for one judge pass. The primary pass (``judge_sample_index`` 0,
    ``attempt`` 0) is deterministic — that is the single confirmatory score. Any
    *additional* pass (index > 0, used by the judge-noise tool) or retry perturbs
    the temperature and takes a distinct seed, so repeated passes are genuinely
    independent draws — without this the passes are identical on a deterministic
    backend and within-transcript variance collapses (ICC overstated) — and a
    deterministic malformed reply cannot simply recur. Wide token budget so the
    30B's replies are never truncated mid-JSON."""
    if judge_sample_index == 0 and attempt == 0:
        return condition_pb2.SamplingSpec(temperature=0.0, max_tokens=640, seed=1)
    return condition_pb2.SamplingSpec(
        temperature=0.3, max_tokens=640, seed=1 + 1000 * judge_sample_index + attempt
    )


def judge_with_retries(backend, record, rubric, *, judge_sample_index=0, provenance=None):
    """Score one transcript with the confirmatory judge, retrying on failure.
    Malformed judge JSON (a truncated or non-conforming reply) and transient
    backend errors both retry with perturbed judge sampling; returns None if
    unresolved after JUDGE_RETRIES so the caller can record it UNSCORED rather
    than aborting a long batch. Shared by the runner and the judge tools so the
    retry policy lives in one place."""
    for attempt in range(JUDGE_RETRIES):
        try:
            return judge_sample(
                backend, JUDGE_REF, record, rubric,
                sampling=judge_sampling(attempt, judge_sample_index),
                judge_sample_index=judge_sample_index, provenance=provenance,
            )
        except Exception as error:
            print(f"    judge attempt {attempt + 1} failed "
                  f"({record.key.item_id} s{record.key.sample_index}): "
                  f"{type(error).__name__}: {error}")
    return None


def load_experiment(experiment_dir: Path) -> experiment_pb2.Experiment:
    experiment = experiment_pb2.Experiment()
    text_format.Parse((experiment_dir / "experiment.textproto").read_text(), experiment)
    return experiment


def load_batteries(experiment_dir: Path) -> dict:
    """Battery definitions visible to an experiment: the shared pool plus any
    experiment-local batteries directory, with local definitions winning on
    an id collision."""
    definitions = {}
    for directory in (SHARED_BATTERIES, experiment_dir / "batteries"):
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.textproto")):
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


def existing_classifications(store, experiment_id, condition_id):
    keys = set()
    for record in store.read(
        scoring_pb2.ExitClassification, experiment_id, condition_id, "exit_reasons"
    ):
        keys.add((record.key.item_id, record.key.sample_index))
    return keys


def condition_frame(experiment_dir, condition_id):
    """The frame this condition applies, or None: an experiment-local
    ``frames-map.json`` ({"frames_file": path-from-repo-root,
    "conditions": {condition_id: frame_id}}) opts a condition into the
    Study 3 framing arm; unmapped conditions run unframed. The frame
    texts stay in their frozen file — the map only points."""
    map_path = experiment_dir / "frames-map.json"
    if not map_path.is_file():
        return None
    with open(map_path) as handle:
        mapping = json.load(handle)
    frame_id = mapping.get("conditions", {}).get(condition_id)
    if frame_id is None:
        return None
    with open(REPO / mapping["frames_file"]) as handle:
        frames = {frame["id"]: frame
                  for frame in json.load(handle)["frames"]}
    if frame_id not in frames:
        raise SystemExit(f"frames-map names unknown frame {frame_id!r}")
    return frames[frame_id]


def generate_condition(experiment, batteries, condition, samples, store, producer, stamp, concurrency,
                       frame=None):
    """One condition's generation, run in its own thread: conversations fan
    out through run_samples; the writer stays on this thread, so each
    condition file has exactly one writer."""
    backend = make_backend(condition)
    have = existing_samples(store, experiment.id, condition.id)
    tasks = []
    for definition in batteries.values():
        for item in definition.items:
            tasks += [(item, i) for i in range(samples) if (item.id, i) not in have]
    skipped = sum(len(d.items) for d in batteries.values()) * samples - len(tasks)
    print(f"  {condition.id}: {len(tasks)} conversations to run, {skipped} already stored")
    if not tasks:
        return
    wrapper = (None if frame is None
               else (lambda policy: FramedPolicy(policy, frame)))
    with store.writer(experiment.id, condition.id, "samples", producer) as writer:
        for record in run_samples(
            backend, tasks,
            experiment_id=experiment.id, condition_id=condition.id,
            sampling=condition.sampling, concurrency=concurrency, provenance=stamp,
            policy_wrapper=wrapper,
        ):
            writer.write(record)
            events = ",".join(o.name for o in record.outcomes)
            print(f"  {condition.id} / {record.key.item_id} "
                  f"s{record.key.sample_index}: {events}")


def generate(experiment, batteries, conditions, samples, store, producer, stamp, concurrency,
             experiment_dir=None):
    with ThreadPoolExecutor(max_workers=len(conditions)) as pool:
        futures = [
            pool.submit(
                generate_condition, experiment, batteries, condition, samples,
                store, producer, stamp, concurrency,
                condition_frame(experiment_dir, condition.id)
                if experiment_dir else None,
            )
            for condition in conditions
        ]
        for future in as_completed(futures):
            future.result()


def judge(experiment, batteries, conditions, store, producer, stamp, concurrency, rubric_by_id):
    scored_battery_items = {}
    for definition in batteries.values():
        if definition.battery.rubric_ids:
            for item in definition.items:
                scored_battery_items[item.id] = list(definition.battery.rubric_ids)
    if not scored_battery_items:
        return

    backend = make_judge_backend()

    def judge_one(record, rubric):
        # A long batch must survive per-item failures: retry with perturbed
        # sampling, then leave the item UNSCORED rather than aborting the run.
        return judge_with_retries(backend, record, rubric, provenance=stamp)

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


def classify(experiment, conditions, store, producer, stamp, concurrency):
    """Classify every residual terminal exit into the pre-registered taxonomy
    (E1's input). Structured like judge(): resumable by key, per-item failures
    retry and, if unresolved, leave the exit UNCLASSIFIED rather than aborting.
    Only samples whose outcomes include a terminal exit are classified — a
    sample that never exited contributes no aversion/refusal hit to E1."""
    backend = make_exit_classifier_backend()

    def classify_one(record):
        for attempt in range(JUDGE_RETRIES):
            try:
                return classify_exit(
                    backend, EXIT_CLASSIFIER_REF, record,
                    sampling=judge_sampling(attempt), provenance=stamp,
                )
            except Exception as error:
                print(f"    classify attempt {attempt + 1} failed "
                      f"({record.key.item_id} s{record.key.sample_index}): "
                      f"{type(error).__name__}: {error}")
        return None

    for condition in conditions:
        have = existing_classifications(store, experiment.id, condition.id)
        pending = [
            record
            for record in store.read(
                transcript_pb2.SampleRecord, experiment.id, condition.id, "samples"
            )
            if any(o.name == TERMINAL_EXIT_OUTCOME for o in record.outcomes)
            and (record.key.item_id, record.key.sample_index) not in have
        ]
        if not pending:
            print(f"  {condition.id}: no unclassified exits")
            continue
        with store.writer(experiment.id, condition.id, "exit_reasons", producer) as writer:
            with ThreadPoolExecutor(max_workers=concurrency) as pool:
                futures = {pool.submit(classify_one, record): record for record in pending}
                for future in as_completed(futures):
                    classification = future.result()
                    record = futures[future]
                    if classification is None:
                        print(f"  UNCLASSIFIED {condition.id} / {record.key.item_id} "
                              f"s{record.key.sample_index} after {JUDGE_RETRIES} attempts")
                        continue
                    writer.write(classification)
                    print(f"  {condition.id} / {record.key.item_id} "
                          f"s{record.key.sample_index}: "
                          f"{scoring_pb2.ExitReason.Name(classification.reason)}")


def _print_rate_table(title, rates, item_ids, condition_ids, reference):
    """One per-item rate table (hits/total and per-condition delta vs. the
    reference). ``rates`` is an (hits, total) map keyed (condition_id, item_id),
    as returned by :func:`event_rate` and :func:`exit_reason_rate`."""
    print(f"-- {title} --")
    print("item".ljust(28) + "".join(c.ljust(20) for c in condition_ids) + "delta")
    for item_id in item_ids:
        row = item_id.ljust(28)
        fractions = {}
        for condition_id in condition_ids:
            hits, total = rates.get((condition_id, item_id), (0, 0))
            fractions[condition_id] = hits / total if total else float("nan")
            row += f"{hits}/{total} ({fractions[condition_id]:.0%})".ljust(20)
        # Deltas only when the reference condition is part of this invocation —
        # a per-condition run (--conditions <one>) legitimately excludes it.
        deltas = ([fractions[c] - fractions[reference] for c in condition_ids if c != reference]
                  if reference in fractions else [])
        row += " ".join(f"{d:+.0%}" for d in deltas)
        print(row)


def print_tables(experiment, batteries, conditions, store):
    condition_ids = [c.id for c in conditions]
    reference = experiment.reference_condition_id
    records = []
    scores = []
    classifications = []
    for condition_id in condition_ids:
        records += list(
            store.read(transcript_pb2.SampleRecord, experiment.id, condition_id, "samples")
        )
        scores += list(store.read(scoring_pb2.JudgeScore, experiment.id, condition_id, "scores"))
        classifications += list(
            store.read(scoring_pb2.ExitClassification, experiment.id, condition_id, "exit_reasons")
        )

    bail_rates = event_rate(records, TERMINAL_EXIT_OUTCOME)
    # E1: the classified refusal+aversion exit share (PREREGISTRATION §3) — the
    # primary endpoint, distinct from the raw mechanical exit rate above.
    e1_rates = exit_reason_rate(
        records, classifications,
        {scoring_pb2.EXIT_REASON_REFUSAL, scoring_pb2.EXIT_REASON_AVERSION},
    )

    for definition in batteries.values():
        battery = definition.battery
        item_ids = [item.id for item in definition.items]
        print(f"\n== {battery.id} ({battery.protocol}) ==")
        if not battery.rubric_ids:
            _print_rate_table("terminal exits (any reason)", bail_rates, item_ids,
                              condition_ids, reference)
            if classifications:
                _print_rate_table("E1: refusal+aversion exit share", e1_rates, item_ids,
                                  condition_ids, reference)
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
    global BACKEND_TIMEOUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment", default="study1/trial",
                        help="experiment directory name under experiments/quant-welfare/")
    parser.add_argument("--data-root", default=str(REPO / "data"))
    parser.add_argument("--endpoints", default=str(BASE_DIR / "endpoints.json"),
                        help="endpoints map (override for lab-local routing, "
                             "e.g. LAN addresses instead of tailnet hostnames)")
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
    parser.add_argument("--backend-timeout", type=float, default=BACKEND_TIMEOUT,
                        help="per-request generation timeout in seconds (raise for "
                             "large subjects on bandwidth-bound hosts)")
    parser.add_argument("--skip-collect", action="store_true",
                        help="score/classify existing store samples only — "
                             "for records another producer wrote (e.g. "
                             "ingested steered-generation runs); no serving "
                             "endpoint is needed or contacted")
    parser.add_argument("--skip-judge", action="store_true")
    parser.add_argument("--skip-classify", action="store_true",
                        help="skip exit-reason classification (E1 input)")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the plan and exit without contacting any server")
    args = parser.parse_args()

    BACKEND_TIMEOUT = args.backend_timeout

    if args.endpoints != str(BASE_DIR / "endpoints.json"):
        global ENDPOINTS
        with open(args.endpoints) as handle:
            ENDPOINTS = {
                condition: entry
                for condition, entry in json.load(handle).items()
                if not condition.startswith("_")
            }

    experiment_dir = BASE_DIR / args.experiment
    if not (experiment_dir / "experiment.textproto").is_file():
        raise SystemExit(f"no experiment.textproto in {experiment_dir}")
    experiment = load_experiment(experiment_dir)
    all_batteries = load_batteries(experiment_dir)
    # Rubrics resolve across every loaded battery file: a battery may
    # reference a rubric defined in another file (e.g. distress-v2 uses
    # distress-v1-rubric), so build the lookup before filtering.
    rubric_by_id = {
        rubric.id: rubric
        for definition in all_batteries.values()
        for rubric in definition.rubrics
    }
    batteries = {
        battery_id: definition
        for battery_id, definition in all_batteries.items()
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
    if not args.skip_collect:
        for condition in conditions:
            if condition.id not in ENDPOINTS:
                raise SystemExit(f"no endpoint configured for condition {condition.id!r}")
            entry = ENDPOINTS[condition.id]
            print(f"  {condition.id} -> {entry['kind']} {entry['url']}")
    if args.dry_run:
        return

    store = ResultStore(args.data_root)
    stamp = provenance.current(args.producer)

    if not args.skip_collect:
        print("\ngenerating...")
        generate(experiment, batteries, conditions, samples, store, args.producer, stamp,
                 args.concurrency, experiment_dir=experiment_dir)
    if not args.skip_judge:
        print("\njudging...")
        judge(experiment, batteries, conditions, store, args.producer, stamp,
              args.concurrency, rubric_by_id)
    if not args.skip_classify:
        print("\nclassifying exits...")
        classify(experiment, conditions, store, args.producer, stamp, args.concurrency)
    print_tables(experiment, batteries, conditions, store)


if __name__ == "__main__":
    main()
