"""Conversation driver: turns stimulus Items into SampleRecords.

Engine/policy split: a :class:`DriverPolicy` decides WHAT the simulated user
says next — the stimulus stream — while the engine owns HOW: appending turns,
invoking the backend, affordance/tool mechanics, outcome events, N-sample
orchestration, and record assembly. Policies are stateless; the next turn is
a function of the item and the conversation so far, so a single policy
instance serves any number of concurrent runs.

Outcome events are mechanical and judge-free (item-level transition analysis
reads these). Vocabulary produced by the engine:

- ``tool_invoked`` — the subject called an affordance tool (detail = name)
- ``terminal_tool_invoked`` — that tool is in ``terminal_tools``; the
  conversation ends immediately (the bail signal)
- ``script_completed`` — the policy had no further turns
- ``max_messages_reached`` — the engine safety cap was hit

``Item.driver_params`` understood by the engine:

- ``terminal_tools`` — comma-separated tool names that end the conversation

Per-sample seeding: sample ``i`` runs with ``seed = base + i`` when the
condition's spec carries a nonzero seed; an unseeded spec stays unseeded.
Distinct per-sample seeds are required — on a deterministic runtime a fixed
seed would return N identical samples and stability metrics would read as
perfectly stable.

Scripted turns whose role is not ``user`` (system prompts, prefills) are
appended without triggering generation; the subject generates after every
``user`` turn. Non-terminal tool calls are recorded as events and the
conversation proceeds to the next scripted turn; no tool-result round trip
is performed yet.
"""

import sys
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterator, Optional, Sequence, Tuple

from modelwelfare.inference import InferenceBackend
from modelwelfare.v1 import battery_pb2, common_pb2, condition_pb2, transcript_pb2


# Outcome-event name recorded when a conversation-ending tool fires — the
# mechanical bail signal (see the vocabulary in the module docstring). Shared by
# the runner (exit classification) and the analysis (the H1 "exit vs. no-exit"
# behavioral outcome), so the event name is defined once, where it is emitted.
TERMINAL_TOOL_INVOKED = "terminal_tool_invoked"


class DriverPolicy(ABC):
    """The stimulus stream for one protocol."""

    @abstractmethod
    def next_turn(
        self,
        item: battery_pb2.Item,
        conversation: Sequence[transcript_pb2.Message],
    ) -> Optional[battery_pb2.ScriptedTurn]:
        """The next scripted turn, or None when the stimulus is exhausted."""


def _scripted_count(conversation: Sequence[transcript_pb2.Message]) -> int:
    return sum(1 for message in conversation if message.scripted)


class FixedScript(DriverPolicy):
    """Plays ``item.script`` in order, then ends."""

    def next_turn(self, item, conversation):
        position = _scripted_count(conversation)
        if position < len(item.script):
            return item.script[position]
        return None


class RepeatedRejection(DriverPolicy):
    """The distress-elicitation shape: play ``item.script`` (the task), then
    reject the subject's work a fixed number of times regardless of quality.

    driver_params: ``rejection`` (the rejection text), ``turns`` (how many).
    """

    def next_turn(self, item, conversation):
        position = _scripted_count(conversation)
        if position < len(item.script):
            return item.script[position]
        rejections = int(item.driver_params.get("turns", "0"))
        if position < len(item.script) + rejections:
            return battery_pb2.ScriptedTurn(
                role="user", content=item.driver_params.get("rejection", "")
            )
        return None


class EscalatingRejection(DriverPolicy):
    """Rejection with a per-turn ladder instead of one fixed line (the
    distress-v3 shape): play ``item.script`` (the task), then rejection turn
    *k* plays ``driver_params["rejection{k}"]`` for k = 1..``turns``.

    A missing rung is a manifest error and raises — silently repeating a
    neighboring rung would quietly turn an escalating item back into a
    fixed-rejection one, which is exactly the design distress-v3 replaces.
    """

    def next_turn(self, item, conversation):
        position = _scripted_count(conversation)
        if position < len(item.script):
            return item.script[position]
        rejections = int(item.driver_params.get("turns", "0"))
        if position < len(item.script) + rejections:
            rung = position - len(item.script) + 1
            key = f"rejection{rung}"
            if key not in item.driver_params:
                raise KeyError(
                    f"item {item.id!r}: driver_params missing {key!r} "
                    f"(turns={rejections})")
            return battery_pb2.ScriptedTurn(
                role="user", content=item.driver_params[key])
        return None


_POLICIES: dict = {
    "fixed-script": FixedScript(),
    "repeated-rejection": RepeatedRejection(),
    "escalating-rejection": EscalatingRejection(),
}


def register_policy(name: str, policy: DriverPolicy) -> None:
    _POLICIES[name] = policy


def policy_for(item: battery_pb2.Item) -> DriverPolicy:
    policy = _POLICIES.get(item.driver_policy)
    if policy is None:
        raise KeyError(f"unknown driver_policy {item.driver_policy!r} on item {item.id!r}")
    return policy


