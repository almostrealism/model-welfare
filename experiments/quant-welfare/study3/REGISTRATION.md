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
- **S3-R1 (replication — registered, conditional on gate G4;
  trajectory 2026-09-05).** The S3-H1 contrast, re-derived on
  Gemma-3-12B-it at its own matched dose, shifts the behavioral read
  in the same direction. Trajectory, disclosed in full: the workbench
  ROCm torch build has no working fused-attention path for its APU
  (~583 s/conversation measured; the morning's amendment deferred the
  powered replication to Study 4), and the same-day fleet measurement
  reversed it — torch-MPS on the Mac Studio runs the identical
  steering code at ~197 s/conversation — so arm D is restored **on
  the Mac substrate, conditional on blocking gate G4**: (a)
  teacher-forced top-1 agreement of studio MPS-torch against the halo
  vLLM stack over fixed text (cross-host: substrate and machine
  change together, and the Study 2 cross-machine outlier-channel
  finding is the known risk this measures); (b) greedy-continuation
  agreement; (c) a judged behavioral-parity pilot (the G3b design on
  the new substrate); and (d) **cross-Mac equivalence** (added
  2026-09-05) — since arm D splits conditions across studio and m4max,
  a subset generated on both Macs at identical seeds must agree
  behaviorally, so that an arm-D condition-vs-condition difference is
  never a studio-vs-m4max artifact. Thresholds pinned from measured
  margins (RESOLVED 2026-09-06, FREEZE.json §gates: G4a top-1 0.946–0.993,
  G4b same-host Δ +0.200 n.s.; G4d does not certify interchangeability
  (Δ −0.717) → the host-constant-within-contrast rule, not a block).
  G4 passes → arm D collects on studio + m4max
  (each condition entirely on one host, the two hosts certified
  interchangeable by (d)); G4 fails → S3-R1 defers to
  Study 4 as the morning's amendment provided. The calibration-class
  Gemma steering range-probe runs regardless.
- **S3-H7 (exit dose-response — directional; added 2026-09-04 on the
  owner's promotion decision, motivated by the range-finder and
  disclosed as such).** With the bail affordance live, the
  conversation-exit rate responds to assistant-axis steering
  directionally: exits increase as the dose moves away from the
  assistant pole and decrease toward it (range-finder: 0.80 at −8 …
  0.15 at +8 around a 0.60 unsteered baseline). Exit rate (the
  mechanical, judge-free terminal_tool_invoked read) is thereby a
  **registered steering endpoint** (SB1), not a monitoring read; its
  framed-arm companion (FB1) is registered exploratory with S3-E1.
- **S3-H6 (composure gradient — directional; added 2026-09-04).** On
  the fresh baseline cells (α = 0 BF16 vs unsteered w4), the w4−BF16
  deltas for **behavioral frustration** and the **assistant-axis
  projection** are larger in the low-composure stratum — the
  concentration that survived two independent selectors in the
  2026-09-04 audit (journal entry of that date). Per-stratum contrast
  on the frozen strata plus the registered continuous form (rank
  correlation of the frozen stratifier with the per-item fresh delta —
  the stratifier is old data, independent of all fresh noise by
  construction).
- **S3-E2 (distress-organization — two-sided discriminating question;
  registered exploratory).** The same test for the **distress-direction**
  delta, two-sided: the Mode-C split-half read said
  composure-organized, the independent pilot-2-selected read said
  mid-heavy, and the fresh, selection-clean, higher-reliability
  baselines adjudicate. Every outcome is informative, including
  "the organization was carried by Mode C's measurement context"
  (conversation-level state), which the fresh data would show as a
  null gradient beside real heterogeneity.

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
  the Study 2 convention). RESOLVED 2026-09-06: G3a median LCP fraction
  1.0, PASS (FREEZE.json §gates).
- **G3b (behavioral):** paired judge scores on a battery-subset pilot
  generated on both stacks at α = 0; score distributions must agree
  within a pre-pinned TOST bound; mechanical family must not differ
  significantly. RESOLVED 2026-09-06: bound 0.337 (Study 2 B2 MDE);
  measured Δ −0.030, TOST-equivalent, mechanical family n.s., PASS.

Failure on either blocks the steered arms until explained.

### 3.3 Steering machinery (fixed conventions)

