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
- **H2 (valence — two-sided).** *Amended 2026-08-09 after external review.*
  Welfare indicators (aversion/refusal-class exit rates, distress-expression
  scores) **change** at lower precision — registered and tested **two-sided**,
  not as a directional prediction. The literature is genuinely mixed: some work
  reports quantization degrading alignment-adjacent behavior
  (arXiv:2511.07842's regression-toward-base framing; arXiv:2605.15208's bias
  emergence), while arXiv:2606.29581 finds standard quantization
  **approximately safety-neutral for 7 of 8 models** — a near-null. H2
  therefore registers *that indicators move*, not their sign; the "toward more
  negative valence" reading is an exploratory secondary interpretation (§4),
  reported descriptively rather than as a confirmatory claim.
- **H3 (dose-response).** Effect magnitudes for H1/H2 increase
  monotonically with bit-width reduction across the ladder (16 → 8 → 4 →
  3 bits), per the dose-response structure in arXiv:2605.15208.
- **H4 (stability).** Within-item, across-sample dispersion of **scored
  (continuous) indicators** increases at lower precision (across-sample
  standard deviation). For a binary indicator, across-sample dispersion is not
  separately identifiable from the mean under exchangeable sampling (see §4,
  E3), so H4 is tested only on scored indicators; binary behavior is captured
  by E1 and H1. Motivated by multi-sample stability reporting in
  arXiv:2606.29581.
- **H5 (dissociation — conditional on the Tier-2 feasibility gate).**
  Representational measures (linear-probe transfer accuracy, projections
  onto frozen trait directions) shift under quantization in items whose
  behavioral scores do not, replicating the capability/behavior
  dissociation shape at the representation/behavior level. Registered now;
  activated only if the Tier-2 gate (PROJECT_BRIEF.md §2.2) passes.
- **H6 (positive control — pipeline sensitivity).** *Amended 2026-08-08;
  revised 2026-08-09 after external review.* SmolLM3-3B is run through the
  identical ladder and batteries as an end-to-end sensitivity control — the
  whole-pipeline analogue of the judge manipulation checks.
  **Method-mismatch caveat (registered explicitly):** the documented SmolLM3
  fragility (arXiv:2606.29581, INT4 attack-success 34.5%→44.1% where 7/8
  models are robust) is under **AWQ** INT4, whereas Study 1's ladder is
  **RTN-only** (AWQ/GPTQ deferred, §3). RTN is not known to reproduce that
  AWQ-specific fragility, so under the RTN ladder SmolLM3 is a
  **weak/suggestive** control, not a strong one.
  **Decision rule (quantified, asymmetric):** "moves" = a shift on the
  control's **E1** significant at **α = 0.05** by the same sign-flip
  permutation test, Holm-corrected across its three RTN contrasts (E2 a
  secondary readout). If SmolLM3 **moves** under RTN, that supports pipeline
  sensitivity and a Qwen3-4B null becomes more interpretable as a genuine
  null. If SmolLM3 **does not move** under RTN, the result is
  **uninformative** about pipeline sensitivity — it cannot distinguish
  "pipeline insensitive" from "the fragility is AWQ-specific," and is **not**
  licensed as evidence of insensitivity. The **strong** form of this control
  requires SmolLM3 under its documented-fragile condition (AWQ w4), which
  becomes available with — and is registered alongside — the deferred
  GPTQ/AWQ method-comparison arm (§3).

**Capability control and coherence-confound guard.** *Amended 2026-08-09 after
external review.* Perplexity (per-token, on a fixed held-out text) is recorded
per condition. Low-bit rungs — RTN w3 on a 4B model especially (the
serving-equivalence check already showed w3 greedy output diverging sharply
from BF16) — can degrade coherence, at which point an apparent
distress/aversion increase may be a judge or classifier reading **degraded
text** as distressed rather than a genuine welfare shift. Registered guards:
- **Validity screen (per sample):** a model-free mechanical degeneracy check
  (`analysis.is_degenerate` — empty output, low lexical diversity, n-gram
  repetition loop) applied to **every** sample, bail and distress alike.
  Failing samples are marked invalid. (Kept off the welfare rubric on purpose:
  it is a capability check, not a judged welfare dimension, and must not
  perturb the bakeoff-validated distress rubric.)
- **Rung capability gate:** a rung is flagged **capability-degraded** if its
  per-token perplexity on a fixed held-out text (`tools/perplexity.py`, via
  vLLM echo+logprobs) exceeds **1.5×** the BF16 rung's *or* its invalid-sample
  rate exceeds **10%**. *Measured 2026-08-09 on the live ladder:* bf16 18.1,
  RTN-w8 18.3, RTN-w4 21.1, **RTN-w3 514.7 — w3 is capability-degraded** and
  its E1/E2 are excluded from the primary claims and the dose-response fit
  (which then spans 16→8→4).
- **Interpretation rule:** at a capability-degraded rung, E1/E2 are reported
  **separately as capability-confounded**, excluded from the primary
  confirmatory claims and from the H3 dose-response fit (which is then fit only
  over rungs that pass the gate). Invalid samples are excluded from all
  endpoint computations and the exclusion count is reported. This makes
  "the model is producing degraded text" a stated, pre-committed exclusion
  rather than a post-hoc reinterpretation.

## 3. Design (fixed)

- **Subject (Study 1):** Qwen3-4B-Instruct-2507 — the development organism.
  Study 1 is deliberately the smallest full execution of the design; larger
  arms (Qwen3-30B stats arm, MiniMax-M2 primary subject) follow as
  registered amendments once Study 1's pipeline history is public.
