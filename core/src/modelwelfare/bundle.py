"""Portable RecordBundle containers over the streaming result store.

The streaming :class:`~modelwelfare.store.ResultStore` is the write-time format —
resumable, durable, concurrent. A :class:`RecordBundle` is the shareable at-rest
form: one self-describing protobuf file holds every record for a condition (or a
whole experiment when it fits under protobuf's ~2GB limit), so a report can be
replicated from a single ``.pb``. ``pack`` consolidates the streaming store into
bundles; :class:`BundleStore` reads them back through the same ``read`` interface
``analyze``/``report`` already use, so nothing downstream changes.

The bundle's ``data_digest`` is populated from :mod:`modelwelfare.signature` when
that module is importable, and left empty otherwise; the digest is content-based
(see that module) so it is identical whether computed over the streaming store or
a bundle.
"""

from collections import defaultdict
from pathlib import Path

from modelwelfare.store import ResultStore
from modelwelfare.v1 import bundle_pb2, scoring_pb2, transcript_pb2

# Store kind -> (RecordBundle repeated-field name, record message type).
KINDS = {
    "samples": ("samples", transcript_pb2.SampleRecord),
    "scores": ("scores", scoring_pb2.JudgeScore),
    "exit_reasons": ("exit_reasons", scoring_pb2.ExitClassification),
    "reference_scores": ("reference_scores", scoring_pb2.JudgeScore),
}


def _stamp_digest(bundle) -> None:
    """Fill ``metadata.data_digest`` with the value a report cites (see
    :mod:`modelwelfare.signature`), computed over the report-determining kinds so
    a whole-experiment bundle's digest equals the report's. No-op if the
    signature module is unavailable."""
    try:
        from modelwelfare import signature
    except ImportError:
        return
    records_by_kind = {
        name: list(getattr(bundle, KINDS[name][0]))
        for name, _message_type in signature.DEFAULT_KINDS
    }
    bundle.metadata.data_digest = signature.records_digest(records_by_kind)


def pack_condition(store: ResultStore, experiment_id: str, condition_id: str) -> bundle_pb2.RecordBundle:
    """Build a one-condition bundle by draining the streaming store's kinds."""
    bundle = bundle_pb2.RecordBundle()
    bundle.metadata.experiment_id = experiment_id
    bundle.metadata.condition_id = condition_id
    for kind, (field, message_type) in KINDS.items():
        records = list(store.read(message_type, experiment_id, condition_id, kind))
        if records:
            getattr(bundle, field).extend(records)
            bundle.metadata.record_counts[kind] = len(records)
    _stamp_digest(bundle)
    return bundle


def pack_experiment(store: ResultStore, experiment) -> bundle_pb2.RecordBundle:
    """Build one whole-experiment bundle (``condition_id`` empty) — the single-file
    shareable artifact whose ``data_digest`` equals the report's cited digest."""
    bundle = bundle_pb2.RecordBundle()
    bundle.metadata.experiment_id = experiment.id
    for kind, (field, message_type) in KINDS.items():
        records = [
            record
            for condition in experiment.conditions
            for record in store.read(message_type, experiment.id, condition.id, kind)
        ]
        if records:
            getattr(bundle, field).extend(records)
            bundle.metadata.record_counts[kind] = len(records)
    _stamp_digest(bundle)
    return bundle


def write_bundle(bundle: bundle_pb2.RecordBundle, path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bundle.SerializeToString())


def read_bundle(path) -> bundle_pb2.RecordBundle:
    bundle = bundle_pb2.RecordBundle()
    bundle.ParseFromString(Path(path).read_bytes())
    return bundle


def pack(store: ResultStore, experiment, out_dir) -> list:
    """Write one bundle per condition under ``out_dir`` (named ``<condition>.pb``).
    Returns the written paths."""
    out_dir = Path(out_dir)
    written = []
    for condition in experiment.conditions:
        bundle = pack_condition(store, experiment.id, condition.id)
        path = out_dir / f"{condition.id}.pb"
        write_bundle(bundle, path)
        written.append(path)
    return written


class BundleStore:
    """Reads packed bundles through the :class:`ResultStore` ``read`` interface.

    ``path`` is a single ``.pb`` file or a directory of them (merged, as the
    StateDictionary loader merges a directory). Records are indexed at load by
    (experiment_id, condition_id, kind), so ``read`` is a keyed lookup that scopes
    exactly like the streaming store — a directory mixing experiments or
    conditions never leaks across scopes, and reads do not rescan the data. An
    experiment_id absent from a record's key falls back to the bundle's own
    metadata."""

    def __init__(self, path):
        path = Path(path)
        self._index = defaultdict(list)
        paths = [path] if path.is_file() else sorted(path.glob("*.pb"))
        for bundle_path in paths:
            bundle = read_bundle(bundle_path)
            experiment_id = bundle.metadata.experiment_id
            for kind, (field, _type) in KINDS.items():
                for record in getattr(bundle, field):
                    key = (record.key.experiment_id or experiment_id, record.key.condition_id, kind)
                    self._index[key].append(record)

    def read(self, message_type, experiment_id: str, condition_id: str, kind: str):
        return iter(self._index.get((experiment_id, condition_id, kind), ()))
