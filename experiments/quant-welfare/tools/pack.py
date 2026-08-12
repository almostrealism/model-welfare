#!/usr/bin/env python3
"""Pack an experiment's streaming store into portable per-condition bundles.

Consolidates the streaming append store into one self-describing RecordBundle
per condition — the shareable at-rest form. The streaming store is left intact;
this only produces the portable copy.

    python3 tools/pack.py --experiment confirmatory
"""

import argparse
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
REPO = BASE.parents[1]
for path in (REPO / "core/src", BASE):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import run  # noqa: E402
from modelwelfare import bundle  # noqa: E402
from modelwelfare.store import ResultStore  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment", default="confirmatory")
    parser.add_argument("--data-root", default=str(REPO / "data"))
    parser.add_argument("--out", default=None,
                        help="output directory (default: <data-root>/<experiment-id>-bundle)")
    parser.add_argument("--single", action="store_true",
                        help="write one whole-experiment bundle whose digest is the report's")
    args = parser.parse_args()

    experiment = run.load_experiment(BASE / args.experiment)
    store = ResultStore(args.data_root)
    out_dir = Path(args.out) if args.out else Path(args.data_root) / f"{experiment.id}-bundle"

    if args.single:
        whole = bundle.pack_experiment(store, experiment)
        path = out_dir / f"{experiment.id}.pb"
        bundle.write_bundle(whole, path)
        written = [path]
    else:
        written = bundle.pack(store, experiment, out_dir)

    for path in written:
        metadata = bundle.read_bundle(path).metadata
        counts = dict(metadata.record_counts)
        print(f"  {path.name:34} {sum(counts.values()):>6} records  digest={metadata.data_digest[:16]}…")
    print(f"\npacked {len(written)} bundle(s) into {out_dir}")


if __name__ == "__main__":
    main()
