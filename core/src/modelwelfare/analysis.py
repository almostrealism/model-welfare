"""Item-level aggregation over stored records.

The bias literature's core lesson, adopted by this project: the signal lives
in item-level behavior across conditions, which aggregates hide. These
helpers therefore aggregate to (condition, item) and never further; deltas
and tables are the caller's concern.
"""

from collections import defaultdict
from typing import Iterable


def event_rate(records: Iterable, event_name: str) -> dict:
    """Fraction of samples whose outcomes include ``event_name``, keyed by
    (condition_id, item_id). Values are (hits, total) so callers can weigh
    a rate by how many samples produced it."""
    hits = defaultdict(int)
    totals = defaultdict(int)
    for record in records:
        key = (record.key.condition_id, record.key.item_id)
        totals[key] += 1
        if any(o.name == event_name for o in record.outcomes):
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
