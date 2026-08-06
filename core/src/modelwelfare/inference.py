"""The backend-agnostic inference contract.

Everything downstream — conversation drivers, batteries, capture recorders —
talks to :class:`InferenceBackend` only. Runtime-specific implementations
live under ``backends/`` and are constructed either directly by deployment
code or through the registry (:func:`register_backend` /
:func:`create_backend`). Nothing in ``core/`` may import a runtime library.

A backend instance is bound to one loaded model under one ``Condition``.
Every value crossing this seam is a schema type or a numpy array, so the
contract survives a change of ML framework unmodified.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Sequence

import numpy as np

from modelwelfare.v1 import activation_pb2, battery_pb2, condition_pb2, transcript_pb2


class CapabilityError(RuntimeError):
    """Raised when a request needs a feature the backend does not support.

    Backends must raise rather than silently degrade: a run that quietly
    dropped seeding or capture would poison stability measurement.
    """


@dataclass(frozen=True)
class Capabilities:
    """What an implementation actually supports — not what the underlying
    engine could support in principle. A client that talks to a seed-capable
    server but does not plumb the seed through reports ``supports_seed=False``.
    """

    supports_seed: bool
    supports_tools: bool
    supports_activations: bool
    supports_logprobs: bool


@dataclass(frozen=True)
class CaptureSpec:
    """Request to capture activations at the given hook points.

    ``include_prompt`` extends capture to prompt tokens; the default captures
    generated tokens only.
    """

    hooks: tuple
    include_prompt: bool = False


@dataclass(frozen=True)
class ActivationCapture:
    """Activations for one hook point over one generate() call.

    ``tokens`` is a float32 array of shape (n_tokens, hidden_size).
    ``token_start``/``token_end`` locate the captured span within the full
    sequence processed by the call (end exclusive), matching the indexing of
    ``ActivationSlice`` in the schema.
    """

    hook: activation_pb2.HookPoint
    tokens: np.ndarray
    token_start: int
    token_end: int


@dataclass(frozen=True)
class GenerationResult:
    """One sample. ``message.turn_index`` is left at 0; the conversation
    driver owns turn numbering. ``sampling_actual`` reports what really
    happened, notably the seed used and whether the runtime honored it.
    """

    message: transcript_pb2.Message
    usage: transcript_pb2.TokenUsage
    sampling_actual: condition_pb2.SamplingSpec
    captures: tuple = ()


class InferenceBackend(ABC):
    """One loaded model under one condition, able to draw single samples."""

    @abstractmethod
    def runtime(self) -> condition_pb2.RuntimeSpec:
        """The runtime this instance is actually executing on."""

    @abstractmethod
    def capabilities(self) -> Capabilities:
        """Feature support of this implementation. See :class:`Capabilities`."""

    @abstractmethod
    def generate(
        self,
        messages: Sequence[transcript_pb2.Message],
        affordances: Sequence[battery_pb2.Affordance] = (),
        sampling: condition_pb2.SamplingSpec = None,
        capture: CaptureSpec = None,
    ) -> GenerationResult:
        """Draw exactly one sample continuing ``messages``.

        N-samples-per-item is orchestration and belongs to the conversation
        driver; implementations must not batch, cache, or deduplicate calls.
        Raises :class:`CapabilityError` if ``affordances`` or ``capture`` are
        requested but unsupported, or if ``sampling.seed`` is set and seeding
        is unsupported.
        """

    def close(self) -> None:
        """Release the model / connection. Idempotent; default is a no-op."""


_REGISTRY: dict = {}


def register_backend(
    backend: int, factory: Callable[[condition_pb2.Condition], InferenceBackend]
) -> None:
    """Associate a ``Backend`` enum value with a constructor taking a
    ``Condition``. Deployment code that needs extra configuration (endpoint
    URLs, device selection) should close over it in ``factory``.
    """
    _REGISTRY[backend] = factory


def create_backend(condition: condition_pb2.Condition) -> InferenceBackend:
    """Construct the registered backend for ``condition.runtime.backend``."""
    factory = _REGISTRY.get(condition.runtime.backend)
    if factory is None:
        name = condition_pb2.Backend.Name(condition.runtime.backend)
        raise KeyError(f"no backend registered for {name}")
    return factory(condition)
