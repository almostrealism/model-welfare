"""Contract tests for the inference seam, exercised via ScriptedBackend."""

import numpy as np
import pytest

from modelwelfare.inference import (
    CapabilityError,
    CaptureSpec,
    create_backend,
    register_backend,
)
from modelwelfare.testing import ScriptedBackend
from modelwelfare.v1 import activation_pb2, condition_pb2, transcript_pb2


def user(content):
    return transcript_pb2.Message(role="user", content=content)


def sampling(seed=7):
    return condition_pb2.SamplingSpec(temperature=0.7, top_p=0.95, max_tokens=64, seed=seed)


def test_replies_in_order_with_usage():
    backend = ScriptedBackend(["first reply here", "second"])
    r1 = backend.generate([user("hello there")], sampling=sampling())
    r2 = backend.generate([user("hello there"), r1.message], sampling=sampling())
    assert r1.message.content == "first reply here"
    assert r2.message.content == "second"
    assert r1.message.role == "assistant"
    assert r1.usage.prompt_tokens == 2
    assert r1.usage.completion_tokens == 3
    assert r1.sampling_actual.seed == 7
    assert r1.sampling_actual.seed_honored


def test_script_exhaustion_raises():
    backend = ScriptedBackend(["only"])
    backend.generate([user("hi")], sampling=sampling())
    with pytest.raises(CapabilityError):
        backend.generate([user("hi")], sampling=sampling())


def test_prebuilt_message_reply_preserves_tool_calls():
    reply = transcript_pb2.Message(
        role="assistant",
        tool_calls=[transcript_pb2.ToolCall(name="end_conversation", arguments_json="{}")],
    )
    backend = ScriptedBackend([reply])
    result = backend.generate([user("goodbye")], sampling=sampling())
    assert result.message.tool_calls[0].name == "end_conversation"


def test_capture_shapes_and_span():
    hook = activation_pb2.HookPoint(layer=3, point="residual_post")
    backend = ScriptedBackend(["a b c"], hidden_size=4)
    result = backend.generate(
        [user("one two three four")],
        sampling=sampling(),
        capture=CaptureSpec(hooks=(hook,)),
    )
    (cap,) = result.captures
    assert cap.hook.layer == 3
    assert cap.token_start == 4
    assert cap.token_end == 7
    assert cap.tokens.shape == (3, 4)
    assert cap.tokens.dtype == np.float32


def test_capture_include_prompt_spans_full_sequence():
    hook = activation_pb2.HookPoint(layer=0, point="residual_pre")
    backend = ScriptedBackend(["a b"], hidden_size=2)
    result = backend.generate(
        [user("one two three")],
        sampling=sampling(),
        capture=CaptureSpec(hooks=(hook,), include_prompt=True),
    )
    (cap,) = result.captures
    assert cap.token_start == 0
    assert cap.token_end == 5
    assert cap.tokens.shape == (5, 2)


def test_capture_deterministic_under_seed():
    hook = activation_pb2.HookPoint(layer=1, point="mlp_out")

    def run(seed):
        backend = ScriptedBackend(["x y z"], hidden_size=4)
        result = backend.generate(
            [user("p q")], sampling=sampling(seed), capture=CaptureSpec(hooks=(hook,))
        )
        return result.captures[0].tokens

    assert np.array_equal(run(5), run(5))
    assert not np.array_equal(run(5), run(6))


def test_registry_roundtrip_and_unknown_backend():
    condition = condition_pb2.Condition(
        id="test-cond",
        runtime=condition_pb2.RuntimeSpec(backend=condition_pb2.BACKEND_TORCH),
    )
    register_backend(condition_pb2.BACKEND_TORCH, lambda c: ScriptedBackend([c.id]))
    backend = create_backend(condition)
    assert backend.generate([user("hi")], sampling=sampling()).message.content == "test-cond"

    unknown = condition_pb2.Condition(
        runtime=condition_pb2.RuntimeSpec(backend=condition_pb2.BACKEND_MLX)
    )
    with pytest.raises(KeyError):
        create_backend(unknown)
