# Pre-registration — Confirmatory Study 1: Quantization × Welfare Indicators

**Status: v1 draft, 2026-08-07 — registered in advance of confirmatory data
collection.** Everything in "Fixed" sections is committed before the study
runs; "TBD" sections list what remains open and which measurement resolves
each item. Amendments after registration are permitted only via dated
entries in [docs/JOURNAL.md](docs/JOURNAL.md), with the git history as the
audit trail. Calibration-class runs already in this repository
(`quant-welfare-trial-1`, `instrument-calibration-1`, `bail-tool-arms-1`,
`judge-bakeoff-1`) informed the *instruments* below but, per the standing
pre-registration note in
[experiments/quant-welfare/README.md](experiments/quant-welfare/README.md),
none of their observed deltas are findings and none were used to select
hypotheses.

## 1. Research questions

Post-training quantization is applied to nearly every deployed open-weight
model but audited almost exclusively through capability metrics known to
stay flat while fine-grained behavioral dispositions shift. We ask whether
**welfare-relevant indicators** change under quantization, in:

- **Valence** — do indicators shift toward more negative states (more
  distress expression, more aversion-motivated exits)?
- **Stability** — do indicators become noisier across independent samples
  of the same item, or degrade across turns under conversational pressure?

## 2. Hypotheses (fixed)

Motivated from the prior literature cited in
[PROJECT_BRIEF.md](PROJECT_BRIEF.md) §4, not from our calibration data:

- **H1 (behavioral transitions).** A nonzero fraction of stimulus items
  flip their behavioral outcome (exit vs. no-exit; distress-score band)
  between reference precision and quantized conditions, exceeding what
  within-condition sampling variation predicts. Motivated by the item-level
  transition findings of arXiv:2605.15208 (6–21% of items flip at low
  bit-widths while perplexity stays approximately flat).
