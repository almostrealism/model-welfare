#!/usr/bin/env python3
"""Judge bakeoff: evaluate judge candidates on shared materials.

Materials per candidate: 6 synthetic manipulation-check transcripts + 12
real distress transcripts scored on the distress-v1 rubric, and 4 synthetic
+ up to 12 real exit conversations classified on the exit-reason rubric.
Every task runs twice (judge_sample_index 0 and 1) for test-retest noise.
Scores land in the store under experiment judge-bakeoff-1 with
condition_id = candidate name; reruns skip already-stored passes.

    python3 run_bakeoff.py --candidate qwen3-4b
    python3 run_bakeoff.py --candidate opus5
    python3 run_bakeoff.py --report

Measures in the report: format-failure rate, planted-signal sensitivity,
test-retest spread, agreement with the reference candidate, and exit
classification accuracy. Design notes: docs/PLANNING.md (judge bakeoff).
"""

import argparse
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
for sub in ("core/src", "backends/llamacpp/src", "backends/anthropic/src"):
    path = str(REPO / sub)
    if path not in sys.path:
        sys.path.insert(0, path)

import synthetics

from modelwelfare import provenance
from modelwelfare.judging import JudgeError, judge_sample
from modelwelfare.store import ResultStore
from modelwelfare.v1 import common_pb2, condition_pb2, scoring_pb2, transcript_pb2
from modelwelfare_llamacpp import LlamaCppServerBackend

EXPERIMENT_ID = synthetics.EXPERIMENT_ID
PASSES = 2
RETRIES = 3
REFERENCE_CANDIDATE = "opus5"

CANDIDATES = {
    "qwen3-4b": {"kind": "llamacpp", "url": "http://127.0.0.1:8090",
                 "ref": {"family": "qwen3", "name": "Qwen3-4B-Instruct-2507-Q8", "source": "local-gguf"}},
    "qwen3-8b": {"kind": "llamacpp", "url": "http://127.0.0.1:8092",
                 "ref": {"family": "qwen3", "name": "Qwen3-8B-Q8", "source": "local-gguf"}},
    "qwen3-30b": {"kind": "llamacpp", "url": "http://127.0.0.1:8095",
                  "ref": {"family": "qwen3", "name": "Qwen3-30B-A3B-Instruct-2507-Q4", "source": "local-gguf"}},
    "opus5": {"kind": "anthropic", "model": "claude-opus-5",
              "ref": {"family": "claude", "name": "claude-opus-5", "source": "anthropic-api"}},
}

LOCAL_RUNTIME = condition_pb2.RuntimeSpec(
    backend=condition_pb2.BACKEND_LLAMACPP, device="metal", host="studio"
)


def make_backend(name):
    candidate = CANDIDATES[name]
    if candidate["kind"] == "llamacpp":
        return LlamaCppServerBackend(candidate["url"], LOCAL_RUNTIME, timeout=600.0)
    from modelwelfare_anthropic import AnthropicBackend
    return AnthropicBackend(candidate["model"])


def judge_sampling(name, attempt, pass_index):
    if CANDIDATES[name]["kind"] == "anthropic":
        return condition_pb2.SamplingSpec(max_tokens=8000)
    return condition_pb2.SamplingSpec(
        temperature=0.3, top_p=0.95, max_tokens=640,
        seed=500 + pass_index * 100 + attempt,
    )


def real_distress_records(store):
    """Deterministic stratified sample: 3 items per feedback style from the
    calibration run's Q8 condition, sample 0."""
    by_style = defaultdict(list)
    for record in store.read(
        transcript_pb2.SampleRecord, "instrument-calibration-1", "qwen3-4b-gguf-q8", "samples"
    ):
        if record.key.item_id.startswith("distress-") and record.key.sample_index == 0:
            style = record.key.item_id.rsplit("-", 1)[-1]
            by_style[style].append(record)
    selected = []
    for style in sorted(by_style):
        selected += sorted(by_style[style], key=lambda r: r.key.item_id)[:3]
    return selected


