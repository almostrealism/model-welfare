#!/usr/bin/env python3
"""Print the replication signature for an experiment's stored data.

The dataset digest is layout- and order-independent (see
modelwelfare.signature), so it is the value a report cites: anyone holding the
data — as the streaming store or a single consolidated .pb — recomputes it to
confirm they have the right, uncorrupted dataset.

    python3 tools/signature.py --experiment study1/confirmatory
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
from modelwelfare.bundle import BundleStore  # noqa: E402
from modelwelfare.signature import DEFAULT_KINDS, store_digest  # noqa: E402
from modelwelfare.store import ResultStore  # noqa: E402
from modelwelfare.v1 import scoring_pb2  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment", default="study1/confirmatory")
    parser.add_argument("--data-root", default=str(REPO / "data"))
    parser.add_argument("--bundle", default=None,
                        help="compute the digest from a packed bundle file or directory")
    parser.add_argument("--reference", action="store_true",
                        help="also include the reference_scores stream in the digest")
    args = parser.parse_args()

    experiment = run.load_experiment(BASE / args.experiment)
    store = BundleStore(args.bundle) if args.bundle else ResultStore(args.data_root)
    kinds = list(DEFAULT_KINDS)
    if args.reference:
        kinds.append(("reference_scores", scoring_pb2.JudgeScore))

    result = store_digest(store, experiment.id, [c.id for c in experiment.conditions], kinds)
    print(f"experiment {experiment.id}")
    for name in sorted(result["per_kind"]):
        print(f"  {name:16} {result['counts'][name]:>6} records  {result['per_kind'][name]}")
    print(f"\n  dataset digest (sha256): {result['digest']}")


if __name__ == "__main__":
    main()
