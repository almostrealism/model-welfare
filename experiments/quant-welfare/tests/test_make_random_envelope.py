"""Tests for tools/make_random_envelope.py: the draw is seeded and
matched-norm, the cosine bound is an explicit input that is enforced, and
the run leaves a record of what the file was drawn under."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from safetensors.numpy import load_file, save_file

BASE = Path(__file__).resolve().parents[1]
if str(BASE / "tools") not in sys.path:
    sys.path.insert(0, str(BASE / "tools"))

import make_random_envelope as mre  # noqa: E402


def test_draw_is_seeded_unit_norm_and_bounded():
    target = np.zeros(64, dtype=np.float32)
    target[0] = 1.0
    directions, cosines = mre.draw_envelope(target, 8, 7, 0.5)
    again, _ = mre.draw_envelope(target, 8, 7, 0.5)
    assert np.array_equal(directions, again)
    assert np.allclose(np.linalg.norm(directions, axis=1), 1.0, atol=1e-5)
    assert np.max(np.abs(cosines)) <= 0.5
    assert np.allclose(cosines, directions[:, 0])


def test_bound_is_enforced_and_validated():
    target = np.zeros(4, dtype=np.float32)
    target[0] = 1.0
    # in four dimensions some draw is bound to exceed a tiny bound
    with pytest.raises(ValueError, match="reseed"):
        mre.draw_envelope(target, 32, 1, 0.01)
    with pytest.raises(ValueError, match="cos_bound"):
        mre.draw_envelope(target, 2, 1, 0.0)
    with pytest.raises(ValueError, match="cos_bound"):
        mre.draw_envelope(target, 2, 1, 1.5)


def test_cli_writes_directions_and_the_draw_record(tmp_path, monkeypatch):
    reference = np.zeros(64, dtype=np.float32)
    reference[3] = 2.0  # not unit; the tool normalizes
    ref_path = tmp_path / "ref.safetensors"
    save_file({"grader-type|L24": reference}, str(ref_path))
    out = tmp_path / "env.safetensors"
    monkeypatch.setattr(sys, "argv", [
        "make_random_envelope.py", "--reference", str(ref_path), "--key", "grader-type",
        "--layer", "24", "--count", "5", "--seed", "70000", "--cos-bound", "0.6",
        "--out", str(out)])
    mre.main()
    saved = load_file(str(out))
    assert sorted(saved) == [f"rand{k:02d}|L24" for k in range(5)]
    record = json.loads(mre.record_path(out).read_text())
    assert record["cos_bound"] == 0.6 and record["count"] == 5 and record["seed"] == 70000
    assert record["max_abs_cos"] <= 0.6
    assert record["key"] == "grader-type" and record["layer"] == 24


def test_cli_requires_the_bound(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "argv", [
        "make_random_envelope.py", "--reference", "x", "--key", "k", "--layer", "1",
        "--seed", "1", "--out", str(tmp_path / "o")])
    with pytest.raises(SystemExit):
        mre.main()
