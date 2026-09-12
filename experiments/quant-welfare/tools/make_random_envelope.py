#!/usr/bin/env python3
"""Matched-norm random-direction envelope for a steering specificity test.

The direction-specificity control (LITERATURE §9): to show a steered
behavioral effect belongs to the target direction and not to any
perturbation of the same size, compare it to the effect of K random unit
directions steered at the same dose. This tool draws those K directions in
the residual space of a reference direction and writes them under
``{name}|L{layer}`` keys so ``steer.py --add`` applies each exactly as it
applies the real one (the saved reference is unit-norm, so unit random
draws are matched-norm). Each draw's cosine to the reference is reported
and asserted small — an accidental near-alignment would make the envelope
leak real signal (LITERATURE §9 audit).

The rejection bound is an explicit input: every invocation declares the
largest |cos| it will accept, and the bound, the measured maximum and
mean, the seed and the count are written to a JSON record beside the
safetensors, so a registration can cite what the file was drawn under.
The Gate 1 and Study 4 artifacts were drawn under 0.15 (their measured
maxima are far below it: 0.021 for the Study 4 file).

    python3 tools/make_random_envelope.py \\
        --reference study4/directions/mediators-14b.safetensors \\
        --key grader-type --layer 24 --count 12 --seed 70000 \\
        --cos-bound 0.15 --out study4/directions/randenv-14b-L24.safetensors
"""
import argparse
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


def random_unit_directions(dim, count, seed):
    """K unit vectors in R^dim from a fixed seed (reproducible envelope)."""
    generator = np.random.default_rng(seed)
    draws = generator.standard_normal((count, dim)).astype(np.float32)
    return draws / np.linalg.norm(draws, axis=1, keepdims=True)


def draw_envelope(target, count, seed, cos_bound):
    """``(directions, cosines)`` for K matched-norm random directions whose
    |cos| to the unit ``target`` all lie within ``cos_bound``; raises
    ValueError otherwise (reseed — the envelope would leak target signal).
    Pure, so the bound is testable without files."""
    if not 0 < cos_bound <= 1:
        raise ValueError(f"cos_bound must be in (0, 1], not {cos_bound}")
    directions = random_unit_directions(target.shape[0], count, seed)
    cosines = directions @ target
    worst = float(np.max(np.abs(cosines)))
    if worst > cos_bound:
        raise ValueError(
            f"a random draw has |cos| {worst:.3f} > {cos_bound} to the "
            "reference — reseed; the envelope would leak target signal")
    return directions, cosines


def record_path(out):
    return Path(str(out) + ".json")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", required=True,
                        help="safetensors holding the reference direction")
    parser.add_argument("--key", required=True,
                        help="direction name in the reference file (without "
                             "the |L{layer} suffix)")
    parser.add_argument("--layer", type=int, required=True)
    parser.add_argument("--count", type=int, default=12)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--cos-bound", type=float, required=True,
                        help="largest |cos| to the reference any draw may "
                             "have; the run refuses a draw above it")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    reference = load_file(args.reference)
    ref_key = f"{args.key}|L{args.layer}"
    if ref_key not in reference:
        raise SystemExit(f"{ref_key!r} not in {args.reference} "
                         f"(has: {sorted(reference)})")
    target = reference[ref_key].astype(np.float32)
    target = target / np.linalg.norm(target)

    try:
        directions, cosines = draw_envelope(target, args.count, args.seed,
                                            args.cos_bound)
    except ValueError as error:
        raise SystemExit(str(error))
    worst = float(np.max(np.abs(cosines)))

    saved = {f"rand{index:02d}|L{args.layer}": directions[index]
             for index in range(args.count)}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    save_file(saved, args.out)
    record = {"reference": str(args.reference), "key": args.key,
              "layer": args.layer, "count": args.count, "seed": args.seed,
              "cos_bound": args.cos_bound, "max_abs_cos": worst,
              "mean_abs_cos": float(np.mean(np.abs(cosines)))}
    record_path(args.out).write_text(json.dumps(record, indent=1) + "\n")
    print(f"wrote {args.count} matched-norm random directions -> {args.out}")
    print(f"|cos to {args.key}|: max {worst:.3f}, mean "
          f"{record['mean_abs_cos']:.3f} (bound {args.cos_bound}); "
          f"record -> {record_path(args.out)}")


if __name__ == "__main__":
    main()
