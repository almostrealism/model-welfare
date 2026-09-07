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
        {"id": "item-a|s0", "seed": 14000, "user_turns": ["u1", "u2"],
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