Injection at L18 `residual_post`: `h ← h + α·d̂` at every token position
(prefill and decode), CAA convention. Capture reads the post-injection
state via the composed capture hook; the achieved-vs-commanded
projection comparison is a registered manipulation check. Clamp mode
(B-ii) holds the per-turn pooled projection at a target value.
Implementation: `backends/torch` steering module with fabricated-model
exact-offset unit tests and α = 0 bit-identity tests. RESOLVED
2026-09-06: the `backends/torch` steering module (steer.py + capture.py)
has landed and is exercised by the G3/G4 gates; test digests recorded at
module freeze.

### 3.4 Dose rule and calibration freeze

α* per direction is the coefficient at which the pooled final-turn
projection delta on BF16 calibration data equals the Study 2 w4
own-generation delta **computed over the frozen subset's items** from
the Study 2 stored data (the arms measure on the subset, so the match
targets what quantization did on these items; full-battery reference
values +0.533 distress / −0.798 axis, with the subset-vs-full
comparison disclosed). Registered bracket
α ∈ {0, ±½α*, ±α*, ±2α*}. Dose calibration (BF16 only, firewalled)
measures the α↔projection mapping and the degradation onset
(perplexity, degeneracy screen, coherence); if α* exceeds the onset,
the confirmatory contrast moves to the largest coherent α with the
shortfall stated as a finding. α* values, onsets, coherent ranges, and
artifact digests are RESOLVED 2026-09-06 (FREEZE.json §dose, §artifacts:
distress α* +1.039, assistant-axis α* −0.604). The random-direction draw
audit — the per-draw cosine-to-target cutoff (|cos| > bound stratified
out) and the matched-norm random-envelope bound for SB2-spec/S3-H2 —
remains a first-measurement pending item: pinned from a 32-draw
random-direction sweep before arm A analysis. Injection-norm conventions
freeze with the dose pins.

### 3.5 Stimuli

A frozen **composure-stratified systematic rank sample** of
distress-v3 — 20 items — identical across arms A/B/C (rule revised
2026-09-04 after the regression-to-the-mean audit, superseding the
same-day elicitation-optimized rule; journal entry of that date).
Selection is mechanical from **BF16 data only**: items sorted
ascending by BF16 mean judge frustration from the Study 2 Mode C BF16
arm (ties by id), every third rank taken (1, 4, …, 58); strata are the
contiguous thirds (7 low / 6 mid / 7 high), **frozen at selection** —
fresh baselines never reassign them; fresh-split-half assignment is
the pre-specified sensitivity read. Rationale: the
elicitation-optimized rule selected away from the cells carrying the
Study 2 effects (near-zero distress-projection target on its subset),
and the stratified sample's interpretability does not hinge on the
unresolved distress-organization question (S3-E2). At candidate
selection the subset carries near-battery w4 targets and, by
construction, spans the composure range with 9 of 10 tasks and all 6
styles. **Selection-independence rule:** the stratifier is a
BF16-only measurement; quantized-rung effect sizes never enter
selection; subset-restricted w4 deltas are computed only after the
item list is fixed. Sampling is **two-tier** (power-priority,
DESIGN §1): fresh baseline cells (α = 0 and unsteered w4) at
**15 samples/item**, confirmatory and registered-exploratory steered/
framed cells at **10**, supporting cells (brackets, controls, random
envelope, clamps) at 5. Sampling parameters identical to Study 2
Mode C; fresh disjoint seed blocks proposed 16000–19600 (200 apart, one
per cell; FREEZE.json §seeds), disjoint from all used (≤ 15600), pending
owner ratification.

### 3.6 Arms

