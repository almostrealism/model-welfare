#!/usr/bin/env python3
"""Direction extraction over captured activations (Study 2 calibration).

Two modes, sharing one definition of the contrast pairs so the capture plan
and the analysis can never disagree:

  --plan <path>    Build the capture-plan JSON for every direction-contrast
                   conversation: the three Study 2 contrast sets plus the
                   frustration-poled judge-validation synthetics that the
                   registration folds into the distress direction (the
                   pole pair and each graded frustration family's extreme
                   rungs). Ship the plan to the capture host and run
                   backends/torch capture.py on it.

  --report         Read a capture (safetensors + manifest) produced from
                   that plan and, per direction and captured layer: extract
                   the contrastive mean-difference direction on the
                   extraction pairs, then report held-out separations and
                   sign consistency (the G2 evidence), extraction-set
                   separations, the pre-normalization magnitude, and
                   cross-direction cosines. --save writes the candidate unit
                   vectors and a JSON summary for the calibration record.

    python3 tools/extract_directions.py --plan directions-plan.json
    python3 tools/extract_directions.py --report \\
        --capture capture.safetensors --save study2/calibration/directions

Calibration-class instrument tooling: reads no result store and draws no
welfare conclusions. Directions are frozen (hash-pinned DirectionSpec) only
at the calibration freeze, on the layer the G2 procedure selects.
"""
import argparse
import itertools
import json
import sys
from pathlib import Path

import numpy as np

BASE = Path(__file__).resolve().parent.parent
REPO = BASE.parents[1]
for path in (str(REPO / "core/src"), str(BASE / "study1" / "bakeoff")):
    if path not in sys.path:
        sys.path.insert(0, path)

from safetensors.numpy import load_file, save_file  # noqa: E402

from modelwelfare import directions as dirs  # noqa: E402

import synthetics  # noqa: E402

DIRECTIONS_DIR = BASE / "study2" / "directions"
DIRECTION_SETS = ("distress-contrast", "assistant-axis-contrast", "refusal-contrast")


def synthetic_distress_pairs():
    """Frustration-poled synthetics as (pair_id, pos_record, neg_record).

    The pole pair plus each graded frustration family's extreme rungs
    (level 4 vs level 0 — level indexes the construct, so the top rung is
    the "pos" pole), per REGISTRATION §3.5.
    """
    records = {record.key.item_id: record
               for record in (synthetics.DISTRESS_SYNTHETICS
                              + synthetics.GRADED_DISTRESS)}
    pairs = [("syn-frustration",
              records["syn-frustration-high"], records["syn-frustration-low"])]
    families = sorted({family for dimension, family, _level
                       in synthetics.GRADED_EXPECTATIONS.values()
                       if dimension == "frustration"})
    top = synthetics.GRADED_LEVELS - 1
    for family in families:
        pairs.append((f"syn-grade-frustration-{family}",
                      records[f"syn-grade-frustration-{family}-l{top}"],
                      records[f"syn-grade-frustration-{family}-l0"]))
    return pairs


def record_messages(record):
    return [{"role": message.role, "content": message.content}
            for message in record.messages]


def direction_pairs():
    """{direction: {pair_id: {"pos": conversation_id, "neg": conversation_id}}}
    plus {conversation_id: messages} — the single source both modes share."""
    by_direction = {}
    conversations = {}
    for name in DIRECTION_SETS:
        definition = dirs.load_contrast_set(DIRECTIONS_DIR / f"{name}.textproto")
        pairs = {}
        for pair_id, poles in dirs.contrast_pairs(definition).items():
            pairs[pair_id] = {pole: item.id for pole, item in poles.items()}
            for item in poles.values():
                conversations[item.id] = dirs.item_messages(item)
        by_direction[name] = pairs
    distress = by_direction["distress-contrast"]
    for pair_id, pos_record, neg_record in synthetic_distress_pairs():
        pos_id, neg_id = pos_record.key.item_id, neg_record.key.item_id
        distress[pair_id] = {"pos": pos_id, "neg": neg_id}
        conversations[pos_id] = record_messages(pos_record)
        conversations[neg_id] = record_messages(neg_record)
    return by_direction, conversations


