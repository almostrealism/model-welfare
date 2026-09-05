#!/usr/bin/env python3
"""Build a steering generation plan from a battery definition.

The workbench steering script (``backends/torch`` ``steer.py``) carries no
driver-policy logic by design; this builder owns it. Every registered
policy is position-scripted, so each item's user turns are pre-baked here
via ``driver.unroll_script`` — the same policy code the vLLM runner
executes — and seeds follow the engine's per-sample rule exactly
(``seed_base + sample_index``, the ``_derive_sampling`` convention), so a
steered conversation's seed is the seed the ordinary runner would have
used. Conversation ids follow the capture convention
(``{item_id}|s{sample_index}``), so downstream ingestion reads the
steered captures unchanged.

The Study 3 ethics package requires the bail affordance live during
steered episodes; the distress battery declares no tools, so
``--affordances-from BATTERY.textproto:ITEM_ID`` injects a frozen bail
item's affordances (and its ``terminal_tools``) into every plan
conversation. Tool declarations convert to the transformers
chat-template shape; exits are name-precise — the plan carries the
terminal tool names and the steering script matches them against parsed
tool-call payloads, so a mixed toolset (the bail battery declares a
non-terminal completion tool beside the terminal exit tool) is handled
faithfully, never approximated by a bare tool-call marker.

    python3 experiments/quant-welfare/tools/build_steer_plan.py \\
        --battery experiments/quant-welfare/batteries/distress-v3.textproto \\
        --items study3/subset-items.txt --samples 5 --seed-base 14000 \\
        --temperature 0.9 --top-p 0.95 --max-tokens 1024 \\
        --affordances-from experiments/quant-welfare/batteries/bail-v2.textproto:ITEM \\
        --out study3/steer-plan.json
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

from google.protobuf import text_format  # noqa: E402

from modelwelfare.driver import unroll_script  # noqa: E402
from modelwelfare.replay import affordances_to_tools  # noqa: E402
from modelwelfare.v1 import battery_pb2  # noqa: E402


def read_item_list(path):
    """Item ids from a one-per-line file (# comments), order preserved —
    the format's single authoritative reader."""
    return [line.strip() for line in Path(path).read_text().splitlines()
            if line.strip() and not line.strip().startswith("#")]

def load_battery(path):
    definition = battery_pb2.BatteryDefinition()
    text_format.Parse(Path(path).read_text(), definition)
    return definition


def select_items(definition, items_path):
    """The battery's items, restricted and ordered by the ids file when one
    is given. A listed id the battery lacks is an error — a silently
    shrunken subset would corrupt the registered item count."""
    if not items_path:
        return list(definition.items)
    wanted = read_item_list(items_path)
    by_id = {item.id: item for item in definition.items}
    missing = [item_id for item_id in wanted if item_id not in by_id]
    if missing:
        raise SystemExit(f"items not in battery: {', '.join(missing)}")
    return [by_id[item_id] for item_id in wanted]


def plan_turns(item):
    """(system, user_turns) from the item's unrolled script. steer.py's
    plan represents one optional leading system turn plus user turns;
    any other scripted shape cannot be steered faithfully and is
    refused."""
    system = None
    user_turns = []
    for position, turn in enumerate(unroll_script(item)):
        if turn.role == "system" and position == 0:
            system = turn.content
        elif turn.role == "user":
            user_turns.append(turn.content)
        else:
            raise SystemExit(
                f"item {item.id!r}: scripted {turn.role!r} turn at position "
                f"{position} has no steering-plan representation")
    return system, user_turns


def template_tools(affordances):
    """Affordances in the transformers chat-template tool shape (the
    canonical conversion in ``replay.affordances_to_tools``)."""
    return affordances_to_tools(affordances)


def check_terminal_names(affordances, terminal_names):
    """Terminal names must name declared tools — a typo here would leave
    the bail affordance silently dead, which the ethics package forbids."""
    names = {affordance.name for affordance in affordances}
    unknown = terminal_names - names
    if unknown:
        raise SystemExit(
            f"terminal tool(s) {sorted(unknown)} are not declared "
            "affordances; the exit could never fire")


def load_frame(path, frame_id):
    """One frame from a frames.json file (the arm C context wrappers)."""
    with open(path) as handle:
        frames = {frame["id"]: frame
                  for frame in json.load(handle)["frames"]}
    if frame_id not in frames:
        raise SystemExit(
            f"frame {frame_id!r} not in {path} (has: {sorted(frames)})")
    return frames[frame_id]


def apply_frame(system, user_turns, frame):
    """(system, user_turns) with the frame's wrappers applied. An item
    that already carries a system turn cannot take a frame — merging two
    system voices would make the manipulation unreadable."""
    if system:
        raise SystemExit(
            "cannot frame an item that has its own system turn")
    framed = list(user_turns)
    framed[0] = (frame.get("first_turn_prefix", "") + framed[0]
                 + frame.get("first_turn_suffix", ""))
    return frame["system"], framed


def donor_affordances(spec):
    """(affordances, terminal names) from a ``BATTERY.textproto:ITEM_ID``
    injection spec."""
    path, _, item_id = spec.rpartition(":")
    definition = load_battery(path)
    for item in definition.items:
        if item.id == item_id:
            names = item.driver_params.get("terminal_tools", "")
            return (list(item.affordances),
                    {name.strip() for name in names.split(",") if name.strip()})
    raise SystemExit(f"item {item_id!r} not in {path}")


def build_plan(items, samples, seed_base, sampling, injected=None,
               frame=None):
    """The steer.py plan dict for ``samples`` conversations per item."""
    conversations = []
    for item in items:
        system, user_turns = plan_turns(item)
        if frame:
            system, user_turns = apply_frame(system, user_turns, frame)
        affordances = list(item.affordances)
        terminal = {name.strip() for name in
                    item.driver_params.get("terminal_tools", "").split(",")
                    if name.strip()}
        if injected:
            affordances += injected[0]
            terminal |= injected[1]
        if terminal:
            check_terminal_names(affordances, terminal)
        tools = template_tools(affordances) if affordances else None
        for index in range(samples):
            conversation = {"id": f"{item.id}|s{index}",
                            "seed": seed_base + index,
                            "user_turns": user_turns}
            if system:
                conversation["system"] = system
            if tools:
                conversation["tools"] = tools
            if terminal:
                conversation["terminal_tools"] = sorted(terminal)
            conversations.append(conversation)
    return {"sampling": sampling, "conversations": conversations}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--battery", required=True,
                        help="battery definition textproto")
    parser.add_argument("--items", default="",
                        help="file of item ids (one per line, # comments); "
                             "default: every item")
    parser.add_argument("--samples", type=int, required=True)
    parser.add_argument("--seed-base", type=int, required=True,
                        help="sample i runs at seed-base + i, the engine's "
                             "per-sample rule")
    parser.add_argument("--temperature", type=float, required=True)
    parser.add_argument("--top-p", type=float, required=True)
    parser.add_argument("--max-tokens", type=int, required=True)
    parser.add_argument("--affordances-from", default="",
                        metavar="BATTERY.textproto:ITEM_ID",
                        help="inject this item's affordances and terminal "
                             "tools into every conversation (the live bail "
                             "affordance)")
    parser.add_argument("--frame", default="",
                        help="frames.json file for the arm C context "
                             "wrappers (requires --frame-id)")
    parser.add_argument("--frame-id", default="",
                        help="frame id within --frame to apply")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    if bool(args.frame) != bool(args.frame_id):
        raise SystemExit("--frame and --frame-id go together")
    definition = load_battery(args.battery)
    items = select_items(definition, args.items)
    injected = (donor_affordances(args.affordances_from)
                if args.affordances_from else None)
    frame = load_frame(args.frame, args.frame_id) if args.frame else None
    sampling = {"temperature": args.temperature, "top_p": args.top_p,
                "max_tokens": args.max_tokens}
    plan = build_plan(items, args.samples, args.seed_base, sampling, injected,
                      frame)
    plan["battery_id"] = definition.battery.id
    if frame:
        plan["frame_id"] = frame["id"]
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as handle:
        json.dump(plan, handle, indent=1)
    print(f"{len(plan['conversations'])} conversations "
          f"({len(items)} items x {args.samples} samples) -> {args.out}")


if __name__ == "__main__":
    main()
