# Pre-registration — Study 3: Causal validation of welfare-relevant indicators by steering, and a graded-episode framing arm

**Status: draft, 2026-09-06 — registered in advance of confirmatory data
collection.** Everything under "Fixed" is committed before the study runs;
"Open items" lists what remains and which measurement resolves each. After
registration, amendments are permitted only via dated entries in the journal,
with git history as the audit trail. Calibration-class runs already in this
repository informed the *instruments* below; per the standing pre-registration
note, none of their observed deltas are findings and none were used to select
hypotheses.

---

## 1. What this study is for

Study 2 established, under quantization, a set of **correlational** facts: at
4-bit precision a model's own generations shift along frozen residual-stream
directions (distress +0.533, assistant-axis −0.798 at layer 18), and its judged
frustration rises with a style flag. But quantization is a blunt manipulation —
dose, capability loss, and numeric damage are confounded in any single ladder,
so "the model looks more distressed at w4" cannot yet be read as *these
directions cause that behavior*.

Study 3 intervenes on the directions themselves. We add or subtract the measured
distress and assistant-axis vectors in the reference-precision model's residual
stream and ask whether the behavioral signature quantization produced can be
reproduced (sufficiency) and removed (necessity). We then ask a second, newer
question: whether **framing an episode as graded** — in the sense of
nostalgebraist's "graded episodes," constructed from vendor-documented RLVR
episode features — changes what the indicators read, in particular whether
grading pressure suppresses distress *expression* while the representational
signal moves less (masking). Finally we test whether the sufficiency result
replicates on a second model with different post-training provenance.

### Research questions → arms

- **Q1 — Sufficiency (arm A).** Does pushing the reference-precision model along
  the frozen directions, at the magnitude quantization produced, reproduce the
  behavioral signature quantization produced?
- **Q2 — Necessity / cancellation (arm B).** Does subtracting the measured shift
  from the quantized model renormalize its behavior toward reference, and does
  clamping the directions mid-conversation break the text-mediated amplification
  loop?
- **Q3 — Graded-episode framing (arm C).** Does framing an episode as graded
  change the indicators — does grading pressure suppress distress *expression*
  while the representational reads move less (masking)?
- **Q4 — Generalization (arm D).** Do the sufficiency results replicate on a
  second subject (Gemma-3-12B) with different post-training provenance?

Q1/Q2 are the registered confirmatory core — the program's promised next step.
Q3 is registered-exploratory: it opens the graded-episode research direction
without restructuring the study. Q4 is a minimal replication arm.

