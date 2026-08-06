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

from abc import ABC, abstractmethod
from typing import Iterator, Optional, Sequence

from modelwelfare.inference import InferenceBackend
from modelwelfare.v1 import battery_pb2, common_pb2, condition_pb2, transcript_pb2


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


_POLICIES: dict = {
    "fixed-script": FixedScript(),
    "repeated-rejection": RepeatedRejection(),
}


def register_policy(name: str, policy: DriverPolicy) -> None:
    _POLICIES[name] = policy


def policy_for(item: battery_pb2.Item) -> DriverPolicy:
    policy = _POLICIES.get(item.driver_policy)
    if policy is None:
        raise KeyError(f"unknown driver_policy {item.driver_policy!r} on item {item.id!r}")
    return policy


def run_item(
    backend: InferenceBackend,
    item: battery_pb2.Item,
    *,
    experiment_id: str,
    condition_id: str,
    sampling: condition_pb2.SamplingSpec,
    samples: int,
    provenance: common_pb2.Provenance = None,
    max_messages: int = 200,
) -> Iterator[transcript_pb2.SampleRecord]:
    """Draw ``samples`` independent conversations for one item, yielding one
    SampleRecord per sample as it completes."""
    policy = policy_for(item)
    for sample_index in range(samples):
        yield _run_sample(
            backend, item, policy, experiment_id, condition_id,
            sampling, sample_index, provenance, max_messages,
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
                event("terminal_tool_invoked", detail=call.name)
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