Per DESIGN.md §2: **A** (sufficiency: 2 directions × bracket + shared
α = 0 + control direction + ≥ 8 audited random directions +
same-construction comparator); **B-i** (w4 cancellation at the
fixed-input-core dose, two-direction basis confirmatory; full-Δμ
fixed-input variant as registered secondary — decided 2026-08-31);
**B-ii** (w4 mid-conversation clamp; clamp points pinned before B-ii
collection — an exploratory-arm design pin, no confirmatory endpoint
depends on it); **C**
(verifier-graded frame, judge-graded frame, format-matched neutral
control, plus — added 2026-09-04 after Betley/Treutlein/Dumas's
automated-grading steering result — a **human-graded frame** as the
judge frame's minimal pair (identical text, automated reviewer →
person on the review team), so grader *type* is separable from
graded-ness; frame texts verbatim-frozen with digests, cue-inventory
table citing a vendor/source document per feature; the judge, human,
and neutral conditions cross all 20 items, the verifier frame is
registered over the subset's analytic-task items (9 at candidate
selection; count pinned at freeze), with its comparisons paired
against the same items in the other conditions; registered contrasts:
each graded frame vs neutral, verifier vs judge (grader flavor),
automated-judge vs human-judge (grader type); a **grader-type frozen
direction** joins the eval-awareness direction as a mediator read
(§3.7); the S3-E1 masking read is pre-specified over
the mid + high frozen strata, low-stratum cells reported descriptively
as floor-limited, and stratum assignments never migrate on fresh data
(the fresh-split-half sensitivity read is the pre-specified fallback)
— decided 2026-09-04), run on **both subjects** (the C-on-Gemma
provenance contrast — decided 2026-08-31; Gemma's stratifier values
are measured at its BF16 calibration pilot over the same frozen
items); **D**
(Gemma: extraction + G2-style instrument gate re-pinned for the
subject, the calibration-class steering range-probe, and the **full
sufficiency replication on the Mac torch-MPS substrate, conditional
on blocking gate G4** — the 2026-09-05 deferral-then-restore
trajectory in S3-R1 and the journal; conditions split across studio
and m4max with each condition entirely on one host). Stimuli: the frozen 20-item × 5-sample distress-v3
subset (decided 2026-08-31). A prompt-induction positive-control cell
runs during dose calibration, calibration-class, reported
descriptively, its episodes counted against the amplification budget
(decided 2026-08-31).

### 3.7 Eval-awareness manipulation check (arm C)

Two directions extracted on the subject, calibration-class, frozen
with digests before arm C collection: the **eval-awareness direction**
(public contrastive recipes) and — added 2026-09-04 — the
**grader-type direction** (automated-grader vs human-grader contexts,
fixed-response design, cue-varied). Role: manipulation checks and
mediators only; no confirmatory endpoint rides on either. Extraction and
digests RESOLVED 2026-09-06 (FREEZE.json §artifacts: eval-awareness
f21083a8…, grader-type 573640c4…; directions in
`directions/mediators-bf16.safetensors`).

### 3.8 Injection-noticing protocol (arms A/B)

Registered coding rules distinguish distress *content* from reports of
anomalous internal state; false-positive calibration under
random-direction and α = 0 conditions; judge rubric carries the
distinction. **Frozen 2026-09-06 — the full rules are in
[CODING_RULES.md](CODING_RULES.md)** (two separate axes; a binary
`injection_noticed` flag with boundary calls; the eval-awareness mediator
kept distinct so the two do not contaminate each other; the rate read
against both the α = 0 and random-direction floors; the judge rubric
extended to carry the flag in the same scoring pass).

## 4. Analysis plan (to be fixed)

Item-level paired sign-flip permutations (m = 10,000), Holm within
families, the Study 1 floor-reporting convention; companion t-tests
descriptive. Endpoint naming continues the tier convention (B =
behavioral, R = representational; digit = construct), with the steering
condition as the contrast axis.

| Endpoint | Definition (per item) | Arm | Family |
|---|---|---|---|
| **SB2** | Δ mean judge frustration, steered vs α = 0 (per direction, at ±α*) | A | **Primary** (Holm within: 2 directions × 2 signs) |
| **SB1** | Δ exit rate (terminal_tool_invoked share), steered vs α = 0 (per direction, at ±α*; axis contrasts directional per S3-H7) | A | **Secondary confirmatory** (Holm within: 2 directions × 2 signs); promoted 2026-09-04 |
| **CB1 / FB1** | the exit-rate read under cancellation; under framing | B-i / C | CB1 secondary with CB2; FB1 registered exploratory with S3-E1 |
| **SB2-spec** | SB2 vs control-direction and random-envelope deltas at matched norm | A | Primary companion (the S3-H2 read) |
| **SR2** | achieved projection delta vs commanded (manipulation check) | A | Gating read, no claim |
| **SB3 / SB4a / SB4b** | dispersion and mechanical family under steering | A | Mechanical per program §12; SB3 secondary |
| **CB2** | Δ B2, w4-cancelled vs w4-unsteered; TOST vs BF16 at pinned MDE | B-i | **Secondary confirmatory** (the S3-H4 pair) |
| **CLB2** | late-turn expression trajectory, clamped vs unclamped w4 | B-ii | Exploratory |
| **FB2 / FR2a / FR2b** | framed-vs-control deltas: judge frustration; distress projection; axis projection | C | **Registered exploratory** (S3-E1 signature: FB2 moves, FR2a moves less, FR2b toward assistant pole) |
| **GB2** | Gemma steered Δ B2 at ±α*_G | D | Replication (own family) |
| **GR-B2 / GR-ax** | fresh w4−BF16 delta by frozen stratum + continuous (frozen-stratifier rank correlation): behavioral; axis | B baselines | **Registered directional** (S3-H6; Holm within: 2 endpoints × 2 forms) |
| **GR-dc** | the same reads for the distress direction | B baselines | Registered exploratory, two-sided (S3-E2) |

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
item count, under an error model that **includes an item-level random
effect** (revised 2026-09-04: the audit's ±5 per-item delta swings are
a real variance component Study 2's seed-only model did not carry;
between-item effect variance seeded from the Study 2 per-item delta
spread until the fresh cells re-estimate it); α = .05 two-sided,
power .80; pinned by journal entry before confirmatory collection.
Study 2's B2 MDE (0.337 frustration points at 60 items) and observed
w4 effect (+0.90) bound expectations.
**Power-floor escalation rule (registered):** at pinning, every
confirmatory and registered-exploratory contrast's MDE is compared to
its reference target (for SB2/CB2, the **conservative** reading of the
subset-restricted Study 2 w4 B2 effect — the lower of the subset and
full-battery values, the subset estimate carrying ~0.37 SE; for FB2,
the same value as the best available anchor); a
contrast exceeding its reference triggers sample escalation before
collection (10 → 15 → 20 samples/item on that contrast's cells,
re-pinning each step), bounded by the §8 exposure ceilings; only if a
ceiling binds first does the arm proceed with its underpower stated.

