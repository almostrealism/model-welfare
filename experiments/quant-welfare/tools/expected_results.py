#!/usr/bin/env python3
"""Golden-results check: analyze.py's output as committed data.

Every statistic in the analysis is seeded (stats.py defaults), so the same
data must reproduce the same numbers exactly — this tool makes that a
checkable claim. ``--write`` serializes the full ``analyze()`` result for
an experiment; ``--check`` (default) recomputes and compares against the
committed file, tolerating only float noise (rel 1e-6 / abs 1e-9).

    # CI, from the released bundle:
    python3 tools/expected_results.py --experiment study1/confirmatory \\
        --bundle quant-welfare-confirmatory-1.pb \\
        --perplexity study1/confirmatory/perplexity.json

    # maintainer-side regeneration after an INTENTIONAL statistical change
    # (a registration/amendment event, never a casual refresh):
    python3 tools/expected_results.py --write ...

The expected file lives beside the experiment manifest
(``<experiment>/expected-results.json``).
"""
import argparse
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
REPO = BASE.parents[1]
for path in (str(REPO / "core/src"), str(BASE)):
    if path not in sys.path:
        sys.path.insert(0, path)

import analyze  # noqa: E402
from modelwelfare.bundle import BundleStore  # noqa: E402
from modelwelfare.store import ResultStore  # noqa: E402

RELATIVE_TOLERANCE = 1e-6
ABSOLUTE_TOLERANCE = 1e-9


def compute(args) -> dict:
    experiment_dir = BASE / args.experiment
    experiment = analyze.load_experiment(experiment_dir)
    store = BundleStore(args.bundle) if args.bundle else ResultStore(args.data_root)
    samples, scores, classifications = analyze.read_streams(store, experiment)
    if not samples:
        raise SystemExit(f"no stored samples for {experiment.id}")
    bail_items, _ = analyze.item_roles(
        experiment, analyze.batteries_for(experiment_dir))
    perplexity = (json.loads(Path(args.perplexity).read_text())
                  if args.perplexity else None)
    result = analyze.analyze(experiment, samples, scores, classifications,
                             perplexity, bail_items)
    return json.loads(json.dumps(result, default=float, sort_keys=True))


def differences(expected, actual, path=""):
    """Recursive comparison with float tolerance; yields human-readable
    difference lines."""
    if isinstance(expected, dict) and isinstance(actual, dict):
        for key in sorted(set(expected) | set(actual)):
            if key not in expected or key not in actual:
                yield f"{path}.{key}: present in only one side"
            else:
                yield from differences(expected[key], actual[key],
                                       f"{path}.{key}")
    elif isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            yield f"{path}: length {len(expected)} != {len(actual)}"
        else:
            for index, (left, right) in enumerate(zip(expected, actual)):
                yield from differences(left, right, f"{path}[{index}]")
    elif isinstance(expected, float) or isinstance(actual, float):
        try:
            left, right = float(expected), float(actual)
        except (TypeError, ValueError):
            yield f"{path}: {expected!r} != {actual!r}"
            return
        if left != right and abs(left - right) > max(
                ABSOLUTE_TOLERANCE, RELATIVE_TOLERANCE * max(abs(left), abs(right))):
            yield f"{path}: {left!r} != {right!r}"
    elif expected != actual:
        yield f"{path}: {expected!r} != {actual!r}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment", default="study1/confirmatory")
    parser.add_argument("--data-root", default=str(REPO / "data"))
    parser.add_argument("--bundle", default=None)
    parser.add_argument("--perplexity", default=None)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    expected_path = BASE / args.experiment / "expected-results.json"
    result = compute(args)
    if args.write:
        expected_path.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
        print(f"wrote {expected_path}")
        return 0

    expected = json.loads(expected_path.read_text())
    diffs = list(differences(expected, result))
    for line in diffs[:40]:
        print(f"RESULT DRIFT: {line}", file=sys.stderr)
    if diffs:
        print(f"{len(diffs)} difference(s) vs {expected_path}", file=sys.stderr)
        return 1
    print(f"results reproduce {expected_path} exactly (within float noise)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
