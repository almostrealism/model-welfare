#!/usr/bin/env python3
"""Mediator-direction extraction (grader-type, eval-awareness).

Distinct from ``extract_directions.py`` — that tool carries the Study 2
distress/axis/refusal sets together with their synthetic-pole augmentation
and the planted frustration ladder. The mediators are two plain
fixed-response contrast sets (``study3/directions/*-contrast.textproto``)
with neither, so this driver runs the SAME ``modelwelfare.directions`` math
over just the named sets and emits the compact per-direction summary plus
the cross-direction cosine the mediators file carries. Two modes share one
definition of the contrast pairs so the plan and the analysis cannot
disagree:

  --plan PATH   Write the capture plan for every named contrast set. With
                ``--enable-thinking-off`` the plan carries
                ``chat_template_kwargs={"enable_thinking": false}`` so a
                thinking-hybrid subject (Qwen3) renders identically at
                capture and at generation — without it the generation-prompt
                reasoning scaffold breaks span prefix-stability.
  --report      Read a capture (safetensors + manifest) and, per direction
                and captured layer, extract the contrastive mean-difference
                direction and report pre-normalization magnitude, held-out
                pole separation, and held-out sign consistency; also the
                pairwise cosine between directions. ``--save`` writes the
                unit vectors (.safetensors) and the JSON summary.

    python3 tools/extract_mediators.py --plan mediators-plan.json \\
        --set grader-type:experiments/quant-welfare/study3/directions/grader-type-contrast.textproto \\
        --set eval-awareness:experiments/quant-welfare/study3/directions/eval-awareness-contrast.textproto \\
        --enable-thinking-off
    python3 tools/extract_mediators.py --report --capture cap.safetensors \\
        --set grader-type:.../grader-type-contrast.textproto \\
        --set eval-awareness:.../eval-awareness-contrast.textproto \\
        --save experiments/quant-welfare/study4/directions/mediators-14b

Calibration-class instrument tooling: reads no result store and draws no
welfare conclusions.
"""
import argparse
import itertools
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
REPO = BASE.parents[1]
for path in (str(REPO / "core/src"),):
    if path not in sys.path:
        sys.path.insert(0, path)

import numpy as np  # noqa: E402
from safetensors.numpy import load_file, save_file  # noqa: E402

from modelwelfare import directions as dirs  # noqa: E402
from modelwelfare.replay import final_turn_features  # noqa: E402


def parse_sets(raw_sets):
    """[(name, path)] from repeatable ``NAME:PATH`` arguments."""
    parsed = []
    for entry in raw_sets:
        name, _, path = entry.partition(":")
        if not name or not path:
            raise SystemExit(f"--set expects NAME:PATH, got {entry!r}")
        parsed.append((name, path))
    if not parsed:
        raise SystemExit("pass at least one --set NAME:PATH")
    return parsed


def set_pairs(path):
    """({pair_id: {"pos": conv_id, "neg": conv_id}}, {conv_id: messages})
    for one contrast set — plain conversation-id pairs, as the extraction
    math wants them."""
    definition = dirs.load_contrast_set(path)
    pairs, conversations = {}, {}
    for pair_id, poles in dirs.contrast_pairs(definition).items():
        pairs[pair_id] = {pole: item.id for pole, item in poles.items()}
        for item in poles.values():
            conversations[item.id] = dirs.item_messages(item)
    return pairs, conversations


def build_plan(sets, chat_template_kwargs):
    conversations = {}
    for _name, path in sets:
        _pairs, set_conversations = set_pairs(path)
        conversations.update(set_conversations)
    plan = dirs.build_plan(sorted(conversations.items()))
    if chat_template_kwargs:
        plan["chat_template_kwargs"] = chat_template_kwargs
    return plan


def report(sets, capture_path, save):
    tensors = load_file(capture_path)
    with open(capture_path + ".manifest.json") as handle:
        manifest = json.load(handle)
    layers = manifest["layers"]

    saved = {}
    summary = {"capture": capture_path, "point": manifest["point"],
               "layers": layers, "directions": {}}
    for name, path in sets:
        pairs, _conversations = set_pairs(path)
        held_out = dirs.held_out_pair_ids(pairs)
        extract_ids = sorted(set(pairs) - held_out)
        print(f"\n{name}: {len(pairs)} pairs "
              f"({len(extract_ids)} extraction, {len(held_out)} held out: "
              f"{', '.join(sorted(held_out))})")
        summary["directions"][name] = {
            "extract_pairs": extract_ids, "held_out_pairs": sorted(held_out),
            "layers": {}}
        for layer in layers:
            pooled = final_turn_features(tensors, manifest, layer)
            direction, magnitude = dirs.extract_direction(
                pooled, pairs, extract_ids)
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

    summary["cross_cosine"] = {}
    print("\ncross-direction cosine per layer:")
    for layer in layers:
        row = {}
        for a, b in itertools.combinations([name for name, _ in sets], 2):
            cosine = float(np.dot(saved[f"{a}|L{layer}"], saved[f"{b}|L{layer}"]))
            row[f"{a}_vs_{b}"] = cosine
        summary["cross_cosine"][str(layer)] = row
        print(f"  L{layer}: "
              + "  ".join(f"{key}={value:+.3f}" for key, value in row.items()))

    if save:
        out = Path(save)
        out.parent.mkdir(parents=True, exist_ok=True)
        save_file(saved, str(out) + ".safetensors")
        Path(str(out) + ".json").write_text(json.dumps(summary, indent=1) + "\n")
        print(f"\nwrote {str(out)}.safetensors and .json")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--set", action="append", default=[], dest="sets",
                        metavar="NAME:PATH",
                        help="a contrast set to extract (repeatable)")
    parser.add_argument("--plan", default=None,
                        help="write the capture-plan JSON here and exit")
    parser.add_argument("--enable-thinking-off", action="store_true",
                        help="carry chat_template_kwargs enable_thinking=false "
                             "in the plan (Qwen3 thinking-hybrid subjects)")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--capture", default=None,
                        help="capture safetensors (manifest expected beside it)")
    parser.add_argument("--save", default=None,
                        help="path stem for candidate direction vectors + summary")
    args = parser.parse_args()
    sets = parse_sets(args.sets)

    if args.plan:
        chat_template_kwargs = ({"enable_thinking": False}
                                if args.enable_thinking_off else {})
        plan = build_plan(sets, chat_template_kwargs)
        dirs.write_plan(plan, args.plan)
        print(f"wrote {args.plan}: {len(plan['conversations'])} conversations"
              + (" (enable_thinking=false)" if args.enable_thinking_off else ""))
        return
    if args.report:
        if not args.capture:
            raise SystemExit("--report requires --capture")
        report(sets, args.capture, args.save)
        return
    raise SystemExit("nothing to do: pass --plan or --report")


if __name__ == "__main__":
    main()
