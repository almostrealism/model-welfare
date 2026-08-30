"""Portable RecordBundle containers over the streaming result store.

The streaming :class:`~modelwelfare.store.ResultStore` is the write-time format —
resumable, durable, concurrent. A :class:`RecordBundle` is the shareable at-rest
form: one self-describing protobuf file holds every record — including each
activation record's tensor, embedded via :func:`embed_bundle` — so a report can
be replicated from the ``.pb`` alone, with no side files. ``pack`` consolidates
the streaming store into bundles; :class:`BundleStore` reads them back through
the same ``read`` interface ``analyze``/``report`` already use, so nothing
downstream changes. A bundle larger than protobuf's ~2GB message bound is
written as sequential volumes (:func:`write_volumes`, :class:`VolumeWriter`)
that readers merge as a directory; splitting is transport, not structure.
``python3 -m modelwelfare.bundle`` is the end-user decomposition tool:
``inspect`` says what a file holds, ``extract`` restores the safetensors
workbench form for whatever subset is wanted.

The bundle's ``data_digest`` is populated from :mod:`modelwelfare.signature` when
that module is importable, and left empty otherwise; the digest is content-based
(see that module) so it is identical whether computed over the streaming store or
a bundle. A combined bundle (several experiments in one file) records each
experiment's digest in ``metadata.experiment_digests`` instead.
"""

from collections import defaultdict
from pathlib import Path

from modelwelfare import activations
from modelwelfare.activations import TENSOR_DIRECTORY
from modelwelfare.store import ResultStore
from modelwelfare.v1 import activation_pb2, bundle_pb2, scoring_pb2, transcript_pb2

# Volume cap: comfortably under protobuf's ~2GB message bound and GitHub's
# ~2GB release-asset bound.
VOLUME_BYTES = 1_800_000_000

