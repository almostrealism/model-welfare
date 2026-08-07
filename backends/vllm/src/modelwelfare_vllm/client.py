"""vLLM wrapper over the shared OpenAI-compatible protocol client.

Differences from llama.cpp that matter here: vLLM routes by the ``model``
field, so the served model name is a required constructor argument; and
per-request seeding interacts with engine state (prefix caching correlates
samples through the cache — the ladder servers disable it; see
services/vllm/README.md). seed_honored still reports what was requested;
determinism is verified per deployment by the live tests, not assumed.
"""

from modelwelfare.inference import Capabilities
from modelwelfare.openai_chat import OpenAiChatBackend
from modelwelfare.v1 import condition_pb2


class VllmServerBackend(OpenAiChatBackend):
    def __init__(
        self,
        base_url: str,
        model: str,
        runtime: condition_pb2.RuntimeSpec,
        transport=None,
        timeout: float = 300.0,
    ):
        if not model:
            raise ValueError("vLLM routes requests by model name; pass the served model name")
        super().__init__(
            base_url,
            runtime,
            Capabilities(
                supports_seed=True,
                supports_tools=True,
                supports_activations=False,
                supports_logprobs=False,
            ),
            model=model,
            transport=transport,
            timeout=timeout,
        )
