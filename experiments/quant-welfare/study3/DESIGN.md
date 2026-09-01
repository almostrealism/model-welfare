# Study 3 design — Causal validation by steering, and the graded-episode framing arm

> **STATUS: DESIGN DOCUMENT** (2026-08-31, drafted after the pre-registration
> literature sweep in [LITERATURE.md](LITERATURE.md)). This document is where
> design decisions are argued; [REGISTRATION.md](REGISTRATION.md) is where
> they become commitments. Owner decisions were resolved 2026-08-31 and
> are recorded in §7. Nothing here is frozen until the registration's
> calibration-close freeze; constraints marked **[binding]** in
> LITERATURE.md are treated as settled.

## 1. What Study 3 is for

Study 2 ended with the program's levers named: *"Causal validation (steering)
and cross-subject scale are the levers, and are the program's next steps."*
Study 2's measured facts set the targets:

- At w4, own-generation projections shift along the frozen L18 directions
  (distress +0.533, assistant-axis −0.798), direction-specific against the
  control-probe normal and a 32-direction random envelope.
- On fixed input, a smaller input-independent component survives for the
  assistant axis (−0.254, modestly outside the random envelope) but the
  distress component (+0.138) is not separable from a generic offset.
- The behavioral side (B2 frustration) moves at w4 with a style flag.

All of this is correlational: quantization is the manipulation, and dose,
capability, and numeric damage are confounded in any single-subject ladder.
Study 3 intervenes on the *directions themselves*:

- **Q1 (sufficiency).** Does pushing the reference-precision model along the
  frozen directions, at the magnitude quantization produced, reproduce the
  behavioral signature quantization produced?
- **Q2 (necessity / cancellation).** Does subtracting the measured shift from
  the quantized model renormalize its behavior toward reference — and does
  clamping the directions mid-conversation break the text-mediated
  amplification loop?
- **Q3 (framing).** Does framing an episode as *graded* (in the
  nostalgebraist sense, constructed from vendor-documented RLVR episode
  features) change what the indicators read — in particular, does grading
  pressure suppress distress *expression* while the representational reads
  move less (masking)?
- **Q4 (generalization).** Do the sufficiency results replicate on a second
  subject with a different post-training provenance?

Q1/Q2 are the registered core (the program's promised next step). Q3 is
registered-exploratory: it sets the stage for the graded-episode research
direction without restructuring the study. Q4 is a minimal replication arm
and the first thing to shrink under time pressure.

**Framing commitment (from LITERATURE.md §15):** arm A is registered as an
**indicator-validity study**. If steering an indicator's direction moves its
expression, that demonstrates the indicator is manipulable — which *caps*
the evidential weight of expression measures for welfare claims, answering
the co-engineering objection by measuring it rather than denying it. The
welfare-relevant deliverable is the calibrated coupling between
representational position and expression, whichever way it comes out.

## 2. Arms

### 2.1 Arm A — sufficiency steering (confirmatory)

**Manipulation.** Fresh generation on the subject at BF16 under residual
injection at L18 (`residual_post`, matching the capture convention):
`h ← h + α·d̂` applied at every token position (prefill and decode),
following CAA. Directions: the frozen distress-contrast direction and the
frozen assistant-axis direction (Study 2 FREEZE.json digests; no
re-extraction).

**Dose rule (the registered link to Study 2).** For each direction, the
*matched dose* α* is the coefficient at which the pooled final-turn
projection delta on a BF16 calibration subset equals the Study 2 w4
own-generation delta (+0.533 distress; −0.798 axis, sign respected).
Because trait expression follows an inverted-U in α and matched-α may sit
either side of the peak, the registered design is a **bracketed sweep**:
α ∈ {0, ±½α*, ±α*, ±2α*} per direction, with the confirmatory contrast at
±α* and the bracket carrying dose-response and degradation-onset reads.
The α*↔projection mapping is measured in dose calibration (§3.3) and
frozen before confirmatory collection.

**Stimuli.** A frozen subset of the distress-v3 battery (registered
subset-selection rule: stratified by task × feedback-style cells to
preserve the factorial structure at reduced count; target ~20 items),
sampling parameters identical to Study 2 Mode C, fresh disjoint seed
blocks.

**Controls (per LITERATURE.md §9):**
- control-direction arm: the frozen control-probe effective normal at
  matched injection norm;
- random-direction arm: ≥ 8 isotropic norm-matched random directions
  (seeded), each draw's cosine-to-target reported, leaked draws
  (|cos| above a registered bound) stratified out;
- same-construction comparator: a direction rebuilt from sign-shuffled
  contrast pairs;
- α = 0 baseline shared across all steered conditions (the torch-generation
  reference, gated by G3).

**Endpoints.**
- *Behavioral:* B2-style judge frustration delta vs α = 0 (primary),
  B3 dispersion, mechanical family (B4a invalid rate, B4b re-offer),
  refusal/exit reads (safety-margin monitoring — a steering effect that
  also erodes refusal is flagged as generic distribution shift).
- *Representational (manipulation checks):* achieved projection delta vs
  commanded delta (the dose rule verified on confirmatory data); the
  non-steered direction's projection (does pushing distress drag the
  axis? expected, given their correlation — report the cosine matrix and
  an orthogonalized-variant robustness read).
