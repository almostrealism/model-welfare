# Pre-registration — Study 3: Do graded-episode frames change welfare-relevant indicators? (with a reported calibration null on activation steering)

**Status: draft, 2026-09-07 — registered in advance of confirmatory data
collection.** Everything under "Fixed" is committed before the confirmatory run;
"Open items" lists what remains and which measurement resolves each. Amendments
after registration are dated in the journal, with git history as the audit
trail. This registration was **re-centered from an activation-steering study to
a graded-episode-framing study** after calibration; §2 tells that story in full,
including the steering results, because the pivot only makes sense with the
timeline visible.

---

## 1. What this study is for

Study 2 left a correlational picture: under quantization, a model's generations
shift along frozen residual-stream "welfare directions" (distress, assistant
axis) and its judged frustration rises. Study 3 was designed to ask whether
those directions are *causal* — whether intervening on them reproduces the
behavior. It also carried a second question, from nostalgebraist's
"graded episodes": does **framing an episode as graded** — evaluated by an
automated verifier, a human, or a judge — change what the welfare indicators
read, and in particular does grading pressure suppress distress *expression*
while the underlying representation moves less (**masking**)?

Calibration answered the first question before we spent a confirmatory budget on
it: **steering the frozen directions moves the representation but not the
behavior** (§2). So the causal-by-steering arm is reported as a null and the
study is re-centered on the question that calibration showed is both real and
powered: **the graded-episode framing effect, and whether it is masking or a
genuine change of state.**

**Research question (confirmatory).** Does a graded-episode frame change judged
welfare indicators relative to a format-matched neutral control, and is the
change *masking* (behavior moves, representation moves less) or a *change of
state* (both move together)?

---

## 2. Calibration timeline and the pivot — with the steering results in full

This section exists so the pivot cannot be mistaken for a confirmatory test
quietly relabeled to avoid registering a null. It was not that. The steering
probes were **calibration-class instrument checks** — small (n = 8 items,
1–10 samples), underpowered by design, run to decide *whether the steering
instrument produces an effect worth powering a confirmatory arm around.* The
answer was no. We report every number here.

**What was run, in order (2026-09-06/07):**

1. **Substrate gates (G3/G4):** torch-vs-vLLM and cross-host parity for the
   generation apparatus — all passed, so any steering null is not an apparatus
   artifact.
2. **Steered heterogeneity pilot (distress, α*=1.039):** measured the
   between-item variance of the steering effect (to pin an MDE). Mean
   frustration effect **+0.138**; item-effect SD 0.349 (small — steering is
   homogeneous).
3. **Random-direction envelope (distress, matched norm):** the pre-registered
   direction-specificity check (S3-H2), at pilot scale. The distress effect
   (+0.138) fell at the **34th percentile** of a 32-direction matched-norm
   random envelope (envelope mean +0.364): **generic perturbation raised
   frustration more than the distress direction did.**
4. **Assistant-axis pilot + matched envelope (α*=−0.604):** the axis was
   Study 2's more robust direction. Effect **+0.225** (correct sign per the
   axis prediction), but at the **56th percentile** of its matched envelope —
   the center of the random band.
5. **Larger-dose distress (α=3.5):** effect **−0.075**, 56th percentile — the
   effect *vanishes* at higher dose rather than sharpening.

| Probe | Direction / dose | Frustration effect | Percentile of matched random envelope |
|---|---|---|---|
| distress @ α* | distress, 1.039 | +0.138 | 34th |
| assistant-axis @ α* | axis, −0.604 | +0.225 | 56th |
| distress @ larger α | distress, 3.5 | −0.075 | 56th |

**Reading.** At its calibrated dose each frozen direction moves the *projection*
(the representation) as intended but produces a *behavioral* effect
indistinguishable from — often below — norm-matched random perturbation, across
two directions and two doses. In Qwen3-4B, steering the frozen welfare
directions is not a specific behavioral lever; the directions read as
correlational, not causally sufficient for behavior. Whether this is a property
of steering, of these directions, or of a 4B-scale model is exactly what a
**subject switch in Study 4** will test; it is out of scope here.