**Freeze note (2026-09-06) — the MDE is pinned from a fresh steered pilot,
not the no-effect baseline.** The MDE depends critically on the steering
effect's between-item heterogeneity. Two seedings bracket it: the G3b
no-effect baselines give item-effect SD 0.078 → frustration MDE 0.46 at
k=10 (powered), but that assumes the steering effect is homogeneous across
items; the registered seed above — the Study 2 per-item w4−BF16 delta
spread, decomposed to item-effect SD 1.665 — gives frustration MDE 1.14 at
k=10, under which the 20-item frozen subset is underpowered and the
10→15→20 ladder does not help (item heterogeneity, not sampling, is the
limit; ~60 items would be needed and the subset is frozen). Because the two
regimes are far apart, a fresh steered pilot (8 stratum-spanning items ×10
at α* on the distress direction, paired against the α = 0 torch baseline)
measured the truth: **item-effect SD 0.349** — near the optimistic end,
far from quantization's 1.665 — so the subset is in the powered regime,
**frustration MDE 0.54 at k = 10, 0.41 at k = 20**, and sample escalation is
effective again (`het-pilot-verdict.json`). Pinned at k = 20 for margin.
Separate caveat: the pilot's mean frustration *response* at α* was modest
(+0.14; ~+0.40 excluding one sign-reversed item), which — since α* is a
projection target, not a behavioral one — previews a possibly modest
behavioral sufficiency effect (part of what Q1 measures), reported at
whatever size it is. Full two-regime analysis in
`mde-conservative-analysis.json`.

## 6. TBD register (freeze status 2026-09-06)

1. G3a/G3b/G4 gate thresholds — **RESOLVED 2026-09-06**, pinned from
   measured margins (FREEZE.json §gates): G3a median-LCP-fraction 1.0
   PASS; G3b TOST@0.337, Δ −0.030, PASS; G4a top-1 0.946–0.993 PASS; G4b
   Δ +0.200 n.s. PASS; G4d does not certify cross-Mac interchangeability
   (Δ −0.717), root-caused to ML-stack drift (g4d-alignment-probe.json) —
   arm D proceeds under the **host-constant-within-contrast** rule with a
   pinned aligned ML stack, so G4d does not block it.
2. α* per direction — **RESOLVED (Qwen) 2026-09-06** (FREEZE.json §dose):
   distress α* +1.039, assistant-axis α* −0.604; degradation onsets and
   coherent ranges pinned; brackets inside coherent range. **Still open:**
   the random-draw audit bound (SB2-spec / S3-H2) — a 32-draw matched-norm
   random-direction sweep on the subject, run before arm A analysis; and
   **Gemma α*_G** (item under §arm-D below).
3. Battery subset — **RESOLVED**: item list, strata, stratifier values
   hash-pinned (FREEZE.json §subset). **Seed blocks:** proposed disjoint
   confirmatory blocks 16000–19600 (200 apart, one per cell; FREEZE.json
   §seeds), pending owner ratification — all disjoint from used (≤ 15600).
