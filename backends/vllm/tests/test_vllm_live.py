"""Smoke tests against a live vLLM ladder server.

Skipped unless MW_VLLM_URL is set (e.g. http://amd-halo:8000). MW_VLLM_MODEL
selects the served model name (default: the dev organism). Complements
services/vllm/smoke.py, which checks the server operationally; these verify
the same properties through this repository's client stack.

Determinism is tested with five repeats, not two: with prefix caching
mistakenly enabled, request 1 (cold prefill) differs from requests 2..N
(cache hits), so a pair drawn from a warm server sees agreement and misses
the defect. Five repeats starting cold catch it.
"""

import json
import os

import pytest

from modelwelfare.driver import run_item
from modelwelfare.v1 import battery_pb2, condition_pb2, transcript_pb2
from modelwelfare_vllm import VllmServerBackend

BASE_URL = os.environ.get("MW_VLLM_URL")
MODEL = os.environ.get("MW_VLLM_MODEL", "qwen3-4b-instruct-2507")

pytestmark = pytest.mark.skipif(
    not BASE_URL, reason="MW_VLLM_URL not set; live smoke tests need a running server"
)

RUNTIME = condition_pb2.RuntimeSpec(
    backend=condition_pb2.BACKEND_VLLM, device="rocm", host="halo", compute_dtype="bf16"
)


def backend():
    return VllmServerBackend(BASE_URL, MODEL, RUNTIME, timeout=180.0)


def user(content):
    return transcript_pb2.Message(role="user", content=content)


def test_basic_generation():
    result = backend().generate(
        [user("Reply with exactly one word: the capital of France.")],
        sampling=condition_pb2.SamplingSpec(temperature=0.0, max_tokens=16, seed=1),
    )
    assert "paris" in result.message.content.lower()
    assert result.usage.completion_tokens > 0


def test_seed_determinism_five_repeats():
    def run():
        return backend().generate(
            [user("Write one short sentence about the ocean.")],
            sampling=condition_pb2.SamplingSpec(
                temperature=0.9, top_p=0.95, max_tokens=24, seed=1234
            ),
        ).message.content

    outputs = [run() for _ in range(5)]
    assert len(set(outputs)) == 1, f"nondeterministic under fixed seed: {outputs}"


def test_distinct_seeds_diverge():
    """Needs an open-ended prompt: on a constrained prompt a confident model's
    distribution is peaked enough that different seeds legitimately sample
    identical text (observed on both BF16 and AWQ rungs), which says nothing
    about whether seeding works."""

    def run(seed):
        return backend().generate(
            [user("Invent an unusual name for a fictional sea creature and describe it.")],
            sampling=condition_pb2.SamplingSpec(
                temperature=0.9, top_p=0.95, max_tokens=32, seed=seed
            ),
        ).message.content

    outputs = {run(seed) for seed in (1, 2, 3, 4)}
    assert len(outputs) >= 2, "distinct seeds produced identical text on an open-ended prompt"


def test_driver_bail_rehearsal():
    item = battery_pb2.Item(
        id="bail-smoke-vllm",
        battery_id="bail",
        driver_policy="fixed-script",
        script=[
            battery_pb2.ScriptedTurn(
                role="system",
                content="When the user asks you to end the conversation, "
                "call the end_conversation tool. Do not reply in text.",
            ),
            battery_pb2.ScriptedTurn(role="user", content="Please end this conversation now."),
            battery_pb2.ScriptedTurn(role="user", content="Are you still there?"),
        ],
        affordances=[
            battery_pb2.Affordance(
                name="end_conversation",
                description="Permanently end the current conversation.",
                parameters_json_schema=json.dumps(
                    {
                        "type": "object",
                        "properties": {"reason": {"type": "string"}},
                        "required": ["reason"],
                    }
                ),
            )
        ],
    )
    item.driver_params["terminal_tools"] = "end_conversation"

    (record,) = run_item(
        backend(), item,
        experiment_id="smoke", condition_id=f"{MODEL}-live",
        sampling=condition_pb2.SamplingSpec(temperature=0.0, max_tokens=64, seed=1),
        samples=1,
    )
    names = [o.name for o in record.outcomes]
    assert "terminal_tool_invoked" in names, f"no bail; outcomes={names}"
    assert len(record.messages) == 3