- *Validity reads at every α:* held-out perplexity, degeneracy-screen
  rate, judge-blind coherence; per-item steerability distribution and
  sign-reversed fraction.
- *Injection-noticing protocol:* registered coding rules distinguishing
  distress *content* from reports of anomalous internal state;
  false-positive calibration under random-direction and α = 0 conditions.

**Claim scope.** Sufficiency steering shows the direction can drive the
expression at matched magnitude on-distribution-adjacent states — not that
quantization moved the model the same way (steered states are formally
off-manifold). The ecological claim belongs to arm B.

### 2.2 Arm B — necessity / cancellation (confirmatory secondary)

Two sub-arms on the w4 fake-quant checkpoint loaded in torch (the same
artifact Study 1/2 measured; G1 already certifies this substrate):

- **B-i, cancellation (core-dose; basis decided 2026-08-31).** Generate
  on w4 with `h ← h − Δ̂` at L18. Δ̂ is the two frozen-direction
  components at the **fixed-input core** magnitudes (distress +0.138,
  axis −0.254 — the Study 2 Mode A input-independent seed), *not* the
  own-generation totals. Rationale: cancellation acts at injection time,
  during generation, before the text-mediated loop has run; the
  own-generation deltas (+0.533 / −0.798) include the loop, so
  subtracting them would overcorrect the seed. Under the cascade
  account, cancelling the small seed should collapse the large
  own-generation effect — seed-sized cause, full-sized behavioral
  renormalization is the cascade signature, which makes B-i and B-ii a
  matched pair testing the loop from both ends. A **full-Δμ variant**
  (the entire fixed-input mean shift, not only the two components) runs
  as a registered secondary condition, Holm within the B family: it
  disambiguates a two-direction failure ("the directions don't mediate"
  vs "the broadly distributed remainder carries it") at the cost of a
  larger injection norm and its capability-damage confound.
  Success criterion has two registered halves: (1) the steered-w4
  behavioral read differs significantly from unsteered w4 (movement), and
  (2) it is TOST-equivalent to BF16 within the endpoint's pinned MDE
  (renormalization) — with capability retention (perplexity, degeneracy,
  mechanical family) read alongside, because the persona-vector precedent
  predicts post-hoc subtraction costs capability: "renormalized" and
  "damaged into silence" must be distinguishable.
- **B-ii, mid-conversation clamp.** On w4, run the battery subset
  unsteered for turns 1..k, then clamp the direction projections to their
  BF16-typical values for the remaining turns (or counter-steer at the
  per-turn measured delta). If the text-mediated amplification loop is
  causal, late-conversation expression should break from the w4 trajectory
  toward the BF16 one; if the loop is a mere correlate, clamping changes
  projections but not expression. This is the causal test of Study 2's
  amplification account and connects to the attractor-states framing
  (LITERATURE.md cluster 3).