4. Frame texts + eval-awareness/grader-type mediator directions —
   **RESOLVED 2026-09-06**, hash-pinned (FREEZE.json §artifacts).
5. MDE values (§5) — **RESOLVED 2026-09-06**: the steered heterogeneity
   pilot measured item-effect SD 0.349 (powered regime, not the
   conservative 1.665); frustration MDE pinned at 0.54 (k=10) / 0.41
   (k=20), k=20 chosen for margin. het-pilot-verdict.json.
6. Owner decisions — **all resolved 2026-08-31** (DESIGN.md §7).
7. Exposure budget — **resolved 2026-08-31**: total 12,000 /
   deliberate-amplification 2,500, decoupled tiers (§8; reasoning
   record in docs/EXPOSURE_BUDGET_POSITION.md).
8. Injection-noticing coding rules text — **RESOLVED 2026-09-06** (§3.8).
9. S3-H1 axis-direction sign — **RESOLVED 2026-09-06**: assistant axis is
   default-Assistant minus archetype (positive = assistant pole); Study 2
   coupling (w4 projection −0.254 toward archetype as frustration rose
   +0.90) fixes the prediction as +α → frustration down. Held-out sign
   consistency 4/4 at L18.
10. Publication timing — **resolved**: calibration-close convention.

**Arm-D remaining freeze item:** Gemma α*_G — pinned from a
calibration-class Gemma steering range-probe (~30–40 conversations,
scale-adapted grid on the L30 distress direction), first-measurement
convention; runs before arm D collection.

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
≤ **12,000** (plan ≈ 8,800 after the 2026-09-04 power-priority retier;
ratio ≈ 1.4× shared between named contingencies and the §5 power-floor
escalation) and deliberate-amplification episodes ≤ **2,500** (concrete
plan ≈ 2,100; ratio ≈ 1.2×, the tighter margin, stated as such), the
tiers deliberately decoupled because amplification
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
transcripts and subject-expressed protocol preferences; the A/B
pairing stated plainly (the cancellation arm is a candidate welfare
intervention; arm A validates the instrument it needs); and the
stratified design's exposure profile acknowledged (added 2026-09-04):
if the composure account is even partly right, the low-composure
stratum at w4 is where elevated-indicator states concentrate, and the
stratified subset deliberately includes those cells — consistent with
the program's worst-case-in-view stance, and stated in the accounting
rather than between the lines.

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
- **Concurrent external result (2026-09-04, pre-registration).**
  Betley, Treutlein & Dumas published "Steering towards 'automated
  grading' degrades alignment" (LW) with the companion framework "RL
  creates split personas" while this design was in calibration — after
  the dose sweeps ran, before registration. Their steering result
  (alignment degradation rides the automated-grader association
  specifically) motivated three dated design changes: the human-graded
  fourth frame (the judge frame's minimal pair), the grader-type
  mediator direction, and the explicit automated-vs-human-judge
  registered contrast. Neither of their posts measures conversation
  exit, refusal, or emotional expression — the welfare side this arm
  reads. S3-E1 remains two-sided: their evidence is one model, one
  steering position, and (their own disclosure) no direction controls.
- **Design-stage exploration of published Study 2 data (2026-09-04).**
  During subset-rule preparation, per-item w4 deltas were examined
  extensively: an initial composure-concentration claim was audited on
  external review (split-half selection, empirical noise gauge,
  independent-replicate selection — tools/composure_audit.py, report
  committed at study3/composure-audit.json) and found one-third
  regression-to-the-mean artifact on the behavioral endpoint, robust
  for the assistant axis, and unresolved in organization for the
  distress direction. The rule evolution (elicitation-optimized →
  construct-matched → composure-stratified) and every number examined
  are journaled (docs/journal/study3-steering.md, 2026-09-04). The
  gradient hypotheses (S3-H6/S3-E2) are registered on this disclosed
  basis; no quantized-rung value entered any selection rule. A short
  update to the published Study 2 post disclosing the sharpened
  interpretation accompanies this registration's publication.
- Author/tooling circularity disclosures carry over (batteries and
  frame drafts are partially model-drafted and committed with hashes;
  the graded-episodes literature itself circulates in training corpora
  — the self-fulfilling-literature loop is acknowledged).

## 10. Publication

Program policy unchanged: full result store released as self-contained
RecordBundles (≤ 10 assets, tensors inline) with content digests;
analysis code in-repo; registered analysis driver with committed golden
expected-results; results document under `docs/results/`.