# Store kind -> (RecordBundle repeated-field name, record message type).
KINDS = {
    "samples": ("samples", transcript_pb2.SampleRecord),
    "scores": ("scores", scoring_pb2.JudgeScore),
    "exit_reasons": ("exit_reasons", scoring_pb2.ExitClassification),
    "reference_scores": ("reference_scores", scoring_pb2.JudgeScore),
    "judge_noise_scores": ("judge_noise_scores", scoring_pb2.JudgeScore),
    "activations": ("activations", activation_pb2.ActivationSlice),
    "projections": ("projections", activation_pb2.ProjectionSeries),
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
    if not any(records_by_kind.values()):
        # Capture-only bundles (activation record kinds without any
        # report-determining stream) get no digest: stamping the constant
        # empty-kinds hash would make unrelated bundles look identical.
        return
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


def _pack_conditions(store: ResultStore, experiment_id: str, condition_ids) -> bundle_pb2.RecordBundle:
    bundle = bundle_pb2.RecordBundle()
    bundle.metadata.experiment_id = experiment_id
    for kind, (field, message_type) in KINDS.items():
        records = [
            record
            for condition_id in condition_ids
            for record in store.read(message_type, experiment_id, condition_id, kind)
        ]
        if records:
            getattr(bundle, field).extend(records)
            bundle.metadata.record_counts[kind] = len(records)
    _stamp_digest(bundle)
    return bundle


def pack_experiment(store: ResultStore, experiment) -> bundle_pb2.RecordBundle:
    """Build one whole-experiment bundle (``condition_id`` empty) — the single-file
    shareable artifact whose ``data_digest`` equals the report's cited digest."""
    return _pack_conditions(store, experiment.id, [c.id for c in experiment.conditions])


def pack_experiment_store(store: ResultStore, experiment_id: str) -> bundle_pb2.RecordBundle:
    """Build one whole-experiment bundle straight from the store layout — no
    manifest needed, so calibration stores without an experiment.textproto
    consolidate the same way. Raises ValueError if the experiment holds no
    conditions (an empty directory must not become an empty release asset) or
    if the store holds a record kind the bundle schema cannot carry: a
    consolidation must never silently drop a stream."""
    condition_ids = store.conditions(experiment_id)
    if not condition_ids:
        raise ValueError(f"{experiment_id}: no conditions in the store — nothing to pack")
    # The tensors directory is not a record stream: bundles carry the
    # activation *records*, and the safetensors they content-address travel
    # beside the bundle as sha-listed assets (activations module).
    unknown = {
        kind
        for condition_id in condition_ids
        for kind in store.kinds(experiment_id, condition_id)
        if kind not in KINDS and kind != TENSOR_DIRECTORY
    }
    if unknown:
        raise ValueError(
            f"{experiment_id}: store kinds {sorted(unknown)} are not representable "
            "in RecordBundle — add them to bundle.proto/KINDS before consolidating"
        )
    return _pack_conditions(store, experiment_id, condition_ids)


def pack_combined_store(store: ResultStore, experiment_ids) -> bundle_pb2.RecordBundle:
    """One bundle spanning several experiments — records carry their own
    keys, so ``metadata.experiment_id`` stays empty and readers scope by
    key exactly as with the streaming store. Each contained experiment's
    report-cited digest lands in ``metadata.experiment_digests``, so the
    combined file still confirms every report it carries. Refuses a record
    without an experiment id in its key: such a record would be unreachable
    once its bundle-level fallback is gone."""
    combined = bundle_pb2.RecordBundle()
    for experiment_id in experiment_ids:
        packed = pack_experiment_store(store, experiment_id)
        for kind, (field, _message_type) in KINDS.items():
            records = getattr(packed, field)
            if not records:
                continue
            for record in records:
                if not record.key.experiment_id:
                    raise ValueError(
                        f"{experiment_id}/{kind}: record without "
                        "key.experiment_id cannot enter a combined bundle")
            getattr(combined, field).extend(records)
            combined.metadata.record_counts[kind] = (
                combined.metadata.record_counts[kind] + len(records))
        if packed.metadata.data_digest:
            combined.metadata.experiment_digests[experiment_id] = (
                packed.metadata.data_digest)
    return combined


def embed_bundle(bundle: bundle_pb2.RecordBundle, root) -> int:
    """Embed every activation record's tensor from its capture file under
    ``root`` — the step that makes a bundle a single self-contained file.
    Returns the number of tensors embedded."""
    return activations.embed_tensor_data(bundle.activations, root)


def write_bundle(bundle: bundle_pb2.RecordBundle, path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bundle.SerializeToString())


def read_bundle(path) -> bundle_pb2.RecordBundle:
    bundle = bundle_pb2.RecordBundle()
    bundle.ParseFromString(Path(path).read_bytes())
    return bundle


class VolumeWriter:
    """Streams records into sequential volume files, each under a byte cap.

    Append records kind by kind; every volume repeats ``metadata`` so each
    file stays self-describing, and readers merge the directory
    (:class:`BundleStore`) — the split is transport, not structure. A
    single-volume result is written as ``<stem>.pb``; a multi-volume one as
    ``<stem>.v00.pb``, ``<stem>.v01.pb``, … ``close()`` returns the written
    paths."""

    def __init__(self, stem, metadata=None, max_bytes: int = VOLUME_BYTES):
        self._stem = Path(stem)
        self._metadata = metadata
        self._max_bytes = max_bytes
        self._current = self._fresh()
        self._current_bytes = self._current.ByteSize()
        self._written = []

    def _fresh(self) -> bundle_pb2.RecordBundle:
        volume = bundle_pb2.RecordBundle()
        if self._metadata is not None:
            volume.metadata.CopyFrom(self._metadata)
            # Counts describe each volume's own contents (set at close).
            volume.metadata.record_counts.clear()
        return volume

    def _flush(self) -> None:
        self._written.append(self._current)
        self._current = self._fresh()
        self._current_bytes = self._current.ByteSize()

    def append(self, kind: str, record) -> None:
        field = KINDS[kind][0]
        # Tag + length framing costs a few bytes per record; 10 over-counts
        # safely for any record size below the cap.
        cost = record.ByteSize() + 10
        if (self._current_bytes + cost > self._max_bytes
                and any(len(getattr(self._current, name))
                        for name, _t in KINDS.values())):
            self._flush()
        getattr(self._current, field).append(record)
        self._current_bytes += cost

    def close(self) -> list:
        self._written.append(self._current)
        volumes = self._written
        self._written = []
        if len(volumes) == 1:
            paths = [self._stem.with_suffix(".pb")]
        else:
            paths = [self._stem.parent / f"{self._stem.name}.v{index:02d}.pb"
                     for index in range(len(volumes))]
        for volume, path in zip(volumes, paths):
            for kind, (field, _message_type) in KINDS.items():
                count = len(getattr(volume, field))
                if count:
                    volume.metadata.record_counts[kind] = count
            write_bundle(volume, path)
        return paths


def write_volumes(bundle: bundle_pb2.RecordBundle, stem,
                  max_bytes: int = VOLUME_BYTES) -> list:
    """Write a bundle as ``<stem>.pb`` when it fits under ``max_bytes``,
    else as sequential volumes. Returns the written paths."""
    if bundle.ByteSize() <= max_bytes:
        path = Path(stem).with_suffix(".pb")
        write_bundle(bundle, path)
        return [path]
    writer = VolumeWriter(stem, metadata=bundle.metadata,
                          max_bytes=max_bytes)
    for kind, (field, _message_type) in KINDS.items():
        for record in getattr(bundle, field):
            writer.append(kind, record)
    return writer.close()


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
        self._root = path.parent if path.is_file() else path
        self._index = defaultdict(list)
        paths = [path] if path.is_file() else sorted(path.glob("*.pb"))
        for bundle_path in paths:
            bundle = read_bundle(bundle_path)
            experiment_id = bundle.metadata.experiment_id
            for kind, (field, _type) in KINDS.items():
                for record in getattr(bundle, field):
                    key = (record.key.experiment_id or experiment_id, record.key.condition_id, kind)
                    self._index[key].append(record)

    @property
    def root(self):
        """Capture assets (TensorRef uris) resolve relative to this — the
        bundle's directory, mirroring the streaming store's data root, so a
        replication lays the sha-listed tensor files beside the bundles."""
        return self._root

    def read(self, message_type, experiment_id: str, condition_id: str, kind: str):
        return iter(self._index.get((experiment_id, condition_id, kind), ()))

    def scopes(self) -> list:
        """Sorted (experiment_id, condition_id, kind, count) rows — the
        inspection surface behind the CLI."""
        return sorted((experiment, condition, kind, len(records))
                      for (experiment, condition, kind), records
                      in self._index.items())


def _cli_inspect(paths) -> None:
    for path in paths:
        bundle = read_bundle(path)
        metadata = bundle.metadata
        scope = metadata.experiment_id or "(combined)"
        print(f"{path}: {scope}"
              + (f" / {metadata.condition_id}" if metadata.condition_id
                 else ""))
        if metadata.data_digest:
            print(f"  data_digest: {metadata.data_digest}")
        for experiment_id in sorted(metadata.experiment_digests):
            print(f"  digest[{experiment_id}]: "
                  f"{metadata.experiment_digests[experiment_id]}")
        rows = defaultdict(int)
        payload = defaultdict(int)
        uris = set()
        for kind, (field, _message_type) in KINDS.items():
            for record in getattr(bundle, field):
                rows[(record.key.experiment_id or metadata.experiment_id,
                      record.key.condition_id, kind)] += 1
                if kind == "activations":
                    payload[record.tensor.dtype] += len(record.tensor.data)
                    if record.tensor.uri:
                        uris.add(record.tensor.uri)
        for (experiment, condition, kind), count in sorted(rows.items()):
            print(f"  {experiment}/{condition}/{kind}: {count}")
        for dtype, size in sorted(payload.items()):
            if size:
                print(f"  embedded {dtype} tensors: {size / 1e6:.1f} MB")
        for uri in sorted(uris):
            print(f"  capture: {uri}")


def _cli_extract(paths, out_dir, experiment=None, condition=None,
                 uri=None) -> None:
    from safetensors.numpy import save_file
    import json

    selected = defaultdict(list)
    for path in paths:
        bundle = read_bundle(path)
        for record in bundle.activations:
            if not record.tensor.data:
                continue
            if experiment and record.key.experiment_id != experiment:
                continue
            if condition and record.key.condition_id != condition:
                continue
            if uri and uri not in record.tensor.uri:
                continue
            group = (Path(record.tensor.uri).name.removesuffix(".safetensors")
                     if record.tensor.uri else
                     f"{record.key.experiment_id}-{record.key.condition_id}")
            selected[group].append(record)
    if not selected:
        raise SystemExit("no embedded tensors matched the selection")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for group, records in sorted(selected.items()):
        tensors = {}
        spans_by_conversation = defaultdict(dict)
        layers, point = [], None
        for record in records:
            tensors[record.tensor.tensor_name] = (
                activations.decode_tensor(record.tensor))
            if record.hook.layer not in layers:
                layers.append(record.hook.layer)
            point = point or record.hook.point
            if record.tensor.tensor_name.endswith("|tokens"):
                continue
            cid = activations.record_conversation_id(record)
            spans_by_conversation[cid][record.turn_index] = {
                "message_index": record.turn_index,
                "start": record.token_start, "end": record.token_end}
        manifest = {
            "point": point, "layers": layers,
            "conversations": [
                {"id": cid,
                 "assistant_spans": [span for _turn, span
                                     in sorted(spans.items())]}
                for cid, spans in sorted(spans_by_conversation.items())]}
        target = out_dir / f"{group}.safetensors"
        save_file(tensors, str(target))
        (out_dir / f"{group}.safetensors.manifest.json").write_text(
            json.dumps(manifest, indent=1))
        print(f"{target}: {len(tensors)} tensors, "
              f"{len(manifest['conversations'])} conversations")


def main(argv=None) -> None:
    """The decomposition tool a release points its readers at: one command
    to see what a bundle holds, one to take the piece you want."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="python3 -m modelwelfare.bundle", description=main.__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser(
        "inspect", help="list a bundle's experiments, conditions, record "
                        "kinds, digests, and embedded tensor payload")
    inspect.add_argument("paths", nargs="+")
    extract = commands.add_parser(
        "extract", help="restore embedded tensors to the safetensors "
                        "workbench form (a .safetensors + manifest pair "
                        "per original capture)")
    extract.add_argument("paths", nargs="+")
    extract.add_argument("--out", required=True)
    extract.add_argument("--experiment", default=None)
    extract.add_argument("--condition", default=None)
    extract.add_argument("--uri", default=None,
                         help="substring match on the capture provenance uri")
    args = parser.parse_args(argv)
    if args.command == "inspect":
        _cli_inspect(args.paths)
    else:
        _cli_extract(args.paths, args.out, experiment=args.experiment,
                     condition=args.condition, uri=args.uri)


if __name__ == "__main__":
    main()
