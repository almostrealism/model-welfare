"""Canonical content signature for a result store (replication integrity).

A layout- and order-independent SHA-256 over the *report-determining* record
content, so the value is stable no matter how the records are split across files
(the streaming store today, a consolidated bundle tomorrow) or in what order
they were written. A report states the digest; anyone holding the data confirms
they have the right, uncorrupted dataset by recomputing it.

Two deliberate choices keep the digest meaningful:

  * Records are hashed independently, then the per-record hashes are sorted and
    combined — so write order and file layout do not affect the result.
  * ``provenance`` (host, timestamp, framework version) is cleared before
    hashing. It records *who/when* collected the data, affects no endpoint, and
    would otherwise make identical data collected on two machines hash
    differently. Everything the analysis reads — messages, outcomes, sampling,
    token usage, scores, exit reasons — is included.
"""

import hashlib

from modelwelfare.store import ResultStore  # noqa: F401 — re-exported for callers
from modelwelfare.v1 import scoring_pb2, transcript_pb2

# The record streams that determine the confirmatory report, with their types.
DEFAULT_KINDS = (
    ("samples", transcript_pb2.SampleRecord),
    ("scores", scoring_pb2.JudgeScore),
    ("exit_reasons", scoring_pb2.ExitClassification),
)


def _canonical_bytes(record) -> bytes:
    """Deterministic serialization of one record with provenance stripped."""
    clone = type(record)()
    clone.CopyFrom(record)
    clone.ClearField("provenance")
    return clone.SerializeToString(deterministic=True)


def kind_digest(records) -> str:
    """Order-independent SHA-256 over a set of records of one kind. Each record
    is serialized canonically, the serializations are sorted, and hashed with a
    length prefix so no concatenation is ambiguous."""
    digest = hashlib.sha256()
    for payload in sorted(_canonical_bytes(record) for record in records):
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def store_digest(store: ResultStore, experiment_id: str, condition_ids, kinds=DEFAULT_KINDS) -> dict:
    """Per-kind digests, record counts, and a single combined digest over the
    whole dataset — the value a report cites for replication."""
    per_kind, counts = {}, {}
    for name, message_type in kinds:
        records = [
            record
            for condition_id in condition_ids
            for record in store.read(message_type, experiment_id, condition_id, name)
        ]
        counts[name] = len(records)
        per_kind[name] = kind_digest(records)
    combined = hashlib.sha256()
    for name in sorted(per_kind):
        combined.update(f"{name}={per_kind[name]}\n".encode())
    return {"digest": combined.hexdigest(), "per_kind": per_kind, "counts": counts}
