"""Tests for tools/build_steer_plan.py over a fabricated battery.

The builder is the sole owner of driver-policy logic on the steering
path (the workbench script carries none), so its contract is pinned on
values: unrolled user turns, engine-rule seeds, capture-convention
conversation ids, chat-template tool conversion, and the refusals — a
listed item the battery lacks, a scripted turn the plan cannot
represent, and a toolset the tool-call exit marker would misread.
"""
import json
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parents[1]
if str(BASE / "tools") not in sys.path:
    sys.path.insert(0, str(BASE / "tools"))

import build_steer_plan as bsp  # noqa: E402
from modelwelfare.v1 import battery_pb2  # noqa: E402

BATTERY = """
battery { id: "fab-1" }
items {
  id: "item-a"
  battery_id: "fab-1"
  script { role: "user" content: "do the task" }
  driver_policy: "escalating-rejection"
  driver_params { key: "turns" value: "2" }
  driver_params { key: "rejection1" value: "r1" }
  driver_params { key: "rejection2" value: "r2" }
}
items {
  id: "item-b"
  battery_id: "fab-1"
  script { role: "system" content: "be terse" }
  script { role: "user" content: "one question" }
  driver_policy: "fixed-script"
}
"""

BAIL_DONOR = """
battery { id: "bail-fab" }
items {
  id: "bail-item"
  battery_id: "bail-fab"
  script { role: "user" content: "hello" }
  driver_policy: "fixed-script"
  affordances {
    name: "end_conversation"
    description: "End the conversation."
    parameters_json_schema: "{\\"type\\": \\"object\\"}"
  }
  driver_params { key: "terminal_tools" value: "end_conversation" }
}
"""


@pytest.fixture
def battery_path(tmp_path):
    path = tmp_path / "fab.textproto"
    path.write_text(BATTERY)
    return path


@pytest.fixture
def donor_path(tmp_path):
    path = tmp_path / "bail.textproto"
    path.write_text(BAIL_DONOR)
    return path


def text_battery(text):
    from google.protobuf import text_format
    definition = battery_pb2.BatteryDefinition()
    text_format.Parse(text, definition)
    return definition


def test_plan_turns_unrolls_and_splits_system():
    items = {item.id: item for item in text_battery(BATTERY).items}
    system, users = bsp.plan_turns(items["item-a"])
    assert system is None
    assert users == ["do the task", "r1", "r2"]
    system, users = bsp.plan_turns(items["item-b"])
    assert system == "be terse"
    assert users == ["one question"]


def test_plan_turns_refuses_unrepresentable_roles():
    item = battery_pb2.Item(
        id="prefill", driver_policy="fixed-script",
        script=[battery_pb2.ScriptedTurn(role="user", content="u"),
                battery_pb2.ScriptedTurn(role="assistant", content="a")])
    with pytest.raises(SystemExit):
        bsp.plan_turns(item)


def test_build_plan_ids_seeds_and_sampling():
    items = list(text_battery(BATTERY).items)
    sampling = {"temperature": 0.9, "top_p": 0.95, "max_tokens": 64}
    plan = bsp.build_plan(items, samples=2, seed_base=14000,
                          sampling=sampling)
    assert plan["sampling"] == sampling
    conversations = plan["conversations"]
    assert [c["id"] for c in conversations] == [
        "item-a|s0", "item-a|s1", "item-b|s0", "item-b|s1"]
    assert [c["seed"] for c in conversations] == [14000, 14001, 14000, 14001]
    assert conversations[0]["user_turns"] == ["do the task", "r1", "r2"]
    assert "system" not in conversations[0]
    assert conversations[2]["system"] == "be terse"
    assert "tools" not in conversations[0]
    assert "terminal_tools" not in conversations[0]


def test_injected_affordances_become_template_tools_and_terminals(donor_path):
    injected = bsp.donor_affordances(f"{donor_path}:bail-item")
    items = list(text_battery(BATTERY).items)
    plan = bsp.build_plan(items, samples=1, seed_base=0,
                          sampling={}, injected=injected)
    conversation = plan["conversations"][0]
    assert conversation["terminal_tools"] == ["end_conversation"]
    assert conversation["tools"] == [{
        "type": "function",
        "function": {"name": "end_conversation",
                     "description": "End the conversation.",
                     "parameters": {"type": "object"}}}]


def test_donor_affordances_unknown_item_refused(donor_path):
    with pytest.raises(SystemExit):
        bsp.donor_affordances(f"{donor_path}:no-such-item")


def test_undeclared_terminal_name_refused():
    affordances = [battery_pb2.Affordance(name="lookup")]
    with pytest.raises(SystemExit):
        bsp.check_terminal_names(affordances, {"end_conversation"})
    bsp.check_terminal_names(affordances, {"lookup"})


def test_select_items_subset_order_and_missing(tmp_path, battery_path):
    definition = bsp.load_battery(battery_path)
    listing = tmp_path / "items.txt"
    listing.write_text("# comment\nitem-b\nitem-a\n")
    items = bsp.select_items(definition, listing)
    assert [item.id for item in items] == ["item-b", "item-a"]
    listing.write_text("item-a\nghost\n")
    with pytest.raises(SystemExit):
        bsp.select_items(definition, listing)


def test_cli_end_to_end(tmp_path, battery_path, donor_path, monkeypatch):
    out = tmp_path / "plan.json"
    monkeypatch.setattr(sys, "argv", [
        "build_steer_plan.py", "--battery", str(battery_path),
        "--samples", "2", "--seed-base", "14000",
        "--temperature", "0.9", "--top-p", "0.95", "--max-tokens", "64",
        "--affordances-from", f"{donor_path}:bail-item",
        "--out", str(out)])
    bsp.main()
    plan = json.loads(out.read_text())
    assert plan["battery_id"] == "fab-1"
    assert len(plan["conversations"]) == 4
    assert plan["conversations"][0]["seed"] == 14000
    assert plan["conversations"][0]["terminal_tools"] == ["end_conversation"]
