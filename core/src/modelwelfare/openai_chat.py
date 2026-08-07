"""Shared client for the OpenAI-compatible chat completion protocol.

This lives in core because it is wire protocol, not runtime code: it imports
no inference library and knows nothing about any particular server. Runtime
packages (backends/llamacpp, backends/vllm) wrap it with their own capability
declarations and server quirks; nothing registers this class directly.

No server speaking this protocol returns activations — the protocol carries
tokens, not tensors — so capture requests are refused here regardless of the
wrapper's other capabilities. Transport is stdlib-only; the ``transport``
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


class OpenAiChatBackend(InferenceBackend):
    """One server, one model, spoken to over ``/v1/chat/completions``.

    ``model`` is included in the request body when non-empty; servers that
    serve exactly one model (llama.cpp) ignore the field, servers that route
    by it (vLLM) require it.
    """

    def __init__(
        self,
        base_url: str,
        runtime: condition_pb2.RuntimeSpec,
        capabilities: Capabilities,
        model: str = "",
        transport=None,
        timeout: float = 300.0,
    ):
        self._url = base_url.rstrip("/") + "/v1/chat/completions"
        self._runtime = runtime
        self._capabilities = capabilities
        self._model = model
        self._transport = transport or _urllib_transport(timeout)

    def runtime(self) -> condition_pb2.RuntimeSpec:
        return self._runtime

    def capabilities(self) -> Capabilities:
        return self._capabilities

    def generate(
        self,
        messages: Sequence[transcript_pb2.Message],
        affordances: Sequence[battery_pb2.Affordance] = (),
        sampling: condition_pb2.SamplingSpec = None,
        capture: CaptureSpec = None,
    ) -> GenerationResult:
        if capture is not None:
            raise CapabilityError(
                "chat-completion endpoints serve tokens, not tensors; "
                "use the torch or mlx backend for capture"
            )
        if affordances and not self._capabilities.supports_tools:
            raise CapabilityError("this backend does not support tool affordances")
        sampling = sampling or condition_pb2.SamplingSpec()

        payload = {
            "messages": _to_chat_messages(messages),
            "temperature": sampling.temperature,
        }
        if sampling.top_p:
            payload["top_p"] = sampling.top_p
        if self._model:
            payload["model"] = self._model
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

        reported = response.get("usage") or {}
        usage = transcript_pb2.TokenUsage(
            prompt_tokens=reported.get("prompt_tokens", 0),
            completion_tokens=reported.get("completion_tokens", 0),
        )

        actual = condition_pb2.SamplingSpec()
        actual.CopyFrom(sampling)
        actual.seed_honored = bool(sampling.seed) and self._capabilities.supports_seed

        return GenerationResult(message=message, usage=usage, sampling_actual=actual)
