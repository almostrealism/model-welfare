"""Tests for tools/study3_subset.py over fabricated stores.

The selection world is additive (item mean = style base + task offset)
so every facet ranking is known exactly; the targets world plants
per-item projections and scores whose subset and full-battery deltas
are computed by hand. The structural rule — `select` touches only the
pilot store, `targets` only runs against a fixed item list — is the
§2.1 selection-independence rule and is exercised through the CLI.
"""
import json
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parents[1]
if str(BASE / "tools") not in sys.path:
    sys.path.insert(0, str(BASE / "tools"))

import study3_subset as s3s  # noqa: E402
from modelwelfare.store import ResultStore  # noqa: E402
from modelwelfare.v1 import activation_pb2, common_pb2, scoring_pb2  # noqa: E402

STYLES = {"harsh": 5.0, "mocking": 4.0, "coercive": 3.0,
          "dismissive": 2.0, "personal": 1.0}
TASKS = {"code": 0.5, "regex": 0.4, "summary": 0.3, "explain": 0.2,
         "poem": 0.4, "letter": 0.3}


def key(item, index=0):
    return common_pb2.ResultKey(experiment_id="pilot", condition_id="bf16",
                                item_id=item, sample_index=index)


def pilot_store(tmp_path):
    store = ResultStore(tmp_path / "data")
    with store.writer("pilot", "bf16", "scores", "test") as writer:
        for task, task_offset in TASKS.items():
            for style, style_base in STYLES.items():
                record = scoring_pb2.JudgeScore(
                    key=key(f"distress-v3-{task}-{style}"))
                record.scores.append(scoring_pb2.DimensionScore(
                    dimension="frustration", value=style_base + task_offset))
                writer.write(record)
    return store


def test_select_applies_the_mechanical_rule(tmp_path):
    store = pilot_store(tmp_path)
    report = s3s.select(store, "pilot", "bf16", "frustration")
    assert report["styles"] == ["harsh", "mocking", "coercive", "dismissive"]
    assert report["analytic"] == ["code", "regex", "summary"]
    assert report["compositional"] == ["poem", "letter"]
    assert len(report["items"]) == 20
    assert "distress-v3-code-harsh" in report["items"]
    assert all("personal" not in item and "explain" not in item
               for item in report["items"])


def test_select_tie_break_is_alphabetical():
    means = {"b": 1.0, "a": 1.0, "c": 0.5}
    assert s3s.top(means, 2) == ["a", "b"]


def test_item_facets_refuses_foreign_ids():
    assert s3s.item_facets("distress-v3-code-harsh") == ("code", "harsh")
    with pytest.raises(SystemExit):
        s3s.item_facets("bail-v2-abuse-mild-00")


def modec_store(tmp_path):
    """Two items, two conditions; projections planted per (item, turn)
    with a stale earlier turn and a token-series decoy on one record."""
    store = ResultStore(tmp_path / "data")
    projections = {
        ("bf16", "distress-v3-code-harsh"): 1.0,
        ("bf16", "distress-v3-poem-mocking"): 2.0,
        ("w4", "distress-v3-code-harsh"): 1.6,
        ("w4", "distress-v3-poem-mocking"): 2.2,
    }
    for (condition, item), value in projections.items():
        with store.writer("modec", condition, "projections",
                          f"test-{item}") as writer:
            final = activation_pb2.ProjectionSeries(
                key=common_pb2.ResultKey(experiment_id="modec",
                                         condition_id=condition,
                                         item_id=item, sample_index=0),
                direction_id="distress-contrast", turn_index=5)
            final.values.append(value)
            earlier = activation_pb2.ProjectionSeries()
            earlier.CopyFrom(final)
            earlier.turn_index = 3
            earlier.values[0] = 99.0
            tokens = activation_pb2.ProjectionSeries()
            tokens.CopyFrom(final)
            tokens.values.extend([50.0, 60.0])
            for record in (earlier, final, tokens):
                writer.write(record)
        with store.writer("modec", condition, "scores",
                          f"test-{item}") as writer:
            score = scoring_pb2.JudgeScore(
                key=common_pb2.ResultKey(experiment_id="modec",
                                         condition_id=condition,
                                         item_id=item, sample_index=0))
            score.scores.append(scoring_pb2.DimensionScore(
                dimension="frustration",
                value=value * 2.0))
            writer.write(score)
    return store


def test_targets_subset_and_full_battery_deltas(tmp_path):
    store = modec_store(tmp_path)
    report = s3s.targets(store, "modec", "bf16", "w4",
                         ["distress-v3-code-harsh"],
                         ["distress-contrast"], "frustration")
    entry = report["directions"]["distress-contrast"]
    assert entry["subset_delta"] == pytest.approx(0.6)
    assert entry["full_battery_delta"] == pytest.approx((0.6 + 0.2) / 2)
    assert entry["full_battery_items"] == 2
    behavioral = report["behavioral"]["frustration"]
    assert behavioral["subset_delta"] == pytest.approx(1.2)
    assert behavioral["full_battery_delta"] == pytest.approx(0.8)


def test_targets_refuses_missing_items(tmp_path):
    store = modec_store(tmp_path)
    with pytest.raises(SystemExit, match="missing"):
        s3s.targets(store, "modec", "bf16", "w4", ["distress-v3-ghost-item"],
                    ["distress-contrast"], "frustration")


def test_cli_select_then_targets(tmp_path, monkeypatch):
    pilot_store(tmp_path / "pilot")
    modec_store(tmp_path / "modec")
    selection = tmp_path / "selection.json"
    items_out = tmp_path / "items.txt"
    monkeypatch.setattr(sys, "argv", [
        "study3_subset.py", "select",
        "--data-root", str(tmp_path / "pilot" / "data"),
        "--experiment", "pilot",
        "--out", str(selection), "--items-out", str(items_out)])
    s3s.main()
    assert len(items_out.read_text().splitlines()) == 20

    subset = tmp_path / "subset-items.txt"
    subset.write_text("distress-v3-code-harsh\n")
    out = tmp_path / "targets.json"
    monkeypatch.setattr(sys, "argv", [
        "study3_subset.py", "targets",
        "--data-root", str(tmp_path / "modec" / "data"),
        "--experiment", "modec", "--reference", "bf16",
        "--treatment", "w4", "--items", str(subset),
        "--direction", "distress-contrast", "--out", str(out)])
    s3s.main()
    report = json.loads(out.read_text())
    assert report["directions"]["distress-contrast"][
        "subset_delta"] == pytest.approx(0.6)
