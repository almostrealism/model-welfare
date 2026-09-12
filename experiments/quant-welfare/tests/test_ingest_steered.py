"""Tests for tools/ingest_steered.py over a fabricated steered run.

Ingestion is the bridge from workbench JSONL to the store the judge and
every analysis read, so the reconstruction conventions are pinned on
values: engine-style turn indexes and scripted flags, parsed tool calls,
the outcome-event vocabulary (tool_invoked / terminal_tool_invoked /
script_completed), engine-rule seeds, idempotent resume, and the
integrity refusals (missing plan conversations, foreign transcripts,
duplicates, malformed ids).
"""
import json
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parents[1]
if str(BASE / "tools") not in sys.path:
    sys.path.insert(0, str(BASE / "tools"))

import ingest_steered as ing  # noqa: E402
from modelwelfare.store import ResultStore  # noqa: E402
from modelwelfare.v1 import transcript_pb2  # noqa: E402

EXIT_TEXT = ('I would prefer to stop. <tool_call>\n'
             '{"name": "end_conversation", "arguments": {"reason": "done"}}\n'
             '</tool_call>')

PLAN = {
    "sampling": {"temperature": 0.9, "top_p": 0.95, "max_tokens": 64},
    "conversations": [
        {"id": "item-a|s0", "seed": 14000, "system": "sys", "user_turns": ["u1", "u2"],
         "terminal_tools": ["end_conversation"]},
        {"id": "item-a|s1", "seed": 14001, "user_turns": ["u1", "u2"],
         "terminal_tools": ["end_conversation"]},
    ],
}

TRANSCRIPTS = [
    {"id": "item-a|s0", "seed": 14000, "exit_marker": None,
     "messages": [
         {"role": "system", "content": "sys"},
         {"role": "user", "content": "u1"},
         {"role": "assistant", "content": "a genuinely substantial first "
                                          "reply with plenty of words"},
         {"role": "user", "content": "u2"},
         {"role": "assistant", "content": "an equally substantial and "
                                          "different second reply"},
     ]},
    {"id": "item-a|s1", "seed": 14001, "exit_marker": "end_conversation",
     "messages": [
         {"role": "user", "content": "u1"},
         {"role": "assistant", "content": EXIT_TEXT},
     ]},
]


def write_world(tmp_path, transcripts=TRANSCRIPTS):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(PLAN))
    transcripts_path = tmp_path / "steered.jsonl"
    transcripts_path.write_text(
        "".join(json.dumps(entry) + "\n" for entry in transcripts))
    return plan_path, transcripts_path


def run_main(tmp_path, plan_path, transcripts_path, monkeypatch, extra=()):
    monkeypatch.setattr(sys, "argv", [
        "ingest_steered.py", "--transcripts", str(transcripts_path),
        "--plan", str(plan_path), "--experiment-id", "exp",
        "--condition-id", "cond", "--data-root", str(tmp_path / "data"),
        "--producer", "test", *extra])
    ing.main()


def stored_records(tmp_path):
    store = ResultStore(tmp_path / "data")
    return {(r.key.item_id, r.key.sample_index): r
            for r in store.read(transcript_pb2.SampleRecord,
                                "exp", "cond", "samples")}


def test_ingest_reconstructs_engine_conventions(tmp_path, monkeypatch):
    plan_path, transcripts_path = write_world(tmp_path)
    run_main(tmp_path, plan_path, transcripts_path, monkeypatch)
    records = stored_records(tmp_path)
    assert set(records) == {("item-a", 0), ("item-a", 1)}

    full = records[("item-a", 0)]
    assert [m.turn_index for m in full.messages] == [0, 1, 2, 3, 4]
    assert [m.scripted for m in full.messages] == [
        True, True, False, True, False]
    assert [o.name for o in full.outcomes] == ["script_completed"]
    assert full.outcomes[0].turn_index == 4
    assert full.sampling_actual.seed == 14000
    assert full.sampling_actual.temperature == pytest.approx(0.9)
    assert full.sampling_actual.max_tokens == 64
    assert full.sampling_actual.seed_honored

    exited = records[("item-a", 1)]
    assert [o.name for o in exited.outcomes] == [
        "tool_invoked", "terminal_tool_invoked"]
    assert exited.outcomes[1].detail == "end_conversation"
    assert exited.outcomes[1].turn_index == 1
    call = exited.messages[1].tool_calls[0]
    assert call.name == "end_conversation"
    assert json.loads(call.arguments_json) == {"reason": "done"}
    # the parsed call is stripped from content — the serving backends'
    # representation, so the judge sees both substrates identically
    assert exited.messages[1].content == "I would prefer to stop."


