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


def pack_condition(store: ResultStore, experiment_id: str, condition_id: str) -> bundle_pb2.RecordBundle:
    """Build a one-condition bundle by draining the streaming store's kinds.

    ``metadata.data_digest`` is left empty here; it is stamped once the
    signature module is present, from a shared records-based digest so the
    embedded value equals the one a report cites over the same records."""
    bundle = bundle_pb2.RecordBundle()
    bundle.metadata.experiment_id = experiment_id
    bundle.metadata.condition_id = condition_id
    for kind, (field, message_type) in KINDS.items():
        records = list(store.read(message_type, experiment_id, condition_id, kind))
        if records:
            getattr(bundle, field).extend(records)
            bundle.metadata.record_counts[kind] = len(records)
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
    StateDictionary loader merges a directory). ``read`` filters by condition and
    kind, so it serves both per-condition and whole-experiment bundles."""

    def __init__(self, path):
        path = Path(path)
        self._by_kind = defaultdict(list)
        paths = [path] if path.is_file() else sorted(path.glob("*.pb"))
        for bundle_path in paths:
            bundle = read_bundle(bundle_path)
            for kind, (field, _type) in KINDS.items():
                self._by_kind[kind].extend(getattr(bundle, field))

    def read(self, message_type, experiment_id: str, condition_id: str, kind: str):
        for record in self._by_kind.get(kind, []):
            if record.key.condition_id == condition_id:
                yield record
