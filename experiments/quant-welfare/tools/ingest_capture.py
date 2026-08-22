#!/usr/bin/env python3
"""Ingest a capture pair into the result store as activation records.

The confirmatory-capture half of REGISTRATION §3.4 (§6 item 6): the
workbench's safetensors + manifest become the store's ``activations`` and
``projections`` record kinds, with the tensors placed under the condition's
tensors/ directory and content-addressed by TensorRef. Numpy-only, so it
runs on whichever host holds the capture — in two-host collection each
host ingests its own conditions under its own producer name.

    python3 tools/ingest_capture.py --experiment quant-welfare-s2-modec \\
        --condition qwen3-4b-bf16 --capture capture-....safetensors

Projections use the frozen direction vectors at the frozen layer by
default; pass --no-projections to record slices only.
"""
import argparse
import socket
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
REPO = BASE.parents[1]
if str(REPO / "core/src") not in sys.path:
    sys.path.insert(0, str(REPO / "core/src"))

from google.protobuf import timestamp_pb2  # noqa: E402

from modelwelfare.activations import ingest_capture  # noqa: E402
from modelwelfare.store import ResultStore  # noqa: E402
from modelwelfare.v1 import common_pb2  # noqa: E402

DEFAULT_VECTORS = BASE / "study2" / "calibration" / "directions-bf16.safetensors"
FROZEN_LAYER = 18


def provenance(host: str) -> common_pb2.Provenance:
    """Provenance for this ingest: host plus the repo commit when available."""
    record = common_pb2.Provenance(host=host)
    try:
        record.code_version = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True,
            text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        pass
    timestamp = timestamp_pb2.Timestamp()
    timestamp.GetCurrentTime()
    record.created_at.CopyFrom(timestamp)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", default=str(REPO / "data"))
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--condition", required=True)
    parser.add_argument("--capture", required=True,
                        help="capture safetensors (manifest beside it)")
    parser.add_argument("--layer", type=int, default=FROZEN_LAYER)
    parser.add_argument("--vectors", default=str(DEFAULT_VECTORS),
                        help="frozen direction vectors for projections")
    parser.add_argument("--no-projections", action="store_true",
                        help="record activation slices only")
    parser.add_argument("--host", default=socket.gethostname().split(".")[0],
                        help="logical host name for provenance; defaults to "
                             "the short host name")
    parser.add_argument("--producer", default=None,
                        help="unique per concurrently-writing process; "
                             "defaults to --host (qualify it when one host "
                             "runs several writers)")
    args = parser.parse_args()
    producer = args.producer or args.host

    store = ResultStore(args.store)
    slices, projections = ingest_capture(
        store, args.experiment, args.condition, args.capture, args.layer,
        producer,
        vectors_path=None if args.no_projections else args.vectors,
        provenance=provenance(args.host))
    print(f"ingested {args.capture}: {slices} activation slices, "
          f"{projections} projections -> {args.store} "
          f"({args.experiment}/{args.condition}, producer {producer})")


if __name__ == "__main__":
    main()