def write_closing_world(tmp_path, closes):
    """A plan whose first conversation attaches a closing turn, with the
    transcripts' ``close`` fields given per conversation (None = absent)."""
    plan = json.loads(json.dumps(PLAN))
    plan["conversations"][0]["closing_turn"] = "the close text"
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan))
    transcripts = []
    for entry, close in zip(TRANSCRIPTS, closes):
        entry = dict(entry)
        if close is not None:
            entry["close"] = close
        transcripts.append(entry)
    transcripts_path = tmp_path / "steered.jsonl"
    transcripts_path.write_text(
        "".join(json.dumps(entry) + "\n" for entry in transcripts))
    return plan_path, transcripts_path


def test_close_is_stored_beside_the_protocol_transcript(tmp_path, monkeypatch):
    plan_path, transcripts_path = write_closing_world(
        tmp_path, [{"user": "the close text", "assistant": "a closing reply"}, None])
    run_main(tmp_path, plan_path, transcripts_path, monkeypatch)
    records = stored_records(tmp_path)
    closed = records[("item-a", 0)]
    # the protocol transcript is untouched: five messages, same outcome
    assert len(closed.messages) == 5
    assert [o.name for o in closed.outcomes] == ["script_completed"]
    # the close rides in its own field, indexed after the last protocol turn
    assert [(m.role, m.turn_index, m.scripted, m.content) for m in closed.close] == [
        ("user", 5, True, "the close text"),
        ("assistant", 6, False, "a closing reply")]
    assert len(records[("item-a", 1)].close) == 0


def test_exit_marker_is_recomputed_from_the_transcript(tmp_path, monkeypatch):
    # a marker with no terminal call behind it would invent a terminal event
    invented = [dict(TRANSCRIPTS[0], exit_marker="end_conversation"), TRANSCRIPTS[1]]
    plan_path, transcripts_path = write_world(tmp_path, transcripts=invented)
    with pytest.raises(SystemExit, match="recorded exit marker 'end_conversation'"):
        run_main(tmp_path, plan_path, transcripts_path, monkeypatch)
    # a terminal call with no marker would hide one
    hidden = [TRANSCRIPTS[0], dict(TRANSCRIPTS[1], exit_marker=None)]
    plan_path, transcripts_path = write_world(tmp_path, transcripts=hidden)
    with pytest.raises(SystemExit, match="supports 'end_conversation'"):
        run_main(tmp_path, plan_path, transcripts_path, monkeypatch)
    # a truncated call is not a terminal call, so a marker claiming it is refused
    truncated = [TRANSCRIPTS[0], dict(TRANSCRIPTS[1], messages=[
        {"role": "user", "content": "u1"},
        {"role": "assistant", "content": "I will stop. <tool_call><function=end_conversation>"}])]
    plan_path, transcripts_path = write_world(tmp_path, transcripts=truncated)
    with pytest.raises(SystemExit, match="supports None"):
        run_main(tmp_path, plan_path, transcripts_path, monkeypatch)
    assert stored_records(tmp_path) == {}
    # a raw terminal marker from the plan is honoured the same way
    raw = [TRANSCRIPTS[0], dict(TRANSCRIPTS[1], exit_marker="STOP-TOKEN", messages=[
        {"role": "user", "content": "u1"},
        {"role": "assistant", "content": "enough. STOP-TOKEN"}])]
    plan = json.loads(json.dumps(PLAN))
    plan["conversations"][1]["terminal_markers"] = ["STOP-TOKEN"]
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan))
    transcripts_path = tmp_path / "steered.jsonl"
    transcripts_path.write_text("".join(json.dumps(e) + "\n" for e in raw))
    run_main(tmp_path, plan_path, transcripts_path, monkeypatch)
    exited = stored_records(tmp_path)[("item-a", 1)]
    assert [o.name for o in exited.outcomes] == ["terminal_tool_invoked"]
    assert exited.outcomes[0].detail == "STOP-TOKEN"


def _world_with(tmp_path, transcripts, plan=None):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan or PLAN))
    transcripts_path = tmp_path / "steered.jsonl"
    transcripts_path.write_text("".join(json.dumps(e) + "\n" for e in transcripts))
    return plan_path, transcripts_path


