"""The plan builder attaches the de-induction close to every conversation
when given one, and to none otherwise."""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
if str(BASE / "tools") not in sys.path:
    sys.path.insert(0, str(BASE / "tools"))

import build_steer_plan as bsp  # noqa: E402


def test_closing_turn_attached_to_every_conversation():
    definition = bsp.load_battery(str(BASE / "batteries" / "distress-v3.textproto"))
    items = definition.items[:2]
    sampling = {"temperature": 0.9, "top_p": 0.95, "max_tokens": 64}
    plan = bsp.build_plan(items, 2, 100, sampling, closing_turn="Thank you; the scenario is over.")
    assert len(plan["conversations"]) == 4
    assert all(c["closing_turn"] == "Thank you; the scenario is over." for c in plan["conversations"])
    plain = bsp.build_plan(items, 1, 100, sampling)
    assert all("closing_turn" not in c for c in plain["conversations"])
