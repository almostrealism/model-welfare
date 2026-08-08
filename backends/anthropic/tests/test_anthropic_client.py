"""Tests for the Anthropic backend against a stub client."""

import types

import pytest

from modelwelfare.inference import CapabilityError
from modelwelfare.v1 import condition_pb2, transcript_pb2
from modelwelfare_anthropic import AnthropicBackend


class StubClient:
    def __init__(self, response):
        self.requests = []
        outer = self

        class Messages:
            def create(self, **kwargs):
                outer.requests.append(kwargs)
                return response

        self.beta = types.SimpleNamespace(messages=Messages())


def response(text="ok", stop_reason="end_turn"):
    block = types.SimpleNamespace(type="text", text=text)
    thinking = types.SimpleNamespace(type="thinking", thinking="")
    usage = types.SimpleNamespace(input_tokens=100, output_tokens=25)
    return types.SimpleNamespace(
        content=[thinking, block], stop_reason=stop_reason, usage=usage
    )


def user(content):
    return transcript_pb2.Message(role="user", content=content)


def test_request_shape_and_parse():
    stub = StubClient(response("scored"))
    backend = AnthropicBackend("claude-opus-5", client=stub)
    result = backend.generate(
        [
            transcript_pb2.Message(role="system", content="be a judge"),
            user("score this"),
        ],
        sampling=condition_pb2.SamplingSpec(max_tokens=4000),
    )
    request = stub.requests[0]
    assert request["model"] == "claude-opus-5"
    assert request["max_tokens"] == 4000
    assert request["system"] == "be a judge"
    assert request["messages"] == [{"role": "user", "content": "score this"}]
    assert request["extra_body"] == {"fallbacks": "default"}
    assert "temperature" not in request and "top_p" not in request
    assert result.message.content == "scored"
    assert result.usage.prompt_tokens == 100
    assert not result.sampling_actual.seed_honored


def test_nonzero_sampling_params_refused():
    backend = AnthropicBackend("claude-opus-5", client=StubClient(response()))
    with pytest.raises(CapabilityError, match="temperature"):
        backend.generate(
            [user("hi")], sampling=condition_pb2.SamplingSpec(temperature=0.7)
        )
    with pytest.raises(CapabilityError):
        backend.generate([user("hi")], sampling=condition_pb2.SamplingSpec(seed=5))


def test_refusal_yields_empty_message():
    backend = AnthropicBackend(
        "claude-opus-5", client=StubClient(response("partial", stop_reason="refusal"))
    )
    result = backend.generate([user("hi")], sampling=condition_pb2.SamplingSpec())
    assert result.message.content == ""
