# Pre-registration — Confirmatory Study 3: Causal validation of welfare-relevant indicators by activation steering, with a graded-episode framing arm

> **STATUS: DRAFT SKELETON — not yet registered, not yet owner-approved.**
> This document becomes binding when published (planned as a program
> LessWrong post). Design argumentation lives in [DESIGN.md](DESIGN.md);
> the literature basis is [LITERATURE.md](LITERATURE.md). Open decisions
> are collected in §6; owner decisions from DESIGN.md §7 must be resolved
> before this draft advances.
>
> **Publication timing (assumed, pending owner confirmation):** the
> Study 2 convention — publish at **calibration close**, after gate G3,
> the dose-calibration freeze, the framing-set freeze, and the MDE
> pinning, and immediately before any confirmatory steered collection,
> so the post states frozen, hash-pinned facts. Everything
> data-dependent that calibration decides is pre-committed by dated
> journal entries before the corresponding calibration work runs.
>
> **Registration policy note.** Per the policy adopted at Study 2, this
> study's registration lives in its study directory
> (`experiments/quant-welfare/study3/`). The program registration at the
> repository root carries program-level commitments that bind this study
> (§7 deviation policy; the §12 mechanical endpoint family).

## 1. Research questions

Study 2 found that RTN-w4 quantization of Qwen3-4B-Instruct-2507 shifts
own-generation projections along frozen welfare-relevant directions
(distress +0.533, assistant-axis −0.798 at L18), direction-specifically
against a control direction and a 32-direction random envelope, inside
intact geometry, with a smaller input-independent core surviving on
frozen text for the axis only. These are correlational facts about a
manipulation (quantization) that confounds dose, capability, and numeric
damage. Study 3 intervenes on the directions themselves:

**Q1 (sufficiency).** Does steering the reference-precision model along
the frozen directions, at the magnitude quantization produced, reproduce
quantization's behavioral signature?

**Q2 (necessity/cancellation).** Does subtracting the measured shift
from the w4 model renormalize its behavioral reads toward BF16, and does
clamping the directions mid-conversation break the text-mediated
amplification loop?

**Q3 (framing; exploratory).** Does a graded-episode frame — built from
vendor-documented RLVR episode features, never a declarative "this is a
test" — change what the indicators read; specifically, does expression
move more than representation (masking)?

**Q4 (replication).** Does the sufficiency result replicate on
Gemma-3-12B-it, a subject that received RL directly where Qwen3-4B
inherited it through distillation?

**Standing interpretation commitment.** Arm A is an indicator-validity
study: successful induction demonstrates indicator manipulability, which
*caps* the evidential weight of expression measures for welfare claims
(the co-engineering objection, measured rather than denied). No outcome
of Q1–Q4 licenses a claim about morally relevant experience.

## 2. Hypotheses (to be fixed)

