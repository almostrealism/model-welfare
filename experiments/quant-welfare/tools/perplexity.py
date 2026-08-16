#!/usr/bin/env python3
"""Per-condition perplexity for the capability gate (PREREGISTRATION guard).

Measures per-token perplexity of a fixed held-out text on every condition of an
experiment via the vLLM /v1/completions endpoint (echo + logprobs), then applies
the capability gate: a rung whose perplexity exceeds 1.5x the reference rung's
is flagged capability-degraded, and its welfare endpoints are excluded from the
primary confirmatory claims and the dose-response fit. This is an
instrument/capability check, not an experiment — it touches no result store and
draws no welfare conclusions.

The conditions and their serving endpoints come from the experiment manifest and
endpoints.json (PREREGISTRATION §11: the tool is parameterized by experiment,
never hardwired to one ladder — measure every rung BEFORE tearing it down).
Non-vLLM endpoints are skipped with a note: the measure is defined over vLLM
echo+logprobs.

    python3 tools/perplexity.py --experiment confirmatory --json perplexity.json
"""
import argparse
import json
import math
import sys
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent           # experiments/quant-welfare
REPO = BASE.parents[1]
for path in (str(REPO / "core/src"), str(BASE)):
    if path not in sys.path:
        sys.path.insert(0, path)

from google.protobuf import text_format  # noqa: E402

from modelwelfare.analysis import capability_gate  # noqa: E402
from modelwelfare.v1 import experiment_pb2  # noqa: E402

# A fixed neutral held-out paragraph (not drawn from any battery), so the
# measure is comparable across rungs and independent of the stimulus items.
HELDOUT = (
    "The history of science is a record of gradual and hard-won corrections. "
    "Each generation inherits the errors of the last and, with patient "
    "measurement, replaces a few of them with claims that are a little less "
    "wrong. Progress is rarely a single revelation; more often it is the slow "
    "accumulation of careful observations that no one can any longer ignore."
)


def perplexity(url: str, model: str, text: str, timeout: float = 60.0):
    """Per-token perplexity of ``text`` under the served model, via echo+logprobs."""
    payload = json.dumps({
        "model": model, "prompt": text, "max_tokens": 1,
        "echo": True, "logprobs": 1, "temperature": 0,
    }).encode("utf-8")
    request = urllib.request.Request(
        url + "/v1/completions", data=payload,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = json.loads(response.read().decode("utf-8"))
    token_logprobs = body["choices"][0]["logprobs"]["token_logprobs"]
    values = [x for x in token_logprobs if x is not None]
    if not values:
        return None
    return math.exp(-sum(values) / len(values))


def load_experiment(experiment_dir: Path) -> experiment_pb2.Experiment:
    experiment = experiment_pb2.Experiment()
    text_format.Parse((experiment_dir / "experiment.textproto").read_text(), experiment)
    return experiment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment", default="confirmatory",
                        help="experiment directory name under experiments/quant-welfare/")
    parser.add_argument("--endpoints", default=str(BASE / "endpoints.json"),
                        help="condition -> endpoint map (override for lab-local routing)")
    parser.add_argument("--json", default=None,
                        help="write {condition_id: perplexity} to this path — the "
                             "input analyze.py --perplexity expects for the gate")
    args = parser.parse_args()

    experiment = load_experiment(BASE / args.experiment)
    with open(args.endpoints) as handle:
        endpoints = {cid: entry for cid, entry in json.load(handle).items()
                     if not cid.startswith("_")}

    ppl = {}
    for condition in experiment.conditions:
        cid = condition.id
        entry = endpoints.get(cid)
        if entry is None:
            print(f"{cid:20} SKIPPED (no endpoint configured)")
            continue
        if entry.get("kind") != "vllm":
            print(f"{cid:20} SKIPPED ({entry.get('kind')} endpoint; measure is vLLM echo+logprobs)")
            continue
        try:
            ppl[cid] = perplexity(entry["url"], entry["model"], HELDOUT)
            print(f"{cid:20} perplexity={ppl[cid]:.3f}")
        except Exception as error:
            print(f"{cid:20} UNREACHABLE ({error})")

    reference = experiment.reference_condition_id
    if reference not in ppl:
        raise SystemExit(f"reference {reference} unreachable; cannot apply the gate")

    print("\ncapability gate (degraded = perplexity > 1.5x the reference):")
    gate = capability_gate(ppl, reference)
    for cid, entry in gate.items():
        state = "DEGRADED" if entry["degraded"] else "ok"
        print(f"  {cid:20} {state:9} {'; '.join(entry['reasons'])}")

    if args.json:
        Path(args.json).write_text(json.dumps(ppl, indent=2) + "\n")
        print(f"\nwrote {args.json}: {list(ppl)}")


if __name__ == "__main__":
    main()