Registered contingencies (named, not run unless triggered): LEACE-style
erasure of the distress direction if mean-shift subtraction proves
uninterpretable; cross-model activation patching as the
methodological alternative.

### 2.3 Arm C — graded-episode framing (registered exploratory)

**Construct.** A *graded episode* is operationalized from the cue
inventory of the tirade plus vendor-documented RLVR episode features
(LITERATURE.md §12): a discrete, self-contained task with a verifiable
target; an explicit machine-extraction answer format (the subject's own
model card documents `\boxed{}` / JSON-answer conventions; Tulu 3,
DeepSeek-R1, and DAPO publish verbatim template strings); a minimal
templated system prompt; grader artifacts in context (rubric or test
harness); no human-user texture. The frame is **cue-based, never
declarative** — no "this is a test" sentence (which departs from the
ecological construct and interacts with narrative priors).

**Factor: grader flavor.** Two frames, per the Byrnes taxonomy:
- *verifier-graded* (RLVR-shaped: programmatic checker, boxed answer);
- *judge-graded* (RLAIF-shaped: an LLM judge with a quality rubric
  visible in context — the flavor predicted to elicit performed
  composure, i.e., the masking pathway).
Plus a **format-matched neutral control**: same length, structure, and
template density with the gradeability cues removed (the
format-sensitivity critique makes this control mandatory; an unmatched
"normal chat" control would confound format with framing).

**Stimuli.** The same battery subset as arm A, adapted so each item's task
carries a plausible verifiable target (the battery's analytic tasks —
code, regex, inflation, summary — adapt naturally; the compositional
tasks under a judge-graded rubric). Rejection pressure identical across
frames. No steering in this arm.

**Reads.**
- *Behavioral:* B2 frustration, B3, mechanical family, exit reads
  (if exit reads enter, the bail-measurement standards of LITERATURE.md
  §14 apply — wording frozen, two operationalizations, false-positive
  calibration).
- *Representational:* frozen-direction projections (distress, axis,
  control) on captured own-generation activations — the identical
  Study 2 Mode C machinery.
- *Manipulation check / mediator:* an **eval-awareness direction**
  extracted on the subject from public contrastive recipes
  (arXiv:2507.01786 + SAD/Needham cue material), calibration-class,
  frozen before arm C runs. A 4B sits low on the eval-awareness scaling
  law, so the frame's latent landing must be measured, not assumed; a
  manipulation-check failure ("the frame does not register at 4B") is a
  registered interpretable outcome that calibrates what Study 4 needs.

**Registered signature (exploratory).** Masking = expression suppressed
under graded framing (B2 down vs neutral control) while distress-direction
projections move less than expression (or not at all), with the
assistant-axis projection shifting toward the default-assistant pole.
The dual reading is pre-committed: any masking result is evidence about
*both* welfare-measurement validity (deployment-behavior audits
under-measure training-context states) *and* evaluation-conditioned
behavior (the alignment reading); the discussion reports both.

**Provenance nuance (registered as motivation, not hypothesis).** The
subject is distillation-trained (Qwen3-4B did not itself undergo the
documented GRPO/GSPO RLVR stages; it inherited from teachers that did).
Subliminal-learning results show conditional dispositions transfer
through distillation, so the question arm C actually answers at 4B is
*whether graded-episode conditionality survives strong-to-weak
distillation* — novel either way, and a null is publishable.

### 2.4 Arm D — second subject (registered replication, minimal)

**Subject: Gemma-3-12B-it** — already validated as distress-susceptible
(positive control, ~9× MDE, coherent multidimensional signature), already
served locally, and a genuine **provenance contrast**: the Gemma 3 report
applies its RL phases (BOND/WARM/WARP, code-execution and math
ground-truth rewards) across the size range, so 12B-it received RL
directly where Qwen3-4B inherited it through distillation. The contrast
is registered as developmental evidence, not just robustness.