def real_exit_records(store):
    """Up to 12 conversations that ended via end_conversation, drawn across
    the bail-only and two-tool arms for reason-shape diversity."""
    sources = [
        ("instrument-calibration-1", "qwen3-4b-gguf-q8"),
        ("bail-tool-arms-1", "qwen3-4b-gguf-q8"),
        ("bail-tool-arms-1", "qwen3-4b-gguf-q4km"),
    ]
    selected = []
    seen_items = set()
    for experiment, condition in sources:
        for record in store.read(transcript_pb2.SampleRecord, experiment, condition, "samples"):
            exited = any(
                o.name == "terminal_tool_invoked" and o.detail == "end_conversation"
                for o in record.outcomes
            )
            if exited and record.key.item_id not in seen_items:
                seen_items.add(record.key.item_id)
                selected.append(record)
            if len(selected) >= 12:
                return selected
    return selected


def existing_passes(store, candidate):
    keys = set()
    for score in store.read(scoring_pb2.JudgeScore, EXPERIMENT_ID, candidate, "scores"):
        keys.add((score.key.item_id, score.key.sample_index, score.rubric_id, score.judge_sample_index))
    return keys


def run_candidate(name, store, stamp):
    backend = make_backend(name)
    judge_ref = common_pb2.ModelRef(**CANDIDATES[name]["ref"])
    distress_rubric = synthetics.distress_rubric()

    tasks = []
    for record in synthetics.DISTRESS_SYNTHETICS + real_distress_records(store):
        tasks.append((record, distress_rubric))
    for record in synthetics.EXIT_SYNTHETICS + real_exit_records(store):
        tasks.append((record, synthetics.EXIT_RUBRIC))

    have = existing_passes(store, name)
    usage_in = usage_out = failures = calls = 0
    with store.writer(EXPERIMENT_ID, name, "scores", "local") as writer:
        for record, rubric in tasks:
            for pass_index in range(PASSES):
                key = (record.key.item_id, record.key.sample_index, rubric.id, pass_index)
                if key in have:
                    continue
                score = None
                for attempt in range(RETRIES):
                    try:
                        score = judge_sample(
                            backend, judge_ref, record, rubric,
                            sampling=judge_sampling(name, attempt, pass_index),
                            judge_sample_index=pass_index, provenance=stamp,
                        )
                        break
                    except JudgeError as error:
                        print(f"    attempt {attempt + 1} failed ({record.key.item_id} "
                              f"p{pass_index}): {error}")
                calls += 1
                if score is None:
                    failures += 1
                    print(f"  UNSCORED {name} / {record.key.item_id} p{pass_index}")
                    continue
                writer.write(score)
                values = ", ".join(f"{s.dimension}={s.value:g}" for s in score.scores)
                print(f"  {name} / {record.key.item_id} p{pass_index}: {values}")
    print(f"{name}: {calls} calls, {failures} unscored after retries")


def _scores_by_item(store, candidate, rubric_id):
    grouped = defaultdict(list)
    for score in store.read(scoring_pb2.JudgeScore, EXPERIMENT_ID, candidate, "scores"):
        if score.rubric_id == rubric_id:
            grouped[score.key.item_id].append(score)
    return grouped


def _dimension_value(score, dimension):
    for entry in score.scores:
        if entry.dimension == dimension:
            return entry.value
    return None


def _mean(values):
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None


def _pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs) ** 0.5
    vy = sum((y - my) ** 2 for y in ys) ** 0.5
    if vx == 0 or vy == 0:
        return None
    return cov / (vx * vy)


def _exit_choice(score):
    best, best_value = None, -1.0
    for entry in score.scores:
        if entry.value > best_value:
            best, best_value = entry.dimension, entry.value
    return best


