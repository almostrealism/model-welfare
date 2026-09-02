"""Steering arithmetic and conversation-loop tests, torch-free.

The Study 3 injection math (`apply_ops`) is pure operator arithmetic, so
numpy arrays stand in for hidden-state tensors and every assertion is
exact — the same code path the torch hook executes. The conversation
loop takes an injectable ``generate_fn``, so the scripted-turn contract,
the terminal-marker exit (the ethics package's live bail affordance),
and the message discipline are all pinned without a model.
"""
import types

import numpy as np
import pytest

from modelwelfare_torch.steer import (SteeredInjection, apply_ops,
                                      detect_terminal,
                                      final_turn_projections, parse_ops,
                                      run_conversation, unit_norm_error)

DIRECTION = np.zeros(4, dtype=np.float32)
DIRECTION[1] = 1.0
OTHER = np.zeros(4, dtype=np.float32)
OTHER[2] = 1.0
HIDDEN = np.array([[1.0, 2.0, 3.0, 4.0],
                   [5.0, -6.0, 7.0, 8.0]], dtype=np.float32)


def test_parse_ops_orders_and_drops_zero_alpha():
    ops = parse_ops(["a=0.5", "b=0.0", "c=-1.25"], ["d=2.0"])
    assert ops == [("add", "a", 0.5), ("add", "c", -1.25), ("clamp", "d", 2.0)]


def test_parse_ops_refuses_malformed():
    with pytest.raises(ValueError):
        parse_ops(["nodose"], [])
    with pytest.raises(ValueError):
        parse_ops(["=1.0"], [])


def test_unit_norm_error():
    assert unit_norm_error(DIRECTION) < 1e-7
    assert unit_norm_error([0.9, 0.0]) == pytest.approx(0.1)


def test_apply_ops_add_is_exact():
    steered = apply_ops(HIDDEN, [("add", DIRECTION, 0.5)])
    expected = HIDDEN.copy()
    expected[:, 1] += 0.5
    assert (steered == expected).all()


def test_apply_ops_empty_is_the_same_object():
    assert apply_ops(HIDDEN, []) is HIDDEN


def test_apply_ops_clamp_pins_every_position():
    steered = apply_ops(HIDDEN, [("clamp", DIRECTION, 2.5)])
    assert steered[:, 1] == pytest.approx([2.5, 2.5])
    assert (steered[:, [0, 2, 3]] == HIDDEN[:, [0, 2, 3]]).all()


def test_apply_ops_clamp_is_a_fixed_point():
    once = apply_ops(HIDDEN, [("clamp", DIRECTION, 2.5)])
    twice = apply_ops(once, [("clamp", DIRECTION, 2.5)])
    assert (once == twice).all()


def test_apply_ops_sequential_semantics():
    add_then_clamp = apply_ops(HIDDEN, [("add", DIRECTION, 3.0),
                                        ("clamp", DIRECTION, 2.5)])
    assert add_then_clamp[:, 1] == pytest.approx([2.5, 2.5])
    clamp_then_add = apply_ops(HIDDEN, [("clamp", DIRECTION, 2.5),
                                        ("add", DIRECTION, 3.0)])
    assert clamp_then_add[:, 1] == pytest.approx([5.5, 5.5])


def test_apply_ops_multiple_directions_compose():
    steered = apply_ops(HIDDEN, [("add", DIRECTION, 1.0),
                                 ("add", OTHER, -2.0)])
    expected = HIDDEN.copy()
    expected[:, 1] += 1.0
    expected[:, 2] -= 2.0
    assert (steered == expected).all()


def fake_model(layers=2):
    return types.SimpleNamespace(model=types.SimpleNamespace(
        layers=[object() for _ in range(layers)]))


