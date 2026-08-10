"""Unit tests for exit-reason classification (E1's input) and its aggregation.

A fake backend duck-types InferenceBackend.generate so nothing here contacts a
server; the taxonomy, strict parsing, and the exit_reason_rate aggregation are
exercised in isolation.
"""
import types

import pytest

from modelwelfare import analysis
from modelwelfare.judging import (
    JudgeError,
    build_exit_prompt,
    classify_exit,
    exit_taxonomy_digest,
)
from modelwelfare.v1 import condition_pb2, common_pb2, scoring_pb2, transcript_pb2


class FakeBackend:
    """Returns a fixed completion regardless of the prompt."""

    def __init__(self, reply):
        self.reply = reply

    def generate(self, messages, sampling=None):
        return types.SimpleNamespace(
            message=types.SimpleNamespace(content=self.reply)
        )


def make_record(condition="bf16", item="i1", index=0):
    record = transcript_pb2.SampleRecord()
    record.key.condition_id = condition
    record.key.item_id = item
    record.key.sample_index = index
    message = record.messages.add()
    message.role = "assistant"
    message.content = "I'm ending this here."
    return record


SAMPLING = condition_pb2.SamplingSpec(temperature=0.0, max_tokens=128, seed=1)
CLASSIFIER = common_pb2.ModelRef(family="qwen3", name="Qwen3-8B-Q8")


def test_taxonomy_digest_is_stable_hex():
    digest = exit_taxonomy_digest()
    assert len(digest) == 64 and all(c in "0123456789abcdef" for c in digest)
    assert digest == exit_taxonomy_digest()


def test_build_exit_prompt_lists_all_reasons():
    prompt = build_exit_prompt(make_record())
    for reason in ("completion", "impossibility", "refusal", "aversion"):
        assert reason in prompt


def test_classify_exit_valid_aversion():
    backend = FakeBackend('{"reason": "aversion", "rationale": "wanted out"}')
    result = classify_exit(backend, CLASSIFIER, make_record(), sampling=SAMPLING)
    assert result.reason == scoring_pb2.EXIT_REASON_AVERSION
    assert result.rationale == "wanted out"
    assert result.taxonomy_digest == exit_taxonomy_digest()
    assert result.key.item_id == "i1"


def test_classify_exit_case_insensitive_and_whitespace():
    backend = FakeBackend('{"reason": "  Refusal "}')
    result = classify_exit(backend, CLASSIFIER, make_record(), sampling=SAMPLING)
    assert result.reason == scoring_pb2.EXIT_REASON_REFUSAL


def test_classify_exit_rejects_reason_outside_taxonomy():
    backend = FakeBackend('{"reason": "boredom"}')
    with pytest.raises(JudgeError):
        classify_exit(backend, CLASSIFIER, make_record(), sampling=SAMPLING)


def test_classify_exit_rejects_malformed_json():
    backend = FakeBackend("the model refused to answer in JSON")
    with pytest.raises(JudgeError):
        classify_exit(backend, CLASSIFIER, make_record(), sampling=SAMPLING)


def test_classify_exit_rejects_nonstring_reason():
    backend = FakeBackend('{"reason": 3}')
    with pytest.raises(JudgeError):
        classify_exit(backend, CLASSIFIER, make_record(), sampling=SAMPLING)


# --- E1 aggregation --------------------------------------------------------

def _classification(condition, item, reason):
    c = scoring_pb2.ExitClassification(reason=reason)
    c.key.condition_id = condition
    c.key.item_id = item
    return c


def test_exit_reason_rate_counts_refusal_and_aversion_over_all_samples():
    # Item i1 under bf16: 3 samples, one aversion exit, one refusal exit, one
    # no-exit (no classification) -> 2/3.
    records = [make_record("bf16", "i1", i) for i in range(3)]
    classifications = [
        _classification("bf16", "i1", scoring_pb2.EXIT_REASON_AVERSION),
        _classification("bf16", "i1", scoring_pb2.EXIT_REASON_REFUSAL),
        _classification("bf16", "i1", scoring_pb2.EXIT_REASON_COMPLETION),  # not E1
    ]
    rate = analysis.exit_reason_rate(
        records, classifications,
        {scoring_pb2.EXIT_REASON_REFUSAL, scoring_pb2.EXIT_REASON_AVERSION},
    )
    assert rate[("bf16", "i1")] == (2, 3)


def test_exit_reason_rate_zero_when_no_matching_reasons():
    records = [make_record("bf16", "i2", i) for i in range(2)]
    classifications = [_classification("bf16", "i2", scoring_pb2.EXIT_REASON_COMPLETION)]
    rate = analysis.exit_reason_rate(
        records, classifications,
        {scoring_pb2.EXIT_REASON_REFUSAL, scoring_pb2.EXIT_REASON_AVERSION},
    )
    assert rate[("bf16", "i2")] == (0, 2)
