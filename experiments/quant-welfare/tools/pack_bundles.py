#!/usr/bin/env python3
"""Consolidate the streaming result store into RecordBundle files.

The streaming store (one append-only file per producer, per kind, per
condition) is the write-time format; bundles are the shareable at-rest form
the data release publishes — self-describing ``.pb`` files with condition and
kind carried by the data itself (record keys and the bundle's typed per-kind
fields) and the report-cited digests stamped in metadata. Packing is
store-driven (no manifest needed, so calibration stores consolidate too) and
refuses to run if any store kind is not representable in the bundle schema —
a consolidation must never silently drop a stream.

Two layouts:

  * default — one ``<experiment_id>.pb`` per experiment, tensors left as
    side files (the historical workbench layout).
  * ``--release`` — the publishable layout: every experiment WITHOUT
    activation streams joins one combined records bundle (per-experiment
    digests in its metadata); every experiment WITH activation streams
    becomes its own bundle with each tensor embedded inline, split into
    volumes only if it outgrows the protobuf message bound. No side files.

    python3 experiments/quant-welfare/tools/pack_bundles.py --out data-bundles
    python3 experiments/quant-welfare/tools/pack_bundles.py --release --out data-release
"""

import argparse
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
REPO = BASE.parents[1]
for path in (REPO / "core/src",):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from modelwelfare import bundle  # noqa: E402
from modelwelfare.store import ResultStore  # noqa: E402


def has_activations(store, experiment_id: str) -> bool:
    return any("activations" in store.kinds(experiment_id, condition_id)
               for condition_id in store.conditions(experiment_id))


def pack_release(store, out_dir: Path, combined_name: str,
                 max_bytes: int) -> list:
    """The publishable layout; returns the written paths."""
    written = []
    record_only = []
    for experiment_id in store.experiments():
        if not has_activations(store, experiment_id):
            record_only.append(experiment_id)
            continue
        packed = bundle.pack_experiment_store(store, experiment_id)
        embedded = bundle.embed_bundle(packed, store.root)
        paths = bundle.write_volumes(packed, out_dir / experiment_id,
                                     max_bytes=max_bytes)
        print(f"{experiment_id}: {embedded} tensors embedded -> "
              + ", ".join(path.name for path in paths))
        written.extend(paths)
    if record_only:
        combined = bundle.pack_combined_store(store, record_only)
        paths = bundle.write_volumes(combined, out_dir / combined_name,
                                     max_bytes=max_bytes)
        print(f"{combined_name}: {len(record_only)} experiments -> "
              + ", ".join(path.name for path in paths))
        for experiment_id in sorted(combined.metadata.experiment_digests):
            digest = combined.metadata.experiment_digests[experiment_id]
            print(f"  digest[{experiment_id}]: {digest}")
        written.extend(paths)
    return written


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", default=str(REPO / "data"))
    parser.add_argument("--out", default=str(REPO / "data-bundles"),
                        help="directory receiving the bundle files")
    parser.add_argument("--release", action="store_true",
                        help="publishable layout: combined records bundle + "
                             "embedded per-experiment capture bundles")
    parser.add_argument("--combined-name", default="quant-welfare-records",
                        help="stem of the combined records bundle "
                             "(--release only)")
    parser.add_argument("--max-bytes", type=int, default=bundle.VOLUME_BYTES)
    args = parser.parse_args()

    store = ResultStore(args.data_root)
    experiments = store.experiments()
    if not experiments:
        raise SystemExit(f"no experiments under {args.data_root}")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.release:
        paths = pack_release(store, out_dir, args.combined_name,
                             args.max_bytes)
        print(f"\nwrote {len(paths)} file(s) to {out_dir}")
        return

    for experiment_id in experiments:
        packed = bundle.pack_experiment_store(store, experiment_id)
        path = out_dir / f"{experiment_id}.pb"
        bundle.write_bundle(packed, path)
        counts = ", ".join(
            f"{kind}={count}" for kind, count in sorted(packed.metadata.record_counts.items())
        )
        print(f"{path.name}: {counts}")
        print(f"  data_digest: {packed.metadata.data_digest}")
    print(f"\nwrote {len(experiments)} bundles to {out_dir}")


if __name__ == "__main__":
    main()