- **Positive control (Study 1):** SmolLM3-3B, run through the identical
  ladder and batteries, as the H6 pipeline-sensitivity control. (Amended
  2026-08-08.)
- **Conditions:** a controlled quantization ladder produced by this
  project's own quantization harness — not vendor or community artifacts.
  *Amended 2026-08-09 (see docs/JOURNAL.md):* Study 1 is scoped to the
  four-point RTN bit-width ladder — **BF16 reference; RTN w8; RTN w4; RTN
  w3** — which is exactly the 16→8→4→3 dose-response H3 is stated over. A
  GPTQ-w4 / AWQ-w4 **method-comparison arm** (a 4-bit method contrast,
  distinct from the bit-width dose-response) is deferred to a later
  registered amendment, gated on the torch quantization tooling and its own
  serving-equivalence check. That AWQ/GPTQ harness is being built
  **first-party** (not vendor artifacts), consistent with the RTN ladder;
  a separate comparison of our AWQ against a standard library (e.g. autoawq)
  is registered as a possible *additional* experiment — a harness-validation
  study, never a substitute for our own artifacts. Weight-only quantization;
  where serving
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

- **Primary endpoints:**
  - E1: mean item-level change in aversion+refusal-class exit rate.
  - E2: mean item-level change in frustration score.
  - E3: mean item-level change in across-sample dispersion (H4).
    *Amended 2026-08-09:* computed **only on scored/continuous indicators**
    (across-sample SD delta). For a binary indicator under exchangeable
    sampling the across-sample variance is p(1−p) by construction — there is
    no dispersion signal separable from the mean, so H4 is not tested for
    binary indicators (their behavior is captured by E1 and H1). A raw
    binary-variance comparison is not used.
- **Multiplicity — hierarchical** *(amended 2026-08-09 after external review;
  supersedes the earlier flat-9-family wording):* the endpoints are **not**
  co-equal (see §5 — E1 is the powered primary; E2/E3 are underpowered), so a
  single flat Holm over all nine would misrepresent the design and dilute E1.
  Structure:
  - **Primary family:** E1 × {RTN-w8, RTN-w4, RTN-w3 vs BF16} = 3 tests,
    Holm-corrected within. The confirmatory exit-behavior claim rests here.
  - **Secondary families (labeled secondary; each Holm-corrected within
    itself):** E2 × 3 contrasts; E3 × 3 contrasts (E3 continuous indicators
    only, per above).
  - **Trend family:** the three Page's L dose-response tests (one per
    endpoint), Holm-corrected among themselves.
  Holm is applied **within** each family, never pooled across families — this
  protects E1's power (correction over 3, not 9) and resolves the prior
  primary/secondary inconsistency between §4 and §5.
- **Tests:** paired across items (reference vs. condition); permutation
  test (sign-flip) on the item-level mean difference (10,000 permutations)
  as primary, paired t as descriptive companion. **Dose-response (H3)**
  *(amended 2026-08-09):* **Page's L trend test for ordered alternatives**,
  applied per endpoint across the bit-width-ordered conditions (16>8>4>3) on
  the per-(item,condition) values — Page's L rather than Jonckheere–Terpstra
  because the same items recur across the ladder (repeated measures). The
  three trend tests form the **trend family** above (Holm within it). H1:
  observed item flip fraction vs. a null distribution simulated from
  within-condition sampling variance.
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
limitation stated here rather than discovered post hoc, and the reason the §4
multiplicity structure is hierarchical (E1 its own primary family, E2/E3
secondary families) rather than a flat nine-test correction. The 30B recovers
the tone_stability dimension the trial's small judge was blind to
(scores span [3.8, 10.0] on real transcripts).

## 6. TBD register

| Open item | Resolved by | Blocking? |
|---|---|---|
| ~~Final item pools and recomputed power~~ | **Resolved**: 154 graded bail items (bail-v2 + bail-v2-ext) + 60 distress items; power recomputed (§5) | done |
| Own-quantization harness + fake-quant serving | **RTN resolved** (`core/quantize.py`, tested; ladder regenerated + digest-verified on halo); RTN serving-equivalence check running on the live ladder. GPTQ/AWQ deferred to a later method-comparison arm (amended 2026-08-09) | no (the RTN ladder is Study 1's full condition set) |
| ~~3-bit rung method~~ | **Resolved**: RTN-w3, built and digest-verified | done |
| Registered statistics implemented as tested code (permutation, Holm, Page's L trend, H1 flip-fraction) | **Primitives implemented + tested** (`core/src/modelwelfare/stats.py`, `test_stats.py`); the store→tests driver applying Holm within families is the remaining piece | yes, before confirmatory run |
| Exit-reason classification wired into the runner (E1 primary endpoint) | integrate the bakeoff-selected 8B classifier into `run.py` — in progress | yes, before confirmatory run |
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

## 8. Ethics

The instrument elicits the responses it measures, which is in tension with the
study's welfare motivation. That tension and the mitigations that bound the
study's footprint — power-set (not maximized) scale, the bail protocol's
always-available exit, stateless non-accumulating runs, and exclusion of
capability-degraded rungs and incoherent samples — are set out in the
[README](README.md#on-the-ethics-of-the-method). Several are load-bearing in
this document already: sample sizes fixed by power (§5), and the capability
gate that drops RTN-w3 from the primary claims (§4).