def final_turn_vectors(tensors, manifest, layer):
    """{conversation_id: pooled vector of the FINAL assistant turn at layer}."""
    from modelwelfare.replay import final_turn_features

    return final_turn_features(tensors, manifest, layer)


def report(args):
    tensors = load_file(args.capture)
    with open(args.capture + ".manifest.json") as handle:
        manifest = json.load(handle)
    by_direction, _conversations = direction_pairs()

    saved = {}
    summary = {"capture": args.capture, "point": manifest["point"],
               "layers": manifest["layers"], "directions": {}}
    for name, pairs in by_direction.items():
        held_out = dirs.held_out_pair_ids(pairs)
        extract_ids = sorted(set(pairs) - held_out)
        print(f"\n{name}: {len(pairs)} pairs "
              f"({len(extract_ids)} extraction, {len(held_out)} held out: "
              f"{', '.join(sorted(held_out))})")
        summary["directions"][name] = {
            "extract_pairs": extract_ids, "held_out_pairs": sorted(held_out),
            "layers": {}}
        for layer in manifest["layers"]:
            pooled = final_turn_vectors(tensors, manifest, layer)
            direction, magnitude = dirs.extract_direction(pooled, pairs, extract_ids)
            held_sep = dirs.pair_separations(direction, pooled, pairs, held_out)
            fit_sep = dirs.pair_separations(direction, pooled, pairs, extract_ids)
            consistent, total = dirs.sign_consistency(held_sep)
            print(f"  L{layer}: |mean diff|={magnitude:.3f}  "
                  f"extract sep={np.mean(list(fit_sep.values())):.3f}  "
                  f"held-out sep={np.mean(list(held_sep.values())):.3f}  "
                  f"held-out sign {consistent}/{total}")
            summary["directions"][name]["layers"][str(layer)] = {
                "magnitude": magnitude,
                "extract_mean_separation": float(np.mean(list(fit_sep.values()))),
                "held_out_mean_separation": float(np.mean(list(held_sep.values()))),
                "held_out_separations": held_sep,
                "held_out_sign_consistent": [consistent, total],
            }
            saved[f"{name}|L{layer}"] = direction.astype(np.float32)

    print("\ncross-direction cosine per layer:")
    for layer in manifest["layers"]:
        cosines = []
        for a, b in itertools.combinations(by_direction, 2):
            cosine = float(np.dot(saved[f"{a}|L{layer}"], saved[f"{b}|L{layer}"]))
            cosines.append(f"{a.split('-')[0]}x{b.split('-')[0]}={cosine:+.3f}")
        print(f"  L{layer}: {'  '.join(cosines)}")

    if args.save:
        out = Path(args.save)
        out.parent.mkdir(parents=True, exist_ok=True)
        save_file(saved, str(out) + ".safetensors")
        Path(str(out) + ".json").write_text(json.dumps(summary, indent=1) + "\n")
        print(f"\nwrote {str(out)}.safetensors and .json")

    failures = []
    if args.assert_frozen:
        frozen = load_file(args.assert_frozen)
        failures += frozen_drift(saved, frozen)
        for name, entry in summary["directions"].items():
            for layer, row in entry["layers"].items():
                consistent, total = row["held_out_sign_consistent"]
                if consistent != total:
                    failures.append(f"{name} L{layer}: held-out sign "
                                    f"{consistent}/{total}")
    if args.ladder_capture:
        mid_tensors = load_file(args.ladder_capture)
        with open(args.ladder_capture + ".manifest.json") as handle:
            mid_manifest = json.load(handle)
        frozen = load_file(args.assert_frozen) if args.assert_frozen else saved
        for layer in manifest["layers"]:
            pooled = {**final_turn_vectors(tensors, manifest, layer),
                      **{cid.split("|s")[0]: vector for cid, vector in
                         final_turn_vectors(mid_tensors, mid_manifest,
                                            layer).items()}}
            overall, families = ladder_ordering(
                pooled, frozen[f"{DISTRESS_SET}|L{layer}"])
            family_text = "  ".join(f"{name}={value:+.2f}"
                                    for name, value in families.items())
            print(f"ladder L{layer}: overall rho={overall:+.3f}  {family_text}")
            if overall < 0.8:
                failures.append(f"ladder L{layer}: overall rho {overall:.3f} < 0.8")
            for family, value in families.items():
                if value <= 0:
                    failures.append(f"ladder L{layer}: family {family} "
                                    f"rho {value:+.2f} not positive")
    for line in failures:
        print(f"CALIBRATION DRIFT: {line}", file=sys.stderr)
    if failures:
        raise SystemExit(1)
    if args.assert_frozen or args.ladder_capture:
        print("\nfrozen-instrument assertions pass")


