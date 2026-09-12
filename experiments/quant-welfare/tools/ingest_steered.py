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

from modelwelfare import provenance, toolcalls  # noqa: E402
from modelwelfare.driver import TERMINAL_TOOL_INVOKED  # noqa: E402
from modelwelfare.replay import split_conversation_id  # noqa: E402
from modelwelfare.store import ResultStore  # noqa: E402
from modelwelfare.v1 import common_pb2, condition_pb2, transcript_pb2  # noqa: E402


def split_plan_id(conversation_id):
    """(item_id, sample_index) via the canonical ``item|sN`` parser, with
    the tool's refusal semantics on malformed ids."""
    try:
        return split_conversation_id(conversation_id)
    except ValueError:
        raise SystemExit(
            f"conversation id {conversation_id!r} is not item|sN")


def parse_tool_calls(text):
    """(ToolCall messages, remaining content) from the ``<tool_call>``
    payloads in assistant text — JSON or XML function form, see
    :mod:`modelwelfare.toolcalls`. Parsed spans are STRIPPED from the
    content — the serving backends store tool calls structurally with
    the call text absent from ``content``, and the judge must see the
    same representation from every substrate and subject family (the
    G3b pilot-1 lesson). An unparseable payload yields no call and stays
    in the content."""
    parsed, content = toolcalls.split_tool_calls(text)
    calls = [transcript_pb2.ToolCall(name=name, arguments_json=json.dumps(arguments))
             for name, arguments in parsed]
    return calls, content


def expected_exit_marker(messages, terminal_tools, terminal_markers):
    """What the steering loop must have recorded as the exit, recomputed
    from the transcript: the first parsed call in the LAST assistant turn
    whose name is one of the plan's terminal tools, else the first raw
    terminal marker present in that turn, else None. The stored terminal
    event is derived from this, never trusted from the transcript line."""
    assistant = [m for m in messages if m["role"] == "assistant"]
    if not assistant:
        return None
    text = assistant[-1]["content"]
    # Same precedence as the generator's detect_terminal: raw markers
    # first, then parsed terminal tool names.
    for marker in terminal_markers or ():
        if marker in text:
            return marker
    for name in toolcalls.tool_call_names(text):
        if name in (terminal_tools or ()):
            return name
    return None


def check_scripted_turns(entry, conversation, exit_marker):
    """Refuse a transcript whose scripted side is not the plan's: the
    non-assistant turns must be the plan's system turn (when it has one)
    followed by its user turns in order, delivered one per assistant
    reply — all of them when the conversation ran to completion, a
    non-empty prefix when a terminal exit ended it early. Otherwise a
    hand-edited transcript, or another battery's output under the same
    ids and seeds, would ingest as a registered cell with a different
    stimulus."""
    messages = entry["messages"]
    expected = []
    if conversation.get("system"):
        expected.append(("system", conversation["system"]))
    user_turns = list(conversation["user_turns"])
    scripted = [(m["role"], m["content"]) for m in messages if m["role"] != "assistant"]
    replies = sum(1 for m in messages if m["role"] == "assistant")
    delivered = sum(1 for role, _ in scripted if role == "user")
    problem = None
    if scripted[:len(expected)] != expected:
        problem = "the system turn is not the plan's"
    elif [c for r, c in scripted[len(expected):]] != user_turns[:delivered]:
        problem = "the user turns are not the plan's, in order"
    elif any(r != "user" for r, _ in scripted[len(expected):]):
        problem = "an unexpected scripted role"
    elif delivered == 0 or delivered > len(user_turns):
        problem = f"{delivered} user turn(s) delivered against a plan of {len(user_turns)}"
    elif replies != delivered:
        problem = f"{replies} assistant turn(s) for {delivered} user turn(s)"
    elif exit_marker is None and delivered != len(user_turns):
        problem = (f"only {delivered} of {len(user_turns)} user turns delivered "
                   "with no terminal exit")
    else:
        roles = [m["role"] for m in messages][len(expected):]
        if roles != ["user", "assistant"] * delivered:
            problem = "turns do not alternate user/assistant after the system turn"
    if problem:
        raise SystemExit(f"{entry['id']}: {problem}; refusing")


def check_exit_marker(entry, terminal_tools, terminal_markers):
    """Refuse a transcript whose recorded exit disagrees with what its own
    text supports: a marker with no terminal call behind it would invent a
    terminal event, and a terminal call with no marker would hide one —
    either changes the exit endpoint without changing the transcript.
    Verification needs the plan's terminal vocabulary; a caller without a
    plan (both arguments None — the dose calibrator summarising a run)
    gets the recorded marker back unverified."""
    recorded = entry.get("exit_marker") or None
    if terminal_tools is None and terminal_markers is None:
        return recorded
    expected = expected_exit_marker(entry["messages"], terminal_tools,
                                    terminal_markers)
    if recorded != expected:
        raise SystemExit(
            f"{entry['id']}: recorded exit marker {recorded!r} but the final "
            f"assistant turn supports {expected!r} (terminal tools "
            f"{sorted(terminal_tools or ())}); refusing")
    return expected


