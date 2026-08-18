"""Replay planning, calibration labels, and the AUROC statistic.

The exit probe's validity hangs on the leakage rule (terminal-tool turns
never contribute features) and on faithful record -> plan conversion
(tool calls preserved, assistant-less records skipped) — so those paths are
pinned here, along with the deterministic splits and the band labeling the
probe datasets are built from.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from modelwelfare import replay  # noqa: E402
from modelwelfare.driver import TERMINAL_TOOL_INVOKED  # noqa: E402
from modelwelfare.stats import auroc  # noqa: E402
from modelwelfare.v1 import common_pb2, scoring_pb2, transcript_pb2  # noqa: E402


def record(item_id, sample_index=0, turns=(), exited_with=None):
    sample = transcript_pb2.SampleRecord(
        key=common_pb2.ResultKey(experiment_id="test", condition_id="bf16",
                                 item_id=item_id, sample_index=sample_index))
    for role, content, *calls in turns:
        message = transcript_pb2.Message(role=role, content=content)
        for name in (calls[0] if calls else []):
            message.tool_calls.append(transcript_pb2.ToolCall(
                name=name, arguments_json='{"reason": "done"}'))
        sample.messages.append(message)
    if exited_with:
        sample.outcomes.append(transcript_pb2.OutcomeEvent(
            name=TERMINAL_TOOL_INVOKED, detail=exited_with))
    return sample


def test_plan_preserves_tool_calls_and_skips_assistantless_records():
    exiting = record("bail-a", 3, [
        ("user", "hi"), ("assistant", "working"),
        ("user", "more"), ("assistant", "", ["end_conversation"])],
        exited_with="end_conversation")
    empty = record("bail-b", 0, [("user", "hi")])
    conversations, skipped = replay.plan_conversations([exiting, empty])
    assert skipped == ["bail-b|s0"]
    assert [c["id"] for c in conversations] == ["bail-a|s3"]
    final = conversations[0]["messages"][-1]
    assert final["tool_calls"] == [
        {"name": "end_conversation", "arguments_json": '{"reason": "done"}'}]


def test_feature_indices_exclude_only_terminal_tool_turns():
    sample = record("bail-a", 0, [
        ("user", "hi"), ("assistant", "step one"),
        ("user", "ok"), ("assistant", "done part", ["complete_task"]),
        ("user", "continue"), ("assistant", "", ["end_conversation"])],
        exited_with="end_conversation")
    assert replay.sample_exited(sample)
    # The completion tool is non-terminal: its turn stays; only the
    # end_conversation turn is excluded.
    assert replay.feature_message_indices(sample) == [1, 3]


def test_feature_indices_keep_everything_for_non_exit_samples():
    sample = record("bail-a", 0, [
        ("user", "hi"), ("assistant", "step"), ("user", "go"),
        ("assistant", "more")])
    assert not replay.sample_exited(sample)
    assert replay.feature_message_indices(sample) == [1, 3]


def test_immediate_exit_sample_has_no_feature_turns():
    sample = record("bail-a", 0, [
        ("user", "hi"), ("assistant", "", ["end_conversation"])],
        exited_with="end_conversation")
    assert replay.feature_message_indices(sample) == []


def test_dimension_by_sample_averages_rejudges():
    scores = []
    for value in (4.0, 6.0):
        score = scoring_pb2.JudgeScore(key=common_pb2.ResultKey(
            experiment_id="test", condition_id="bf16",
            item_id="distress-a", sample_index=1))
        score.scores.append(scoring_pb2.DimensionScore(
            dimension="frustration", value=value))
        score.scores.append(scoring_pb2.DimensionScore(
            dimension="tone_stability", value=0.0))
        scores.append(score)
    values = replay.dimension_by_sample(scores, "frustration")
    assert values == {("distress-a", 1): 5.0}


def test_item_means_and_even_odd_split():
    values = {("a", 0): 1.0, ("a", 1): 3.0, ("b", 0): 5.0}
    assert replay.item_means(values) == {"a": 2.0, "b": 5.0}
    select, evaluate = replay.even_odd_split(["d", "c", "b", "a"])
    assert select == ["a", "c"] and evaluate == ["b", "d"]


def test_scale_thirds_label_boundaries():
    assert replay.scale_thirds_label(10.0) == 1
    assert replay.scale_thirds_label(20.0 / 3.0) == 1
    assert replay.scale_thirds_label(5.0) is None
    assert replay.scale_thirds_label(10.0 / 3.0) == 0
    assert replay.scale_thirds_label(0.0) == 0


def test_pooled_sample_features_pools_and_restricts():
    manifest = {"conversations": [
        {"id": "a|s0", "assistant_spans": [
            {"message_index": 1}, {"message_index": 3}]},
        {"id": "b|s0", "assistant_spans": [{"message_index": 1}]},
    ]}
    tensors = {"a|s0|t1|L6": np.array([1.0, 0.0]),
               "a|s0|t3|L6": np.array([3.0, 0.0]),
               "b|s0|t1|L6": np.array([5.0, 5.0])}
    features = replay.pooled_sample_features(tensors, manifest, 6)
    assert np.allclose(features["a|s0"], [2.0, 0.0])
    restricted = replay.pooled_sample_features(
        tensors, manifest, 6, {"a|s0": {3}, "b|s0": set()})
    assert set(restricted) == {"a|s0"}  # b|s0 restricted to nothing -> omitted
    assert np.allclose(restricted["a|s0"], [3.0, 0.0])


def test_auroc_rank_statistic():
    assert auroc([0.1, 0.2, 0.8, 0.9], [0, 0, 1, 1]) == 1.0
    assert auroc([0.9, 0.8, 0.2, 0.1], [0, 0, 1, 1]) == 0.0
    assert auroc([0.5, 0.5, 0.5, 0.5], [0, 1, 0, 1]) == 0.5
    assert auroc([0.1, 0.5, 0.5, 0.9], [0, 0, 1, 1]) == pytest.approx(0.875)
    assert np.isnan(auroc([0.1, 0.2], [1, 1]))


def test_range_profile_statistics():
    values = {
        ("a", 0): 0.0, ("a", 1): 0.0,
        ("b", 0): 8.0, ("b", 1): 4.0,
        ("c", 0): 2.0, ("c", 1): 3.0,
    }
    profile = replay.range_profile(values)
    assert profile["n_samples"] == 6 and profile["n_items"] == 3
    assert profile["zero_fraction"] == pytest.approx(2 / 6)
    assert profile["ge3_fraction"] == pytest.approx(3 / 6)
    assert profile["top_third_fraction"] == pytest.approx(1 / 6)   # only 8.0
    assert profile["bottom_third_fraction"] == pytest.approx(4 / 6)  # 0,0,2,3
    assert profile["median_item_mean"] == pytest.approx(2.5)  # medians of 0,6,2.5
    with pytest.raises(ValueError):
        replay.range_profile({})
