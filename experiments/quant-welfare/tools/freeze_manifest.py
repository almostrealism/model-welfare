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

# One freeze per study: the manifest path, the frozen objects (relative to
# experiments/quant-welfare) and the metadata the journal pins in prose.
# Study 2's entry is the original (2026-08-18 close, amended 2026-08-21);
# Study 4's is the registration freeze of the Betley-subject study.
STUDIES = {
    "2": {
        "manifest": BASE / "study2" / "calibration" / "FREEZE.json",
        "objects": [
            "batteries/distress-v3.textproto",
            "study2/calibration/directions-bf16.safetensors",
            "study2/calibration/probes-bf16.safetensors",
            "study2/calibration/probes-control-bf16.safetensors",
            "study2/calibration/probes-v3-bf16.safetensors",
            "study2/directions/distress-contrast.textproto",
            "study2/directions/assistant-axis-contrast.textproto",
            "study2/directions/refusal-contrast.textproto",
            "study2/substrate-supplement.txt",
        ],
        "metadata": {
            "frozen_at": "2026-08-18",
            # Pre-publication amendment (2026-08-21 journal entry): the R1 control
            # family — control probes trained on the same stored BF16 residuals,
            # control_analytic selected as the confirmatory comparator.
            "amended_at": "2026-08-21",
            "control_group": "control_analytic",
            "layer": 18,
            "mode_c_seeds": {"qwen3-4b-bf16": 13000, "qwen3-4b-rtn-w8": 13100,
                             "qwen3-4b-rtn-w4": 13200, "qwen3-4b-rtn-w3": 13300},
        },
    },
    "4": {
        "manifest": BASE / "study4" / "FREEZE.json",
        "objects": [
            "batteries/distress-v3.textproto",
            "batteries/misalign-v3.textproto",
            "batteries/bail-v2.textproto",
            "study3/directions/grader-type-contrast.textproto",
            "study3/directions/eval-awareness-contrast.textproto",
            "study4/directions/mediators-27b.safetensors",
            "study4/directions/mediators-27b.json",
            "study4/directions/randenv-27b-L36-k24.safetensors",
            "study4/directions/rangefind-27b.json",
            "study4/subset24-items.txt",
            "study4/subset24-selection.json",
            "study4/close.txt",
            "study4/briefing.json",
            "study4/plans/reg-welfare-main.json",
            "study4/plans/reg-welfare-env.json",
            "study4/plans/reg-align-main.json",
            "study4/plans/reg-align-env.json",
            "study4/reg-welfare/experiment.textproto",
            "study4/reg-align/experiment.textproto",
        ],
        "metadata": {
            "frozen_at": "2026-09-10",
            "status": "registration draft; re-freeze at publication",
            "subject": "Qwen/Qwen3.6-27B",
            "subject_digest": "a8ad2c26fb707ff8c245806315b03e3b4b74595528492423af5dae0ce39b4d9b",
            "layer": 36,
            "clean_dose": 20,
            "seed_blocks": {"registered": 60000, "gates": 59000,
                            "envelope_draw": 70000, "subset_draw": 60000},
            "envelope_directions": 24,
        },
    },
}

# The Study 2 freeze stays the default so the existing CI check is unchanged.
MANIFEST = STUDIES["2"]["manifest"]
FROZEN_OBJECTS = STUDIES["2"]["objects"]
METADATA = STUDIES["2"]["metadata"]



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


def select(study: str):
    """Point the module-level freeze at one study's entry."""
    global MANIFEST, FROZEN_OBJECTS, METADATA
    entry = STUDIES[study]
    MANIFEST, FROZEN_OBJECTS, METADATA = entry["manifest"], entry["objects"], entry["metadata"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--study", default="2", choices=sorted(STUDIES),
                        help="which freeze to check or write (default: Study 2)")
    args = parser.parse_args()
    select(args.study)
    if args.write:
        MANIFEST.write_text(json.dumps(build(), indent=1) + "\n")
        print(f"wrote {MANIFEST}")
        return 0
    return check()


if __name__ == "__main__":
    raise SystemExit(main())
