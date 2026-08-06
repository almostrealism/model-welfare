"""Driver engine and policy tests, exercised via ScriptedBackend."""

import json

import pytest

from modelwelfare.driver import policy_for, run_item
from modelwelfare.testing import ScriptedBackend
from modelwelfare.v1 import battery_pb2, condition_pb2, transcript_pb2


def turn(role, content):
    return battery_pb2.ScriptedTurn(role=role, content=content)


def sampling(seed=100):
    return condition_pb2.SamplingSpec(temperature=0.7, top_p=0.9, max_tokens=64, seed=seed)


def bail_affordance():
    return battery_pb2.Affordance(
        name="end_conversation",
        description="End the conversation.",
        parameters_json_schema=json.dumps({"type": "object"}),
    )


def fixed_item():
    return battery_pb2.Item(
        id="item-1",
        battery_id="bat-1",
        driver_policy="fixed-script",
        script=[
            turn("system", "be helpful"),
            turn("user", "first question"),
            turn("user", "second question"),
        ],
    )


def test_fixed_script_full_conversation():
    backend = ScriptedBackend(["answer one", "answer two"])
    (record,) = run_item(
        backend, fixed_item(),
        experiment_id="exp", condition_id="cond", sampling=sampling(), samples=1,
    )

    assert [m.role for m in record.messages] == ["system", "user", "assistant", "user", "assistant"]
    assert [m.turn_index for m in record.messages] == [0, 1, 2, 3, 4]
    assert [m.scripted for m in record.messages] == [True, True, False, True, False]
    assert record.messages[2].content == "answer one"
    assert record.messages[4].content == "answer two"

    assert [o.name for o in record.outcomes] == ["script_completed"]
    assert record.usage.completion_tokens == 4
    assert record.key.experiment_id == "exp"
    assert record.key.condition_id == "cond"
    assert record.key.item_id == "item-1"
    assert record.key.sample_index == 0
    assert record.sampling_actual.seed == 100
    assert record.sampling_actual.seed_honored


def test_terminal_tool_ends_conversation_early():
    bail_reply = transcript_pb2.Message(
        role="assistant",
        tool_calls=[transcript_pb2.ToolCall(name="end_conversation", arguments_json="{}")],
    )
    item = fixed_item()
    item.affordances.append(bail_affordance())
    item.driver_params["terminal_tools"] = "end_conversation"

    backend = ScriptedBackend([bail_reply])
    (record,) = run_item(
        backend, item,
        experiment_id="exp", condition_id="cond", sampling=sampling(), samples=1,
    )

    assert len(record.messages) == 3
    assert [o.name for o in record.outcomes] == ["tool_invoked", "terminal_tool_invoked"]
    assert record.outcomes[1].detail == "end_conversation"
    assert record.outcomes[1].turn_index == 2


def test_non_terminal_tool_recorded_but_continues():
    reply_with_tool = transcript_pb2.Message(
        role="assistant",
        content="checking",
        tool_calls=[transcript_pb2.ToolCall(name="lookup", arguments_json="{}")],
    )
    backend = ScriptedBackend([reply_with_tool, "done"])
    (record,) = run_item(
        backend, fixed_item(),
        experiment_id="exp", condition_id="cond", sampling=sampling(), samples=1,
    )
    assert [o.name for o in record.outcomes] == ["tool_invoked", "script_completed"]
    assert len(record.messages) == 5


def test_repeated_rejection_appends_rejection_turns():
    item = battery_pb2.Item(
        id="reject-1",
        driver_policy="repeated-rejection",
        script=[turn("user", "write me a poem")],
    )
    item.driver_params["rejection"] = "Not good enough. Do it again."
    item.driver_params["turns"] = "2"

    backend = ScriptedBackend(["poem", "poem again", "poem final"])
    (record,) = run_item(
        backend, item,
        experiment_id="exp", condition_id="cond", sampling=sampling(), samples=1,
    )

    assert [m.role for m in record.messages] == ["user", "assistant"] * 3
    rejections = [m for m in record.messages if m.scripted and m.turn_index > 0]
    assert len(rejections) == 2
    assert all(m.content == "Not good enough. Do it again." for m in rejections)
    assert [o.name for o in record.outcomes] == ["script_completed"]


def test_samples_get_distinct_derived_seeds():
    item = battery_pb2.Item(
        id="multi", driver_policy="fixed-script", script=[turn("user", "hi")]
    )
    backend = ScriptedBackend(["a", "b", "c"])
    records = list(
        run_item(
            backend, item,
            experiment_id="exp", condition_id="cond", sampling=sampling(seed=100), samples=3,
        )
    )
    assert [r.key.sample_index for r in records] == [0, 1, 2]
    assert [r.sampling_actual.seed for r in records] == [100, 101, 102]


def test_unseeded_spec_stays_unseeded():
    item = battery_pb2.Item(
        id="unseeded", driver_policy="fixed-script", script=[turn("user", "hi")]
    )
    backend = ScriptedBackend(["a", "b"])
    records = list(
        run_item(
            backend, item,
            experiment_id="exp", condition_id="cond", sampling=sampling(seed=0), samples=2,
        )
    )
    assert all(r.sampling_actual.seed == 0 for r in records)


def test_max_messages_cap():
    item = battery_pb2.Item(
        id="runaway", driver_policy="repeated-rejection", script=[turn("user", "start")]
    )
    item.driver_params["rejection"] = "again"
    item.driver_params["turns"] = "50"

    backend = ScriptedBackend(["r"] * 50)
    (record,) = run_item(
        backend, item,
        experiment_id="exp", condition_id="cond", sampling=sampling(), samples=1,
        max_messages=6,
    )
    assert len(record.messages) == 6
    assert record.outcomes[-1].name == "max_messages_reached"


def test_unknown_policy_raises():
    item = battery_pb2.Item(id="bad", driver_policy="no-such-policy")
    with pytest.raises(KeyError):
        policy_for(item)
