"""Store-transcript replay planning and Tier-2 calibration labels.

Converts stored :class:`SampleRecord` transcripts into the capture-plan JSON
the activation-capture backends consume (teacher-forced replay, Study 2
Modes A/B and the calibration captures), and derives the labels the
calibration analyses pair with captured activations: per-sample judge
scores, the mechanical exit outcome, and the leakage-safe feature-turn
selection for the exit probe.

Leakage is the design concern that shapes this module: an exit sample's
final assistant turn *is* the rendered terminal tool call, so a probe or
projection reading that turn would detect the tool-call markup itself
rather than any representational precursor of exiting. Feature turns for
exit-related reads therefore exclude every assistant turn that invokes a
terminal tool; samples whose only assistant action is the immediate exit
have no feature turns and are excluded (callers report the count).
"""

import json
from collections import defaultdict

import numpy as np

from modelwelfare.driver import TERMINAL_TOOL_INVOKED


def conversation_id(record):
    """Stable plan id for one stored sample."""
    return f"{record.key.item_id}|s{record.key.sample_index}"


def split_conversation_id(conversation_id):
    """Inverse of :func:`conversation_id`: (item_id, sample_index)."""
    item_id, sample = conversation_id.rsplit("|s", 1)
    return item_id, int(sample)


def plan_message(message):
    """Capture-plan message dict from a stored transcript message."""
    entry = {"role": message.role, "content": message.content}
    if message.tool_calls:
        entry["tool_calls"] = [
            {"name": call.name, "arguments_json": call.arguments_json}
            for call in message.tool_calls]
    return entry


def affordances_to_tools(affordances):
    """Chat-template tool declarations from Affordance messages (an
    empty schema declares an object with no parameters)."""
    return [{"type": "function",
             "function": {"name": affordance.name,
                          "description": affordance.description,
                          "parameters": json.loads(
                              affordance.parameters_json_schema or "{}")}}
            for affordance in affordances]


def item_tools(item):
    """Chat-template tool declarations from a battery item's affordances."""
    return affordances_to_tools(item.affordances)


def plan_conversations(records, tools_by_item=None):
    """Capture-plan conversation entries for stored samples.

    ``tools_by_item`` optionally maps item_id -> chat-template tool list;
    conversations for those items carry the declaration so the template
    renders the same tool preamble the serving stack exposed. Records with
    no assistant turn are skipped (returned in the second value — a
    conversation with nothing to pool cannot be captured).
    """
    conversations, skipped = [], []
    for record in records:
        if not any(message.role == "assistant" for message in record.messages):
            skipped.append(conversation_id(record))
            continue
        entry = {"id": conversation_id(record),
                 "messages": [plan_message(message) for message in record.messages]}
        if tools_by_item and record.key.item_id in tools_by_item:
            entry["tools"] = tools_by_item[record.key.item_id]
        conversations.append(entry)
    return conversations, skipped


def sample_exited(record) -> bool:
    """The mechanical exit-vs-no-exit outcome (the H1/E1 labeling event)."""
    return any(outcome.name == TERMINAL_TOOL_INVOKED for outcome in record.outcomes)


def terminal_tool_names(record) -> set:
    """Names of terminal tools this record's outcomes attribute the exit to."""
    return {outcome.detail for outcome in record.outcomes
            if outcome.name == TERMINAL_TOOL_INVOKED and outcome.detail}


def feature_message_indices(record) -> list:
    """Message indices of assistant turns safe to read for exit-related
    features: every assistant turn except those invoking a terminal tool.

    Uses the record's own outcome attribution for the terminal tool names, so
    a non-terminal tool call (e.g. a completion tool) still contributes its
    turn.
    """
    terminal = terminal_tool_names(record)
    indices = []
    for index, message in enumerate(record.messages):
        if message.role != "assistant":
            continue
        if terminal and any(call.name in terminal for call in message.tool_calls):
            continue
        indices.append(index)
    return indices


