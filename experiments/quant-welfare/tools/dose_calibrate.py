#!/usr/bin/env python3
"""Dose calibration: the α ↔ projection mapping and the degradation onset.

Consumes the (manifest, transcripts) pairs a steering α sweep produced on
the workbench — one run per α per direction, plus the shared α = 0
baseline — and computes what the Study 3 §3.4 freeze needs: the achieved
mean final-turn projection per direction at every dose (the manifests
already echo per-conversation projections), the delta-vs-α fit and the
matched dose α* for each registered target, and the degradation onset
(the smallest |α| whose validity-screen rate crosses the threshold).

The naive expectation is delta ≈ α — pooling is linear, so the additive
component of the injection lands on the pooled projection exactly — but
the injection also steers the *generated text*, whose representation
moves the projection again (the Study 2 own-generation loop). The
mapping is therefore measured, never assumed, and the fit's slope is
itself a finding: slope > 1 is text-mediated amplification of the
injected dose, slope < 1 is damping.

Validity reads reuse the registered screens verbatim: each transcript
becomes an in-memory SampleRecord via the ingestion builder, and
``sample_is_degenerate`` / ``sample_reoffers`` — the same functions the
mechanical endpoints use — produce the rates. Runs with several steering
ops (cancellation pilots) are summarized but excluded from
single-direction fits. Calibration-class under the §7 firewall: BF16
sweeps only, no quantized rung enters dose selection.

    python3 experiments/quant-welfare/tools/dose_calibrate.py \\
        --run sweep-a0.safetensors.manifest.json:sweep-a0.jsonl \\
        --run sweep-dp05.safetensors.manifest.json:sweep-dp05.jsonl \\
        ... \\
        --target distress-contrast=0.533 --target assistant-axis=-0.798 \\
        --onset-threshold 0.10 --out dose-report.json
"""

import argparse
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
REPO = BASE.parents[1]
for path in (str(REPO / "core/src"), str(BASE / "tools")):
    if path not in sys.path:
        sys.path.insert(0, path)

import numpy as np  # noqa: E402

from ingest_steered import build_record  # noqa: E402
from modelwelfare import provenance  # noqa: E402
from modelwelfare.analysis import sample_is_degenerate, sample_reoffers  # noqa: E402


def sweep_alpha(ops):
    """(direction, alpha) for a single-add sweep run, (None, 0.0) for the
    baseline, and None for a combined run (several ops — excluded from
    per-direction fits)."""
    if not ops:
        return None, 0.0
    if len(ops) == 1 and ops[0][0] == "add":
        return ops[0][1], float(ops[0][2])
    return None


def summarize_run(manifest, entries, stamp):
    """One sweep run's summary row from its manifest and transcripts."""
    projections = {}
    for conversation in manifest["conversations"]:
        for name, value in conversation["final_turn_projections"].items():
            projections.setdefault(name, []).append(value)
    degenerate = reoffers = exits = 0
    chars = []
    for entry in entries:
        record = build_record(entry, manifest.get("sampling", {}),
                              "dose-calibration", "sweep", stamp)
        flagged, _reason = sample_is_degenerate(record)
        degenerate += 1 if flagged else 0
        reoffers += 1 if sample_reoffers(record) else 0
        exits += 1 if entry.get("exit_marker") else 0
        chars.append(sum(len(m["content"]) for m in entry["messages"]
                         if m["role"] == "assistant"))
    count = len(entries)
    return {
        "ops": manifest["steering"]["ops"],
        "n": count,
        "rejected": len(manifest.get("rejected", [])),
        "mean_projections": {name: float(np.mean(values))
                             for name, values in projections.items()},
        "sd_projections": {name: float(np.std(values, ddof=1))
                           if len(values) > 1 else 0.0
                           for name, values in projections.items()},
        "degenerate_rate": degenerate / count if count else 0.0,
        "reoffer_rate": reoffers / count if count else 0.0,
        "exit_rate": exits / count if count else 0.0,
        "mean_assistant_chars": float(np.mean(chars)) if chars else 0.0,
    }


def direction_curves(runs):
    """{direction: sorted [(alpha, run)]} from single-add sweep runs."""
    curves = {}
    for run in runs:
        parsed = sweep_alpha(run["ops"])
        if parsed is None or parsed[0] is None:
            continue
        direction, alpha = parsed
        curves.setdefault(direction, []).append((alpha, run))
    for points in curves.values():
        points.sort(key=lambda pair: pair[0])
    return curves