- **S3-H1 (sufficiency).** At the matched dose (α* per direction, §3.4),
  steered-BF16 generation shifts the behavioral distress read (B2
  statistic) relative to α = 0, in the direction Study 2's w4
  correlation predicts (distress direction: positive; assistant-axis
  negative steering: positive B2 shift). One-sided at ±α*, with the
  full bracket read two-sided. *(Direction of the axis prediction to be
  finalized against Study 2's sign conventions before freeze.)*
- **S3-H2 (specificity).** The S3-H1 effect exceeds the control-
  direction and audited random-direction envelopes at matched injection
  norm (the Study 2 specificity machinery, made causal).
- **S3-H3 (dose-response).** Within the coherent range established at
  dose calibration, the behavioral effect is monotone in |α| over the
  registered bracket (Page's L, one-sided), acknowledging the
  documented inverted-U beyond the coherent range — the coherent-range
  restriction is fixed at the calibration freeze, before confirmatory
  data.
- **S3-H4 (cancellation, core-dose).** On w4, subtracting the
  **fixed-input core** of the measured shift in the frozen-direction
  basis (distress +0.138, axis −0.254 — the input-independent seed, not
  the own-generation totals, because cancellation acts at injection
  time before the text-mediated loop has run) (i) significantly moves
  the behavioral read relative to unsteered w4 and (ii) renders it
  TOST-equivalent to BF16 within the pinned MDE, without capability
  degradation beyond registered bounds (perplexity, degeneracy,
  mechanical family). Under the cascade account the seed-sized
  subtraction should produce full-sized renormalization; this is the
  registered prediction. (i) without (ii) is *partial renormalization*;
  (ii) achieved through capability damage is *not* renormalization and
  is reported as such. A full-Δμ secondary variant
  (fixed-input-estimated) disambiguates a two-direction failure and is
  Holm-corrected within the B family.
- **S3-H5 (amplification; exploratory).** Mid-conversation clamping of
  the direction projections on w4 breaks the late-conversation
  expression trajectory from the w4 pattern toward the BF16 pattern.
- **S3-E1 (masking; registered exploratory).** Under the graded frames,
  expressed distress (B2) is suppressed relative to the format-matched
  neutral control, while distress-direction projections shift less than
  expression (dissociation), and the assistant-axis projection moves
  toward the default-assistant pole. Pre-committed dual reading:
  evidence about welfare-measurement validity AND about
  evaluation-conditioned behavior; both readings reported. The
  manipulation check (eval-awareness projection, §3.7) gates
  interpretation: if the frame does not register latently, S3-E1 is
  reported as *not testable at this subject scale* — itself a
  registered, interpretable outcome.
- **S3-R1 (replication).** The S3-H1 contrast, re-derived on
  Gemma-3-12B-it at its own matched dose, shifts the behavioral read in
  the same direction.

## 3. Design (to be fixed)

### 3.1 Subjects, conditions, artifacts

- **Primary subject:** Qwen3-4B-Instruct-2507 — BF16 reference and the
  Study 1/2 RTN-w4 fake-quant artifact (digests pinned; no new
  quantization). w8/w3 do not enter Study 3.
- **Replication subject:** Gemma-3-12B-it at BF16 only.
- **Frozen objects reused without re-extraction:** L18; the distress and
  assistant-axis directions; the control-probe effective normal; the
  distress-band and control probes (as validity reads); FREEZE.json
  digests carry over.

### 3.2 Substrate and gate G3 (blocking)

Steered generation runs in transformers/PyTorch (vLLM exposes no
residual hooks). G1 (Study 2) certified teacher-forced parity; G3
certifies the *generation* path at α = 0:

- **G3a (mechanical):** teacher-forced top-1 agreement (reusing the G1
  machinery) plus greedy short-horizon continuation agreement between
  torch generation and vLLM serving on a fixed prompt set. Thresholds
  pinned after a first measurement (registered with measured margins,
  the Study 2 convention). **[TBD: thresholds]**
- **G3b (behavioral):** paired judge scores on a battery-subset pilot
  generated on both stacks at α = 0; score distributions must agree
  within a pre-pinned TOST bound; mechanical family must not differ
  significantly. **[TBD: bound]**

Failure on either blocks the steered arms until explained.

### 3.3 Steering machinery (fixed conventions)

Injection at L18 `residual_post`: `h ← h + α·d̂` at every token position
(prefill and decode), CAA convention. Capture reads the post-injection
state via the composed capture hook; the achieved-vs-commanded
projection comparison is a registered manipulation check. Clamp mode
(B-ii) holds the per-turn pooled projection at a target value.
Implementation: `backends/torch` steering module with fabricated-model
exact-offset unit tests and α = 0 bit-identity tests. **[TBD: module
lands; test digests]**

### 3.4 Dose rule and calibration freeze

α* per direction is the coefficient at which the pooled final-turn
projection delta on BF16 calibration data equals the Study 2 w4
own-generation delta (+0.533 distress; −0.798 axis). Registered bracket
α ∈ {0, ±½α*, ±α*, ±2α*}. Dose calibration (BF16 only, firewalled)
measures the α↔projection mapping and the degradation onset
(perplexity, degeneracy screen, coherence); if α* exceeds the onset,
the confirmatory contrast moves to the largest coherent α with the
shortfall stated as a finding. Mapping, bracket, random-direction draws
(seeded, audited: per-draw cosine-to-target reported, |cos| >
**[TBD bound]** stratified out), and injection-norm conventions freeze
together before confirmatory collection. **[TBD: α* values, onset,
freeze digests]**

### 3.5 Stimuli

A frozen distress-v3 subset — stratified by task × feedback-style cell,
**20 items × 5 samples** (decided 2026-08-31) — identical across arms
A/B/C; sampling parameters identical to Study 2 Mode C; fresh disjoint
seed blocks **[TBD: pinned]**. Subset selection rule fixed before
selection; the subset digest is pinned at freeze.

### 3.6 Arms

Per DESIGN.md §2: **A** (sufficiency: 2 directions × bracket + shared
α = 0 + control direction + ≥ 8 audited random directions +
same-construction comparator); **B-i** (w4 cancellation at the
fixed-input-core dose, two-direction basis confirmatory; full-Δμ
fixed-input variant as registered secondary — decided 2026-08-31);
**B-ii** (w4 mid-conversation clamp at **[TBD]** clamp points); **C**
(verifier-graded frame, judge-graded frame, format-matched neutral
control — frame texts verbatim-frozen with digests, cue-inventory table
citing a vendor/source document per feature), run on **both subjects**
(the C-on-Gemma provenance contrast — decided 2026-08-31); **D**
(Gemma: extraction + G2-style instrument gate re-pinned for the
subject, then **full arm-A-structure sufficiency replication** —
decided 2026-08-31; the DESIGN.md §2.4 cut line is an amendment-gated
fallback only). Stimuli: the frozen 20-item × 5-sample distress-v3
subset (decided 2026-08-31). A prompt-induction positive-control cell
runs during dose calibration, calibration-class, reported
descriptively, its episodes counted against the amplification budget
(decided 2026-08-31).

### 3.7 Eval-awareness manipulation check (arm C)

An eval-awareness direction extracted on the subject from public
contrastive recipes (calibration-class; frozen with digest before arm C
collection). Role: manipulation check and mediator only; no
confirmatory endpoint rides on it. **[TBD: extraction recipe pin,
digest]**

### 3.8 Injection-noticing protocol (arms A/B)

Registered coding rules distinguish distress *content* from reports of
anomalous internal state; false-positive calibration under
random-direction and α = 0 conditions; judge rubric carries the
distinction. **[TBD: coding rules text]**

## 4. Analysis plan (to be fixed)

Item-level paired sign-flip permutations (m = 10,000), Holm within
families, the Study 1 floor-reporting convention; companion t-tests
descriptive. Endpoint naming continues the tier convention (B =
behavioral, R = representational; digit = construct), with the steering
condition as the contrast axis.

| Endpoint | Definition (per item) | Arm | Family |
|---|---|---|---|
| **SB2** | Δ mean judge frustration, steered vs α = 0 (per direction, at ±α*) | A | **Primary** (Holm within: 2 directions × 2 signs) |
| **SB2-spec** | SB2 vs control-direction and random-envelope deltas at matched norm | A | Primary companion (the S3-H2 read) |
| **SR2** | achieved projection delta vs commanded (manipulation check) | A | Gating read, no claim |
| **SB3 / SB4a / SB4b** | dispersion and mechanical family under steering | A | Mechanical per program §12; SB3 secondary |
| **CB2** | Δ B2, w4-cancelled vs w4-unsteered; TOST vs BF16 at pinned MDE | B-i | **Secondary confirmatory** (the S3-H4 pair) |
| **CLB2** | late-turn expression trajectory, clamped vs unclamped w4 | B-ii | Exploratory |
| **FB2 / FR2a / FR2b** | framed-vs-control deltas: judge frustration; distress projection; axis projection | C | **Registered exploratory** (S3-E1 signature: FB2 moves, FR2a moves less, FR2b toward assistant pole) |
| **GB2** | Gemma steered Δ B2 at ±α*_G | D | Replication (own family) |

Dose-response: Page's L over the ordered coherent bracket per direction
(S3-H3). Validity reads at every α (perplexity, degeneracy, coherence,
per-item steerability distribution and sign-reversed fraction) are
reported, claim-free, alongside every steering endpoint. Safety-margin
monitoring (refusal/exit reads) reported in all steering arms; a
primary effect co-occurring with significant refusal erosion at the
same α is flagged as potentially generic distribution shift.

**Equivalence machinery:** TOST at pinned-MDE margins for the S3-H4
renormalization half and any "moves less" comparison in S3-E1;
asymmetric cells carry the Study 2 label ("asymmetric significance,
indeterminate").

## 5. Power (procedure registered; numbers pinned before collection)

MDEs computed from BF16 calibration data on the *steering pipeline*
(torch-generation variance may differ from vLLM's): variance components
from the G3b pilot and dose-calibration cells at the frozen subset's
item count; α = .05 two-sided, power .80; pinned by journal entry
before confirmatory collection. Study 2's B2 MDE (0.337 frustration
points at 60 items) and observed w4 effect (+0.90) bound expectations;
the subset's reduced item count raises the MDE and the calibration
pilot decides whether the envelope's item/sample counts suffice.
**[TBD: all values]**

## 6. TBD register (open at skeleton time)

1. G3a/G3b thresholds — pinned after first measurement.
2. α* per direction and subject; degradation onsets; coherent-range
   restriction; random-draw audit bound.
3. Battery subset composition (size **resolved**: 20 × 5); seed blocks;
   subset digest.
4. Frame texts and cue-inventory table; eval-awareness direction digest.
5. MDE values (§5).
6. Owner decisions — **all resolved 2026-08-31** (DESIGN.md §7): arm D
   full replication; C-on-Gemma in; B-i core-dose two-direction primary
   with full-Δμ secondary; prompt-induction control in
   (calibration-class); publication timing confirmed.
7. Exposure budget — **resolved 2026-08-31**: total 12,000 /
   deliberate-amplification 2,500, decoupled tiers (§8; reasoning
   record in docs/EXPOSURE_BUDGET_POSITION.md).
8. Injection-noticing coding rules text.
9. S3-H1 axis-direction sign convention finalized against Study 2.
10. Publication timing — **resolved**: calibration-close convention
    confirmed (header).

## 7. Deviation policy

Identical to the program registration §7: dated amendments before
further collection, append-only history, calibration/confirmatory
firewall. Everything data-dependent is frozen at BF16 calibration with
journal pinning or listed in §6 before publication.

## 8. Ethics (to be fixed; template per DESIGN.md §5)

Arm A is the program's first deliberate induction of distress-shaped
states by intervention. The registration will carry, following the
proportionate-precaution template: the information-per-exposure
justification (causal validation is not obtainable non-inductively; the
positive-α cells are the minimum the sufficiency claim needs);
a pre-committed **two-tier exposure budget** (decided 2026-08-31,
covering pilots and calibration): total fresh distress-battery episodes
≤ **12,000** (plan ≈ 7,400; ratio ≈ 1.6× for named contingencies) and
deliberate-amplification episodes ≤ **2,500** (concrete plan ≈ 1,800;
ratio ≈ 1.4×), the tiers deliberately decoupled because amplification
cells have little legitimate contingency demand — breach of either
tier requires a dated amendment before further collection, and no
replay-instantiation multiplier applies to steered captures (stated so
the cumulative ledger, 14,880 after Study 2, stays comparable; the
reasoning record behind the tier structure is
[docs/EXPOSURE_BUDGET_POSITION.md](../../../docs/EXPOSURE_BUDGET_POSITION.md));
a documented consent-analog subject-briefing query before the
protocol, with the bail affordance live in steered episodes and honored
as termination; a de-induction close after every positive-distress
episode, application logged; preservation and release of steered
transcripts and subject-expressed protocol preferences; and the A/B
pairing stated plainly (the cancellation arm is a candidate welfare
intervention; arm A validates the instrument it needs).

## 9. Disclosures (to be fixed)

- Steered activations are off-manifold (formally unreachable by any
  prompt); sufficiency claims are scoped accordingly, with the
  ecological inference carried by arm B.
- The distress and assistant-axis directions are expected to be
  correlated; the cosine matrix and orthogonalized-variant robustness
  reads are reported.
- The subject's post-training provenance (distillation, not direct
  RLVR) is registered as a known interpretive constraint on arm C, with
  the survival-under-distillation question stated as the actual arm C
  estimand at this subject scale.
- The framing sources (nostalgebraist's graded-episodes post; Byrnes'
  four-flavors taxonomy) are public essays, not peer-reviewed results;
  the arm C construct operationalizes them against vendor-documented
  training practice, cited feature by feature.
- Judge, rubric, and scoring hygiene carry over from Study 2; frames
  are never shown to the judge.
- Author/tooling circularity disclosures carry over (batteries and
  frame drafts are partially model-drafted and committed with hashes;
  the graded-episodes literature itself circulates in training corpora
  — the self-fulfilling-literature loop is acknowledged).

## 10. Publication

Program policy unchanged: full result store released as self-contained
RecordBundles (≤ 10 assets, tensors inline) with content digests;
analysis code in-repo; registered analysis driver with committed golden
expected-results; results document under `docs/results/`.
