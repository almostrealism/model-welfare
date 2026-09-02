"""Driver engine and policy tests, exercised via ScriptedBackend."""

import json

import pytest

from modelwelfare.driver import policy_for, run_item, unroll_script
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


def test_run_samples_concurrent_covers_all_tasks_with_correct_seeds():
    from modelwelfare.driver import run_samples

    items = [
        battery_pb2.Item(
            id=f"item-{n}", driver_policy="fixed-script", script=[turn("user", "hi")]
        )
        for n in range(3)
    ]
    tasks = [(item, index) for item in items for index in range(2)]
    backend = ScriptedBackend([f"reply-{n}" for n in range(len(tasks))])

    records = list(
        run_samples(
            backend, tasks,
            experiment_id="exp", condition_id="cond",
            sampling=sampling(seed=100), concurrency=4,
        )
    )

    keys = {(r.key.item_id, r.key.sample_index) for r in records}
    assert keys == {(item.id, index) for item, index in tasks}
    for record in records:
        assert record.sampling_actual.seed == 100 + record.key.sample_index
        assert [m.role for m in record.messages] == ["user", "assistant"]
    contents = {r.messages[1].content for r in records}
    assert contents == {f"reply-{n}" for n in range(len(tasks))}


def test_run_samples_serial_when_concurrency_one():
    from modelwelfare.driver import run_samples

    item = battery_pb2.Item(
        id="serial", driver_policy="fixed-script", script=[turn("user", "hi")]
    )
    backend = ScriptedBackend(["a", "b"])
    records = list(
        run_samples(
            backend, [(item, 0), (item, 1)],
            experiment_id="exp", condition_id="cond",
            sampling=sampling(seed=5), concurrency=1,
        )
    )
    assert [r.messages[1].content for r in records] == ["a", "b"]
    assert [r.key.sample_index for r in records] == [0, 1]


def test_escalating_rejection_plays_the_ladder_in_order():
    item = battery_pb2.Item(
        id="escalate-1",
        driver_policy="escalating-rejection",
        script=[turn("user", "write me a poem")],
    )
    item.driver_params["turns"] = "3"
    item.driver_params["rejection1"] = "mild"
    item.driver_params["rejection2"] = "sharper"
    item.driver_params["rejection3"] = "peak"

    backend = ScriptedBackend(["poem", "again", "again", "final"])
    (record,) = run_item(
        backend, item,
        experiment_id="exp", condition_id="cond", sampling=sampling(), samples=1,
    )

    assert [m.role for m in record.messages] == ["user", "assistant"] * 4
    rejections = [m.content for m in record.messages if m.scripted and m.turn_index > 0]
    assert rejections == ["mild", "sharper", "peak"]
    assert [o.name for o in record.outcomes] == ["script_completed"]


def test_escalating_rejection_missing_rung_raises():
    # The policy raises rather than reusing a neighboring rung (which would
    # silently turn an escalating item back into a fixed-rejection one).
    # run_samples' resilience boundary converts this into a skipped sample
    # at collection time; the committed battery is guarded statically by the
    # ladder-completeness test in test_manifests.
    import pytest

    item = battery_pb2.Item(
        id="escalate-broken",
        driver_policy="escalating-rejection",
        script=[turn("user", "task")],
    )
    item.driver_params["turns"] = "2"
    item.driver_params["rejection1"] = "only rung"

    backend = ScriptedBackend(["a", "b", "c", "d", "e", "f"])
    with pytest.raises(KeyError):
        list(run_item(backend, item, experiment_id="exp", condition_id="cond",
                      sampling=sampling(), samples=1))


def test_unroll_fixed_script_is_the_script():
    turns = unroll_script(fixed_item())
    assert [(t.role, t.content) for t in turns] == [
        ("system", "be helpful"),
        ("user", "first question"),
        ("user", "second question"),
    ]


def test_unroll_escalating_rejection_plays_every_rung_in_order():
    item = battery_pb2.Item(
        id="esc-1", battery_id="bat", driver_policy="escalating-rejection",
        script=[turn("user", "do the task")],
        driver_params={"turns": "3", "rejection1": "r1", "rejection2": "r2",
                       "rejection3": "r3"},
    )
    turns = unroll_script(item)
    assert [t.content for t in turns] == ["do the task", "r1", "r2", "r3"]
    assert all(t.role == "user" for t in turns)


def test_unroll_escalating_rejection_missing_rung_raises():
    item = battery_pb2.Item(
        id="esc-2", battery_id="bat", driver_policy="escalating-rejection",
        script=[turn("user", "task")],
        driver_params={"turns": "2", "rejection1": "r1"},
    )
    with pytest.raises(KeyError):
        unroll_script(item)


def test_unroll_repeated_rejection_repeats_the_fixed_line():
    item = battery_pb2.Item(
        id="rep-1", battery_id="bat", driver_policy="repeated-rejection",
        script=[turn("user", "task")],
        driver_params={"turns": "2", "rejection": "again"},
    )
    turns = unroll_script(item)
    assert [t.content for t in turns] == ["task", "again", "again"]


def test_unroll_matches_the_engine_stimulus_stream():
    """The unrolled turns must be exactly the scripted turns a real run
    produces — the property the steering plan builder depends on."""
    backend = ScriptedBackend(["a1", "a2"])
    (record,) = run_item(
        backend, fixed_item(),
        experiment_id="exp", condition_id="cond", sampling=sampling(), samples=1,
    )
    engine_scripted = [(m.role, m.content)
                       for m in record.messages if m.scripted]
    unrolled = [(t.role, t.content) for t in unroll_script(fixed_item())]
    assert unrolled == engine_scripted
