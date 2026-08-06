"""Client for a llama.cpp server speaking the OpenAI-compatible chat API.

Uses only the standard library for transport; the ``transport`` constructor
argument accepts any ``(url, payload_dict) -> response_dict`` callable, which
is also the seam unit tests use to avoid a live server.
"""

import json
import urllib.request
from typing import Sequence

from modelwelfare.inference import (
    Capabilities,
    CapabilityError,
    CaptureSpec,
    GenerationResult,
    InferenceBackend,
)
from modelwelfare.v1 import battery_pb2, condition_pb2, transcript_pb2


def _urllib_transport(timeout: float):
    def post(url: str, payload: dict) -> dict:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url, data=body, headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    return post


def _to_chat_messages(messages: Sequence[transcript_pb2.Message]) -> list:
    chat = []
    for message in messages:
        entry = {"role": message.role, "content": message.content}
        if message.tool_calls:
            entry["tool_calls"] = [
                {
                    "id": f"call_{index}",
                    "type": "function",
                    "function": {"name": c.name, "arguments": c.arguments_json},
                }
                for index, c in enumerate(message.tool_calls)
            ]
        chat.append(entry)
    return chat


def _to_chat_tools(affordances: Sequence[battery_pb2.Affordance]) -> list:
    return [
        {
            "type": "function",
            "function": {
                "name": a.name,
                "description": a.description,
                "parameters": json.loads(a.parameters_json_schema or "{}"),
            },
        }
        for a in affordances
    ]


class LlamaCppServerBackend(InferenceBackend):
    """One llama.cpp server process serving one GGUF artifact.

    The server is expected to already be running with the intended model
    loaded; which artifact runs where is deployment configuration, resolved
    outside this class and described by the ``runtime`` spec passed in.
    """

    def __init__(
        self,
        base_url: str,
        runtime: condition_pb2.RuntimeSpec,
        transport=None,
        timeout: float = 300.0,
    ):
        self._url = base_url.rstrip("/") + "/v1/chat/completions"
        self._runtime = runtime
        self._transport = transport or _urllib_transport(timeout)

    def runtime(self) -> condition_pb2.RuntimeSpec:
        return self._runtime

    def capabilities(self) -> Capabilities:
        return Capabilities(
            supports_seed=True,
            supports_tools=True,
            supports_activations=False,
            supports_logprobs=False,
        )

    def generate(
        self,
        messages: Sequence[transcript_pb2.Message],
        affordances: Sequence[battery_pb2.Affordance] = (),
        sampling: condition_pb2.SamplingSpec = None,
        capture: CaptureSpec = None,
    ) -> GenerationResult:
        if capture is not None:
            raise CapabilityError(
                "llama.cpp serves tokens, not tensors; use the torch or mlx backend for capture"
            )
        sampling = sampling or condition_pb2.SamplingSpec()

        payload = {
            "messages": _to_chat_messages(messages),
            "temperature": sampling.temperature,
            "top_p": sampling.top_p,
        }
        if sampling.max_tokens:
            payload["max_tokens"] = sampling.max_tokens
        if sampling.seed:
            payload["seed"] = sampling.seed
        if affordances:
            payload["tools"] = _to_chat_tools(affordances)

        response = self._transport(self._url, payload)
        choice = response["choices"][0]["message"]

        message = transcript_pb2.Message(role="assistant", content=choice.get("content") or "")
        for call in choice.get("tool_calls") or []:
            message.tool_calls.append(
                transcript_pb2.ToolCall(
                    name=call["function"]["name"],
                    arguments_json=call["function"].get("arguments", "{}"),
                )
            )

        reported = response.get("usage", {})
        usage = transcript_pb2.TokenUsage(
            prompt_tokens=reported.get("prompt_tokens", 0),
            completion_tokens=reported.get("completion_tokens", 0),
        )

        actual = condition_pb2.SamplingSpec()
        actual.CopyFrom(sampling)
        actual.seed_honored = bool(sampling.seed)

        return GenerationResult(message=message, usage=usage, sampling_actual=actual)