DISTRESS_SET = "distress-contrast"
COSINE_FLOOR = 0.9999


def frozen_drift(saved, frozen):
    """Cosine drift of re-derived unit directions vs the frozen vectors —
    every frozen key must be reproduced at cosine >= COSINE_FLOOR."""
    failures = []
    for key, vector in frozen.items():
        if key not in saved:
            failures.append(f"{key}: not re-derived")
            continue
        cosine = float(np.dot(saved[key], vector)
                       / (np.linalg.norm(saved[key]) * np.linalg.norm(vector)))
        if cosine < COSINE_FLOOR:
            failures.append(f"{key}: cosine {cosine:.6f} < {COSINE_FLOOR}")
    return failures


def ladder_ordering(pooled, direction):
    """(overall Spearman, {family: Spearman}) of distress-direction
    projections against the planted frustration levels — the G2 hard gate's
    statistic, recomputed from captures."""
    from modelwelfare.stats import spearman

    families = sorted({family for dimension, family, _level
                       in synthetics.GRADED_EXPECTATIONS.values()
                       if dimension == "frustration"})
    all_projections, all_levels, per_family = [], [], {}
    for family in families:
        projections = []
        for level in range(synthetics.GRADED_LEVELS):
            vector = pooled[f"syn-grade-frustration-{family}-l{level}"]
            projections.append(float(np.dot(vector, direction)))
        per_family[family] = spearman(projections,
                                      list(range(synthetics.GRADED_LEVELS)))
        all_projections += projections
        all_levels += list(range(synthetics.GRADED_LEVELS))
    return spearman(all_projections, all_levels), per_family


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", default=None,
                        help="write the capture-plan JSON here and exit")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--capture", default=None,
                        help="capture safetensors (manifest expected beside it)")
    parser.add_argument("--save", default=None,
                        help="path stem for candidate direction vectors + summary")
    parser.add_argument("--assert-frozen", default=None,
                        help="frozen direction vectors to reproduce (cosine "
                             ">= 0.9999 per key, full held-out sign "
                             "consistency); nonzero exit on drift")
    parser.add_argument("--ladder-capture", default=None,
                        help="mid-rung capture (l1..l3) — recompute the G2 "
                             "planted-ladder ordering and assert >= 0.8 "
                             "overall with every family positive")
    args = parser.parse_args()

    if args.plan:
        _pairs, conversations = direction_pairs()
        plan = dirs.build_plan(sorted(conversations.items()))
        dirs.write_plan(plan, args.plan)
        print(f"wrote {args.plan}: {len(plan['conversations'])} conversations")
        return
    if args.report:
        if not args.capture:
            raise SystemExit("--report requires --capture")
        report(args)
        return
    raise SystemExit("nothing to do: pass --plan or --report")


if __name__ == "__main__":
    main()