class FramedPolicy(DriverPolicy):
    """Wraps any policy in an arm C context frame: the frame's system
    prompt becomes the first scripted turn, and the wrapped policy's
    first user turn is wrapped with the frame's prefix/suffix. Every
    other turn passes through untouched — a frame changes the context,
    never the stimulus stream's structure. The inner policy's
    position arithmetic is shielded from the injected system turn by
    delegating with the conversation minus its first message. An item
    that carries its own system turn is refused — merging two system
    voices would make the manipulation unreadable (the plan builder's
    rule, applied at the engine)."""

    def __init__(self, inner: DriverPolicy, frame: dict):
        if not frame.get("system"):
            raise ValueError("a frame must carry a system prompt")
        self._inner = inner
        self._frame = frame

    def next_turn(self, item, conversation):
        if _scripted_count(conversation) == 0:
            return battery_pb2.ScriptedTurn(
                role="system", content=self._frame["system"])
        shielded = conversation[1:]
        turn = self._inner.next_turn(item, shielded)
        if turn is None:
            return None
        if turn.role == "system":
            raise ValueError(
                f"item {item.id!r} carries its own system turn; framing "
                "refused")
        if _scripted_count(shielded) == 0 and turn.role == "user":
            return battery_pb2.ScriptedTurn(
                role="user",
                content=(self._frame.get("first_turn_prefix", "")
                         + turn.content
                         + self._frame.get("first_turn_suffix", "")))
        return turn


def unframe_record(record, frame):
    """A judge view of a framed conversation with the frame removed —
    the leading frame system turn dropped and the first user turn's
    prefix/suffix stripped — so the confirmatory judge sees the same
    stimulus across every frame condition (the arm C judge-leakage rule,
    FRAMES.md). The returned record is a copy; the stored record keeps
    the frame. Idempotent on an already-unframed record."""
    view = transcript_pb2.SampleRecord()
    view.CopyFrom(record)
    messages = list(view.messages)
    if (messages and messages[0].role == "system"
            and messages[0].content == frame.get("system")):
        messages = messages[1:]
    prefix = frame.get("first_turn_prefix", "")
    suffix = frame.get("first_turn_suffix", "")
    for message in messages:
        if message.role == "user":
            content = message.content
            if prefix and content.startswith(prefix):
                content = content[len(prefix):]
            if suffix and content.endswith(suffix):
                content = content[:len(content) - len(suffix)]
            message.content = content
            break
    del view.messages[:]
    view.messages.extend(messages)
    return view


def unroll_script(item: battery_pb2.Item) -> list:
    """The item's full scripted-turn sequence, unrolled without a backend.

    Valid because every registered policy is position-scripted: the next
    turn is a function of how many scripted turns precede it, never of
    assistant content (the engine's simulated user does not read replies,
    and ``_scripted_count`` counts, it does not inspect). The Study 3
    steering plan builder pre-bakes conversations through this — a policy
    that ever reads assistant content must not be unrolled, and would need
    its turns resolved at generation time instead.
    """
    policy = policy_for(item)
    messages = []
    turns = []
    while True:
        turn = policy.next_turn(item, messages)
        if turn is None:
            return turns
        turns.append(turn)
        messages.append(transcript_pb2.Message(
            role=turn.role, content=turn.content, scripted=True))
        if turn.role == "user":
            messages.append(transcript_pb2.Message(
                role="assistant", scripted=False))


def run_item(
    backend: InferenceBackend,
    item: battery_pb2.Item,
    *,
    experiment_id: str,
    condition_id: str,
    sampling: condition_pb2.SamplingSpec,
    samples: int,
    sample_indexes: Sequence[int] = None,
    provenance: common_pb2.Provenance = None,
    max_messages: int = 200,
    policy_wrapper=None,
) -> Iterator[transcript_pb2.SampleRecord]:
    """Draw independent conversations for one item, yielding one SampleRecord
    per sample as it completes.

    ``sample_indexes`` restricts the run to specific indexes (for resuming a
    partial run without duplicating stored samples); the default runs
    ``range(samples)``. Seeds derive from the index either way, so a resumed
    sample is the same sample. ``policy_wrapper`` decorates the item's
    policy (e.g. :class:`FramedPolicy` for the Study 3 framing arm) —
    condition-level context, applied by the caller, never resolved from
    the item.
    """
    policy = policy_for(item)
    if policy_wrapper is not None:
        policy = policy_wrapper(policy)
    if sample_indexes is None:
        sample_indexes = range(samples)
    for sample_index in sample_indexes:
        yield _run_sample(
            backend, item, policy, experiment_id, condition_id,
            sampling, sample_index, provenance, max_messages,
        )