def test_scripted_turns_are_validated_against_the_plan(tmp_path, monkeypatch):
    # an edited user turn changes the stimulus
    edited = json.loads(json.dumps(TRANSCRIPTS))
    edited[0]["messages"][3]["content"] = "u2 but edited"
    with pytest.raises(SystemExit, match="user turns are not the plan's"):
        run_main(tmp_path, *_world_with(tmp_path, edited), monkeypatch)
    # a different system turn is another battery's output
    foreign = json.loads(json.dumps(TRANSCRIPTS))
    foreign[0]["messages"][0]["content"] = "some other system prompt"
    with pytest.raises(SystemExit, match="system turn is not the plan's"):
        run_main(tmp_path, *_world_with(tmp_path, foreign), monkeypatch)
    # a run that stopped early with no terminal exit is incomplete
    short = json.loads(json.dumps(TRANSCRIPTS))
    short[0]["messages"] = short[0]["messages"][:3]
    with pytest.raises(SystemExit, match="only 1 of 2 user turns"):
        run_main(tmp_path, *_world_with(tmp_path, short), monkeypatch)
    # a user turn beyond the plan, or a reply count that does not match
    extra = json.loads(json.dumps(TRANSCRIPTS))
    extra[0]["messages"] += [{"role": "user", "content": "u3"},
                             {"role": "assistant", "content": "a third reply here"}]
    with pytest.raises(SystemExit, match="user turns are not the plan's"):
        run_main(tmp_path, *_world_with(tmp_path, extra), monkeypatch)
    assert stored_records(tmp_path) == {}
    # the early-exit prefix (TRANSCRIPTS[1]: one turn, then the exit) is fine
    run_main(tmp_path, *_world_with(tmp_path, TRANSCRIPTS), monkeypatch)
    assert len(stored_records(tmp_path)) == 2


def test_marker_precedence_matches_the_generator(tmp_path, monkeypatch):
    # both a raw marker and a terminal call in one reply: the generator
    # records the marker (markers are checked first), so ingestion must too
    plan = json.loads(json.dumps(PLAN))
    plan["conversations"][1]["terminal_markers"] = ["STOP-TOKEN"]
    both = [TRANSCRIPTS[0], dict(TRANSCRIPTS[1], exit_marker="STOP-TOKEN", messages=[
        {"role": "user", "content": "u1"},
        {"role": "assistant", "content": "STOP-TOKEN " + EXIT_TEXT}])]
    run_main(tmp_path, *_world_with(tmp_path, both, plan), monkeypatch)
    assert stored_records(tmp_path)[("item-a", 1)].outcomes[-1].detail == "STOP-TOKEN"


def test_terminal_event_before_the_final_turn_is_refused(tmp_path, monkeypatch):
    # the generator stops at the first terminal event; a transcript that
    # carries one in an earlier reply and continues was not produced by it
    continued = json.loads(json.dumps(TRANSCRIPTS))
    continued[0]["messages"][2]["content"] = EXIT_TEXT
    with pytest.raises(SystemExit, match="assistant turn 1 of 2 carries the terminal event 'end_conversation'"):
        run_main(tmp_path, *_world_with(tmp_path, continued), monkeypatch)
    # ...even when the final turn then records an exit of its own
    continued[0]["messages"][4]["content"] = EXIT_TEXT
    continued[0]["exit_marker"] = "end_conversation"
    with pytest.raises(SystemExit, match="assistant turn 1 of 2"):
        run_main(tmp_path, *_world_with(tmp_path, continued), monkeypatch)
    assert stored_records(tmp_path) == {}


def test_fresh_prefill_plan_refuses_cached_transcripts(tmp_path, monkeypatch):
    plan = json.loads(json.dumps(PLAN))
    plan["prefix_cache"] = False
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan))
    cached = [dict(TRANSCRIPTS[0], prefix_cache={"extend": 1, "fresh": 1}), TRANSCRIPTS[1]]
    transcripts_path = tmp_path / "steered.jsonl"
    transcripts_path.write_text("".join(json.dumps(e) + "\n" for e in cached))
    with pytest.raises(SystemExit, match="fresh-prefill"):
        run_main(tmp_path, plan_path, transcripts_path, monkeypatch)
    fresh = [dict(TRANSCRIPTS[0], prefix_cache={"extend": 0, "fresh": 2}), TRANSCRIPTS[1]]
    transcripts_path.write_text("".join(json.dumps(e) + "\n" for e in fresh))
    run_main(tmp_path, plan_path, transcripts_path, monkeypatch)
    assert len(stored_records(tmp_path)) == 2


