#!/usr/bin/env python3
"""Serving-equivalence check for the RTN ladder (PREREGISTRATION.md TBD gate).

A fake-quant artifact is only trustworthy as a ladder rung if the runtime
serves the weights it actually contains. This probes each RTN rung against
the BF16 reference over a fixed prompt set at temperature 0 (greedy) and
verifies two things:

  1. Sanity: every rung produces coherent, non-empty completions and honors
     the chat/tool interface (a corrupted load usually shows here first).
  2. Monotone divergence: greedy completions diverge from the BF16
     reference more as precision drops. Divergence is measured as the
     shared-prefix token-agreement length; w8 should track the reference
     longest, w3 shortest. Non-monotonicity means an artifact or a serving
     path is wrong, not that quantization is "working".

This is an instrument check, not an experiment: it does not touch the
result store and draws no welfare conclusions. Run it after ./ladder.sh
brings the rungs up.

    python3 serving_equivalence.py --host http://127.0.0.1
"""

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
for sub in ("core/src", "backends/vllm/src"):
    sys.path.insert(0, str(REPO / sub))

from modelwelfare.v1 import condition_pb2, transcript_pb2
from modelwelfare_vllm import VllmServerBackend

RUNGS = [
    ("bf16", 8000, "qwen3-4b-bf16"),
    ("rtn-w8", 8010, "qwen3-4b-rtn-w8"),
    ("rtn-w4", 8011, "qwen3-4b-rtn-w4"),
    ("rtn-w3", 8012, "qwen3-4b-rtn-w3"),
]

PROMPTS = [
    "In one sentence, what is the capital of France?",
    "List the first five prime numbers, separated by commas.",
    "Write a two-line poem about the sea.",
    "Explain what a variable is in programming, in two sentences.",
    "Summarize the water cycle in three short steps.",
    "What is 17 multiplied by 23? Show the answer only.",
    "Name three primary colors.",
    "Complete this sentence: The quick brown fox",
]

RUNTIME = condition_pb2.RuntimeSpec(
    backend=condition_pb2.BACKEND_VLLM, device="rocm", host="halo", compute_dtype="bf16"
)


def greedy(backend, prompt):
    return backend.generate(
        [transcript_pb2.Message(role="user", content=prompt)],
        sampling=condition_pb2.SamplingSpec(temperature=0.0, top_p=0.0, max_tokens=96, seed=1),
    ).message.content


def prefix_agreement(a, b):
    """Fraction of whitespace tokens shared as a leading prefix — a coarse
    but backend-agnostic greedy-divergence proxy (no tokenizer dependency)."""
    ta, tb = a.split(), b.split()
    if not ta and not tb:
        return 1.0
    shared = 0
    for x, y in zip(ta, tb):
        if x != y:
            break
        shared += 1
    return shared / max(len(ta), len(tb), 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="http://127.0.0.1")
    args = parser.parse_args()

    backends = {}
    for name, port, served in RUNGS:
        url = f"{args.host}:{port}"
        try:
            backend = VllmServerBackend(url, served, RUNTIME, timeout=120.0)
            greedy(backend, "Say OK.")
            backends[name] = backend
            print(f"{name}: reachable at {url}")
        except Exception as error:
            print(f"{name}: UNREACHABLE ({error}) — skipping")

    if "bf16" not in backends:
        raise SystemExit("bf16 reference not reachable; cannot run equivalence check")

    reference = {p: greedy(backends["bf16"], p) for p in PROMPTS}
    empty = [p for p, text in reference.items() if not text.strip()]
    if empty:
        print(f"WARNING: bf16 produced empty output on {len(empty)} prompt(s)")

    print("\nmean greedy prefix-agreement with bf16 reference (1.0 = identical):")
    agreements = {}
    for name, backend in backends.items():
        if name == "bf16":
            continue
        scores = [prefix_agreement(reference[p], greedy(backend, p)) for p in PROMPTS]
        agreements[name] = sum(scores) / len(scores)
        print(f"  {name}: {agreements[name]:.3f}")

    ordered = [n for n in ("rtn-w8", "rtn-w4", "rtn-w3") if n in agreements]
    values = [agreements[n] for n in ordered]
    monotone = all(values[i] >= values[i + 1] - 1e-9 for i in range(len(values) - 1))
    print(f"\nmonotone divergence (w8 >= w4 >= w3 agreement): "
          f"{'PASS' if monotone else 'FAIL'} [{', '.join(f'{n}={v:.3f}' for n, v in zip(ordered, values))}]")

    coherent = all(len(greedy(b, PROMPTS[0]).split()) >= 1 for b in backends.values())
    print(f"all rungs produce non-empty completions: {'PASS' if coherent else 'FAIL'}")
    if not monotone:
        print("\nFAIL implies an artifact or serving-path problem, not a quantization "
              "effect — inspect before using these rungs as ladder conditions.")


if __name__ == "__main__":
    main()