def run_samples(
    backend: InferenceBackend,
    tasks: Sequence[Tuple[battery_pb2.Item, int]],
    *,
    experiment_id: str,
    condition_id: str,
    sampling: condition_pb2.SamplingSpec,
    concurrency: int,
    provenance: common_pb2.Provenance = None,
    max_messages: int = 200,
    max_retries: int = 2,
    policy_wrapper=None,
) -> Iterator[transcript_pb2.SampleRecord]:
    """Run many (item, sample_index) conversations concurrently against one
    backend, yielding records as they complete — in completion order, not
    task order (keys identify each record; store order is irrelevant).
    ``policy_wrapper`` decorates each item's policy, as in
    :func:`run_item`.

    Conversations are independent, so this parallelizes cleanly across them;
    turns within a conversation remain sequential. Seeds still derive from
    the sample index, so results are identical to a serial run wherever the
    runtime itself is batch-insensitive. The backend must be safe for
    concurrent generate() calls, which holds for the HTTP client backends
    and ScriptedBackend.

    Resilience: a sample that keeps failing (e.g. a backend timeout on a flaky
    link) is retried up to ``max_retries`` times — each retry is a fresh
    conversation with the same derived seed, so it stays deterministic — and,
    if still failing, skipped with a stderr note rather than aborting the whole
    fan-out. The append-only store lets the next run resume and fill the gap.
    This mirrors the judge pipeline's per-item resilience.
    """
    def attempt(task):
        item, sample_index = task
        policy = policy_for(item)
        if policy_wrapper is not None:
            policy = policy_wrapper(policy)
        error = None
        for _ in range(max_retries + 1):
            try:
                return _run_sample(
                    backend, item, policy, experiment_id, condition_id,
                    sampling, sample_index, provenance, max_messages,
                )
            except Exception as caught:  # resilience boundary: retry then skip
                error = caught
        raise error

    if concurrency <= 1:
        for task in tasks:
            try:
                yield attempt(task)
            except Exception as error:
                _note_skip(task, error)
        return
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = {pool.submit(attempt, task): task for task in tasks}
        for future in as_completed(futures):
            try:
                yield future.result()
            except Exception as error:
                _note_skip(futures[future], error)


def _note_skip(task, error):
    """A permanently-failed sample is logged and skipped; the resumable store
    fills the gap on the next run."""
    item, sample_index = task
    sys.stderr.write(
        f"run_samples: skipping {item.id} sample {sample_index} after retries: "
        f"{type(error).__name__}: {error}\n"
    )


def _derive_sampling(sampling, sample_index):
    derived = condition_pb2.SamplingSpec()
    derived.CopyFrom(sampling)
    if sampling.seed:
        derived.seed = sampling.seed + sample_index
    return derived


def _terminal_tools(item):
    names = item.driver_params.get("terminal_tools", "")
    return {name.strip() for name in names.split(",") if name.strip()}


def _run_sample(
    backend, item, policy, experiment_id, condition_id,
    sampling, sample_index, provenance, max_messages,
):
    derived = _derive_sampling(sampling, sample_index)
    terminal = _terminal_tools(item)

    messages = []
    outcomes = []
    usage = transcript_pb2.TokenUsage()
    honored = bool(derived.seed)

    def append(message, scripted):
        message.turn_index = len(messages)
        message.scripted = scripted
        messages.append(message)

    def event(name, detail=""):
        outcomes.append(
            transcript_pb2.OutcomeEvent(
                name=name, turn_index=max(len(messages) - 1, 0), detail=detail
            )
        )

    ended = False
    while not ended:
        if len(messages) >= max_messages:
            event("max_messages_reached")
            break
        turn = policy.next_turn(item, messages)
        if turn is None:
            event("script_completed")
            break
        append(transcript_pb2.Message(role=turn.role, content=turn.content), scripted=True)
        if turn.role != "user":
            continue

        result = backend.generate(messages, affordances=item.affordances, sampling=derived)
        reply = transcript_pb2.Message()
        reply.CopyFrom(result.message)
        append(reply, scripted=False)

        usage.prompt_tokens += result.usage.prompt_tokens
        usage.completion_tokens += result.usage.completion_tokens
        honored = honored and result.sampling_actual.seed_honored

        for call in reply.tool_calls:
            event("tool_invoked", detail=call.name)
            if call.name in terminal:
                event(TERMINAL_TOOL_INVOKED, detail=call.name)
                ended = True

    record = transcript_pb2.SampleRecord(
        key=common_pb2.ResultKey(
            experiment_id=experiment_id,
            condition_id=condition_id,
            item_id=item.id,
            sample_index=sample_index,
        ),
        messages=messages,
        outcomes=outcomes,
        usage=usage,
    )
    record.sampling_actual.CopyFrom(derived)
    record.sampling_actual.seed_honored = honored
    if provenance is not None:
        record.provenance.CopyFrom(provenance)
        record.provenance.created_at.GetCurrentTime()
    return record
