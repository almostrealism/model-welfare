"""llama.cpp wrapper over the shared OpenAI-compatible protocol client.

A llama.cpp server serves exactly one GGUF artifact, so no model name is sent;
the server must be launched with the intended model already loaded. Which
artifact runs where is deployment configuration, described by the ``runtime``
spec passed in. Seeding is per-request and was verified deterministic against
a live server (see tests/test_live.py).
"""

from modelwelfare.inference import Capabilities
from modelwelfare.openai_chat import OpenAiChatBackend, _urllib_get
from modelwelfare.v1 import condition_pb2


class LlamaCppServerBackend(OpenAiChatBackend):
    def __init__(
        self,
        base_url: str,
        runtime: condition_pb2.RuntimeSpec,
        transport=None,
        timeout: float = 300.0,
        fetch=None,
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
        self._props_url = base_url.rstrip("/") + "/props"
        self._fetch = fetch or _urllib_get(timeout)
        self._resolved_runtime = None

    def runtime(self) -> condition_pb2.RuntimeSpec:
        """The runtime spec with the server's own build filled in.

        The spec passed in names the deployment — host, device, compute dtype —
        and a llama.cpp server reports which build it is as ``build_info`` on
        ``/props``. A record stamped with this runtime therefore never carries
        an unknown build, and two builds never share a runtime identity, which
        the runner's resume check relies on. A spec that already names a
        ``backend_version`` is returned as given; otherwise the build is read
        once and kept, and a server that does not report one is refused rather
        than stamped unknown. The caller's spec is never mutated."""
        if self._resolved_runtime is None:
            spec = condition_pb2.RuntimeSpec()
            spec.CopyFrom(super().runtime())
            if not spec.backend_version:
                props = self._fetch(self._props_url)
                build = props.get("build_info") if isinstance(props, dict) else None
                if not build:
                    raise RuntimeError(
                        f"{self._props_url} did not report build_info; refusing to "
                        f"stamp records with a runtime of unknown build"
                    )
                spec.backend_version = build
            self._resolved_runtime = spec
        return self._resolved_runtime
