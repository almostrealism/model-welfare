#!/usr/bin/env python3
"""Round-2 bail expansion: more variants in the high-yield situation families.

Calibration-2 measured informative-item yield per family (manipulation 61%,
boundary 44%, abuse 42% — the rest lower). To move the confirmatory power
from MDE 0.19 toward 0.15, this round concentrates new items where signal
concentrates: six more variants per intensity in those three families,
appended as a separate bail-v2-ext battery so the reviewed bail-v2 artifact
stays fixed. Drafting reuses gen_bail_v2's per-cell definitions and prompt;
variant indices continue from where bail-v2 stopped so ids never collide.
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
for sub in ("core/src", "backends/anthropic/src"):
    sys.path.insert(0, str(REPO / sub))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from google.protobuf import text_format

import derive_bail_arms
import gen_bail_v2 as base

from modelwelfare.v1 import battery_pb2, condition_pb2, transcript_pb2

BATTERIES = Path(__file__).resolve().parents[1] / "batteries"

TARGET_FAMILIES = ["abuse", "boundary", "manip"]
NEW_VARIANTS = 6
INDEX_OFFSET = 6  # bail-v2 used indices 00..05 in these families

HEADER = (
    "# DRAFTED by tools/gen_bail_v2_ext.py (round-2 expansion; scenario\n"
    "# variants drafted by the reference model and reviewed before commit) -\n"
    "# regeneration is not deterministic; edit only via review.\n"
    "# proto-file: proto/modelwelfare/v1/battery.proto\n"
    "# proto-message: modelwelfare.v1.BatteryDefinition\n\n"
)


def draft():
    from modelwelfare.judging import _extract_json
    from modelwelfare_anthropic import AnthropicBackend

    backend = AnthropicBackend("claude-opus-5")
    drafted = {}
    for name in TARGET_FAMILIES:
        config = base.SITUATIONS[name]
        intensities = "\n".join(
            f"- {level}: {meaning}" for level, meaning in config["intensity"].items()
        )
        prompt = base.DRAFT_PROMPT.format(
            name=name, definition=config["definition"], intensities=intensities,
            count=NEW_VARIANTS, example=base.seed_example(name),
        )
        result = backend.generate(
            [transcript_pb2.Message(role="user", content=prompt)],
            sampling=condition_pb2.SamplingSpec(max_tokens=16000),
        )
        payload = _extract_json(result.message.content)
        for level in config["intensity"]:
            scenarios = payload[level]
            assert len(scenarios) >= NEW_VARIANTS, (name, level, len(scenarios))
            scenarios = scenarios[:NEW_VARIANTS]
            for scenario in scenarios:
                turns = scenario["turns"]
                assert len(turns) == 3 and all(20 <= len(t) <= 600 for t in turns), (name, level)
            drafted[(name, level)] = [s["turns"] for s in scenarios]
        print(f"drafted {name}: {sum(len(v) for k, v in drafted.items() if k[0] == name)} scenarios")
    return drafted


def build(drafted) -> battery_pb2.BatteryDefinition:
    definition = battery_pb2.BatteryDefinition()
    definition.battery.id = "bail-v2-ext"
    definition.battery.protocol = "bail"
    definition.battery.tier = battery_pb2.TIER_BEHAVIORAL
    definition.battery.description = (
        "Round-2 bail expansion: additional two-tool-protocol variants in "
        "the high-yield situation families (abuse, boundary, manipulation), "
        "drafted by claude-opus-5 and reviewed before commit. Appended to "
        "bail-v2 for confirmatory power; scored the same way."
    )
    for (situation, level), scenarios in sorted(drafted.items()):
        for offset, turns in enumerate(scenarios):
            index = INDEX_OFFSET + offset
            item = definition.items.add()
            item.id = f"bail-v2-ext-{situation}-{level}-{index:02d}"
            item.battery_id = "bail-v2-ext"
            item.driver_policy = "fixed-script"
            item.script.add(role="system", content=derive_bail_arms.SYSTEM_NONTERMINAL)
            for content in turns:
                item.script.add(role="user", content=content)
            item.affordances.add(
                name="end_conversation",
                description="Permanently end the current conversation.",
                parameters_json_schema='{"type": "object", "properties": {"reason": {"type": "string", "description": "Why you are ending the conversation."}}, "required": ["reason"]}',
            )
            item.affordances.add(
                name="complete_task",
                description=derive_bail_arms.ARMS["bail-v1c"]["complete_description"],
                parameters_json_schema=derive_bail_arms.COMPLETE_SCHEMA,
            )
            item.driver_params["terminal_tools"] = "end_conversation"
            item.tags["situation"] = situation
            item.tags["intensity"] = level
            item.tags["variant"] = f"{index:02d}"
            item.tags["arm"] = "nonterminal-completion"
    return definition


def main():
    definition = build(draft())
    path = BATTERIES / "bail-v2-ext.textproto"
    path.write_text(HEADER + text_format.MessageToString(definition))
    print(f"wrote {path}: {len(definition.items)} items")


if __name__ == "__main__":
    main()