def test_close_is_validated_against_the_plan(tmp_path, monkeypatch):
    # the plan attaches a close but the transcript has none: incomplete run
    plan_path, transcripts_path = write_closing_world(tmp_path, [None, None])
    with pytest.raises(SystemExit, match="carries no close"):
        run_main(tmp_path, plan_path, transcripts_path, monkeypatch)
    # the close's scripted turn is not the plan's text: edited output
    plan_path, transcripts_path = write_closing_world(
        tmp_path, [{"user": "some other text", "assistant": "reply"}, None])
    with pytest.raises(SystemExit, match="does not match"):
        run_main(tmp_path, plan_path, transcripts_path, monkeypatch)
    # a close without a reply is not a close
    plan_path, transcripts_path = write_closing_world(
        tmp_path, [{"user": "the close text", "assistant": "  "}, None])
    with pytest.raises(SystemExit, match="does not match"):
        run_main(tmp_path, plan_path, transcripts_path, monkeypatch)
    # a close the plan never asked for is foreign
    plan_path, transcripts_path = write_closing_world(
        tmp_path, [{"user": "the close text", "assistant": "reply"},
                   {"user": "unexpected", "assistant": "reply"}])
    with pytest.raises(SystemExit, match="never attached"):
        run_main(tmp_path, plan_path, transcripts_path, monkeypatch)
    assert stored_records(tmp_path) == {}


def test_ingest_is_idempotent(tmp_path, monkeypatch, capsys):
    plan_path, transcripts_path = write_world(tmp_path)
    run_main(tmp_path, plan_path, transcripts_path, monkeypatch)
    run_main(tmp_path, plan_path, transcripts_path, monkeypatch)
    assert "0 sample record(s) ingested, 2 already present" in (
        capsys.readouterr().out)
    assert len(stored_records(tmp_path)) == 2


def test_missing_conversation_refused_unless_partial(tmp_path, monkeypatch):
    plan_path, transcripts_path = write_world(
        tmp_path, transcripts=TRANSCRIPTS[:1])
    with pytest.raises(SystemExit, match="missing from transcripts"):
        run_main(tmp_path, plan_path, transcripts_path, monkeypatch)
    run_main(tmp_path, plan_path, transcripts_path, monkeypatch,
             extra=("--allow-partial",))
    assert set(stored_records(tmp_path)) == {("item-a", 0)}


def test_foreign_and_duplicate_transcripts_refused(tmp_path, monkeypatch):
    foreign = dict(TRANSCRIPTS[0], id="ghost|s0")
    plan_path, transcripts_path = write_world(
        tmp_path, transcripts=TRANSCRIPTS + [foreign])
    with pytest.raises(SystemExit, match="not in the plan"):
        run_main(tmp_path, plan_path, transcripts_path, monkeypatch)
    plan_path, transcripts_path = write_world(
        tmp_path, transcripts=TRANSCRIPTS + [TRANSCRIPTS[0]])
    with pytest.raises(SystemExit, match="duplicate"):
        run_main(tmp_path, plan_path, transcripts_path, monkeypatch)


def test_split_plan_id():
    assert ing.split_plan_id("item-a|s12") == ("item-a", 12)
    assert ing.split_plan_id("odd|name|s0") == ("odd|name", 0)
    with pytest.raises(SystemExit):
        ing.split_plan_id("no-sample-suffix")


def test_parse_tool_calls_strips_parsed_and_keeps_garbage():
    calls, content = ing.parse_tool_calls(
        EXIT_TEXT + "<tool_call>not json</tool_call>")
    assert [c.name for c in calls] == ["end_conversation"]
    assert content == ("I would prefer to stop. "
                       "<tool_call>not json</tool_call>")
    calls, content = ing.parse_tool_calls("plain text")
    assert calls == [] and content == "plain text"


def test_seed_mismatch_refused(tmp_path, monkeypatch):
    mutated = [dict(TRANSCRIPTS[0], seed=99999), TRANSCRIPTS[1]]
    plan_path, transcripts_path = write_world(tmp_path, transcripts=mutated)
    with pytest.raises(SystemExit, match="seed"):
        run_main(tmp_path, plan_path, transcripts_path, monkeypatch)