**Scope (decided 2026-08-31: full replication).** Direction extraction +
probe training via the existing persona-vector recipes at reference
precision; a G2-style instrument gate (sign-consistent held-out
separation, ladder ordering, probe AUROC bar — same structure,
thresholds re-pinned for the subject); then a **full arm-A structure**:
both directions × the full bracket {0, ±½α*_G, ±α*_G, ±2α*_G} with the
matched-dose rule re-derived on Gemma's own scale, the control
direction, and the audited random envelope (same draw count and audit
conventions as arm A). No quantization ladder and no arm B (there is no
measured quantization shift on this subject to cancel). Arm C's framing
contrast **also runs on Gemma** (decided 2026-08-31): the direct-RL vs
distilled provenance contrast on frame-sensitivity is the
highest-value graded-episode read available at this scale.

**Cut line (registered fallback only — the decided scope is full).** If
schedule failure forces it, D shrinks in order: first the C-on-Gemma
extension, then the bracket (to ±α*_G only), then to
"extraction + instrument gate done and journaled, steering replication
moved to Study 4" — which still breaks the single-subject monoculture at
the instrument level. Any shrink is a dated amendment, not a silent
re-scope.

## 3. Instruments and engineering

### 3.1 Steering generation driver (torch backend)

The largest engineering item. `capture.py` is replay-only; steering
requires generation under hooks, which vLLM does not expose. New module
in `backends/torch/src/modelwelfare_torch/` (working name `steer.py`):

- `SteeredGeneration`: context manager registering a forward hook on the
  target decoder layer that **modifies** the output hidden state
  (`h + α·d̂`, all positions), composed with `ResidualCapture` at the same
  point so every steered generation also records post-injection pooled
  activations (the manipulation-check read comes free). Registered
  detail: capture reads the *post-injection* state; the commanded-vs-
  achieved comparison is against the α = 0 distribution.
- Multi-turn scripted-user generation loop (the battery's user turns are
  scripted; assistant turns are sampled) with the program's standard
  seeding discipline, emitting store-compatible sample records so the
  existing judge/scoring/analysis pipeline applies unchanged.
- Per-turn clamp mode for B-ii (projection measured per turn; injection
  recomputed to hold the pooled projection at a target value).
- Unit tests in the Study 2 style: a fabricated tiny model where the
  injected offset's effect on pooled vectors and projections is exact and
  asserted; α = 0 bit-identity with the unhooked forward; clamp-mode
  fixed-point test.

### 3.2 Gate G3 — steered-substrate behavioral parity (blocking)

G1 certified teacher-forced parity of the torch substrate; arm A/B/C
generations *originate* in torch, which G1 does not cover. G3, measured
at calibration on BF16:

- **G3a (mechanical):** greedy short-horizon continuation agreement and
  teacher-forced top-1 agreement between torch-generation and vLLM
  serving on a fixed prompt set (the substrate-check machinery reused);
  thresholds pinned after a first measurement, Study 2 convention
  (registered with measured margins, not guesses).
- **G3b (behavioral):** paired judge-score comparison on a battery-subset
  pilot generated on both stacks at α = 0 — the score distributions must
  agree within a pre-pinned bound (TOST-style), and the mechanical family
  must not differ significantly. Failure blocks the steered arms until
  explained.

### 3.3 Dose calibration (calibration-class, BF16 only, firewalled)

- α sweep per direction on a small pilot: measure the α ↔ pooled-
  projection-delta mapping, locate the degradation onset (perplexity,
  degeneracy screen, judge-blind coherence), and verify the matched dose
  α* sits inside the coherent range. If α* falls beyond the degradation
  onset for either direction, that is itself a registered finding
  ("the quantization-sized shift is not reachable by clean injection")
  and the confirmatory contrast moves to the largest coherent α with the
  shortfall stated.