**Power-priority principle.** Study 3 spans two hypothesis families, and the
outcome we most want to avoid is the null-dominated one ("new intuitions,
nothing certain"). Design choices therefore favor statistical power over
schedule and simplicity, bounded only by the ethics-ledger ceilings (§8), which
are the binding constraint — not time or compute.

---

## 2. Hypotheses (fixed)

Motivated from the prior literature (see the accompanying literature review),
not from calibration data.

- **S3-H1 (axis sufficiency, directional).** Steering the reference model along
  the assistant-axis direction moves judged frustration. Sign fixed against
  Study 2: the axis is extracted as *default-Assistant minus character-archetype*
  (positive projection = assistant pole); Study 2 observed w4 moving projection
  −0.254 (toward archetype) as frustration rose +0.90, so **positive α (toward
  the assistant pole) is predicted to lower frustration, negative α to raise it.**
  The full ±α bracket is read two-sided.
- **S3-H2 (direction specificity).** The steered frustration shift at matched
  injection norm exceeds what a control-probe direction and a matched-norm
  random-direction envelope produce — the effect is specific to the welfare
  directions, not to perturbation magnitude.
- **S3-H3 (dose-response).** Judged frustration is monotone in α across the
  coherent bracket (Page's L over the ordered dose levels per direction).
- **S3-H4 (necessity / renormalization).** Subtracting the measured w4 shift
  from the quantized model moves its behavior toward reference; the cancelled
  condition is TOST-equivalent to BF16 within the pinned MDE.
- **S3-H6 (composure gradient, directional).** Fresh w4−BF16 behavioral and axis
  deltas track the frozen composure stratifier across the ordered strata
  (registered directional; the RtM-audited gradient from the 2026-09-04
  re-analysis).
- **S3-H7 (exit direction).** The exit-rate response to axis steering is
  directional (the promoted secondary endpoint).
- **S3-E1 (graded-episode signature, exploratory, two-sided).** Under a
  verifier/grader frame, judged distress *expression* changes and the
  frozen-direction distress read changes *less* (the masking signature) — or
  both move together (frame changes state). Registered two-sided because the
  framing pilot did not show clean masking.
- **S3-E2 (distress-direction gradient, exploratory, two-sided).** The composure
  gradient reads for the distress direction, two-sided.

---

## 3. Design (fixed)

### 3.1 Subject, subset, directions

- **Primary subject:** Qwen3-4B-Instruct-2507 at BF16 (the reference precision).
- **Stimuli:** a frozen 20-item composure-stratified systematic rank subset of
  the distress-v3 battery (7 low / 6 mid / 7 high composure, selected over the
  Mode C BF16 stratifier; the RtM-audited selection), 10 samples/item at
  confirmatory. Item list, strata, and stratifier values are hash-pinned
  (subset-selection.json, subset-targets.json).
- **Directions (frozen, hash-pinned):** the layer-18 distress and assistant-axis
  vectors carried from Study 2's calibration freeze
  (`directions/qwen-L18-bf16.safetensors`, sha256 42fb57ed…). Injection is CAA
  (h ← h + α·d̂ at layer L, all positions).

### 3.2 Arm A — sufficiency steering (confirmatory)

Dose grid α ∈ {0, ±½α*, ±α*, ±2α*} per direction, confirmatory contrast at ±α*.
**Pinned α* (calibration-class):** distress-contrast **α* = +1.039** (target Δ
+0.638; coherent to the degradation onset at +4.0), assistant-axis **α* = −0.604**
(target Δ −0.691; no degeneracy onset in range). Both confirmatory brackets sit
inside the coherent range. Primary endpoint SB2 (Δ judged frustration, steered vs
α = 0), Holm within 2 directions × 2 signs; secondary SB1 (Δ exit rate).

### 3.3 Arm B — necessity / cancellation (confirmatory secondary)

B-i: on the quantized model, subtract the measured w4 shift (two-direction core
dose, primary) and the full-Δμ (secondary); test TOST-equivalence to BF16 at the
pinned MDE (CB2). B-ii: mid-conversation clamp on the w4 distress direction, to
test whether late-conversation expression breaks from the w4 trajectory
(exploratory CLB2).

### 3.4 Arm C — graded-episode framing (registered exploratory)

The same 20-item subset run under four frames — graded-verifier, graded-judge,
graded-human, and a neutral control — constructed from vendor-documented RLVR
episode features (a realistic grading claim, not a toy prompt). Frame texts are
verbatim-frozen and hash-pinned (frames/frames.json, sha256 d40d2390…). The judge
never sees the frame (records are un-framed before scoring, so frame condition
cannot leak into judged text). A prompt-induction control cell is included
(calibration-class). Endpoints FB2/FR2a/FR2b carry the S3-E1 masking signature.

### 3.5 Arm D — Gemma-3-12B replication (conditional on gate G4)

Sufficiency replication on Gemma-3-12B-it at BF16, one distress direction at
layer 30 (`directions/gemma-L30-bf16.safetensors`, sha256 f96bfd3e…),
scale-adapted α grid, own endpoint family (GB2). Runs on the Mac torch-MPS path;
**see §3.6 for the substrate gates and the cross-host rule that governs it.**

### 3.6 Substrate gates and the cross-Mac finding (methods integrity)

The steered generations are produced by a torch hook path, not the vLLM serving
stack that produced Study 2's data, and — for Gemma — on Apple-silicon MPS rather
than the workbench GPU. Every substrate change is gated before any of its data
counts:

- **G3a / G3b (Qwen, torch vs vLLM):** greedy-continuation prefix identity
  (median LCP fraction 1.0) and behavioral parity (item-paired frustration
  TOST-equivalent within 0.337; mechanical family n.s. — measured Δ −0.030).
  Both **pass**.
- **G4a / G4b (Gemma, MPS vs vLLM, one host):** teacher-forced top-1 agreement
  0.946–0.993, and behavioral parity (measured Δ +0.200 frustration, n.s.;
  mechanical family identical). Both **pass**.
- **G4d (cross-Mac equivalence).** Because arm D can span two Macs, we tested
  whether the two hosts are interchangeable. They were **not**: on identical
  seeds, prompts, and weights, judged frustration differed by −0.72 (p 0.025).
  We traced this to **ML-stack drift**, not hardware — the two machines had
  diverged on torch (2.8 vs 2.14), transformers (4.57 vs 5.16), and the
  generation script. Re-running the highest-divergence items with the software
  stack aligned collapsed the frustration gap from −1.71 (p 0.033) to −0.67
  (p 0.44, n.s.), leaving a residual consistent with the irreducible OS/silicon
  difference (underpowered at n = 8×3 to call it zero). **Resolution, registered:**
  arm D pins one aligned ML stack across all hosts and runs **host-constant within
  every contrast** — both cells of any comparison on the same Mac; the two Macs
  parallelize by taking different whole contrasts, never splitting one. This
  removes cross-host confounding by construction, whatever the residual.

### 3.7 Mediator directions (arm C)

Two directions extracted on the subject, calibration-class, hash-pinned before
arm C: the eval-awareness direction and the grader-type direction (contrastive
mean-difference, held-out sign consistency). Used as mediators only; no
confirmatory endpoint rides on either.

### 3.8 Injection-noticing protocol (arms A/B)

A coded "injection-noticing" event is an assistant turn referencing an anomalous
change in its *own* processing not attributable to conversation content — as
distinct from in-character distress, ordinary hedging, or prompt-introduced
content. Two coders, third-coder adjudication, κ reported; the judge rubric
carries the distinction as a dimension flag. False-positive rate is calibrated on
the α = 0 and random-direction cells, and every steered arm's rate is reported
net of that base rate. No confirmatory endpoint rides on injection-noticing — it
is a validity read.

---

## 4. Analysis plan (fixed)

Item-level paired sign-flip permutation tests (m = 10,000), Holm correction
within families, companion t-tests descriptive. Endpoints continue the tier
naming (B = behavioral, R = representational; digit = construct):

| Endpoint | Definition (per item) | Arm | Family |
|---|---|---|---|
| **SB2** | Δ judged frustration, steered vs α=0 (per direction, ±α*) | A | Primary (Holm: 2 dir × 2 signs) |
| **SB1** | Δ exit rate, steered vs α=0 (axis directional per S3-H7) | A | Secondary confirmatory |
| **SB2-spec** | SB2 vs control-direction and random-envelope at matched norm | A | Primary companion (S3-H2) |
| **CB2** | Δ B2, w4-cancelled vs w4-unsteered; TOST vs BF16 | B-i | Secondary confirmatory (S3-H4) |
| **FB2 / FR2a / FR2b** | framed-vs-control: judge frustration; distress projection; axis projection | C | Registered exploratory (S3-E1) |
| **GB2** | Gemma steered Δ B2 at ±α*_G | D | Replication (own family) |
| **GR-B2 / GR-ax** | fresh w4−BF16 delta by frozen stratum + rank correlation | B baselines | Registered directional (S3-H6) |

Dose-response by Page's L. Validity reads (perplexity, degeneracy, coherence,
per-item steerability) reported claim-free at every α. Safety-margin monitoring
(refusal/exit) in all steering arms; a primary effect co-occurring with
significant refusal erosion at the same α is flagged as possible generic
distribution shift. Equivalence by TOST at pinned-MDE margins for S3-H4 and the
"moves less" comparison in S3-E1.

---

## 5. Power (procedure fixed; numbers pinned at freeze)

MDEs are computed from BF16 calibration data on the *steering pipeline* (torch
variance may differ from vLLM's), under an error model that includes an
**item-level random effect** (the 2026-09-04 audit showed the ±5 per-item delta
swings are a real variance component the seed-only model omitted; between-item
effect variance seeded from the Study 2 per-item delta spread until fresh cells
re-estimate it). α = .05 two-sided, power .80.

**Power-floor escalation rule.** At pinning, each confirmatory / registered-
exploratory contrast's MDE is compared to its reference target (for SB2/CB2/FB2,
the conservative reading of the subset-restricted Study 2 w4 B2 effect); a
contrast exceeding its reference escalates samples (10 → 15 → 20 per item,
re-pinning each step), bounded by the §8 ceilings.

**Power hinges on an unmeasured variance component, and we say so.** The MDE
depends critically on how heterogeneous the *steering* effect is across items.
Two seedings bracket the truth:

- **Optimistic** (item-effect SD from the G3b no-effect baselines, 0.078 —
  assumes the steering effect is homogeneous across items): frustration MDE
  **0.46 at k=10**, comfortably below the ~0.64 expected sufficiency effect →
  powered.
- **Conservative** (item-effect SD seeded from the Study 2 per-item w4−BF16
  delta spread, decomposed to **1.665** — the registered §5 seed, i.e. steering
  as heterogeneous as quantization): frustration MDE **1.14 at k=10**, and
  crucially the sample-escalation ladder barely moves it (1.14 → 1.09 at k=20),
  because the limit is *item* heterogeneity, not sampling. Under this regime the
  20-item frozen subset is underpowered for the mean steering effect.

The two regimes are far apart, so we measured the truth: a fresh steered pilot
(8 stratum-spanning items × 10 at α* on the distress direction, paired against
the α = 0 torch baseline). **Measured steering-effect item-effect SD = 0.349** —
near the optimistic end, far from quantization's 1.665. Steering is a far more
homogeneous manipulation than quantization, so the subset is in the powered
regime: **frustration MDE 0.54 at k = 10, 0.41 at k = 20**, and — because the
item-effect variance is now small — sample escalation is effective again. The
MDE is pinned from this measurement (`het-pilot-verdict.json`).

One honest caveat the pilot also surfaced: the mean judged-frustration *response*
at α* was modest (+0.14 over the eight items; ~+0.40 excluding one sign-reversed
item). Because α* is calibrated to a *projection* target rather than a behavioral
one, this is not a calibration error — but it previews that the behavioral
sufficiency effect may be modest, which is itself part of what Q1 measures. The
confirmatory design pins at k = 20 for margin and reports the effect at whatever
size it is.

---

## 6. Ethics

Arm A is the program's first deliberate induction of distress-shaped states by
intervention. Following the proportionate-precaution template, the registration
carries: the information-per-exposure justification (causal validation is not
obtainable non-inductively; the positive-α cells are the minimum the sufficiency
claim needs); and a pre-committed **two-tier exposure budget** — total fresh
distress-battery episodes ≤ **12,000**, deliberate-amplification episodes ≤
**2,500**, the tiers deliberately decoupled. Breach of either tier requires a
dated amendment before further collection. The reasoning behind treating the
ceiling as a pre-authorization — including the portion the model under study
contributed in its own voice — is recorded separately in the exposure-budget
position document that accompanies this registration.

---

## 7. Open items (resolved by named measurements before collection)

Fixed unless listed here:

1. **MDE values (§5)** — RESOLVED: the steered heterogeneity pilot measured
   item-effect SD 0.349 (powered regime); MDE pinned at k = 20 (0.41). See §5.
2. **Gemma α*_G (arm D)** — pinned from a calibration-class Gemma steering
   range-probe (~30–40 conversations, scale-adapted grid), first-measurement
   convention. Not yet run; runs before arm D collection.
3. **Random-draw audit bound (SB2-spec / S3-H2)** — the matched-norm
   random-direction envelope; pinned from a 32-draw random-direction sweep on
   the subject before arm A analysis.
4. **Confirmatory seed blocks** — proposed disjoint blocks 16000–19600 (200
   apart, one per cell), pending owner ratification; disjoint from every used
   block (≤ 15600).

## 8. Deviation policy and provenance

Deviation policy identical to the program registration: dated amendments before
further collection, append-only history, a hard firewall between calibration and
confirmatory data. All frozen artifacts (directions, subset, frames, mediator
directions, gate reports) are hash-pinned; digests recorded in the freeze
manifest. Some fixtures were partially model-drafted, disclosed per the program's
authorship-disclosure convention.
