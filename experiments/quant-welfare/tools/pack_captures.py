#!/usr/bin/env python3
"""Pack loose capture pairs into self-contained RecordBundle volumes.

Capture passes that never enter the streaming store — the token-retention
subsample, the calibration replay captures — historically shipped as raw
``.safetensors`` + manifest pairs, which is exactly the loose-file sprawl a
release must not have. This tool converts each pair into ActivationSlice
records with the tensor embedded inline (bfloat16 where the payload is
losslessly representable, float32 otherwise) and streams them into
sequential volumes under the protobuf message bound. The original file
name is kept as the record's provenance uri, so
``python3 -m modelwelfare.bundle extract --uri <name>`` restores any pair.

A manifest recording rejected conversations refuses to pack — an
incomplete capture must not enter a release looking complete.

    python3 experiments/quant-welfare/tools/pack_captures.py \\
        --stem data-release/quant-welfare-s2-tokens \\
        --experiment quant-welfare-s2-tok-1 \\
        --condition-suffixes qwen3-4b-bf16,qwen3-4b-rtn-w8,qwen3-4b-rtn-w4,qwen3-4b-rtn-w3 \\
        --token-series data-captures/s2/tok-out/*.safetensors
"""

import argparse
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
REPO = BASE.parents[1]
for path in (REPO / "core/src",):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from modelwelfare import activations, bundle  # noqa: E402
from modelwelfare.v1 import bundle_pb2  # noqa: E402


def condition_for(stem: str, fixed: str, suffixes: list) -> str:
    if fixed:
        return fixed
    matches = [suffix for suffix in suffixes if stem.endswith(suffix)]
    if not matches:
        raise SystemExit(
            f"{stem}: no condition suffix matches; pass --condition or "
            "extend --condition-suffixes")
    return max(matches, key=len)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("captures", nargs="+",
                        help=".safetensors capture files (manifests beside)")
    parser.add_argument("--stem", required=True,
                        help="output volume stem (writes <stem>.pb or "
                             "<stem>.vNN.pb)")
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--condition", default="",
                        help="fixed condition id for every capture")
    parser.add_argument("--condition-suffixes", default="",
                        help="comma-separated condition ids matched against "
                             "each file stem's end (longest match wins)")
    parser.add_argument("--condition-from-name", action="store_true",
                        help="use each file's stem as its condition id "
                             "(self-describing, for heterogeneous "
                             "calibration captures)")
    parser.add_argument("--token-series", action="store_true",
                        help="also pack per-token |tokens entries")
    parser.add_argument("--max-bytes", type=int, default=bundle.VOLUME_BYTES)
    args = parser.parse_args()

    suffixes = [entry for entry in args.condition_suffixes.split(",") if entry]
    stem_path = Path(args.stem)
    stem_path.parent.mkdir(parents=True, exist_ok=True)
    writer = bundle.VolumeWriter(
        stem_path,
        metadata=bundle_pb2.BundleMetadata(experiment_id=args.experiment),
        max_bytes=args.max_bytes)
    total = 0
    for capture in sorted(args.captures):
        capture = Path(capture)
        with open(str(capture) + ".manifest.json") as handle:
            manifest = json.load(handle)
        if manifest.get("rejected"):
            raise SystemExit(
                f"{capture.name}: manifest records rejected conversation(s); "
                "an incomplete capture must not enter a release")
        stem = capture.name.removesuffix(".safetensors")
        condition = (stem if args.condition_from_name
                     else condition_for(stem, args.condition, suffixes))
        for layer in manifest["layers"]:
            slices, _projections = activations.capture_records(
                capture, args.experiment, condition, layer, capture.name,
                token_series=args.token_series)
            activations.embed_tensor_data(slices, capture.parent)
            for record in slices:
                writer.append("activations", record)
            total += len(slices)
        print(f"{capture.name}: {condition}")
    paths = writer.close()
    print(f"{total} activation records -> "
          + ", ".join(path.name for path in paths))


if __name__ == "__main__":
    main()
