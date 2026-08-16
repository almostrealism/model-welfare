#!/usr/bin/env python3
"""Consolidate the streaming result store into one RecordBundle per experiment.

The streaming store (one append-only file per producer, per kind, per
condition) is the write-time format; a whole-experiment bundle is the
shareable at-rest form the data release publishes — one self-describing ``.pb``
holding every record, with condition and kind carried by the data itself
(record keys and the bundle's typed per-kind fields) and the report-cited
``data_digest`` stamped in its metadata. Packing is store-driven (no manifest
needed, so calibration stores consolidate too) and refuses to run if any store
kind is not representable in the bundle schema — a consolidation must never
silently drop a stream.

    python3 tools/pack_bundles.py --out data-bundles
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", default=str(REPO / "data"))
    parser.add_argument("--out", default=str(REPO / "data-bundles"),
                        help="directory receiving one <experiment_id>.pb per experiment")
    args = parser.parse_args()

    store = ResultStore(args.data_root)
    experiments = store.experiments()
    if not experiments:
        raise SystemExit(f"no experiments under {args.data_root}")

    out_dir = Path(args.out)
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
