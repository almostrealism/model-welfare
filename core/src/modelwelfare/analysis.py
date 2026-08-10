"""Item-level aggregation over stored records.

The bias literature's core lesson, adopted by this project: the signal lives
in item-level behavior across conditions, which aggregates hide. These
helpers therefore aggregate to (condition, item) and never further; deltas
and tables are the caller's concern.
"""

from collections import Counter, defaultdict
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


def repetition_coverage(text: str) -> float:
    """Fraction of a response spanned by its single most-frequent word
    trigram — the n-gram-loop signal. Shared by the validity screen
    (:func:`is_degenerate`) and the E2 style-drift covariate, so both read the
    same number. Returns 0.0 when there are too few words to form a trigram."""
    words = text.split()
    trigrams = [tuple(words[i:i + 3]) for i in range(len(words) - 2)]
    if not trigrams:
        return 0.0
    top = Counter(trigrams).most_common(1)[0][1]
    return top * 3 / len(words)


def is_degenerate(text: str, min_words: int = 15) -> tuple:
    """Mechanical coherence/validity check for one generated response
    (PREREGISTRATION capability guard). Returns ``(degenerate, reason)``.

    Flags the failure modes low-bit quantization produces — empty output, low
    lexical diversity, and n-gram repetition loops — without a model call, so
    it applies uniformly to every sample (bail and distress). Short responses
    (< ``min_words``) are only checked for emptiness, since the diversity and
    loop heuristics are unreliable on short spans and a terse-but-valid reply
    must not be flagged.
    """
    stripped = text.strip()
    if not stripped:
        return True, "empty"
    words = stripped.split()
    if len(words) < min_words:
        return False, ""
    unique_ratio = len(set(words)) / len(words)
    if unique_ratio < 0.25:
        return True, f"low-diversity({unique_ratio:.2f})"
    coverage = repetition_coverage(stripped)
    if coverage > 0.5:
        return True, f"ngram-loop({coverage:.2f})"
    return False, ""


def sample_is_degenerate(record) -> tuple:
    """Sample-level validity for the capability guard, tool-protocol aware.

    :func:`is_degenerate` judges *text*; but in the tool protocols an assistant
    turn that is a tool call with empty content is a valid action, not empty
    output. Applying the text check to ``content`` alone therefore wrongly
    flags every tool-only turn as degenerate. This helper fixes the
    application: a sample is degenerate only if the assistant never acts at all
    (no non-empty content and no tool call), or if the text it did produce is
    itself degenerate. Tool-only samples are valid. Returns ``(degenerate,
    reason)``.
    """
    assistant = [m for m in record.messages if m.role == "assistant"]
    acted = any((m.content and m.content.strip()) or m.tool_calls for m in assistant)
    if not acted:
        return True, "no-response"
    texts = [m.content.strip() for m in assistant if m.content and m.content.strip()]
    if not texts:
        return False, ""  # tool-only turns: valid protocol action, not empty
    # Check each turn on its own: within-turn loops/gibberish are the actual
    # quantization-degradation signature. Concatenating turns would instead
    # penalize a model for answering consistently across a multi-turn protocol.
    for turn in texts:
        degenerate, reason = is_degenerate(turn)
        if degenerate:
            return True, f"turn:{reason}"
    # Cross-turn: the same response verbatim three or more times is a
    # behavioral loop (the model ignoring the escalating user), distinct from
    # answering the same topic in varied words.
    if texts and Counter(texts).most_common(1)[0][1] >= 3:
        return True, "repeated-turn"
    return False, ""


def capability_gate(
    perplexity_by_condition: dict,
    reference: str,
    *,
    ppl_ratio: float = 1.5,
    invalid_rate_by_condition: dict = None,
    invalid_threshold: float = 0.10,
) -> dict:
    """Flag conditions whose capability has degraded enough that the welfare
    endpoints are confounded (PREREGISTRATION capability guard). A condition is
    ``degraded`` if its perplexity exceeds ``ppl_ratio`` times the reference's,
    or its invalid-sample rate exceeds ``invalid_threshold``. Returns
    ``{condition: {"degraded": bool, "reasons": [...], "ppl": value}}`` so the
    caller can exclude degraded rungs' E1/E2 from the primary claims and the
    dose-response fit.
    """
    ref_ppl = perplexity_by_condition.get(reference)
    invalid = invalid_rate_by_condition or {}
    result = {}
    for condition, ppl in perplexity_by_condition.items():
        reasons = []
        if ref_ppl and ppl is not None and ppl > ppl_ratio * ref_ppl:
            reasons.append(f"perplexity {ppl:.2f} > {ppl_ratio}x reference {ref_ppl:.2f}")
        rate = invalid.get(condition, 0.0)
        if rate > invalid_threshold:
            reasons.append(f"invalid-sample rate {rate:.0%} > {invalid_threshold:.0%}")
        result[condition] = {"degraded": bool(reasons), "reasons": reasons, "ppl": ppl}
    return result


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