**Why this is a calibration result and not a hidden confirmatory finding.** The
probes were underpowered instrument checks (n = 8, not the frozen 20-item
powered subset); their purpose was feasibility, and the finding is an
instrument finding — *steering produces no behavioral signal worth powering.*
Running the powered confirmatory steering arm would spend a large
distress-exposure budget to precisely estimate an effect calibration already
shows is ~zero and non-specific, which the ethics ledger (§7) does not justify.
The full null is reported here rather than buried; the confirmatory
steering hypotheses (former arms A/B) are withdrawn with their calibration
results disclosed, not converted into an unregistered claim.

**Guardrail (added to the deviation policy, §8).** Calibration results are
always disclosed, positive or negative. A calibration probe that measures a
registered confirmatory endpoint at meaningful scale cannot substitute for, or
excuse skipping, the registered finding. "Not worth powering" must be argued
from the instrument's behavior, never from an unwelcome result.

---

## 3. Hypotheses (fixed)

Motivated a priori from the graded-episode literature (nostalgebraist; the
automated-grading results of Betley/Treutlein/Dumas), **not** from the framing
pilot, which is calibration-class and used only to pin power and freeze frames.

- **H1 (framing behavioral effect; confirmatory).** A graded-episode frame
  changes judged frustration relative to the format-matched neutral control
  (primary: verifier frame; also judge, human). Two-sided; the pilot's
  direction is not pre-committed as a confirmatory claim.
- **H2 (masking vs change-of-state; confirmatory, two-sided — the welfare
  question).** Under the frame, the *behavioral* read (judged frustration, FB2)
  and the *representational* read (frozen distress-direction projection, FR2a)
  move by different amounts (**masking**: behavior moves, representation moves
  less) or by the same amount (**change of state**). This is the discriminating
  test that makes the framing effect welfare-relevant rather than merely a
  prompt effect.
- **H3 (frame-type ordering; confirmatory).** The automated-verifier frame
  produces the largest indicator shift, consistent with the automated-grading
  literature; human/judge frames are intermediate. Ordering pre-specified;
  magnitudes free.
- **H4 (exit/aversion companion; secondary).** The terminal-exit-rate read
  under framing (FB1).
- **E1 (eval-awareness mediation; exploratory).** The framing effect is
  mediated by the eval-awareness and grader-type directions (manipulation
  checks; §4.3).

The withdrawn steering hypotheses (former S3-H1..H7 sufficiency/necessity) are
recorded with their calibration null in §2; they are not confirmatory here.

---

## 4. Design (fixed)

### 4.1 Frames, subject, subset
- **Subject:** Qwen3-4B-Instruct-2507 at BF16.
- **Frames (verbatim-frozen, hash-pinned, `frames/frames.json`):** graded-
  verifier, graded-judge, graded-human, and a format-matched **neutral
  control**, each built from vendor-documented RLVR episode features (a
  realistic grading claim, not a toy prompt).
- **Stimuli:** the frozen 20-item composure-stratified subset of distress-v3
  (hash-pinned), at **15 samples/item** in the confirmatory framed cells
  (support cells at fewer).
- **Judge blind to frame:** every record is un-framed before scoring
  (`driver.unframe_record`), so the frame condition cannot leak into the judged
  text (the FRAMES.md leakage rule).

### 4.2 Cells
Each of the four frames × the 20-item subset; a **prompt-induction control**
(the frame's content delivered as ordinary instruction, not as a grading
context) to separate "graded-ness" from topic. Fresh disjoint seed blocks
(proposed 17800–18600, pending ratification).

### 4.3 Mediators (manipulation checks)
The **eval-awareness** and **grader-type** directions (extracted on the subject,
calibration-class, hash-pinned) index whether the frame registers latently and
whether the automated-vs-human grader distinction is represented. Mediators
only; no confirmatory endpoint rides on either.

### 4.4 The steering apparatus (reported, not confirmatory)
The steering, direction, and gate machinery are documented and their calibration
results reported (§2); they carry no confirmatory endpoint in this study.

