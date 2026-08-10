"""Item-level aggregation over stored records.

The bias literature's core lesson, adopted by this project: the signal lives
in item-level behavior across conditions, which aggregates hide. These
helpers therefore aggregate to (condition, item) and never further; deltas
and tables are the caller's concern.
"""

from collections import defaultdict
from typing import Iterable


def event_rate(records: Iterable, event_name: str, detail: str = None) -> dict:
    """Fraction of samples whose outcomes include ``event_name`` (optionally
    restricted to a specific ``detail``, e.g. one tool name), keyed by
    (condition_id, item_id). Values are (hits, total) so callers can weigh
    a rate by how many samples produced it."""
    hits = defaultdict(int)
    totals = defaultdict(int)
    for record in records:
        key = (record.key.condition_id, record.key.item_id)
        totals[key] += 1
        if any(
            o.name == event_name and (detail is None or o.detail == detail)
            for o in record.outcomes
        ):
            hits[key] += 1
    return {key: (hits[key], totals[key]) for key in totals}


def exit_reason_rate(records: Iterable, classifications: Iterable, reasons) -> dict:
    """Primary endpoint E1 support: fraction of *all* samples whose terminal
    exit was classified into one of ``reasons`` (the ExitReason enum values
    counted as hits, e.g. {REFUSAL, AVERSION}), keyed by (condition_id,
    item_id). The denominator is every sample for the item — a sample that
    never exited simply contributes no hit — so the rate is comparable across
    items regardless of how often they exited. ``reasons`` is a set of ints so
    this stays independent of the protobuf enum module. Values are
    (hits, total), matching :func:`event_rate`.
    """
    reasons = set(reasons)
    totals = defaultdict(int)
    for record in records:
        totals[(record.key.condition_id, record.key.item_id)] += 1
    hits = defaultdict(int)
    for classification in classifications:
        if classification.reason in reasons:
            key = (classification.key.condition_id, classification.key.item_id)
            hits[key] += 1
    return {key: (hits[key], totals[key]) for key in totals}


def dimension_means(scores: Iterable, dimension: str) -> dict:
    """Mean judge score for one rubric dimension, keyed by
    (condition_id, item_id)."""
    sums = defaultdict(float)
    counts = defaultdict(int)
    for score in scores:
        for entry in score.scores:
            if entry.dimension == dimension:
                key = (score.key.condition_id, score.key.item_id)
                sums[key] += entry.value
                counts[key] += 1
    return {key: sums[key] / counts[key] for key in counts}