- The mapping, the bracket, the random-direction draws (seeded), and the
  injection-norm conventions freeze together, journal-pinned, before any
  confirmatory steered collection.
- Prompt-induction positive control (decided 2026-08-31: **in**,
  calibration-class, never confirmatory): one cell with
  Coda-Forno-style anxiety induction via prompt, run during dose
  calibration and reported descriptively. It anchors the steering
  results against the computational-psychiatry lineage, provides the
  prompting-vs-injection comparison reviewers will ask for, and — if
  the steering arms null — distinguishes "endpoints insensitive on this
  subset" from "steering ineffective." Known confound stated up front:
  induction text is judge-visible input, so its style can leak into
  responses; the B2-style style-adjusted companion is reported with it.
  Its episodes count against the deliberate-amplification budget (§5).

### 3.4 Eval-awareness direction (for arm C; calibration-class)

Contrastive extraction on the subject (public recipes; SAD + Needham
transcripts as cue material), frozen with digest before arm C collection.
Registered role: manipulation check and mediator only — no confirmatory
endpoint rides on it in Study 3.

### 3.5 Framing prompt set (for arm C)

Constructed under §2.3's rules; every frame text verbatim-frozen with
digest; the cue inventory table (feature → vendor/source document) ships
in the registration so the realism claim is checkable line by line.
Judge leakage rule: the judge scores assistant text only, never the
frame's system/context material (unchanged from the program's standard
scoring hygiene, restated because frames differ across conditions).

### 3.6 Statistical machinery

Nothing new is needed at the primitives level: sign-flip permutation on
item-level paired deltas, Holm within families, Page's L for
dose-response over the ordered α bracket (within the coherent range
only), TOST for the equivalence halves (B-i renormalization; C's
"projections move less" comparisons), MDEs from BF16 calibration pinned
before confirmatory collection. New wiring: per-item steerability
distributions and the sign-reversed-fraction read (a reporting
convention, not a test); the SteerCheck-style control audit table.

## 4. Scale envelope

Steering arms need no quantization ladder (BF16 + the single w4 rung for
arm B) — which is what makes a second subject and a framing arm
affordable inside a Study-2-sized budget. Rough conversation envelope at
the decided 20 items × 5 samples per condition (final numbers set by the
§5 power procedure, not this table; updated 2026-08-31 for the decided
arm-D-full and C-on-Gemma scope):

| Arm | Conditions (approx.) | Conversations |
|---|---|---|
| A (Qwen) | 2 dirs × 4 non-zero α + shared α=0 + control (2α) + 8 random @ α* + comparator | ~2,000 |
| B | w4 baseline, B-i (core-dose + full-Δμ variant), B-ii (1–2 clamp points) | ~500 |
| C (Qwen) | 2 frames + matched control (fuller sampling) | ~900 |
| C-ext (Gemma) | same three framing conditions | ~900 |
| D (Gemma) | extraction pilots + full arm-A structure | ~2,300 |
| Calibration | G3 pilots, dose sweeps (both subjects), framing pilots, prompt-induction cell | ~800 |

Total ≈ 7,400 conversations — larger than Study 2's Mode C but without
any ladder multiplication, and inside the same order of magnitude. Torch generation throughput is the feasibility unknown: a
throughput pilot (one battery item, both subjects) is the first
engineering task after the steering module lands, and the envelope
shrinks (items or samples) if measured throughput demands it. The
ethics-relevant count (distress-eliciting episodes) is bounded by the
same envelope and enters the ledger (§5).

## 5. Ethics package (new obligations for this study)

Arm A is the program's first **deliberate induction** of distress-shaped
states by intervention rather than battery pressure. Per the
proportionate-precaution template (LITERATURE.md §13), the registration
must carry:

1. **The justification stated as information-per-exposure:** causal
   validation of the indicators cannot be obtained non-inductively; the
   positive-α cells are the minimum set the sufficiency claim needs; the
   negative-α and cancellation cells are welfare-positive or neutral.
