"""Tests for the vLLM client against a fake transport."""

import pytest

from modelwelfare.v1 import condition_pb2, transcript_pb2
from modelwelfare_vllm import VllmServerBackend


RUNTIME = condition_pb2.RuntimeSpec(
    backend=condition_pb2.BACKEND_VLLM,
    device="rocm",
    host="halo",
    compute_dtype="bf16",
    backend_version="vllm-0.21.0+rocm713",
)


def fake_transport(response):
    calls = []

    def post(url, payload):
        calls.append((url, payload))
        return response

    return post, calls


def test_model_field_sent():
    post, calls = fake_transport(
        {
            "choices": [{"message": {"role": "assistant", "content": "ok"}}],
            "usage": {"prompt_tokens": 3, "completion_tokens": 1},
        }
    )
    backend = VllmServerBackend(
        "http://amd-halo:8000", "qwen3-4b-instruct-2507", RUNTIME, transport=post
    )
    backend.generate(
        [transcript_pb2.Message(role="user", content="hi")],
        sampling=condition_pb2.SamplingSpec(temperature=0.5, max_tokens=8, seed=3),
    )
    url, payload = calls[0]
    assert url == "http://amd-halo:8000/v1/chat/completions"
    assert payload["model"] == "qwen3-4b-instruct-2507"
    assert payload["seed"] == 3


def test_model_name_required():
    with pytest.raises(ValueError, match="model name"):
        VllmServerBackend("http://amd-halo:8000", "", RUNTIME)
