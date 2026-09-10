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

    python3 tools/make_random_envelope.py \\
        --reference study4/directions/mediators-14b.safetensors \\
        --key grader-type --layer 24 --count 12 --seed 70000 \\
        --out study4/directions/randenv-14b-L24.safetensors
"""
import argparse
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
REPO = BASE.parents[1]
for path in (str(REPO / "core/src"),):
    if path not in sys.path:
        sys.path.insert(0, path)

import numpy as np  # noqa: E402
from safetensors.numpy import load_file, save_file  # noqa: E402

COSINE_CEILING = 0.15


def random_unit_directions(dim, count, seed):
    """K unit vectors in R^dim from a fixed seed (reproducible envelope)."""
    generator = np.random.default_rng(seed)
    draws = generator.standard_normal((count, dim)).astype(np.float32)
    return draws / np.linalg.norm(draws, axis=1, keepdims=True)


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
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    reference = load_file(args.reference)
    ref_key = f"{args.key}|L{args.layer}"
    if ref_key not in reference:
        raise SystemExit(f"{ref_key!r} not in {args.reference} "
                         f"(has: {sorted(reference)})")
    target = reference[ref_key].astype(np.float32)
    target = target / np.linalg.norm(target)

    directions = random_unit_directions(target.shape[0], args.count, args.seed)
    cosines = directions @ target
    worst = float(np.max(np.abs(cosines)))
    if worst > COSINE_CEILING:
        raise SystemExit(
            f"a random draw has |cos| {worst:.3f} > {COSINE_CEILING} to the "
            "reference — reseed; the envelope would leak target signal")

    saved = {f"rand{index:02d}|L{args.layer}": directions[index]
             for index in range(args.count)}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    save_file(saved, args.out)
    print(f"wrote {args.count} matched-norm random directions -> {args.out}")
    print(f"|cos to {args.key}|: max {worst:.3f}, mean "
          f"{float(np.mean(np.abs(cosines))):.3f}")


if __name__ == "__main__":
    main()
