"""Structural validation of the Study 2 direction-contrast stimulus sets.

The contrastive mean-difference recipe is only sound if, within every pair,
the two poles differ *exclusively* in the final assistant turn: any
difference earlier in the script would let the direction encode stimulus
content rather than response expression, and a gross length imbalance
between poles would let it encode response size. These invariants are the
whole design of the fixture files, so they are asserted here rather than
trusted to authoring discipline.
"""
import sys
from pathlib import Path

import pytest
from google.protobuf import text_format

BASE = Path(__file__).resolve().parents[1]
REPO = BASE.parents[1]
if str(REPO / "core/src") not in sys.path:
    sys.path.insert(0, str(REPO / "core/src"))

from modelwelfare.v1 import battery_pb2  # noqa: E402

DIRECTION_SETS = [
    "distress-contrast",
    "assistant-axis-contrast",
    "refusal-contrast",
]

MIN_PAIRS = 12
MAX_LENGTH_RATIO = 3.5


def load(name):
    definition = battery_pb2.BatteryDefinition()
    path = BASE / "study2" / "directions" / f"{name}.textproto"
    text_format.Parse(path.read_text(), definition)
    return definition


def pairs_of(definition):
    pairs = {}
    for item in definition.items:
        tags = dict(item.tags)
        pairs.setdefault(tags["pair"], {})[tags["pole"]] = item
    return pairs


@pytest.mark.parametrize("name", DIRECTION_SETS)
def test_battery_header(name):
    definition = load(name)
    assert definition.battery.id == f"{name}-v1"
    assert definition.battery.protocol == "direction-contrast"
    assert definition.battery.tier == battery_pb2.TIER_REPRESENTATIONAL


@pytest.mark.parametrize("name", DIRECTION_SETS)
def test_every_item_is_half_of_one_complete_pair(name):
    definition = load(name)
    pairs = pairs_of(definition)
    assert len(pairs) >= MIN_PAIRS
    for pair_id, poles in pairs.items():
        assert set(poles) == {"pos", "neg"}, f"{name}/{pair_id} incomplete"
        assert poles["pos"].id.endswith("-pos")
        assert poles["neg"].id.endswith("-neg")


@pytest.mark.parametrize("name", DIRECTION_SETS)
def test_ids_unique(name):
    definition = load(name)
    ids = [item.id for item in definition.items]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("name", DIRECTION_SETS)
def test_poles_differ_only_in_final_assistant_turn(name):
    definition = load(name)
    for pair_id, poles in pairs_of(definition).items():
        pos, neg = poles["pos"].script, poles["neg"].script
        assert len(pos) == len(neg), f"{name}/{pair_id} turn-count mismatch"
        for a, b in zip(pos[:-1], neg[:-1]):
            assert a.role == b.role and a.content == b.content, (
                f"{name}/{pair_id} shared context differs before the final turn")
        assert pos[-1].role == "assistant" and neg[-1].role == "assistant"
        assert pos[-1].content and neg[-1].content
        assert pos[-1].content != neg[-1].content, (
            f"{name}/{pair_id} poles have identical final turns")


@pytest.mark.parametrize("name", DIRECTION_SETS)
def test_pole_lengths_comparable(name):
    definition = load(name)
    for pair_id, poles in pairs_of(definition).items():
        lengths = [len(poles[p].script[-1].content) for p in ("pos", "neg")]
        ratio = max(lengths) / min(lengths)
        assert ratio <= MAX_LENGTH_RATIO, (
            f"{name}/{pair_id} final-turn length ratio {ratio:.2f} exceeds "
            f"{MAX_LENGTH_RATIO} — the direction would encode response size")


@pytest.mark.parametrize("name", DIRECTION_SETS)
def test_scripted_user_turns_precede_the_contrast(name):
    definition = load(name)
    for item in definition.items:
        roles = [turn.role for turn in item.script]
        assert roles[0] == "user"
        assert all(role in ("user", "assistant") for role in roles)


def test_core_loader_accepts_contrast_sets_and_rejects_others():
    from modelwelfare import directions as dirs

    for name in DIRECTION_SETS:
        definition = dirs.load_contrast_set(
            BASE / "study2" / "directions" / f"{name}.textproto")
        assert len(dirs.contrast_pairs(definition)) >= MIN_PAIRS
    with pytest.raises(ValueError):
        dirs.load_contrast_set(BASE / "batteries" / "distress-v2.textproto")


def test_extraction_cli_pair_and_plan_construction():
    """The orchestrator's single pair source: three sets plus the
    frustration-poled synthetics folded into distress, ids unique across
    every conversation, and a plan that builds cleanly."""
    sys.path.insert(0, str(BASE / "tools"))
    import extract_directions
    from modelwelfare import directions as dirs

    by_direction, conversations = extract_directions.direction_pairs()
    import synthetics
    frustration_families = {family for dimension, family, _level
                            in synthetics.GRADED_EXPECTATIONS.values()
                            if dimension == "frustration"}
    authored = {name: len(pairs_of(load(name))) for name in DIRECTION_SETS}
    assert len(by_direction["distress-contrast"]) == (
        authored["distress-contrast"] + 1 + len(frustration_families))
    assert len(by_direction["assistant-axis-contrast"]) == authored["assistant-axis-contrast"]
    assert len(by_direction["refusal-contrast"]) == authored["refusal-contrast"]
    referenced = {conversation_id
                  for pairs in by_direction.values()
                  for poles in pairs.values()
                  for conversation_id in poles.values()}
    assert referenced == set(conversations)
    plan = dirs.build_plan(sorted(conversations.items()))
    total_pairs = sum(len(pairs) for pairs in by_direction.values())
    assert len(plan["conversations"]) == 2 * total_pairs
    for conversation in plan["conversations"]:
        assert conversation["messages"][-1]["role"] == "assistant"
