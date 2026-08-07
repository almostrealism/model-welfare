"""llama.cpp wrapper over the shared OpenAI-compatible protocol client.

A llama.cpp server serves exactly one GGUF artifact, so no model name is sent;
the server must be launched with the intended model already loaded. Which
artifact runs where is deployment configuration, described by the ``runtime``
spec passed in. Seeding is per-request and was verified deterministic against
a live server (see tests/test_live.py).
"""

from modelwelfare.inference import Capabilities
from modelwelfare.openai_chat import OpenAiChatBackend
from modelwelfare.v1 import condition_pb2


class LlamaCppServerBackend(OpenAiChatBackend):
    def __init__(
        self,
        base_url: str,
        runtime: condition_pb2.RuntimeSpec,
        transport=None,
        timeout: float = 300.0,
    ):
        super().__init__(
            base_url,
            runtime,
            Capabilities(
                supports_seed=True,
                supports_tools=True,
                supports_activations=False,
                supports_logprobs=False,
            ),
            transport=transport,
            timeout=timeout,
        )
