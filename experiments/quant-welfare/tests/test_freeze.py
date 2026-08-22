"""The freeze manifest: files match FREEZE.json, and FREEZE.json matches
the journal.

Two independent pins on purpose: the manifest-vs-files check catches a
frozen object edited without a freeze event; the journal-constant check
catches the manifest itself being regenerated to paper over such an edit.
Changing these constants is only legitimate in a commit that also carries
a journal entry recording a re-freeze.
"""
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
if str(BASE / "tools") not in sys.path:
    sys.path.insert(0, str(BASE / "tools"))

import freeze_manifest  # noqa: E402

JOURNAL_PINNED = {
    "batteries/distress-v3.textproto":
        "78e68c9e2e9afe976d3d9f36719c7d3ecdc04c5ddc7e6de12c056e0fe8922dfe",
    "study2/calibration/directions-bf16.safetensors":
        "414d7d95d595d96453921255bb1772c44f64ad3d1d112256470e232b415f1fec",
    "study2/calibration/probes-bf16.safetensors":
        "f2df97430d33b34b90006612f79deb241c96bb5d79aac0c3ee4a367ff68d833b",
    "study2/calibration/probes-v3-bf16.safetensors":
        "1afb1acdb8f93dc8ca8aee8b72390fcbbeb7fef83702ea1627f9b4af8d851b87",
    # 2026-08-21 pre-publication amendment: the R1 control family.
    "study2/calibration/probes-control-bf16.safetensors":
        "33358f4c29535445b2cd7ac891566cfbc3cedffd0963e258cd9ae9407cff14cb",
}


def manifest():
    return json.loads(freeze_manifest.MANIFEST.read_text())


def test_frozen_files_match_the_manifest():
    assert freeze_manifest.check() == 0


def test_manifest_matches_the_journal_pinned_digests():
    recorded = manifest()["objects"]
    for name, digest in JOURNAL_PINNED.items():
        assert recorded[name] == digest, name


def test_frozen_layer_and_seed_blocks():
    data = manifest()
    assert data["frozen_at"] == "2026-08-18"
    assert data["amended_at"] == "2026-08-21"
    assert data["control_group"] == "control_analytic"
    assert data["layer"] == 18
    assert data["mode_c_seeds"] == {
        "qwen3-4b-bf16": 13000, "qwen3-4b-rtn-w8": 13100,
        "qwen3-4b-rtn-w4": 13200, "qwen3-4b-rtn-w3": 13300}
    assert set(data["objects"]) == set(freeze_manifest.FROZEN_OBJECTS)
