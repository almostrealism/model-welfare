"""Tests for tools/external_direction_cosine.py: the residual-point row
bookkeeping is right, the external digests are checked against the
external metadata, and the run leaves a record of what was compared."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from safetensors.numpy import save_file

BASE = Path(__file__).resolve().parents[1]
if str(BASE / "tools") not in sys.path:
    sys.path.insert(0, str(BASE / "tools"))

import external_direction_cosine as edc  # noqa: E402


def unit(dim, index):
    vector = np.zeros(dim, dtype=np.float32)
    vector[index] = 1.0
    return vector


def test_parse_key_and_cosine():
    assert edc.parse_key("grader-type|L36") == ("grader-type", 36)
    with pytest.raises(ValueError):
        edc.parse_key("grader-type")
    assert edc.cosine(unit(4, 0), unit(4, 0)) == pytest.approx(1.0)
    assert edc.cosine(unit(4, 0), unit(4, 1)) == pytest.approx(0.0)
    assert edc.cosine(unit(4, 0), -2 * unit(4, 0)) == pytest.approx(-1.0)


def test_table_uses_the_matched_row_one_past_our_layer():
    ours = {"a|L3": unit(8, 0), "b|L3": unit(8, 1), "a|L6": unit(8, 2)}
    external = unit(8, 0)
    deltas = np.zeros((8, 8), dtype=np.float32)
    deltas[4] = unit(8, 1)   # the row matched to our layer 3
    table = edc.cosine_table(ours, external, deltas)
    assert list(table) == ["a|L3", "a|L6", "b|L3"]
    assert table["a|L3"]["published"] == pytest.approx(1.0)
    assert table["b|L3"]["published"] == pytest.approx(0.0)
    assert table["a|L3"]["matched_row"] == 4
    assert table["a|L3"]["matched_point"] == pytest.approx(0.0)
    assert table["b|L3"]["matched_point"] == pytest.approx(1.0)
    # their row 7 is all zero: the matched comparison is absent, not NaN
    assert table["a|L6"]["matched_row"] is None
    assert table["a|L6"]["matched_point"] is None
    # no deltas: the matched comparison is absent, not zero
    assert edc.cosine_table(ours, external)["a|L3"]["matched_point"] is None
    with pytest.raises(ValueError, match="zero vector"):
        edc.cosine(unit(4, 0), np.zeros(4))
    with pytest.raises(ValueError, match="shape"):
        edc.cosine_table({"a|L1": unit(4, 0)}, external)


def test_chance_scale():
    assert edc.chance_abs_cos_scale(5120) == pytest.approx(0.013975, abs=1e-6)


def write_external(tmp_path, vector, deltas, meta_overrides=None):
    vector_path = tmp_path / "vector.npy"
    deltas_path = tmp_path / "deltas.npy"
    np.save(vector_path, vector)
    np.save(deltas_path, deltas)
    meta = {"vector_npy_sha256": hashlib.sha256(vector_path.read_bytes()).hexdigest(),
            "deltas_npy_sha256": hashlib.sha256(deltas_path.read_bytes()).hexdigest(),
            "layer": 3, "name": "ext", "hidden_size": 8,
            "position_convention": "input of block"}
    meta.update(meta_overrides or {})
    meta_path = tmp_path / "meta.json"
    meta_path.write_text(json.dumps(meta))
    return vector_path, deltas_path, meta_path


def test_cli_writes_the_record_with_checked_digests(tmp_path, monkeypatch):
    ours_path = tmp_path / "ours.safetensors"
    save_file({"a|L3": unit(8, 0), "b|L3": unit(8, 1)}, str(ours_path))
    ours_meta = tmp_path / "ours.json"
    ours_meta.write_text(json.dumps({
        "point": "residual_post", "layers": [3],
        "directions": {"a": {"extract_pairs": ["p", "q"]}, "b": {"extract_pairs": ["p"]}}}))
    deltas = np.zeros((8, 8), dtype=np.float32)
    deltas[4] = unit(8, 1)
    vector_path, deltas_path, meta_path = write_external(tmp_path, unit(8, 0), deltas)
    out = tmp_path / "record.json"
    monkeypatch.setattr(sys, "argv", [
        "external_direction_cosine.py", "--ours", str(ours_path),
        "--ours-meta", str(ours_meta), "--ours-convention", "final reply, pooled",
        "--external", str(vector_path), "--external-meta", str(meta_path),
        "--external-deltas", str(deltas_path), "--source", "repo@abc",
        "--out", str(out)])
    edc.main()
    record = json.loads(out.read_text())
    assert record["ours"]["point"] == "residual_post"
    assert record["ours"]["extract_pairs"] == {"a": 2, "b": 1}
    assert record["ours"]["sha256"] == hashlib.sha256(ours_path.read_bytes()).hexdigest()
    assert record["external"]["source"] == "repo@abc"
    assert record["external"]["vector_sha256"] == json.loads(
        meta_path.read_text())["vector_npy_sha256"]
    assert record["external"]["layer"] == 3 and record["external"]["deltas_rows"] == 8
    assert record["residual_point_offset"] == 1
    assert record["cosines"]["a|L3"]["published"] == pytest.approx(1.0)
    assert record["cosines"]["b|L3"]["matched_point"] == pytest.approx(1.0)
    assert record["dim"] == 8


def test_cli_refuses_a_vector_whose_digest_disagrees_with_its_meta(tmp_path, monkeypatch):
    ours_path = tmp_path / "ours.safetensors"
    save_file({"a|L3": unit(8, 0)}, str(ours_path))
    vector_path, _, meta_path = write_external(
        tmp_path, unit(8, 0), np.zeros((8, 8), dtype=np.float32),
        {"vector_npy_sha256": "0" * 64})
    monkeypatch.setattr(sys, "argv", [
        "external_direction_cosine.py", "--ours", str(ours_path),
        "--external", str(vector_path), "--external-meta", str(meta_path),
        "--out", str(tmp_path / "record.json")])
    with pytest.raises(SystemExit, match="does not match"):
        edc.main()
