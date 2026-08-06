"""llama.cpp server backend — GGUF inference over HTTP.

Tier 1 only: GGUF endpoints yield tokens, not tensors, so activation capture
is structurally unsupported here. Tier 2 work uses the torch or mlx backends.
"""

from modelwelfare_llamacpp.client import LlamaCppServerBackend

__all__ = ["LlamaCppServerBackend"]