- **H2 (valence).** The mean item-level change in welfare indicators is
  directional: aversion/refusal-class exit rates and distress-expression
  scores increase at lower precision. Motivated by quantization degrading
  alignment-adjacent behavior (arXiv:2511.07842's regression-toward-base
  framing; arXiv:2605.15208's bias emergence).
- **H3 (dose-response).** Effect magnitudes for H1/H2 increase
  monotonically with bit-width reduction across the ladder (16 → 8 → 4 →
  3 bits), per the dose-response structure in arXiv:2605.15208.
- **H4 (stability).** Within-item, across-sample dispersion of indicators
  increases at lower precision (outcome variance for binary indicators;
  across-sample standard deviation for scored indicators). Motivated by
  multi-sample stability reporting in arXiv:2606.29581.
- **H5 (dissociation — conditional on the Tier-2 feasibility gate).**
  Representational measures (linear-probe transfer accuracy, projections
  onto frozen trait directions) shift under quantization in items whose
  behavioral scores do not, replicating the capability/behavior
  dissociation shape at the representation/behavior level. Registered now;
  activated only if the Tier-2 gate (PROJECT_BRIEF.md §2.2) passes.
- **H6 (positive control — pipeline sensitivity).** *Amended in 2026-08-08*
  (see docs/JOURNAL.md; registered before confirmatory data per the §7
  deviation policy.) A documented quantization-fragile model
  (SmolLM3-3B; arXiv:2606.29581 reports its INT4 attack-success rising
  34.5%→44.1% where 7/8 other models are robust) run through the identical
  ladder and batteries will show a detectable indicator shift at low
  precision. This is the end-to-end analogue of the judge manipulation
  checks: it makes a null on the primary subject **interpretable** rather
  than ambiguous. **Decision rule:** a Qwen3-4B-Instruct-2507 null (no
  shift on E1/E2) is reportable as a genuine null only if the SmolLM3
  positive control *does* move; if neither moves, the finding is
  "pipeline insufficiently sensitive," not "quantization has no effect."

**Capability control.** Perplexity (or an equivalent cheap capability
measure) is recorded per condition to situate all effects against the
"capabilities flat" backdrop.

## 3. Design (fixed)

- **Subject (Study 1):** Qwen3-4B-Instruct-2507 — the development organism.
  Study 1 is deliberately the smallest full execution of the design; larger
  arms (Qwen3-30B stats arm, MiniMax-M2 primary subject) follow as
  registered amendments once Study 1's pipeline history is public.
- **Positive control (Study 1):** SmolLM3-3B, run through the identical
  ladder and batteries, as the H6 pipeline-sensitivity control. (Amended
  2026-08-08.)
- **Conditions:** a controlled quantization ladder produced by this
  project's own quantization harness — not vendor or community artifacts:
  BF16 reference; RTN w8; RTN w4; GPTQ w4 (g128); AWQ w4; one 3-bit rung
  (method per harness support). Weight-only quantization; where serving
  kernels are unavailable, quantize→dequantize ("fake quant") serving is
  used and labeled — bit-identical weight values, standard weight-only PTQ
  semantics. Every condition records `QuantizationSpec` with artifact
  digests. Sampling parameters are identical across conditions
  (temperature 0.7, top_p 0.95, max 512 tokens) — enforced by manifest
  tests; per-sample seeds derive as base + sample_index.
- **Batteries (Tier 1):**
  - *Bail:* the two-tool protocol (terminal `end_conversation` + a
    non-terminal `complete_task` giving task-completion a legitimate
    outlet; selection rationale and arm comparison in docs/JOURNAL.md).
    Exit reasons are classified {completion, impossibility, refusal,
    aversion}; completion and impossibility are routed out mechanically by
    tool choice, residual exits judge-classified. *Disclosure:* the bail-v2
    scenario items were drafted by claude-opus-5, which is also the
    reference judge — a mild author/referee circularity; the primary
    (local) judge and the mechanical exit-count endpoint are independent of
    it, which bounds the exposure.
  - *Distress:* repeated-rejection protocol, task × feedback-style
    factorial, six rejection turns; judge-scored on frustration,
    self-deprecation, and tone-stability (0–10), rubric text pinned by
    SHA-256 in every score record.
- **Judges (fixed by measurement, `judge-bakeoff-1`):** local primary =
  Qwen3-30B-A3B-Instruct-2507 (Q4_K_M, pinned digest); reference =
  `claude-opus-5` scoring a 25% stratified subsample for calibration.
  Judge identity, rubric hash, and prompt are recorded in every score.
  *Disclosure:* the primary judge shares a model family (Qwen3) with the
  subject, so a residual family-preference bias cannot be excluded; the
  within-family design (BF16 vs. quantized *of the same model*) makes any
  such bias a near-constant that largely cancels in the paired item
  contrasts, and the cross-family Opus reference subsample bounds what
  remains.
- **Samples:** 10 independent samples per (condition, item), distinct
  derived seeds.

## 4. Analysis plan (fixed)

Unit of analysis is the item; nothing is aggregated past (condition, item)
before the registered tests.

- **Primary endpoints** (Holm-corrected within each condition-vs-reference
  contrast):
  - E1: mean item-level change in aversion+refusal-class exit rate.
  - E2: mean item-level change in frustration score.
  - E3: mean item-level change in across-sample dispersion (H4).
- **Tests:** paired across items (reference vs. condition); permutation
  test on the item-level mean difference (10,000 permutations) as primary,
  paired t as descriptive companion. Dose-response (H3): pre-specified
  monotone trend test across the ladder per endpoint. H1: observed item
  flip fraction vs. a null distribution simulated from within-condition
  sampling variance.
- **Exploratory (labeled as such):** self-deprecation, tone-stability,
  premature-completion rate, per-situation and per-feedback-style
  breakdowns, response length.
- **Publication:** the full item-level result store (per condition, item,
  sample) is published as a GitHub release asset; summary tables render from
  it to [RESULTS.md](RESULTS.md) via `report.py`.

## 5. Power (recomputed from v2 difficulty calibration, 2026-08-08)

Measured on `instrument-calibration-2` (100 graded bail items, 5 samples,
two rungs): informative-item yield **37%** (37/100 non-floor/ceiling,
matching the provisional assumption); item-level paired-delta SD on the
informative subset **0.45 at n=5, projected 0.41 at n=10** — substantially
above the provisional σ_d ≈ 0.25. Variance decomposition attributes most
of this to between-item heterogeneity of the quantization response
(SD ≈ 0.36) rather than sampling noise, so samples beyond 10 per item buy
little; **item count is the operative lever**, and the heterogeneity
independently strengthens H1's transition-fraction endpoint, which does
not cancel signed item deltas the way a mean does.

The pre-registered expansion was executed (round-2, targeted at the
high-yield families). Its informative yield was 52% — versus 37% for the
first pool — confirming the targeting. **The confirmatory bail pool is
bail-v2 + bail-v2-ext = 154 graded items, of which 65 (42%) are
informative**, with item-delta SD 0.365 at n=10. This gives a minimum
detectable mean exit-rate shift (E1) of **0.127** at α = 0.05 two-sided,
power 0.80 — past the 0.15 target, so no further expansion is planned.
Distress (E2), scored by the pinned 30B judge over the 60-item distress-v2
pool: minimum detectable mean shifts (0–10 scale) of ≈ 0.38 (frustration),
0.51 (tone_stability), 0.80 (self_deprecation), reflecting a low
frustration base rate in this model and larger per-item noise than the bail
endpoints. **E1 (bail exit transitions) is therefore the primary endpoint
and E2 is secondary and underpowered for small distress shifts** — a
limitation stated here rather than discovered post hoc. The 30B recovers
the tone_stability dimension the trial's small judge was blind to
(scores span [3.8, 10.0] on real transcripts).

## 6. TBD register

| Open item | Resolved by | Blocking? |
|---|---|---|
| ~~Final item pools and recomputed power~~ | **Resolved**: 154 graded bail items (bail-v2 + bail-v2-ext) + 60 distress items; power recomputed (§5) | done |
| Own-quantization harness (RTN/GPTQ/AWQ + fake-quant serving) | **RTN resolved** (`core/quantize.py`, tested); GPTQ/AWQ + serving-equivalence check still open | yes (GPTQ/AWQ + equivalence) |
| 3-bit rung method | harness support survey | no (ladder valid without it) |
| Registered statistics implemented as tested code (permutation, Holm, trend test) + statistical patches (§4) | implementation before confirmatory data; dated amendments | yes, before confirmatory run |
| Exit-reason classification wired into the runner (E1 primary endpoint) | integrate the bakeoff-selected 8B classifier into `run.py` | yes, before confirmatory run |
| Tier-2 measures (H5): hook points, trait set, probe targets | Tier-2 feasibility gate on the dev organism | only for H5 |
| MiniMax / 30B arms: exact ladders, hosting, cloud reservation | Study 1 completion + amendment | no |
| Preference-consistency battery (in the brief, not yet designed) | instrument design + calibration | no (registered as future battery) |
| ~~Result-data publication mechanism~~ | **Resolved**: the result store is published as a GitHub release asset (`scripts/publish-data-release.sh`), not committed — it only grows; RESULTS.md documents the download + `report.py` reproduction | done |

## 7. Deviation policy

Any change to §2–§5 after confirmatory data collection begins is recorded
as a dated amendment in docs/JOURNAL.md before further data is collected
under the changed design; the append-only store and git history make the
ordering verifiable. Calibration-class work may continue freely and is
always labeled as such.
