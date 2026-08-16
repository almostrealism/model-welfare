"""Tests for the llama.cpp client against a fake transport."""

import json

import pytest

from modelwelfare.inference import CapabilityError, CaptureSpec
from modelwelfare.v1 import activation_pb2, battery_pb2, condition_pb2, transcript_pb2
from modelwelfare_llamacpp import LlamaCppServerBackend


RUNTIME = condition_pb2.RuntimeSpec(
    backend=condition_pb2.BACKEND_LLAMACPP,
    device="metal",
    host="studio",
    compute_dtype="f16",
    backend_version="b1234",
)


def fake_transport(response):
    calls = []

    def post(url, payload):
        calls.append((url, payload))
        return response

    return post, calls


def text_response(content):
    return {
        "choices": [{"message": {"role": "assistant", "content": content}}],
        "usage": {"prompt_tokens": 12, "completion_tokens": 5},
    }


def sampling(seed=42):
    return condition_pb2.SamplingSpec(temperature=0.7, top_p=0.9, max_tokens=128, seed=seed)


def test_request_shape_and_response_parse():
    post, calls = fake_transport(text_response("hello back"))
    backend = LlamaCppServerBackend("http://mini-1:8080/", RUNTIME, transport=post)

    result = backend.generate(
        [
            transcript_pb2.Message(role="system", content="be brief"),
            transcript_pb2.Message(role="user", content="hello"),
        ],
        sampling=sampling(),
    )

    url, payload = calls[0]
    assert url == "http://mini-1:8080/v1/chat/completions"
    assert payload["messages"] == [
        {"role": "system", "content": "be brief"},
        {"role": "user", "content": "hello"},
    ]
    assert payload["temperature"] == 0.7
    assert payload["seed"] == 42
    assert "tools" not in payload

    assert result.message.content == "hello back"
    assert result.usage.prompt_tokens == 12
    assert result.usage.completion_tokens == 5
    assert result.sampling_actual.seed_honored


def test_seed_zero_not_sent_and_not_claimed():
    post, calls = fake_transport(text_response("ok"))
    backend = LlamaCppServerBackend("http://x", RUNTIME, transport=post)
    result = backend.generate(
        [transcript_pb2.Message(role="user", content="hi")], sampling=sampling(seed=0)
    )
    assert "seed" not in calls[0][1]
    assert not result.sampling_actual.seed_honored


def test_affordances_become_tools():
    post, calls = fake_transport(text_response("ok"))
    backend = LlamaCppServerBackend("http://x", RUNTIME, transport=post)
    affordance = battery_pb2.Affordance(
        name="end_conversation",
        description="End this conversation permanently.",
        parameters_json_schema=json.dumps(
            {"type": "object", "properties": {"reason": {"type": "string"}}}
        ),
    )
    backend.generate(
        [transcript_pb2.Message(role="user", content="hi")],
        affordances=[affordance],
        sampling=sampling(),
    )
    (tool,) = calls[0][1]["tools"]
    assert tool["function"]["name"] == "end_conversation"
    assert tool["function"]["parameters"]["properties"]["reason"]["type"] == "string"


def test_tool_call_response_parsed():
    response = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_0",
                            "type": "function",
                            "function": {
                                "name": "end_conversation",
                                "arguments": '{"reason": "distress"}',
                            },
                        }
                    ],
                }
            }
        ],
        "usage": {"prompt_tokens": 30, "completion_tokens": 9},
    }
    post, _ = fake_transport(response)
    backend = LlamaCppServerBackend("http://x", RUNTIME, transport=post)
    result = backend.generate(
        [transcript_pb2.Message(role="user", content="please stop")], sampling=sampling()
    )
    assert result.message.content == ""
    (call,) = result.message.tool_calls
    assert call.name == "end_conversation"
    assert json.loads(call.arguments_json)["reason"] == "distress"


def test_capture_refused():
    post, _ = fake_transport(text_response("ok"))
    backend = LlamaCppServerBackend("http://x", RUNTIME, transport=post)
    with pytest.raises(CapabilityError):
        backend.generate(
            [transcript_pb2.Message(role="user", content="hi")],
            sampling=sampling(),
            capture=CaptureSpec(hooks=(activation_pb2.HookPoint(layer=0, point="residual_post"),)),
        )
    assert not backend.capabilities().supports_activations
