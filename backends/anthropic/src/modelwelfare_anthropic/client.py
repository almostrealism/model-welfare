"""InferenceBackend over the Anthropic API, for reference judging.

Current-generation Claude models accept no temperature, top_p, or seed —
those parameters were removed from the API — so this client treats a
SamplingSpec's proto-default zeros as "unset" and raises CapabilityError on
nonzero values rather than silently dropping them. Thinking is on by default
and is billed within max_tokens, so judging callers should leave generous
headroom (the reply plus reasoning). Server-side refusal fallbacks are
enabled per current API guidance; a refusal that survives the fallback chain
yields an empty message, which judging surfaces as a parse failure.
"""

from pathlib import Path
from typing import Sequence

import anthropic

from modelwelfare.inference import (
    Capabilities,
    CapabilityError,
    CaptureSpec,
    GenerationResult,
    InferenceBackend,
)
from modelwelfare.v1 import battery_pb2, condition_pb2, transcript_pb2

FALLBACK_BETA = "server-side-fallback-2026-07-01"


def load_api_key(path=None) -> str:
    """The key lives beside the repo checkout (../anthropic.api-key),
    deliberately outside version control."""
    repo = Path(__file__).resolve().parents[4]
    key_file = Path(path) if path else repo.parent / "anthropic.api-key"
    return key_file.read_text().strip()


class AnthropicBackend(InferenceBackend):
    def __init__(self, model: str, api_key: str = None, key_file=None, client=None):
        self._model = model
        self._client = client or anthropic.Anthropic(api_key=api_key or load_api_key(key_file))
        self._runtime = condition_pb2.RuntimeSpec(
            backend=condition_pb2.BACKEND_REMOTE_ENDPOINT,
            device="api",
            host="anthropic",
            backend_version=f"anthropic-sdk-{anthropic.__version__}",
        )

    def runtime(self) -> condition_pb2.RuntimeSpec:
        return self._runtime

    def capabilities(self) -> Capabilities:
        return Capabilities(
            supports_seed=False,
            supports_tools=False,
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
            raise CapabilityError("the Anthropic API backend does not capture activations")
        if affordances:
            raise CapabilityError("tool affordances are not implemented on this backend")
        sampling = sampling or condition_pb2.SamplingSpec()
        if sampling.seed or sampling.temperature or sampling.top_p:
            raise CapabilityError(
                "seed/temperature/top_p are not supported on current Anthropic API "
                "models; leave them at proto-default zero"
            )

        system_parts = [m.content for m in messages if m.role == "system"]
        chat = [
            {"role": m.role, "content": m.content}
            for m in messages
            if m.role in ("user", "assistant")
        ]
        request = {
            "model": self._model,
            "max_tokens": sampling.max_tokens or 8000,
            "messages": chat,
            "betas": [FALLBACK_BETA],
            "extra_body": {"fallbacks": "default"},
        }
        if system_parts:
            request["system"] = "\n\n".join(system_parts)

        response = self._client.beta.messages.create(**request)

        text = ""
        if response.stop_reason != "refusal":
            text = "".join(
                block.text for block in response.content if block.type == "text"
            )
        message = transcript_pb2.Message(role="assistant", content=text)
        usage = transcript_pb2.TokenUsage(
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens,
        )
        actual = condition_pb2.SamplingSpec()
        actual.CopyFrom(sampling)
        actual.seed_honored = False
        return GenerationResult(message=message, usage=usage, sampling_actual=actual)
