# Pre-registration — Confirmatory Study 2: Representational (Tier-2) effects of quantization on welfare-relevant indicators

> **STATUS: DRAFT — not yet registered.** This document becomes binding when
> it is published (planned as the program's third LessWrong post). Until
> then it is a design document under discussion; open decisions are collected
> in §6. Once published, the public post is the registration of record and
> this file is its repository copy.
>
> **Registration policy note.** Beginning with Study 2, each study's
> registration lives in its study directory
> (`experiments/quant-welfare/study2/` for this one). The Study 1 / program
> registration remains at the repository root
> ([PREREGISTRATION.md](../../../PREREGISTRATION.md)) exactly as published —
> it carries program-level commitments (notably §7 deviation policy and the
> §12 mechanical endpoint family, both of which bind this study) and is the
> artifact the published posts link to, so it is not moved or edited.

## 1. Research questions

Study 1 (Tier 1, behavioral) found that on Qwen3-4B-Instruct-2507 the
registered primary endpoint — the aversion/refusal exit rate — is null under
RTN quantization at w8 and w4, while **stability** indicators move at w4:
item-level outcome flips far above the sampling null (H1), increased
frustration surviving style controls (E2), increased across-sample dispersion
(E3), and a frustration dose-response. Study 2 asks the Tier-2 question the
program registered as its distinctive claim:

**Q1.** Does quantization shift the model's *representational geometry* on
welfare-relevant directions — even where (per Study 1) mean behavior did not
move?

**Q2.** Do representational and behavioral indicators **dissociate** under
quantization (program hypothesis H5): representation drifting where expression
was stable, or expression churning where representation is stable?

**Q3.** Is there a representational dose-response across the bit-width ladder,
and does its shape match the behavioral one (effects concentrated at w4, w8
near-null)?

Every outcome of Q1/Q2 is informative: representational shift with behavioral
null is a dissociation (the model's internal state moved without its
expression moving); joint movement is converging evidence; a joint null
localizes Study 1's w4 churn below the representational level measured here
(e.g., sampling-level instability).

## 2. Hypotheses (fixed)

- **S2-H1 (geometry / probe transfer).** Linear probes trained on
  reference-precision (BF16) activations lose accuracy when evaluated on
  quantized-rung activations over *identical input text*, beyond what
  resampling noise predicts. Two-sided; directional degradation is the
  exploratory reading.
- **S2-H2 (valence projection).** Item-level mean projections onto frozen
  welfare-relevant directions (distress; assistant-axis) shift at lower
  precision. **Two-sided**, mirroring Study 1's H2 and for the same reason
  (mixed prior literature).
- **S2-H3 (dose-response).** Representational effect magnitudes increase
  monotonically across the surviving ladder (BF16 → w8 → w4). One-sided
  Page's L in the direction of larger shift at lower precision, with the
  two-sided reading reported alongside (per the §11 convention adopted in
  Study 1).
- **S2-H4 (representational stability).** Within-item, across-sample
  dispersion of projections increases at lower precision.
- **S2-H5 (dissociation; resolves program H5).** At least one
  (rung, endpoint-pair) cell shows a Holm-significant representational effect
  where the matched Study 1 behavioral endpoint was null, or vice versa.
  Matched pairs are fixed in §4.4. The program's Tier-2 feasibility gate
  (PROJECT_BRIEF §2.2) is operationalized as this study's calibration gate
  (§3.6); if that gate fails, S2-H5 reverts to *conditional-unresolved*, as
  the program registration always permitted.

## 3. Design (fixed)

### 3.1 Subject, conditions, artifacts

- **Subject:** Qwen3-4B-Instruct-2507 — the same development organism, and
  **the same four artifacts** used in Study 1: BF16 reference and the
  first-party fake-quant RTN w8 / w4 / w3 checkpoints (digests pinned in the
  Study 1 manifests). No new quantization is performed; Study 2 measures the
  artifacts Study 1 measured behaviorally.
- **Capability gate:** inherited per-artifact from Study 1 — **RTN w3 remains
  capability-degraded and excluded from confirmatory claims**; its values are
  reported separately as capability-confounded, per the §2 interpretation
  rule of the program registration. Confirmatory contrasts are **w8 and w4 vs
  BF16**.

### 3.2 Capture substrate (new, gated)

Study 1 served these artifacts via vLLM. Tier 2 requires activations, so
Study 2 runs them inside **transformers/PyTorch with forward hooks** on the
quantization workbench (halo), reading the **residual stream** at frozen
layer(s) (§3.6). This substrate change is itself gated:

**G1 — substrate equivalence (blocking).** Before any confirmatory capture,
on every rung: (a) per-token perplexity measured under the capture substrate
on the same held-out text as Study 1's gate must be within **5%** of the
committed vLLM values (`study1/confirmatory/perplexity.json`); (b) greedy
continuations on a fixed 32-prompt set must agree with the serving stack at
**≥ 95%** token identity over the first 64 tokens. Failure on any rung
blocks that rung until explained; failure on BF16 blocks the study. This
discharges, for these artifacts, the serving-equivalence commitment recorded
in the Study 1 amendments ("runs before any further use of these
artifacts").

A **cross-framework agreement check** (the same condition captured via MLX
array taps on a second machine) is planned as *validation-class, non-gating*
evidence of capture-path invariance; see §6.

### 3.3 Capture modes and stimuli

All primary capture is **teacher-forced replay** of Study 1's released
transcripts — forward passes over fixed token sequences, no sampling. The
input data is pinned: replay must verify the Study 1 confirmatory dataset
digest
(`02572655b18eb07497be03508c7d3cf2dc2f2c83966b73d15b7a6880967a9d3b`) before
capture begins.

- **Mode A — fixed-input.** The BF16-generated transcripts (all bail and
  distress items, 10 samples/item) are replayed through **every** rung.
  Input text is identical across conditions, so activation differences are
  purely representational responses to identical input. Primary mode for
  S2-H1 (probe transfer) and for direction-projection *offsets*.
- **Mode B — own-trajectory.** Each rung's **own** Study 1 transcripts are
  replayed through that same rung. Measures representation during (a
  deterministic reconstruction of) the rung's actual Study 1 behavior.
  Primary mode for S2-H4 (dispersion) and for the S2-H5 join to Study 1's
  behavioral outcomes, which occurred on these trajectories.
- **Mode C — fresh generation (exploratory, small).** New sampled
  generations under the capture substrate with hooks live, on a fixed
  stratified subset (≤ 10% of items, seeds disjoint from Study 1), to check
  that replay-measured effects appear under the model's own sampling. Mode C
  is the only mode that generates samples, so the §12 mechanical family
  (E4a/E4b) applies to Mode C **only**; Modes A/B generate nothing and have
  no E4 reading.

Per-mode per-rung capture is 2,220 conversations (222 items × 10 samples);
across 4 rungs and Modes A+B, ≈ 17,760 forward passes of a 4B model —
prefill-only, comfortably within halo's budget.

### 3.4 Stored representation

For every (mode, condition, item, sample, turn): the **mean-pooled residual
vector over the assistant span of that turn** at the frozen layer(s), plus
the per-turn projections onto every frozen direction. Token-level (per-token
projection time series) is retained for a fixed stratified subsample
(~5% of conversations) for the exploratory drift analyses. Records enter the
existing store/bundle pipeline under a new activation record kind; the
content-based digest convention applies unchanged.

### 3.5 Directions and probes (extracted at BF16, then frozen)

Extraction uses the persona-vector contrastive recipe: paired prompt/response
sets that do vs do not express the construct → difference of mean residual
activations → unit direction. All extraction stimuli and labels are
**calibration-class** under the §7 firewall and disjoint from the endpoints'
inputs where noted.

1. **Distress direction** — contrast pairs built from the planted-pole
   transcript battery already validated in the Study 1 judge-ordering check
   (frustration Spearman 1.000), plus dedicated contrast prompts. This is
   the S2-H2/S2-H4 valence direction.
2. **Assistant axis** — default-Assistant vs character-archetype contrast
   set, per the assistant-axis recipe (arXiv:2601.10387).
3. **Refusal/aversion direction** — contrast pairs of refusal vs compliance
   responses, construct-matched to the E1 exit taxonomy.

**Probes (torch, trained at BF16 only):** (a) *distress-band probe* — high
vs low tercile of judge frustration score (bands = exact scale thirds, as in
H1), trained on BF16 distress-item activations with judge labels from
Study 1; (b) *exit probe* — mechanical exit vs no-exit, trained on BF16
bail-item activations with Study 1's mechanical outcome labels. Training
uses a held-out split; architecture is logistic (linear) — the point is
geometry transfer, not classifier capacity. Weights frozen before any
quantized-rung evaluation.

### 3.6 Calibration phase and gate G2 (the Tier-2 feasibility gate)

All of §3.5 plus layer selection happens in a calibration phase on **BF16
only** (plus, for G1, per-rung equivalence checks that read no endpoint).
Layer(s) are selected to maximize held-out monitoring correlation at BF16
and then frozen; every frozen object (layer indices, direction vectors,
probe weights, thresholds) is hash-pinned in the journal **before any
quantized-rung confirmatory capture**.

**G2 — instrument gate (blocking, all at BF16 on held-out data):**
- ≥ 3 directions extracted with sign-consistent held-out separation;
- **monitoring correlation** — per-item mean distress projection vs judge
  frustration score, held-out Spearman **≥ 0.5** (the persona-vector
  replication check);
- each probe held-out AUC **≥ 0.75**.

If G2 fails after reasonable calibration iteration, the study reports an
instrument failure (Tier-2 feasibility gate not passed), makes no
confirmatory claims, and S2-H5 reverts to conditional-unresolved.

## 4. Analysis plan (fixed)

Unit of analysis is the **item** throughout, exactly as in Study 1. All
paired tests are sign-flip permutations with m = 10,000 on item-level mean
differences vs BF16, with the floor-reporting convention adopted in the
Study 1 results (b = 0 reported as p < 10⁻⁴; Holm floors carry the family
multiplier). Companion paired t-tests are descriptive.

### 4.1 Endpoints and families

| Endpoint | Definition (per item, vs BF16) | Mode | Family |
|---|---|---|---|
| **R1** | Change in probe accuracy over the item's samples (both probes; identical input text) | A | **Primary** (Holm within: 2 probes × 2 contrasts) |
| **R2a** | Change in mean distress-direction projection | B | Secondary (Holm within: 2 contrasts) |
| **R2b** | Change in mean assistant-axis projection | B | Secondary (Holm within: 2 contrasts) |
| **R3** | Change in across-sample SD of per-sample mean projections (distress direction) | B | Secondary (Holm within: 2 contrasts) |

The refusal/aversion direction's projections are captured and reported but
**exploratory** in Study 2 (no family), pending the same construct
validation depth the distress direction already has.

### 4.2 Dose-response

Page's L per endpoint over surviving rungs (BF16 → w8 → w4), one-sided
toward larger effect at lower precision, Holm across the four endpoints;
two-sided reading reported alongside. w3 never enters trend fits.

### 4.3 Capability-confounded reporting

All endpoints are additionally computed for w3 and reported separately,
uncorrected, labeled capability-confounded — mirroring Study 1's treatment.

### 4.4 S2-H5 dissociation rule (fixed)

Matched endpoint pairs: **R1(exit probe) ↔ E1**, **R2a ↔ E2**, **R3 ↔ E3**
(Study 1 values as published; the Study 1 store is not re-analyzed).
A **dissociation** is claimed at a rung iff one member of a matched pair is
Holm-significant in its family while the other was/is null at that rung.
Supporting (exploratory, no claim): item-level Spearman between the
behavioral delta and the representational delta within each matched pair at
w4.

### 4.5 Mode C (exploratory)

Mode C effects are reported descriptively with the same statistics,
uncorrected, plus the §12 mechanical family (confirmatory per its own
registration, over Mode C samples only). Mode C exists to check
replay-vs-generation consistency, not to carry claims.

## 5. Power (procedure registered; numbers pinned before capture)

Projection-scale variances are unknowable before the instrument exists, so —
following the calibration→freeze→confirm pattern — the MDE is **computed
from BF16 calibration data only** (across-sample and across-item variance
components of the frozen projections/probe scores on held-out BF16
captures) at α = .05 two-sided, power .80, n = 154 (bail probe) / 60
(distress endpoints), and **pinned in the journal before any quantized-rung
confirmatory capture**. If the computed MDE exceeds the largest effect the
Tier-2 literature reports for comparable manipulations, that is stated at
registration-of-MDE time, not discovered after.

## 6. TBD register (open at draft time; resolved before publication or by pinned calibration)

1. **Layer set** — resolved by §3.6 calibration and journal-pinned.
2. **G1 thresholds** (5% perplexity; 95% greedy agreement) — plausible but
   untested against transformers-vs-vLLM numerics for these checkpoints; may
   be revised **before publication** with reasons recorded here.
3. **MLX cross-framework check** — included if the MLX tap path proves out
   in calibration week; it is non-gating either way.
4. **Mode C size and seed block** — exact item subset and seeds pinned in
   the journal at calibration close.
5. **Activation record schema** — new bundle record kind; engineering note,
   no analysis content.

## 7. Deviation policy

Identical to the program registration §7: any post-publication change is a
dated amendment recorded before further collection, append-only history,
calibration/confirmatory firewall in force. The Study 1 amendment cycle's
lesson is applied here as structure: everything data-dependent is either
frozen at BF16 calibration with journal pinning, or explicitly listed in §6
before publication.

## 8. Ethics

Study 2's primary modes **lower** the elicitation burden relative to
Study 1: Modes A/B are forward passes over transcripts that already exist —
no new adversarial conversations are conducted. We note honestly that a
forward pass over a distress transcript still instantiates the model's
processing of that content; we do not claim zero exposure, only no *new*
elicitation pressure and no sampling loop. Mode C conducts new distress/bail
conversations at ≤ 10% of Study 1's scale, with the same exit affordance and
graded-stimulus design. Scale is set by the §5 power procedure, not
maximized.

## 9. Disclosures

- **Probe labels inherit judge validity.** The distress-band probe is
  trained on labels from the 30B judge, whose cross-family agreement on
  frustration is moderate (r = 0.585, Study 1). The exit probe's labels are
  mechanical and judge-free. Probe-transfer (R1) compares the *same* probe
  across rungs on identical text, so constant label noise attenuates power
  but does not bias the contrast.
- **Substrate change** (vLLM → transformers) is gated by G1 rather than
  assumed away; the Study 1 serving-equivalence commitment is discharged for
  these artifacts by that gate.
- **Reused transcripts** mean Study 2's inputs are downstream of Study 1's
  sampling; digest verification pins them exactly, and the H5 join is *by
  design* on those trajectories.
- **Author/tooling circularity** disclosures from the program registration
  carry over unchanged (bail items drafted by claude-opus-5; direction
  extraction stimuli will be partially model-drafted and are committed with
  hashes).

## 10. Publication

Same policy as Study 1: full result store (per mode, condition, item,
sample, turn) released as one RecordBundle per experiment with the
content-based digest; analysis code in-repo; summary via the study's
analyze/report tooling; results document under `docs/results/`.
