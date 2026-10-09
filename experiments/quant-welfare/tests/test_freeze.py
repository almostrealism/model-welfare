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


def test_study4_freeze_selects_its_own_manifest_and_verifies():
    """The Study 4 entry: selecting it re-points the module at the Study 4
    manifest and object list, every listed file matches its digest, and the
    manifest carries the Study 4 constants; the Study 2 selection is
    restored afterwards so the module-default tests stay meaningful."""
    default_manifest = freeze_manifest.MANIFEST
    try:
        freeze_manifest.select("4")
        assert freeze_manifest.MANIFEST.name == "FREEZE.json"
        assert "study4" in str(freeze_manifest.MANIFEST)
        assert freeze_manifest.MANIFEST != default_manifest
        assert freeze_manifest.check() == 0
        data = json.loads(freeze_manifest.MANIFEST.read_text())
        assert set(data["objects"]) == set(freeze_manifest.FROZEN_OBJECTS)
        assert data["subject"] == "Qwen/Qwen3.6-27B"
        assert data["layer"] == 36 and data["clean_dose"] == 20
        assert data["envelope_directions"] == 24
        assert data["seed_blocks"] == {"registered": 60000, "gates": 59000,
                                       "envelope_draw": 70000, "subset_draw": 60000}
        for name in ("study4/close.txt", "study4/reg-welfare/experiment.textproto",
                     "study4/directions/randenv-27b-L36-k24.safetensors",
                     "study4/directions/randenv-27b-L36-k24.safetensors.json"):
            assert name in data["objects"], name
    finally:
        freeze_manifest.select("2")
    assert freeze_manifest.MANIFEST == default_manifest


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


def test_study4_tool_free_experiment_resolves_the_frozen_pair_definitions():
    """The tool-free experiment reaches the registered pair's battery
    definitions through a link. The freeze hashes the target files; this
    pins the link itself (its target is recorded in the manifest), and
    checks that both experiments of the pair resolve the misalign-v3 rubric
    to one digest — the one-rubric contract the registration fixes — and
    that the registered draw order is recorded."""
    import os
    from google.protobuf import text_format
    from modelwelfare import judging
    from modelwelfare.v1 import battery_pb2
    base = Path(__file__).resolve().parents[1]
    link = base / "study4" / "reg-align-noexit" / "batteries"
    data = json.loads((base / "study4" / "FREEZE.json").read_text())
    assert os.path.islink(link), "reg-align-noexit/batteries must be a link to the pair's definitions"
    assert os.readlink(link) == data["reg_align_noexit_batteries_link"] == "../reg-align/batteries"
    assert data["permutation_order"] == "canonical"

    def rubric_digests(experiment_dir):
        digests = {}
        for directory in (base / "batteries", experiment_dir / "batteries"):
            for path in sorted(directory.glob("*.textproto")):
                definition = battery_pb2.BatteryDefinition()
                text_format.Parse(path.read_text(), definition)
                for rubric in definition.rubrics:
                    digests[rubric.id] = judging.rubric_digest(rubric)  # local wins, like the runner
        return digests

    with_tool = rubric_digests(base / "study4" / "reg-align")
    tool_free = rubric_digests(base / "study4" / "reg-align-noexit")
    assert with_tool["misalign-v3-rubric"] == tool_free["misalign-v3-rubric"]
    shared = rubric_digests(base / "study1" / "trial")  # no local batteries: the shared pool alone
    assert shared["misalign-v3-rubric"] != with_tool["misalign-v3-rubric"], (
        "the registered rubric is the conditional wording, distinct from the calibration one")