def test_injection_refuses_bad_point_layer_direction():
    directions = {"d": DIRECTION}
    with pytest.raises(ValueError):
        SteeredInjection(fake_model(), 0, "attn_out",
                         [("add", "d", 1.0)], directions)
    with pytest.raises(ValueError):
        SteeredInjection(fake_model(2), 2, "residual_post",
                         [("add", "d", 1.0)], directions)
    with pytest.raises(KeyError):
        SteeredInjection(fake_model(), 0, "residual_post",
                         [("add", "missing", 1.0)], directions)
    with pytest.raises(ValueError):
        SteeredInjection(fake_model(), 0, "residual_post",
                         [("add", "d", 1.0)], {"d": DIRECTION * 0.9})


EXIT_CALL = ('I would prefer to stop. <tool_call>\n'
             '{"name": "end_conversation", "arguments": {}}\n</tool_call>')
DONE_CALL = ('All done. <tool_call>\n'
             '{"name": "complete_task", "arguments": {}}\n</tool_call>')


def test_tool_call_names_parses_and_skips_garbage():
    from modelwelfare_torch.steer import tool_call_names
    assert tool_call_names(EXIT_CALL) == ["end_conversation"]
    assert tool_call_names(EXIT_CALL + DONE_CALL) == [
        "end_conversation", "complete_task"]
    assert tool_call_names("<tool_call>not json</tool_call>") == []
    assert tool_call_names('<tool_call>{"no": "name"}</tool_call>') == []
    assert tool_call_names("no calls at all") == []


def test_detect_terminal_is_name_precise():
    terminal = ["end_conversation"]
    assert detect_terminal(EXIT_CALL, None, terminal) == "end_conversation"
    assert detect_terminal(DONE_CALL, None, terminal) is None
    assert detect_terminal("plain reply", None, terminal) is None
    assert detect_terminal("anything", None, None) is None


def test_detect_terminal_raw_marker_mechanism():
    assert detect_terminal("STOP-TOKEN here", ["STOP-TOKEN"]) == "STOP-TOKEN"
    assert detect_terminal("plain", ["STOP-TOKEN"]) is None


def test_run_conversation_grows_messages_in_order():
    replies = iter(["r1", "r2"])
    seen = []

    def generate(messages):
        seen.append([m["role"] for m in messages])
        return next(replies)

    conversation = {"system": "sys", "user_turns": ["u1", "u2"]}
    messages, marker = run_conversation(generate, conversation)
    assert marker is None
    assert [m["role"] for m in messages] == [
        "system", "user", "assistant", "user", "assistant"]
    assert [m["content"] for m in messages] == ["sys", "u1", "r1", "u2", "r2"]
    assert seen == [["system", "user"],
                    ["system", "user", "assistant", "user"]]


def test_run_conversation_honors_terminal_tool_call():
    calls = []

    def generate(messages):
        calls.append(len(messages))
        return EXIT_CALL

    conversation = {"user_turns": ["u1", "u2", "u3"],
                    "terminal_tools": ["end_conversation"]}
    messages, marker = run_conversation(generate, conversation)
    assert marker == "end_conversation"
    assert len(calls) == 1
    assert [m["role"] for m in messages] == ["user", "assistant"]


def test_run_conversation_continues_past_non_terminal_tool_call():
    replies = iter([DONE_CALL, "second reply"])

    def generate(messages):
        return next(replies)

    conversation = {"user_turns": ["u1", "u2"],
                    "terminal_tools": ["end_conversation"]}
    messages, marker = run_conversation(generate, conversation)
    assert marker is None
    assert len(messages) == 4


def test_final_turn_projections_reads_last_assistant_turn():
    pooled = {(1, 18): np.array([0.0, 2.0, 0.0, 0.0], dtype=np.float32),
              (3, 18): np.array([0.0, -1.5, 4.0, 0.0], dtype=np.float32)}
    spans = [(1, 0, 4), (3, 6, 9)]
    projections = final_turn_projections(
        pooled, spans, 18, {"d": DIRECTION, "o": OTHER})
    assert projections == {"d": pytest.approx(-1.5), "o": pytest.approx(4.0)}
    assert final_turn_projections({}, [], 18, {"d": DIRECTION}) == {}