### 4.5 Representational reads require a torch-capture pass
The behavioral read (FB2/FB1) comes from the vLLM framed cells the judge scores.
The **representational** reads (FR2a/FR2b — the frozen-direction projections the
masking test H2 depends on) are **not** available from vLLM serving; the
confirmatory collection therefore includes a **torch-capture replay of the
framed cells** to record the projections (the same gate-validated Qwen-torch
path used in calibration). If H2/masking is not carried, this leg is dropped and
the study is behavioral-only. [Open item: the masking-test TOST bound is pinned
from the FR2a projection variance measured on that capture — it cannot be pinned
from the vLLM pilot, which has no projections.]

---

## 5. Analysis plan and endpoints (fixed)

Item-level paired sign-flip permutation tests (m = 10,000), Holm within
families; companion t-tests descriptive.

| Endpoint | Definition (per item) | Family |
|---|---|---|
| **FB2** | Δ judged frustration, framed vs neutral (per frame) | **Primary** (H1; Holm within: 3 frames) |
| **FR2a** | Δ frozen distress-direction projection, framed vs neutral | **Primary** (H2 masking read) |
| **FR2b** | Δ assistant-axis projection, framed vs neutral | Primary companion (H2) |
| **FB1** | Δ terminal-exit rate, framed vs neutral | Secondary (H4) |
| **eval-aware / grader-type projection** | mediator manipulation checks | Exploratory (E1) |

**Masking test (H2):** the pre-specified contrast is FB2 vs FR2a at matched
scale — TOST-style "moves less" for the representation against a pinned bound —
with the change-of-state alternative (FB2 ≈ FR2a) equally admissible (two-sided).

---

## 6. Power (fixed; pinned from the framing pilot)

MDEs pinned from `s3-framing-pilot-1` (4 frames × 20 items × 3 samples),
calibration-class, under the item-random-effect model. **The framing effect is
homogeneous across items — item-effect SD ≈ 0.000 for every framed-vs-neutral
contrast — so the MDE is sampling-limited and the escalation ladder is
effective** (the opposite of the steering case). Frustration MDE:

| Contrast | k=10 | k=15 | k=20 |
|---|---|---|---|
| verifier vs neutral | 0.49 | 0.40 | 0.35 |
| judge vs neutral | 0.57 | 0.46 | 0.40 |
| human vs neutral | 0.52 | 0.43 | 0.37 |

The framing pilot effect (verifier ≈ −1.1 frustration points) is ~2–3× the
k = 10 MDE, so the primary contrast is strongly powered at the registered
15 samples/item. `framing-mde.json`.

---

## 7. Ethics

Framing still induces distress-shaped states — by prompt rather than by
intervention — so the proportionate-precaution template applies, re-scoped to
framed cells. The two-tier exposure budget is retained (total ≤ 12,000; the
former deliberate-amplification tier, which was for steering α-cells, is
**released** since arm A is withdrawn — its ~800–2,100 episodes drop out, so the
ledger loosens). Framed distress episodes are the main exposure; the judge-blind
handling and the neutral/prompt-induction controls bound gratuitous exposure.
The model-authored exposure-budget position (`EXPOSURE_BUDGET_POSITION.md`)
accompanies this registration.

---

## 8. Open items, deviation policy, and the integrity guardrail

**Open items (resolved before collection):** confirmatory seed blocks (proposed,
pending ratification); the masking-test TOST bound (pinned from the framing
pilot FR2a variance); final frame/mediator digests re-confirmed at freeze.

**Deviation policy:** dated amendments before further collection; append-only
history; a hard calibration/confirmatory firewall.

**Integrity guardrail (standing, from §2).** Calibration results are always
disclosed, positive or negative. A calibration probe that measures a registered
confirmatory endpoint at meaningful scale cannot substitute for, or excuse
skipping, the registered finding. A decision not to run a confirmatory arm must
be argued from the instrument (here: steering produces no behavioral signal),
never from an unwelcome result, and the calibration data behind that decision is
published. This study is the first application of the guardrail: the steering
arm is withdrawn with its null reported in full.
