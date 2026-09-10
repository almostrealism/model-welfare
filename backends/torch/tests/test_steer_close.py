"""Tests for the de-induction close in the steering script: the close is
generated as one extra user turn on the finished protocol transcript,
returned as a record separate from the messages, and the injection can be
suspended around it so the close runs with steering off."""
from test_steer import DIRECTION, fake_model
from modelwelfare_torch.steer import SteeredInjection, run_close, run_conversation


def test_run_close_appends_one_turn_and_keeps_messages_intact():
    calls = []

    def generate(messages):
        calls.append([m["role"] for m in messages])
        return "closing reply"

    messages, marker = run_conversation(generate, {"user_turns": ["a", "b"]})
    close = run_close(generate, messages, "the close text")
    assert close == {"user": "the close text", "assistant": "closing reply"}
    assert calls[-1] == ["user", "assistant", "user", "assistant", "user"]
    assert len(messages) == 4  # the close never enters the protocol transcript


def test_suspended_empties_ops_and_restores_them():
    injection = SteeredInjection(fake_model(), 0, "residual_post",
                                 [("add", "d", 2.0)], {"d": DIRECTION})
    with injection.suspended() as same:
        assert same is injection
        assert injection._ops == []
    assert injection._ops == [("add", "d", 2.0)]
    # a failure inside the context still restores the ops
    try:
        with injection.suspended():
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    assert injection._ops == [("add", "d", 2.0)]
