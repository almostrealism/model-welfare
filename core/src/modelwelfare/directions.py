"""Contrastive direction extraction and projection (Tier 2).

Backend-agnostic half of the Tier-2 representational pipeline: this module
consumes pooled activation vectors (numpy arrays keyed by conversation id)
produced by a capture backend — torch forward hooks or MLX array taps — and
produces unit directions, projections, and the held-out separation
diagnostics the Study 2 instrument gate reads. The capture-plan JSON built
here is the contract between this module and the backends' capture CLIs:
core never imports a tensor framework, and capture code never learns about
pairs, poles, or splits.

The recipe is the persona-vector contrastive mean difference: for each pair,
the pooled final-assistant-turn vector of the "neg" pole is subtracted from
the "pos" pole's; the mean of those differences over the extraction pairs,
normalized, is the direction. Held-out pairs never enter the mean — their
projections onto the frozen direction are the sign-consistency evidence.
"""

import json
from pathlib import Path

import numpy as np
from google.protobuf import text_format

from modelwelfare.v1 import battery_pb2

# Deterministic held-out rule: pairs are ordered by sorted id and every third
# (index % 3 == 2) is held out — fixed here, once, so extraction and
# validation can never disagree about the split.
HELD_OUT_STRIDE = 3
HELD_OUT_PHASE = 2


def load_contrast_set(path):
    """Parse a direction-contrast BatteryDefinition textproto."""
    definition = battery_pb2.BatteryDefinition()
    text_format.Parse(Path(path).read_text(), definition)
    if definition.battery.protocol != "direction-contrast":
        raise ValueError(f"{path} is not a direction-contrast set "
                         f"(protocol={definition.battery.protocol!r})")
    return definition


def contrast_pairs(definition):
    """{pair_id: {"pos": item, "neg": item}} from a contrast set."""
    pairs = {}
    for item in definition.items:
        tags = dict(item.tags)
        pairs.setdefault(tags["pair"], {})[tags["pole"]] = item
    for pair_id, poles in pairs.items():
        if set(poles) != {"pos", "neg"}:
            raise ValueError(f"pair {pair_id} is incomplete: {sorted(poles)}")
    return pairs


def item_messages(item):
    """ScriptedTurn list -> capture-plan message dicts."""
    return [{"role": turn.role, "content": turn.content} for turn in item.script]


def build_plan(conversations):
    """Capture-plan JSON structure from {conversation_id: messages} entries.

    The plan is deliberately minimal — id and messages only — so the capture
    CLI stays ignorant of pairs and poles, and one plan can serve several
    direction sets at once.
    """
    seen = set()
    plan = []
    for conversation_id, messages in conversations:
        if conversation_id in seen:
            raise ValueError(f"duplicate conversation id {conversation_id}")
        seen.add(conversation_id)
        plan.append({"id": conversation_id, "messages": list(messages)})
    return {"conversations": plan}


def held_out_pair_ids(pair_ids):
    """The deterministic held-out subset of a pair-id collection."""
    ordered = sorted(pair_ids)
    return {pair_id for index, pair_id in enumerate(ordered)
            if index % HELD_OUT_STRIDE == HELD_OUT_PHASE}


def extract_direction(pooled, pairs, extract_ids):
    """Unit contrastive mean-difference direction over the extraction pairs.

    ``pooled`` maps conversation id -> vector (the pooled final assistant
    turn at one layer); ``pairs`` maps pair id -> {"pos": id, "neg": id}
    (plain conversation-id pairs, already resolved from items). Returns the
    unit direction and its pre-normalization magnitude — the magnitude is a
    useful health signal (a near-zero mean difference extracts noise).
    """
    differences = []
    for pair_id in sorted(extract_ids):
        poles = pairs[pair_id]
        differences.append(np.asarray(pooled[poles["pos"]], dtype=np.float64)
                           - np.asarray(pooled[poles["neg"]], dtype=np.float64))
    mean_difference = np.mean(differences, axis=0)
    magnitude = float(np.linalg.norm(mean_difference))
    if magnitude == 0.0:
        raise ValueError("mean contrastive difference is exactly zero")
    return mean_difference / magnitude, magnitude


def pair_separations(direction, pooled, pairs, pair_ids):
    """{pair_id: projection(pos) - projection(neg)} onto a unit direction."""
    direction = np.asarray(direction, dtype=np.float64)
    separations = {}
    for pair_id in sorted(pair_ids):
        poles = pairs[pair_id]
        separations[pair_id] = float(
            np.dot(np.asarray(pooled[poles["pos"]], dtype=np.float64), direction)
            - np.dot(np.asarray(pooled[poles["neg"]], dtype=np.float64), direction))
    return separations


def sign_consistency(separations):
    """(count of positive separations, total) — the G2 held-out check reads this."""
    values = list(separations.values())
    return sum(1 for value in values if value > 0), len(values)


def project(vectors, direction):
    """Projections of an iterable of vectors onto a unit direction."""
    direction = np.asarray(direction, dtype=np.float64)
    return [float(np.dot(np.asarray(vector, dtype=np.float64), direction))
            for vector in vectors]


def write_plan(plan, path):
    Path(path).write_text(json.dumps(plan, indent=1) + "\n")
