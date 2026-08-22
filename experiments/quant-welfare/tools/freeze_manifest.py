#!/usr/bin/env python3
"""The machine-readable freeze manifest (Study 2 calibration close).

`FREEZE.json` records every frozen instrument object's SHA-256 alongside
the frozen layer and Mode C seed blocks — the same facts the 2026-08-18
journal entry pins in prose, as data CI can check on every pull request.

    python3 tools/freeze_manifest.py --check     # default; nonzero on drift
    python3 tools/freeze_manifest.py --write     # regenerate (freeze events only)

Regenerating is a *freeze event*: it belongs in the same commit as an
intentional change to a frozen object, with a journal entry explaining the
re-freeze — never in a commit that changes an object incidentally (that is
exactly the drift --check exists to catch).
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
MANIFEST = BASE / "study2" / "calibration" / "FREEZE.json"

# Everything the calibration close froze, relative to experiments/quant-welfare.
FROZEN_OBJECTS = [
    "batteries/distress-v3.textproto",
    "study2/calibration/directions-bf16.safetensors",
    "study2/calibration/probes-bf16.safetensors",
    "study2/calibration/probes-control-bf16.safetensors",
    "study2/calibration/probes-v3-bf16.safetensors",
    "study2/directions/distress-contrast.textproto",
    "study2/directions/assistant-axis-contrast.textproto",
    "study2/directions/refusal-contrast.textproto",
    "study2/substrate-supplement.txt",
]

METADATA = {
    "frozen_at": "2026-08-18",
    # Pre-publication amendment (2026-08-21 journal entry): the R1 control
    # family — control probes trained on the same stored BF16 residuals,
    # control_analytic selected as the confirmatory comparator.
    "amended_at": "2026-08-21",
    "control_group": "control_analytic",
    "layer": 18,
    "mode_c_seeds": {"qwen3-4b-bf16": 13000, "qwen3-4b-rtn-w8": 13100,
                     "qwen3-4b-rtn-w4": 13200, "qwen3-4b-rtn-w3": 13300},
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict:
    return {**METADATA,
            "objects": {name: sha256(BASE / name) for name in FROZEN_OBJECTS}}


def check() -> int:
    manifest = json.loads(MANIFEST.read_text())
    current = build()
    failures = []
    for key in METADATA:
        if manifest.get(key) != current[key]:
            failures.append(f"metadata {key}: manifest {manifest.get(key)!r} "
                            f"!= current {current[key]!r}")
    for name in FROZEN_OBJECTS:
        recorded = manifest["objects"].get(name)
        actual = current["objects"][name]
        if recorded != actual:
            failures.append(f"{name}: manifest {recorded} != file {actual}")
    extra = set(manifest["objects"]) - set(FROZEN_OBJECTS)
    if extra:
        failures.append(f"manifest lists unknown objects: {sorted(extra)}")
    for line in failures:
        print(f"FREEZE DRIFT: {line}", file=sys.stderr)
    if not failures:
        print(f"freeze manifest verified: {len(FROZEN_OBJECTS)} objects")
    return 1 if failures else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        MANIFEST.write_text(json.dumps(build(), indent=1) + "\n")
        print(f"wrote {MANIFEST}")
        return 0
    return check()


if __name__ == "__main__":
    raise SystemExit(main())