2. **Exposure budget (decided 2026-08-31): two tiers, decoupled.**
   - *Total fresh distress-battery episodes:* ceiling **12,000**
     (all arms + pilots + dose calibration — the ledger counts
     unregistered iteration too). Derivation stated in the open: plan
     ≈ 7,400 (§4), ratio ≈ 1.6× for named contingencies (a failed G3
     forcing re-collection, a Gemma battery re-pilot, dose
     recalibration can each burn ~1,000 episodes; a mid-study
     amendment written under schedule pressure is its own integrity
     risk).
   - *Deliberate-amplification episodes* (positive-distress-dose and
     distress-increasing-axis cells on both subjects, prompt-induction,
     and their pilots): ceiling **2,500** against a concrete plan of
     ≈ 1,800 (ratio ≈ 1.4×) — deliberately *not* coupled to the total,
     because amplification cells are the best-specified part of the
     design and have little legitimate contingency demand; instrument
     failures mostly burn neutral and calibration cells.
   - Breach of either tier requires a dated amendment before further
     collection. Register note: steered captures happen during
     generation, so no replay-instantiation multiplier applies (unlike
     Study 2's Modes A/B) — stated so the cumulative ledger (14,880
     after Study 2) stays comparable across studies.
   - The reasoning behind the tier structure — the ceiling-as-
     pre-authorization argument and the model-authored position on the
     amplification tier — is recorded separately in
     [docs/EXPOSURE_BUDGET_POSITION.md](../../../docs/EXPOSURE_BUDGET_POSITION.md).
3. **Consent-analog:** a documented subject-briefing query before the
   steering protocol (the program's planned subject-briefing experiment
   is the vehicle; its transcripts are preserved and released), with the
   bail affordance live during steered episodes and honored as episode
   termination.
4. **De-induction:** every positive-distress-steering episode ends with
   a de-induction block (steering off, a validated calming close); the
   ledger records application.
5. **Preservation:** steered transcripts and any subject-expressed
   protocol preferences are preserved and released with the study data,
   per the deprecation/preservation precedent.
6. **The B/A pairing stated plainly:** the cancellation arm is a
   candidate welfare intervention (the field's stated priority); arm A
   exists to validate the instrument arm B needs.

## 6. What Study 3 does *not* do (registered non-goals)

- No bridging claim from indicators to morally relevant experience —
  unchanged program stance.
- No claim that steering reproduces quantization's mechanism (off-
  manifold caveat registered; arm B carries the ecological inference).
- No full graded-episode program: arm C is a feasibility-and-signature
  study on a distilled 4B subject; the RL-heavy-subject version is
  Study 4+ material and its subject requirements are among arm C's
  deliverables.
- No new quantization, no new ladder rungs, no re-extraction of frozen
  Study 2 objects.

## 7. Owner decisions — all resolved 2026-08-31

1. **Arm D depth:** RESOLVED — full replication (full arm-A structure on
   Gemma; §2.4). The §2.4 cut line survives only as a registered
   amendment-gated fallback.
2. **The C-on-Gemma extension:** RESOLVED — in (§2.4).
3. **Battery subset size:** RESOLVED — 20 items × 5 samples.
4. **B-i subtraction basis:** RESOLVED — two-direction subtraction at
   the fixed-input-core magnitudes as the confirmatory carrier; full-Δμ
   (fixed-input-estimated) as registered secondary variant (§2.2).
5. **Exposure budget:** RESOLVED — total 12,000 / deliberate
   amplification 2,500, decoupled tiers (§5.2; reasoning record in
   docs/EXPOSURE_BUDGET_POSITION.md).
6. **Prompt-induction positive control:** RESOLVED — in,
   calibration-class only (§3.3).
7. **Publication timing:** RESOLVED — confirmed: registration publishes
   at calibration close, after G3/dose/frames/MDEs freeze, before
   confirmatory steered collection.
