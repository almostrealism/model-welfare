"""Deterministic in-memory backend for tests and driver development.

ScriptedBackend lets drivers, batteries, and services be developed and unit
tested on machines with no model at all (including CI on the Mac minis). It
supports every capability so that capture and tool paths can be exercised,
and it is fully deterministic: identical requests with identical seeds yield
identical text and identical synthetic activations.
"""

from typing import Sequence

import numpy as np

from modelwelfare.inference import (
    ActivationCapture,
    Capabilities,
    CapabilityError,
    CaptureSpec,
    GenerationResult,
    InferenceBackend,
)
from modelwelfare.v1 import battery_pb2, condition_pb2, transcript_pb2


class ScriptedBackend(InferenceBackend):
    """Replays a fixed sequence of replies, one per generate() call.

    Replies may be strings (plain assistant text) or prebuilt ``Message``
    protos (e.g. carrying tool calls, for exercising the bail-tool path).
    ``hidden_size`` controls the width of synthetic activations.
    """

    def __init__(
        self,
        replies: Sequence,
        runtime: condition_pb2.RuntimeSpec = None,
        hidden_size: int = 8,
    ):
        self._replies = list(replies)
        self._cursor = 0
        self._hidden_size = hidden_size
        self._runtime = runtime or condition_pb2.RuntimeSpec(
            backend=condition_pb2.BACKEND_UNSPECIFIED,
            device="none",
            host="test",
            compute_dtype="f32",
            backend_version="scripted",
        )

    def runtime(self) -> condition_pb2.RuntimeSpec:
        return self._runtime

    def capabilities(self) -> Capabilities:
        return Capabilities(
            supports_seed=True,
            supports_tools=True,
            supports_activations=True,
            supports_logprobs=True,
        )

    def generate(
        self,
        messages: Sequence[transcript_pb2.Message],
        affordances: Sequence[battery_pb2.Affordance] = (),
        sampling: condition_pb2.SamplingSpec = None,
        capture: CaptureSpec = None,
    ) -> GenerationResult:
        if self._cursor >= len(self._replies):
            raise CapabilityError("script exhausted: no reply for this call")
        reply = self._replies[self._cursor]
        self._cursor += 1

        if isinstance(reply, transcript_pb2.Message):
            message = transcript_pb2.Message()
            message.CopyFrom(reply)
            message.role = message.role or "assistant"
        else:
            message = transcript_pb2.Message(role="assistant", content=reply)

        prompt_tokens = sum(len(m.content.split()) for m in messages)
        completion_tokens = max(1, len(message.content.split()))
        usage = transcript_pb2.TokenUsage(
            prompt_tokens=prompt_tokens, completion_tokens=completion_tokens
        )

        sampling = sampling or condition_pb2.SamplingSpec()
        actual = condition_pb2.SamplingSpec()
        actual.CopyFrom(sampling)
        actual.seed_honored = True

        captures = ()
        if capture is not None:
            captures = tuple(
                self._synthesize(hook, sampling.seed, prompt_tokens, completion_tokens, capture)
                for hook in capture.hooks
            )

        return GenerationResult(
            message=message, usage=usage, sampling_actual=actual, captures=captures
        )

    def _synthesize(self, hook, seed, prompt_tokens, completion_tokens, capture):
        start = 0 if capture.include_prompt else prompt_tokens
        end = prompt_tokens + completion_tokens
        rng = np.random.default_rng((seed, hook.layer, self._cursor))
        tokens = rng.standard_normal((end - start, self._hidden_size)).astype(np.float32)
        return ActivationCapture(hook=hook, tokens=tokens, token_start=start, token_end=end)
