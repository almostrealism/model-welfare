# Steering-sufficiency probes — summary (calibration-class, 2026-09-06/07)

Three probes tested whether steering the frozen welfare directions produces a
**direction-specific** behavioral (judged-frustration) effect, each compared to
a matched-norm 32-direction random envelope. All n=8 items (calibration
previews). Verdict: **no direction-specific steering effect** across two
directions and two doses.

| Probe | Direction / dose | Effect | Percentile of matched random envelope | Specific? |
|---|---|---|---|---|
| distress @ α* | distress-contrast, α*=+1.039 | +0.138 | 34th | no (below envelope) |
| assistant-axis @ α* | assistant-axis, α*=−0.604 | +0.225 (right sign per S3-H1) | 56th | no (center of band) |
| distress @ larger α | distress-contrast, α=3.5 | −0.075 | 56th | no (effect ~vanished) |

**Reading.** At its calibrated dose, each frozen direction moves the
*representation* (projection) as intended but produces a *behavioral* effect
indistinguishable from — often below — norm-matched random perturbation. The
assistant axis (Study 2's more robust direction) is marginally the best, right
sign, but still centered in the random band. A larger dose degrades rather than
sharpens the effect. So in Qwen3-4B, steering frozen welfare directions is not a
specific behavioral lever — the directions read as correlational, not causally
sufficient for behavior.

**By contrast**, the framing arm (Q3) already moved judged frustration −1.13
(verifier frame), far outside any envelope — a real, prompt-level behavioral
intervention.

Artifacts: `randenv-verdict.json` (distress @ α*), `axisenv-verdict.json`
(axis; internal labels say "distress" but the reference value is the axis
effect 0.225), `bigdose-verdict.json` (distress @ 3.5), `het-pilot-verdict.json`
(distress effect + heterogeneity).

**Open fork for the owner:** conclude the steering-null holds for this subject
and make framing the registration spine (Q1/Q2 reported as an honest null), or
first test whether it is a small-model artifact via a subject switch (d) before
concluding. The null is robust *within* Qwen3-4B across direction and dose.
