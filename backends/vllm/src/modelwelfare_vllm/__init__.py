"""vLLM server backend — the controlled quantization ladder's serving arm.

Tier 1 only over this client: vLLM speaks the chat protocol, so no
activations. Tier 2 hooks the same checkpoints in transformers instead.
"""

from modelwelfare_vllm.client import VllmServerBackend

__all__ = ["VllmServerBackend"]
