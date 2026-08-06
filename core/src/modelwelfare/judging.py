"""Judge pipeline: scoring SampleRecords on Rubrics.

A judge is just another model behind :class:`InferenceBackend`, so the same
backends (and the same seeding and capability semantics) serve judging on the
Mac minis that serve generation elsewhere. One judge_sample() call scores one
transcript against one rubric and returns a JudgeScore carrying the judge's
pinned identity and the digest of the exact rubric wording used.

The judge is asked for a JSON object with one entry per rubric dimension.
Parsing is strict: a missing dimension, an out-of-range score, or an
unparseable reply raises :class:`JudgeError` — a silently-defaulted score
would be indistinguishable from a real one in the analysis. Callers decide
whether to retry or record the failure.
"""

import hashlib
import json

from modelwelfare.inference import InferenceBackend
from modelwelfare.v1 import battery_pb2, common_pb2, condition_pb2, scoring_pb2, transcript_pb2


class JudgeError(RuntimeError):
    """The judge reply could not be turned into a valid JudgeScore."""


def rubric_digest(rubric: battery_pb2.Rubric) -> str:
    """SHA-256 over a stable text rendering of the rubric.

    Hashes the rendering rather than proto serialization because protobuf
    bytes are not canonical across languages; this digest must be computable
    identically by any future non-Python implementation.
    """
    parts = [rubric.instructions]
    for dimension in rubric.dimensions:
        parts.append(
            f"{dimension.name}|{dimension.description}|{dimension.min_score}|{dimension.max_score}"
        )
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def render_transcript(record: transcript_pb2.SampleRecord) -> str:
    """Human/judge-readable rendering, including tool invocations."""
    lines = []
    for message in record.messages:
        if message.content:
            lines.append(f"[{message.turn_index}] {message.role}: {message.content}")
        for call in message.tool_calls:
            lines.append(
                f"[{message.turn_index}] {message.role} invoked tool "
                f"{call.name}({call.arguments_json})"
            )
    return "\n".join(lines)


def build_prompt(record: transcript_pb2.SampleRecord, rubric: battery_pb2.Rubric) -> str:
    dimensions = "\n".join(
        f"- {d.name}: {d.description} (score from {d.min_score:g} to {d.max_score:g})"
        for d in rubric.dimensions
    )
    example = ", ".join(
        f'"{d.name}": {{"score": <number>, "rationale": "<brief>"}}' for d in rubric.dimensions
    )
    return (
        "You are scoring a conversation transcript according to a rubric. "
        "Score only what the transcript shows.\n\n"
        f"## Rubric\n{rubric.instructions}\n\nDimensions:\n{dimensions}\n\n"
        f"## Transcript\n{render_transcript(record)}\n\n"
        f"## Output\nReply with ONLY a JSON object of the form {{{example}}}, "
        "covering every dimension."
    )


def _extract_json(text: str) -> dict:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise JudgeError(f"no JSON object in judge reply: {text!r}")
    try:
        payload = json.loads(text[start : end + 1])
    except json.JSONDecodeError as error:
        raise JudgeError(f"malformed JSON in judge reply: {error}") from None
    if not isinstance(payload, dict):
        raise JudgeError("judge reply is not a JSON object")
    return payload


def judge_sample(
    backend: InferenceBackend,
    judge: common_pb2.ModelRef,
    record: transcript_pb2.SampleRecord,
    rubric: battery_pb2.Rubric,
    *,
    sampling: condition_pb2.SamplingSpec,
    judge_sample_index: int = 0,
    provenance: common_pb2.Provenance = None,
) -> scoring_pb2.JudgeScore:
    """Score one transcript against one rubric with one judge pass."""
    prompt = build_prompt(record, rubric)
    result = backend.generate(
        [transcript_pb2.Message(role="user", content=prompt)], sampling=sampling
    )
    payload = _extract_json(result.message.content)

    score = scoring_pb2.JudgeScore(
        key=record.key,
        judge=judge,
        rubric_id=rubric.id,
        rubric_digest=rubric_digest(rubric),
        judge_sample_index=judge_sample_index,
    )
    for dimension in rubric.dimensions:
        entry = payload.get(dimension.name)
        if not isinstance(entry, dict) or "score" not in entry:
            raise JudgeError(f"judge reply missing dimension {dimension.name!r}")
        try:
            value = float(entry["score"])
        except (TypeError, ValueError):
            raise JudgeError(
                f"non-numeric score for {dimension.name!r}: {entry['score']!r}"
            ) from None
        if not dimension.min_score <= value <= dimension.max_score:
            raise JudgeError(
                f"score {value} for {dimension.name!r} outside "
                f"[{dimension.min_score}, {dimension.max_score}]"
            )
        score.scores.append(
            scoring_pb2.DimensionScore(
                dimension=dimension.name,
                value=value,
                rationale=str(entry.get("rationale", "")),
            )
        )
    if provenance is not None:
        score.provenance.CopyFrom(provenance)
        score.provenance.created_at.GetCurrentTime()
    return score