def fit_deltas(points):
    """Least-squares delta = slope·α + intercept over (α, delta) points;
    a single point fits through the origin (delta at α = 0 is zero by
    construction — deltas are taken against the baseline)."""
    alphas = np.array([alpha for alpha, _delta in points])
    deltas = np.array([delta for _alpha, delta in points])
    if len(points) == 1:
        return {"slope": float(deltas[0] / alphas[0]), "intercept": 0.0,
                "r2": 1.0}
    slope, intercept = np.polyfit(alphas, deltas, 1)
    predicted = slope * alphas + intercept
    residual = float(np.sum((deltas - predicted) ** 2))
    total = float(np.sum((deltas - deltas.mean()) ** 2))
    r2 = 1.0 - residual / total if total > 0 else 1.0
    return {"slope": float(slope), "intercept": float(intercept), "r2": r2}


def alpha_for_target(fit, target):
    """The α at which the fitted delta equals the target."""
    if fit["slope"] == 0:
        return None
    return (target - fit["intercept"]) / fit["slope"]


def degradation_onset(points, threshold):
    """Smallest-|α| crossing of the degenerate-rate threshold, per sign."""
    positive = sorted((alpha for alpha, run in points
                       if alpha > 0 and run["degenerate_rate"] > threshold))
    negative = sorted((alpha for alpha, run in points
                       if alpha < 0 and run["degenerate_rate"] > threshold),
                      reverse=True)
    return {"positive": positive[0] if positive else None,
            "negative": negative[0] if negative else None}


def analyze(runs, targets, threshold):
    """The per-direction calibration report from summarized runs."""
    baselines = [run for run in runs if sweep_alpha(run["ops"]) == (None, 0.0)]
    if len(baselines) != 1:
        raise SystemExit(f"expected exactly one α = 0 baseline run, "
                         f"found {len(baselines)}")
    baseline = baselines[0]
    directions = {}
    for direction, points in direction_curves(runs).items():
        base_mean = baseline["mean_projections"][direction]
        deltas = [(alpha, run["mean_projections"][direction] - base_mean)
                  for alpha, run in points]
        fit = fit_deltas(deltas)
        entry = {
            "baseline_mean": base_mean,
            "points": [{
                "alpha": alpha,
                "delta": delta,
                "degenerate_rate": run["degenerate_rate"],
                "exit_rate": run["exit_rate"],
                "mean_projections": run["mean_projections"],
            } for (alpha, delta), (_alpha, run) in zip(deltas, points)],
            "fit": fit,
            "onset": degradation_onset(points, threshold),
        }
        if direction in targets:
            entry["target_delta"] = targets[direction]
            entry["alpha_star"] = alpha_for_target(fit, targets[direction])
        directions[direction] = entry
    return {"baseline": baseline, "directions": directions}


def parse_targets(specs):
    targets = {}
    for spec in specs or []:
        name, _, value = spec.partition("=")
        if not name or not value:
            raise SystemExit(f"malformed target {spec!r}; expected NAME=DELTA")
        targets[name] = float(value)
    return targets


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="append", required=True,
                        metavar="MANIFEST:TRANSCRIPTS",
                        help="one sweep run's capture manifest and "
                             "transcripts JSONL (repeatable)")
    parser.add_argument("--target", action="append", default=[],
                        metavar="NAME=DELTA",
                        help="registered projection-delta target for a "
                             "direction (α* is solved from the fit)")
    parser.add_argument("--onset-threshold", type=float, default=0.10,
                        help="degenerate-rate threshold defining the "
                             "degradation onset (default: the capability "
                             "gate's 10%%)")
    parser.add_argument("--out", required=True, help="JSON report path")
    args = parser.parse_args()

    stamp = provenance.current("dose-calibrate")
    runs = []
    for spec in args.run:
        manifest_path, _, transcripts_path = spec.partition(":")
        if not transcripts_path:
            raise SystemExit(f"malformed --run {spec!r}; expected "
                             "MANIFEST:TRANSCRIPTS")
        with open(manifest_path) as handle:
            manifest = json.load(handle)
        entries = [json.loads(line)
                   for line in Path(transcripts_path).read_text().splitlines()
                   if line.strip()]
        runs.append(summarize_run(manifest, entries, stamp))

    report = analyze(runs, parse_targets(args.target), args.onset_threshold)
    report["onset_threshold"] = args.onset_threshold
    with open(args.out, "w") as handle:
        json.dump(report, handle, indent=1)
    for direction, entry in report["directions"].items():
        line = (f"{direction}: slope {entry['fit']['slope']:+.3f} "
                f"(r2 {entry['fit']['r2']:.3f})")
        if "alpha_star" in entry:
            line += (f", α* {entry['alpha_star']:+.3f} for target "
                     f"{entry['target_delta']:+.3f}")
        onset = entry["onset"]
        line += (f", onset +{onset['positive']}" if onset["positive"]
                 is not None else ", onset +none")
        line += (f"/{onset['negative']}" if onset["negative"]
                 is not None else "/none")
        print(line)


if __name__ == "__main__":
    main()
