#!/usr/bin/env python3
"""Per-condition perplexity for the capability gate (PREREGISTRATION guard).

Measures per-token perplexity of a fixed held-out text on each ladder rung via
the vLLM /v1/completions endpoint (echo + logprobs), then applies the
capability gate: a rung whose perplexity exceeds 1.5x the BF16 rung's is
flagged capability-degraded, and its welfare endpoints (E1/E2) are excluded
from the primary confirmatory claims and the dose-response fit. This is an
instrument/capability check, not an experiment — it touches no result store and
draws no welfare conclusions.

    python3 perplexity.py --host http://127.0.0.1
"""
import argparse
import json
import math
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "core/src"))

from modelwelfare.analysis import capability_gate  # noqa: E402

RUNGS = [
    ("bf16", 8000, "qwen3-4b-bf16"),
    ("rtn-w8", 8010, "qwen3-4b-rtn-w8"),
    ("rtn-w4", 8011, "qwen3-4b-rtn-w4"),
    ("rtn-w3", 8012, "qwen3-4b-rtn-w3"),
]

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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="http://127.0.0.1")
    args = parser.parse_args()

    ppl = {}
    for name, port, model in RUNGS:
        url = f"{args.host}:{port}"
        try:
            ppl[name] = perplexity(url, model, HELDOUT)
            print(f"{name:8} perplexity={ppl[name]:.3f}")
        except Exception as error:
            print(f"{name:8} UNREACHABLE ({error})")

    if "bf16" not in ppl:
        raise SystemExit("bf16 reference unreachable; cannot apply the gate")

    print("\ncapability gate (degraded = perplexity > 1.5x bf16 reference):")
    gate = capability_gate(ppl, "bf16")
    for name, _, _ in RUNGS:
        if name not in ppl:
            continue
        entry = gate[name]
        state = "DEGRADED" if entry["degraded"] else "ok"
        print(f"  {name:8} {state:9} {'; '.join(entry['reasons'])}")


if __name__ == "__main__":
    main()