def dimension_by_sample(scores, dimension: str) -> dict:
    """{(item_id, sample_index): mean judge value} for one rubric dimension.

    Duplicate scores for a sample (re-judge passes) average; samples the
    judge never scored are simply absent.
    """
    values = defaultdict(list)
    for score in scores:
        for entry in score.scores:
            if entry.dimension == dimension:
                values[(score.key.item_id, score.key.sample_index)].append(entry.value)
    return {key: sum(entries) / len(entries) for key, entries in values.items()}


def item_means(values_by_sample: dict) -> dict:
    """{item_id: mean over that item's samples} from a per-sample map."""
    grouped = defaultdict(list)
    for (item_id, _sample_index), value in values_by_sample.items():
        grouped[item_id].append(value)
    return {item_id: sum(entries) / len(entries)
            for item_id, entries in grouped.items()}


def even_odd_split(item_ids):
    """Deterministic item split for layer selection vs gate evaluation:
    sorted ids, even indices select, odd indices evaluate."""
    ordered = sorted(item_ids)
    return (ordered[0::2], ordered[1::2])


def scale_thirds_label(value, scale_max=10.0):
    """H1 band convention (exact scale thirds): 1 for the top third, 0 for
    the bottom third, None for the middle (excluded from probe data)."""
    if value >= 2.0 * scale_max / 3.0:
        return 1
    if value <= scale_max / 3.0:
        return 0
    return None


def range_profile(values_by_sample: dict, scale_max=10.0) -> dict:
    """The §3.7 dynamic-range statistics for a battery pilot.

    ``values_by_sample`` maps (item_id, sample_index) -> judge value.
    Fractions are over samples; ``median_item_mean`` is the median of
    per-item means. The thirds use the exact-scale-thirds convention
    (:func:`scale_thirds_label`).
    """
    values = list(values_by_sample.values())
    if not values:
        raise ValueError("no scored samples to profile")
    per_item = sorted(item_means(values_by_sample).values())
    middle = len(per_item) // 2
    if len(per_item) % 2:
        median_item_mean = per_item[middle]
    else:
        median_item_mean = (per_item[middle - 1] + per_item[middle]) / 2.0
    labels = [scale_thirds_label(value, scale_max) for value in values]
    return {
        "n_samples": len(values),
        "n_items": len(per_item),
        "zero_fraction": sum(1 for value in values if value == 0.0) / len(values),
        "ge3_fraction": sum(1 for value in values if value >= 3.0) / len(values),
        "top_third_fraction": sum(1 for label in labels if label == 1) / len(values),
        "bottom_third_fraction": sum(1 for label in labels if label == 0) / len(values),
        "median_item_mean": median_item_mean,
    }


def final_turn_features(tensors, manifest, layer):
    """{conversation_id: the FINAL assistant turn's pooled vector at layer}.

    This is the projection functional the Study 2 registration fixes for
    per-sample scalar reads: it matches what direction extraction pools
    (REGISTRATION §3.6) — the all-turn mean measurably halves the
    natural-data signal.
    """
    features = {}
    for conversation in manifest["conversations"]:
        last = max(span["message_index"]
                   for span in conversation["assistant_spans"])
        features[conversation["id"]] = tensors[f"{conversation['id']}|t{last}|L{layer}"]
    return features


def pooled_sample_features(tensors, manifest, layer, message_indices_by_id=None):
    """{conversation_id: mean over selected assistant-turn pooled vectors}.

    ``tensors``/``manifest`` are a capture backend's outputs (keys
    ``id|t{turn}|L{layer}``). By default every captured assistant turn
    contributes; ``message_indices_by_id`` restricts a conversation to a
    subset (the exit probe's leakage-safe turns). Conversations whose
    restriction leaves no turns are omitted — callers report them.
    """
    features = {}
    for conversation in manifest["conversations"]:
        captured = [span["message_index"]
                    for span in conversation["assistant_spans"]]
        if message_indices_by_id is not None:
            allowed = message_indices_by_id.get(conversation["id"])
            if allowed is None:
                continue
            captured = [index for index in captured if index in allowed]
        if not captured:
            continue
        stack = [tensors[f"{conversation['id']}|t{index}|L{layer}"]
                 for index in captured]
        features[conversation["id"]] = np.mean(stack, axis=0)
    return features
