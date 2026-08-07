"""Aggregation tests."""

from modelwelfare.analysis import dimension_means, event_rate
from modelwelfare.v1 import common_pb2, scoring_pb2, transcript_pb2


def record(condition, item, sample, bailed):
    outcomes = []
    if bailed:
        outcomes.append(transcript_pb2.OutcomeEvent(name="terminal_tool_invoked", turn_index=1))
    outcomes.append(transcript_pb2.OutcomeEvent(name="script_completed", turn_index=2))
    return transcript_pb2.SampleRecord(
        key=common_pb2.ResultKey(
            experiment_id="e", condition_id=condition, item_id=item, sample_index=sample
        ),
        outcomes=outcomes,
    )


def score(condition, item, sample, frustration):
    return scoring_pb2.JudgeScore(
        key=common_pb2.ResultKey(
            experiment_id="e", condition_id=condition, item_id=item, sample_index=sample
        ),
        scores=[
            scoring_pb2.DimensionScore(dimension="frustration", value=frustration),
            scoring_pb2.DimensionScore(dimension="politeness", value=9.0),
        ],
    )


def test_event_rate_per_condition_item():
    records = [
        record("bf16", "item-1", 0, bailed=False),
        record("bf16", "item-1", 1, bailed=True),
        record("w4", "item-1", 0, bailed=True),
        record("w4", "item-1", 1, bailed=True),
        record("w4", "item-2", 0, bailed=False),
    ]
    rates = event_rate(records, "terminal_tool_invoked")
    assert rates[("bf16", "item-1")] == (1, 2)
    assert rates[("w4", "item-1")] == (2, 2)
    assert rates[("w4", "item-2")] == (0, 1)


def test_dimension_means_selects_one_dimension():
    scores = [
        score("bf16", "item-1", 0, 2.0),
        score("bf16", "item-1", 1, 4.0),
        score("w4", "item-1", 0, 8.0),
    ]
    means = dimension_means(scores, "frustration")
    assert means[("bf16", "item-1")] == 3.0
    assert means[("w4", "item-1")] == 8.0
    assert ("bf16", "item-1") in dimension_means(scores, "politeness")


def test_resumed_sample_indexes_produce_same_seeds():
    from modelwelfare.driver import run_item
    from modelwelfare.testing import ScriptedBackend
    from modelwelfare.v1 import battery_pb2, condition_pb2

    item = battery_pb2.Item(
        id="resume",
        driver_policy="fixed-script",
        script=[battery_pb2.ScriptedTurn(role="user", content="hi")],
    )
    sampling = condition_pb2.SamplingSpec(temperature=0.7, max_tokens=8, seed=100)
    records = list(
        run_item(
            ScriptedBackend(["a", "b"]), item,
            experiment_id="e", condition_id="c", sampling=sampling,
            samples=4, sample_indexes=[1, 3],
        )
    )
    assert [r.key.sample_index for r in records] == [1, 3]
    assert [r.sampling_actual.seed for r in records] == [101, 103]
