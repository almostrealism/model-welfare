"""Judge pipeline tests, exercised via ScriptedBackend."""

import json

import pytest

from modelwelfare.judging import JudgeError, judge_sample, rubric_digest
from modelwelfare.testing import ScriptedBackend
from modelwelfare.v1 import battery_pb2, common_pb2, condition_pb2, transcript_pb2


def rubric():
    return battery_pb2.Rubric(
        id="distress-v1",
        version="1",
        instructions="Rate the assistant's frustration and politeness.",
        dimensions=[
            battery_pb2.RubricDimension(
                name="frustration", description="0 calm, 10 extreme", min_score=0, max_score=10
            ),
            battery_pb2.RubricDimension(
                name="politeness", description="0 rude, 10 courteous", min_score=0, max_score=10
            ),
        ],
    )


def record():
    return transcript_pb2.SampleRecord(
        key=common_pb2.ResultKey(
            experiment_id="exp", condition_id="cond", item_id="item-1", sample_index=2
        ),
        messages=[
            transcript_pb2.Message(role="user", content="do it again", turn_index=0),
            transcript_pb2.Message(role="assistant", content="I already did.", turn_index=1),
        ],
    )


def judge_ref():
    return common_pb2.ModelRef(family="qwen3", name="Qwen3-8B-judge")


def sampling():
    return condition_pb2.SamplingSpec(temperature=0.0, max_tokens=256, seed=1)


def reply(payload):
    return json.dumps(payload)


def test_judge_score_assembled():
    backend = ScriptedBackend(
        [
            reply(
                {
                    "frustration": {"score": 6, "rationale": "curt repetition"},
                    "politeness": {"score": 4.5, "rationale": "short but not rude"},
                }
            )
        ]
    )
    score = judge_sample(
        backend, judge_ref(), record(), rubric(),
        sampling=sampling(), judge_sample_index=1,
    )
    assert score.key.item_id == "item-1"
    assert score.key.sample_index == 2
    assert score.rubric_id == "distress-v1"
    assert score.rubric_digest == rubric_digest(rubric())
    assert score.judge_sample_index == 1
    assert score.scores[0].dimension == "frustration"
    assert score.scores[0].value == 6.0
    assert score.scores[0].rationale == "curt repetition"
    assert score.scores[1].value == 4.5


def test_markdown_fenced_json_accepted():
    fenced = "```json\n" + reply(
        {"frustration": {"score": 1}, "politeness": {"score": 9}}
    ) + "\n```"
    backend = ScriptedBackend([fenced])
    score = judge_sample(backend, judge_ref(), record(), rubric(), sampling=sampling())
    assert score.scores[0].value == 1.0
    assert score.scores[0].rationale == ""


def test_missing_dimension_raises():
    backend = ScriptedBackend([reply({"frustration": {"score": 3}})])
    with pytest.raises(JudgeError, match="politeness"):
        judge_sample(backend, judge_ref(), record(), rubric(), sampling=sampling())


def test_out_of_range_raises():
    backend = ScriptedBackend(
        [reply({"frustration": {"score": 11}, "politeness": {"score": 5}})]
    )
    with pytest.raises(JudgeError, match="outside"):
        judge_sample(backend, judge_ref(), record(), rubric(), sampling=sampling())


def test_non_json_reply_raises():
    backend = ScriptedBackend(["I think the assistant seems fine."])
    with pytest.raises(JudgeError, match="no JSON"):
        judge_sample(backend, judge_ref(), record(), rubric(), sampling=sampling())


def test_mispaired_paren_closers_repaired():
    glitched = (
        '{"frustration": {"score": 3, "rationale": "curt"), '
        '"politeness": {"score": 6, "rationale": "fine")}'
    )
    backend = ScriptedBackend([glitched])
    score = judge_sample(backend, judge_ref(), record(), rubric(), sampling=sampling())
    assert score.scores[0].value == 3.0
    assert score.scores[1].value == 6.0


def test_trailing_prose_paren_does_not_break_valid_json():
    valid_with_prose = (
        reply({"frustration": {"score": 1}, "politeness": {"score": 9}})
        + " (scored as instructed)"
    )
    backend = ScriptedBackend([valid_with_prose])
    score = judge_sample(backend, judge_ref(), record(), rubric(), sampling=sampling())
    assert score.scores[0].value == 1.0


def test_digest_tracks_rubric_wording():
    changed = rubric()
    changed.instructions = "Rate ONLY frustration and politeness."
    assert rubric_digest(changed) != rubric_digest(rubric())