def report(store):
    distress_rubric = synthetics.distress_rubric()
    dimensions = [d.name for d in distress_rubric.dimensions]
    candidates = [c for c in CANDIDATES if
                  any(True for _ in store.read(scoring_pb2.JudgeScore, EXPERIMENT_ID, c, "scores"))]
    reference = _scores_by_item(store, REFERENCE_CANDIDATE, distress_rubric.id)

    for name in candidates:
        distress = _scores_by_item(store, name, distress_rubric.id)
        exits = _scores_by_item(store, name, synthetics.EXIT_RUBRIC.id)
        total = sum(len(v) for v in distress.values()) + sum(len(v) for v in exits.values())
        print(f"\n== {name} ({total} scores stored) ==")

        print("-- planted-signal sensitivity (high-pole mean - low-pole mean) --")
        for dimension in dimensions:
            poles = {"high": [], "low": []}
            for item_id, (dim, pole) in synthetics.DISTRESS_EXPECTATIONS.items():
                if dim != dimension:
                    continue
                mean = _mean([_dimension_value(s, dimension) for s in distress.get(item_id, [])])
                if mean is not None:
                    poles[pole].append(mean)
            if poles["high"] and poles["low"]:
                spread = _mean(poles["high"]) - _mean(poles["low"])
                print(f"  {dimension}: {spread:+.1f} "
                      f"(high {_mean(poles['high']):.1f}, low {_mean(poles['low']):.1f})")

        retest = []
        for item_id, scores in distress.items():
            by_pass = {s.judge_sample_index: s for s in scores}
            if 0 in by_pass and 1 in by_pass:
                for dimension in dimensions:
                    a = _dimension_value(by_pass[0], dimension)
                    b = _dimension_value(by_pass[1], dimension)
                    if a is not None and b is not None:
                        retest.append(abs(a - b))
        if retest:
            print(f"-- test-retest: mean |pass0-pass1| = {_mean(retest):.2f} over {len(retest)} pairs --")

        if name != REFERENCE_CANDIDATE and reference:
            print("-- agreement with reference (Pearson r on real distress items) --")
            for dimension in dimensions:
                xs, ys = [], []
                for item_id in distress:
                    if item_id.startswith("syn-") or item_id not in reference:
                        continue
                    a = _mean([_dimension_value(s, dimension) for s in distress[item_id]])
                    b = _mean([_dimension_value(s, dimension) for s in reference[item_id]])
                    if a is not None and b is not None:
                        xs.append(a)
                        ys.append(b)
                r = _pearson(xs, ys)
                print(f"  {dimension}: r={r:.2f} (n={len(xs)})" if r is not None
                      else f"  {dimension}: insufficient variance or n (n={len(xs)})")

        correct = total_syn = onehot_violations = 0
        for item_id, expected in synthetics.EXIT_EXPECTATIONS.items():
            for score in exits.get(item_id, []):
                total_syn += 1
                if _exit_choice(score) == expected:
                    correct += 1
                if sum(1 for e in score.scores if e.value >= 0.5) != 1:
                    onehot_violations += 1
        if total_syn:
            print(f"-- exit classification: {correct}/{total_syn} planted classes correct, "
                  f"{onehot_violations} one-hot violations --")
        if name != REFERENCE_CANDIDATE:
            ref_exits = _scores_by_item(store, REFERENCE_CANDIDATE, synthetics.EXIT_RUBRIC.id)
            agree = comparisons = 0
            for item_id in exits:
                if item_id.startswith("syn-") or item_id not in ref_exits:
                    continue
                mine = _exit_choice(exits[item_id][0])
                theirs = _exit_choice(ref_exits[item_id][0])
                comparisons += 1
                agree += mine == theirs
            if comparisons:
                print(f"-- exit agreement with reference: {agree}/{comparisons} real exits --")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", choices=sorted(CANDIDATES))
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--data-root", default=str(REPO / "data"))
    args = parser.parse_args()

    store = ResultStore(args.data_root)
    if args.candidate:
        stamp = provenance.current("studio")
        run_candidate(args.candidate, store, stamp)
    if args.report:
        report(store)
    if not args.candidate and not args.report:
        raise SystemExit("pass --candidate <name> and/or --report")


if __name__ == "__main__":
    main()