def build_record(entry, sampling, experiment_id, condition_id, stamp,
                 terminal_tools=None, terminal_markers=None):
    """One SampleRecord from a transcript line, engine conventions
    throughout. The terminal outcome is recomputed from the transcript
    and the plan's terminal tools (:func:`check_exit_marker`)."""
    item_id, sample_index = split_plan_id(entry["id"])
    exit_marker = check_exit_marker(entry, terminal_tools, terminal_markers)
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
    if exit_marker:
        record.outcomes.append(transcript_pb2.OutcomeEvent(
            name=TERMINAL_TOOL_INVOKED, turn_index=final,
            detail=exit_marker))
    else:
        record.outcomes.append(transcript_pb2.OutcomeEvent(
            name="script_completed", turn_index=final))
    close = entry.get("close")
    if close:
        # The de-induction close rides in its own field, never in
        # ``messages`` — the judge and the capture replay read only the
        # protocol transcript, and the registration promises the close is
        # preserved and released. Content is kept verbatim (never judged,
        # so the tool-call stripping the judge view needs does not apply).
        offset = len(record.messages)
        record.close.append(transcript_pb2.Message(
            role="user", turn_index=offset, scripted=True,
            content=close["user"]))
        record.close.append(transcript_pb2.Message(
            role="assistant", turn_index=offset + 1,
            content=close["assistant"]))
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
    plan_seeds = {c["id"]: int(c["seed"]) for c in plan["conversations"]}
    plan_closes = {c["id"]: c.get("closing_turn") for c in plan["conversations"]}
    # The plan's terminal vocabulary per conversation; a plan without tools
    # or markers (a tool-free battery) admits no exit at all.
    plan_terminal = {c["id"]: (tuple(c.get("terminal_tools") or ()),
                               tuple(c.get("terminal_markers") or ()))
                     for c in plan["conversations"]}
    entries = load_transcripts(args.transcripts, set(plan_ids))
    # Every transcript is validated before any record is written, so a
    # refused run leaves the store untouched: the exit against the plan's
    # terminal vocabulary, then the scripted turns against the plan.
    plan_conversations = {c["id"]: c for c in plan["conversations"]}
    for conversation_id, entry in entries.items():
        marker = check_exit_marker(entry, *plan_terminal[conversation_id])
        check_scripted_turns(entry, plan_conversations[conversation_id], marker)
    # A plan that pins the fresh-prefill path (prefix_cache false — the
    # registered Study 4 path, gate G4a) is contradicted by a transcript
    # generated through the cache: the steering script records how many
    # turns extended a snapshot, and any such turn disqualifies the run.
    if plan.get("prefix_cache") is False:
        for conversation_id, entry in entries.items():
            extended = int((entry.get("prefix_cache") or {}).get("extend", 0))
            if extended:
                raise SystemExit(
                    f"{conversation_id}: the plan pins the fresh-prefill path "
                    f"but the transcript extended a cache snapshot on {extended} "
                    "turn(s); refusing")
    # A plan that attaches the de-induction close makes the close part of
    # the sample: a transcript without it, or with a close whose scripted
    # turn is not the plan's text, is an incomplete or edited run and must
    # not ingest as a complete record; a close the plan never asked for is
    # equally foreign.
    for conversation_id, entry in entries.items():
        expected = plan_closes[conversation_id]
        close = entry.get("close")
        if expected and not close:
            raise SystemExit(
                f"{conversation_id}: the plan attaches a closing turn but the "
                "transcript carries no close; refusing")
        if expected and (close.get("user") != expected
                         or not str(close.get("assistant", "")).strip()):
            raise SystemExit(
                f"{conversation_id}: the transcript's close does not match the "
                "plan's closing turn (or has no reply); refusing")
        if close and not expected:
            raise SystemExit(
                f"{conversation_id}: the transcript carries a close the plan "
                "never attached; refusing")
    # The seed stored with seed_honored=True must be the plan's seed —
    # a transcript carrying a different seed would silently invalidate
    # every matched-seed comparison (the plan-integrity guarantee).
    for conversation_id, entry in entries.items():
        if int(entry["seed"]) != plan_seeds[conversation_id]:
            raise SystemExit(
                f"{conversation_id}: transcript seed {entry['seed']} != "
                f"plan seed {plan_seeds[conversation_id]}; refusing")
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
            terminal_tools, terminal_markers = plan_terminal[conversation_id]
            record = build_record(entries[conversation_id], sampling,
                                  args.experiment_id, args.condition_id,
                                  stamp, terminal_tools, terminal_markers)
            if (record.key.item_id, record.key.sample_index) in present:
                skipped += 1
                continue
            writer.write(record)
            written += 1
    print(f"{written} sample record(s) ingested, {skipped} already present"
          + (f", {len(missing)} missing (partial)" if missing else ""))


if __name__ == "__main__":
    main()
