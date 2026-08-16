# Pre-scale audit — the way forward

Purpose: stop the registration-amendment churn *before* we spend compute on the
larger-subject arms. Every amendment so far (§9, §10, the §2 reconciliation) came
from discovering — only after data was in hand — either that the registered text
claimed behavior the code never implemented, or that a design blind spot the data
exposed (SmolLM3-as-control, the verbatim-rejection distress battery, a
powerless refusal probe). Those are pre-run failures we have been catching
post-run. This audit front-loads that discovery so the big studies don't surface
it one gap at a time.

This is calibration/hygiene work, not a new experiment. It runs **now, once,
before resuming step 2** of the instrument-validation plan (see
`docs/PLANNING.md` → "Instrument validation, decoupled from quantization").

## Part 1 — Registration ↔ code conformance audit

Walk `PREREGISTRATION.md` §1–§8 claim by claim. For every *testable* claim, do
one of two things: point to the code that implements it **and** a test that pins
it, or record a gap. Then fix all gaps in a **single** reconciliation (one
amendment and/or code change), rather than a trickle of amendments. Where a claim
is pinned by a test, the registration becomes executable: the next drift fails CI
instead of waiting for a reviewer.

Claims to check (non-exhaustive; expand while reading):

- **Capability gate** — perplexity threshold (1.5× BF16) and invalid-rate
  threshold (10%); rung-level vs per-sample scope (just reconciled in §2/§10 —
  confirm the text now matches `analysis.capability_gate` + `analyze.py`).
- **Endpoint definitions** — E1 (aversion/refusal exit rate, bail items only),
  E2 (frustration, style-adjusted), E3 (across-sample SD, continuous only); each
  must match the function that computes it.
- **Multiplicity** — hierarchical Holm *within* families (E1 primary; E2/E3/trend
  separate), not a flat pool; confirm `analyze.py` matches the registered
  structure.
- **Trend test** — Page's L, ≥3 ordered rungs, over gate-passing rungs only; and
  that it is *not* applied to non-dose contrasts (e.g. the method arm).
- **H1 tests** — bail exit flip-fraction and distress band-flip nulls.
- **Determinism / sampling** — per-sample seed derivation (`base + sample_index`);
  sampling parameters identical across conditions in a manifest (already
  test-enforced — confirm the test covers what §3 claims).
- **Validity screen** — empty / low-diversity / n-gram-loop / repeated-turn
  criteria as described vs `analysis.is_degenerate` + `sample_is_degenerate`.
- **Judge / rubric** — pinned judge model + rubric versions, taxonomy digests.

Deliverable: an updated `PREREGISTRATION.md` (single reconciliation) plus a
`test_conformance`-style suite that asserts the registered constants and
behaviors, so code cannot silently drift from the registration.

## Part 2 — Pre-scale readiness gate

A checklist that must pass before any larger-subject (Qwen3-30B, MiniMax-M2) run.
It is the design-side complement to Part 1:

- **Power / MDE per endpoint.** A minimum-detectable-effect statement for every
  endpoint — the method-arm refusal centerpiece had none, and n = 28 near ceiling
  could not have detected a realistic shift. No endpoint ships without an MDE.
- **A known-effect positive control the instrument passes.** At least one
  manipulation with a known ground-truth effect that the pipeline detects
  (reviewer steps 3–4: base-vs-instruct, and a controllable prompt dial /
  Gemma-on-distress with a stated MDE). Instrument validation must be decoupled
  from quantization.
- **Batteries exercised against structural edge cases.** Each battery run against
  the shapes that confound the screens — verbatim-repeated turns, floor/ceiling
  items — so a Bug-A-style screen misfire is caught at authoring time.

## Sequencing

1. This audit (Part 1 now; Part 2 checklist drafted now, enforced before scaling).
2. Resume the reviewer's five steps **in order**: step 2 (graded judge
   validation) → step 3 (regression-toward-base) → step 4 (controllable positive
   control + MDE, which absorbs the Bug B distress-battery escalation) → step 5
   (invalid-rate shift as a formal mechanical endpoint).

Do not jump ahead: Bug B is fixed *at* step 4, not before it.
