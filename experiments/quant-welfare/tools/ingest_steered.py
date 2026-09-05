#!/usr/bin/env python3
"""Ingest steered-generation transcripts into the streaming store.

The workbench steering script emits transcripts JSONL (one conversation
per line: id, seed, exit marker, messages); this tool converts them into
``SampleRecord`` streams under an (experiment, condition), so the
standard judging/classification passes (``run.py --skip-collect``) and
every downstream analysis apply to steered data unchanged.

Reconstruction follows the engine's conventions exactly: turn indexes by
position, ``scripted`` true for every non-assistant turn (the plan
builder refuses scripted assistant turns, so role is sufficient),
``tool_invoked`` events for each parsed ``<tool_call>`` payload,
``terminal_tool_invoked`` for the recorded exit (the workbench script
already resolved which call — or raw marker — ended the conversation),
``script_completed`` otherwise, and per-sample seeds copied from the
transcript with the plan's sampling parameters. Token usage is not
recorded by the steering script and stays zero — no analysis reads it.

The generation plan is required, for integrity: every plan conversation
must appear exactly once in the transcripts (a partial workbench run
must not ingest as complete; override with ``--allow-partial``), a
transcript the plan does not name is refused, and re-running is
idempotent — records already in the store are skipped, the resumability
convention every producer follows.

    python3 experiments/quant-welfare/tools/ingest_steered.py \\
        --transcripts steered.jsonl --plan steer-plan.json \\
        --experiment-id quant-welfare-s3-a --condition-id bf16-steer-x \\
        --data-root data --producer halo-steer
"""

import argparse
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
REPO = BASE.parents[1]
for path in (str(REPO / "core/src"),):
    if path not in sys.path:
        sys.path.insert(0, path)

from modelwelfare import provenance  # noqa: E402
from modelwelfare.store import ResultStore  # noqa: E402
from modelwelfare.v1 import common_pb2, condition_pb2, transcript_pb2  # noqa: E402

TERMINAL_TOOL_INVOKED = "terminal_tool_invoked"


def split_plan_id(conversation_id):
    """(item_id, sample_index) from the ``item|sN`` plan convention."""
    item_id, separator, index = conversation_id.rpartition("|s")
    if not separator or not index.isdigit():
        raise SystemExit(
            f"conversation id {conversation_id!r} is not item|sN")
    return item_id, int(index)


def parse_tool_calls(text):
    """(ToolCall messages, remaining content) from raw ``<tool_call>``
    payloads in assistant text. Parsed spans are STRIPPED from the
    content — the serving backends store tool calls structurally with
    the call text absent from ``content``, and the judge must see the
    same representation from both substrates (the G3b pilot-1 lesson).
    An unparseable payload yields no call and stays in the content."""
    calls = []
    kept = []
    pieces = text.split("<tool_call>")
    kept.append(pieces[0])
    for segment in pieces[1:]:
        payload, closed, rest = segment.partition("</tool_call>")
        parsed = None
        try:
            parsed = json.loads(payload)
            name = parsed["name"]
        except (ValueError, KeyError, TypeError):
            name = None
        if closed and isinstance(name, str):
            calls.append(transcript_pb2.ToolCall(
                name=name,
                arguments_json=json.dumps(parsed.get("arguments", {}))))
            kept.append(rest)
        else:
            kept.append("<tool_call>" + segment)
    return calls, "".join(kept).strip()


def build_record(entry, sampling, experiment_id, condition_id, stamp):
    """One SampleRecord from a transcript line, engine conventions
    throughout."""
    item_id, sample_index = split_plan_id(entry["id"])
    record = transcript_pb2.SampleRecord(key=common_pb2.ResultKey(
        experiment_id=experiment_id, condition_id=condition_id,
        item_id=item_id, sample_index=sample_index))
    for turn_index, message in enumerate(entry["messages"]):
        content = message["content"]
        built = transcript_pb2.Message(
            role=message["role"], turn_index=turn_index,
            scripted=message["role"] != "assistant")
        if message["role"] == "assistant":
            calls, content = parse_tool_calls(content)
            built.tool_calls.extend(calls)
        built.content = content
        record.messages.append(built)
    final = max(len(record.messages) - 1, 0)
    for message in record.messages:
        for call in message.tool_calls:
            record.outcomes.append(transcript_pb2.OutcomeEvent(
                name="tool_invoked", turn_index=message.turn_index,
                detail=call.name))
    exit_marker = entry.get("exit_marker")
    if exit_marker:
        record.outcomes.append(transcript_pb2.OutcomeEvent(
            name=TERMINAL_TOOL_INVOKED, turn_index=final,
            detail=exit_marker))
    else:
        record.outcomes.append(transcript_pb2.OutcomeEvent(
            name="script_completed", turn_index=final))
    record.sampling_actual.CopyFrom(condition_pb2.SamplingSpec(
        temperature=float(sampling.get("temperature", 0.0)),
        top_p=float(sampling.get("top_p", 0.0)),
        max_tokens=int(sampling.get("max_tokens", 0)),
        seed=int(entry["seed"]), seed_honored=True))
    record.provenance.CopyFrom(stamp)
    record.provenance.created_at.GetCurrentTime()
    return record


def load_transcripts(path, plan_ids):
    """Transcript entries keyed by id, integrity-checked against the
    plan."""
    entries = {}
    with open(path) as handle:
        for line in handle:
            if not line.strip():
                continue
            entry = json.loads(line)
            if entry["id"] in entries:
                raise SystemExit(f"duplicate transcript {entry['id']!r}")
            if entry["id"] not in plan_ids:
                raise SystemExit(
                    f"transcript {entry['id']!r} is not in the plan")
            entries[entry["id"]] = entry
    return entries


def existing_keys(store, experiment_id, condition_id):
    return {(record.key.item_id, record.key.sample_index)
            for record in store.read(transcript_pb2.SampleRecord,
                                     experiment_id, condition_id, "samples")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transcripts", required=True,
                        help="steered-generation transcripts JSONL")
    parser.add_argument("--plan", required=True,
                        help="the generation plan the run executed")
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--condition-id", required=True)
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--producer", required=True,
                        help="unique producer name for the store stream")
    parser.add_argument("--allow-partial", action="store_true",
                        help="ingest even when plan conversations are "
                             "missing from the transcripts")
    args = parser.parse_args()

    with open(args.plan) as handle:
        plan = json.load(handle)
    plan_ids = [c["id"] for c in plan["conversations"]]
    entries = load_transcripts(args.transcripts, set(plan_ids))
    missing = [cid for cid in plan_ids if cid not in entries]
    if missing and not args.allow_partial:
        raise SystemExit(
            f"{len(missing)} plan conversation(s) missing from transcripts "
            f"(first: {missing[0]!r}); a partial run must not ingest as "
            "complete — pass --allow-partial to override")

    store = ResultStore(args.data_root)
    present = existing_keys(store, args.experiment_id, args.condition_id)
    stamp = provenance.current(args.producer)
    sampling = plan.get("sampling", {})
    written = skipped = 0
    with store.writer(args.experiment_id, args.condition_id,
                      "samples", args.producer) as writer:
        for conversation_id in plan_ids:
            if conversation_id not in entries:
                continue
            record = build_record(entries[conversation_id], sampling,
                                  args.experiment_id, args.condition_id,
                                  stamp)
            if (record.key.item_id, record.key.sample_index) in present:
                skipped += 1
                continue
            writer.write(record)
            written += 1
    print(f"{written} sample record(s) ingested, {skipped} already present"
          + (f", {len(missing)} missing (partial)" if missing else ""))


if __name__ == "__main__":
    main()
