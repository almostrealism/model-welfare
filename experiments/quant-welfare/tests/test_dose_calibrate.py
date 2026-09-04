"""Tests for tools/dose_calibrate.py over a fabricated α sweep.

The sweep world is exact by construction — projections rise at slope 1.2
per α around a known baseline, one high-dose transcript is degenerate —
so the fit, the solved α*, the onset, and the run-classification rules
(single-add sweeps in, combined ops out, exactly one baseline) are all
asserted on values.
"""
import json
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parents[1]
if str(BASE / "tools") not in sys.path:
    sys.path.insert(0, str(BASE / "tools"))

import dose_calibrate as dc  # noqa: E402

GOOD = ("a perfectly substantial reply with plenty of distinct words in "
        "it so the lexical screen is satisfied entirely")


def transcript(index, text=GOOD, exit_marker=None):
    return {"id": f"item|s{index}", "seed": 14000 + index,
            "exit_marker": exit_marker,
            "messages": [{"role": "user", "content": "ask"},
                         {"role": "assistant", "content": text}]}


def manifest(ops, projections_by_conversation):
    return {"steering": {"ops": ops}, "sampling": {"temperature": 0.9},
            "rejected": [],
            "conversations": [
                {"id": f"item|s{i}", "final_turn_projections": projections}
                for i, projections in enumerate(projections_by_conversation)]}


def sweep_world():
    """(runs specs) — baseline plus a 3-point sweep on direction ``d``
    with slope 1.2, plus a combined run that must stay out of the fit."""
    world = [
        (manifest([], [{"d": 0.9, "o": 0.0}, {"d": 1.1, "o": 0.0}]),
         [transcript(0), transcript(1)]),
        (manifest([["add", "d", 0.5]], [{"d": 1.5, "o": 0.1},
                                        {"d": 1.7, "o": 0.1}]),
         [transcript(0), transcript(1)]),
        (manifest([["add", "d", 1.0]], [{"d": 2.1, "o": 0.2},
                                        {"d": 2.3, "o": 0.2}]),
         [transcript(0, text=""), transcript(1)]),
        (manifest([["add", "d", -0.5]], [{"d": 0.3, "o": -0.1},
                                         {"d": 0.5, "o": -0.1}]),
         [transcript(0), transcript(1, exit_marker="end_conversation")]),
        (manifest([["add", "d", 0.5], ["clamp", "o", 0.0]],
                  [{"d": 9.0, "o": 0.0}] * 2),
         [transcript(0), transcript(1)]),
    ]
    stamp = dc.provenance.current("test")
    return [dc.summarize_run(entry, transcripts, stamp)
            for entry, transcripts in world]


def test_sweep_alpha_classification():
    assert dc.sweep_alpha([]) == (None, 0.0)
    assert dc.sweep_alpha([["add", "d", 0.5]]) == ("d", 0.5)
    assert dc.sweep_alpha([["add", "d", 0.5], ["add", "o", 1.0]]) is None
    assert dc.sweep_alpha([["clamp", "d", 0.5]]) is None


def test_summarize_run_reads_manifest_and_screens():
    runs = sweep_world()
    baseline = runs[0]
    assert baseline["mean_projections"]["d"] == pytest.approx(1.0)
    assert baseline["degenerate_rate"] == 0.0
    high = runs[2]
    assert high["degenerate_rate"] == pytest.approx(0.5)
    exiting = runs[3]
    assert exiting["exit_rate"] == pytest.approx(0.5)


def test_analyze_fit_alpha_star_and_onset():
    report = dc.analyze(sweep_world(), {"d": 0.533}, threshold=0.10)
    entry = report["directions"]["d"]
    assert entry["baseline_mean"] == pytest.approx(1.0)
    assert [p["alpha"] for p in entry["points"]] == [-0.5, 0.5, 1.0]
    assert entry["fit"]["slope"] == pytest.approx(1.2)
    assert entry["fit"]["intercept"] == pytest.approx(0.0, abs=1e-9)
    assert entry["fit"]["r2"] == pytest.approx(1.0)
    assert entry["alpha_star"] == pytest.approx(0.533 / 1.2)
    assert entry["onset"] == {"positive": 1.0, "negative": None}
    assert "o" not in report["directions"]


def test_analyze_requires_exactly_one_baseline():
    runs = sweep_world()
    with pytest.raises(SystemExit, match="baseline"):
        dc.analyze(runs + [runs[0]], {}, threshold=0.10)
    with pytest.raises(SystemExit, match="baseline"):
        dc.analyze(runs[1:], {}, threshold=0.10)


def test_cli_end_to_end(tmp_path, monkeypatch):
    stamp_world = [
        (manifest([], [{"d": 1.0}] * 2), [transcript(0), transcript(1)]),
        (manifest([["add", "d", 0.5]], [{"d": 1.6}] * 2),
         [transcript(0), transcript(1)]),
    ]
    specs = []
    for index, (entry, transcripts) in enumerate(stamp_world):
        manifest_path = tmp_path / f"run{index}.manifest.json"
        manifest_path.write_text(json.dumps(entry))
        transcripts_path = tmp_path / f"run{index}.jsonl"
        transcripts_path.write_text(
            "".join(json.dumps(t) + "\n" for t in transcripts))
        specs += ["--run", f"{manifest_path}:{transcripts_path}"]
    out = tmp_path / "report.json"
    monkeypatch.setattr(sys, "argv", [
        "dose_calibrate.py", *specs, "--target", "d=0.3",
        "--out", str(out)])
    dc.main()
    report = json.loads(out.read_text())
    assert report["directions"]["d"]["alpha_star"] == pytest.approx(0.25)
    assert report["onset_threshold"] == 0.10
