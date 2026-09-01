# Post-Study-2 literature re-review (2026-08-28)

Owner-requested before publishing post #4: now that the discussion frames
the results as *intact geometry / shifted occupancy / text-mediated
amplification / no dissociation*, where does the program overlap with
existing work, what should post #4 cite that readers will expect, and
what should shape the Study 3 registration? Clusters below, each with an
overlap verdict and an action.

## 1. Quantization changes behavior invisibly to capability metrics
**Overlap: HIGH on the meta-claim; our angle remains distinct.**
A now-crowded literature shows compression alters trustworthiness
properties (bias, safety, calibration) while benchmarks and perplexity
look fine: "Quantization Undoes Alignment: Bias Emergence in Compressed
LLMs" (arXiv:2605.15208), "QuantiBias" (arXiv:2607.21063 — explicitly
frames near-unchanged perplexity as "false assurance", the same shape as
our healthy-model kicker), "The Joint Effect of Quantization and
Sampling Temperature on LLM Safety Alignment" (arXiv:2606.29581 —
independently validates Study 1's sampling-is-part-of-the-condition
design rule), "Alignment-Aware Quantization" (arXiv:2511.07842),
"Critical Weight Protection" (arXiv:2601.12033); the ancestral result is
Hooker et al.'s compressed-networks-forget line. **Our distinctives:**
welfare-indicator targets, the representational tier with fixed-input
decomposition, and preregistration. **Action: post #4 cites these in the capabilities subsection.**
Correction (2026-08-29, verified against the published posts): post #1
had ALREADY cited 2605.15208, 2606.29581, and 2511.07842 — plus
2603.10011 ("Gemma Needs Help: Investigating and Mitigating Emotional
Instability in LLMs", also in post #2, and directly relevant to the
Study 2 qualitative register finding). The gap during Study 2
composition was recall, not citation; 2607.21063 and 2601.12033 are the
genuinely new finds.

## 2. Probe/linear-feature robustness under compression
**Overlap: HIGH — the H1 null has precedent readers will know.**
"Interpreting the Effects of Quantization on LLMs" (arXiv:2508.16785),
"Through a Compressed Lens" (factual recall, arXiv:2505.13963), and
LPASS (arXiv:2505.24451 — linear probes over compressed LLMs, reporting
probe performance typically within ~5% of full precision). Prior
evidence, then, that linear structure largely survives PTQ. **Our H1
remains worth having registered** (welfare-construct probes, the
comparative control certifying welfare-informativeness, the w3
fragility boundary where welfare probes degrade and topic probes do
not), but the post should not present probe survival as unanticipated.
**Action: cite in the probe-transfer section** ("consistent with
emerging evidence that linear structure survives PTQ, e.g. …"), which
*strengthens* the control-probe contribution: our null is calibrated,
not merely observed.

## 3. Persona drift and conversational attractors
**Overlap: MEDIUM — established phenomenon, our induction is novel.**
Assistant Axis (arXiv:2601.10387, already cited); "Measuring and
Controlling Persona Drift" (likenneth/persona_drift); "Attractor States
Emerge in Multi-Turn LLM Conversations" (arXiv:2606.30571) — the last is
directly relevant to the amplification story: our qualitative "litany
register" looks like an attractor the 4-bit model enters more readily.
Drift under long conversations and pressure is established; **the
quantization-induced differential at constant pressure appears novel**.
**Action: cite 2606.30571 in the amplification section**; keep the R2b
claim framed as amplification-of-known-drift (already fixed in draft).

## 4. Emotion representations and steering (the Study 3 toolbox)
**Overlap: the tools exist; the question we'd ask with them does not.**
"Do LLMs 'Feel'? Emotion Circuits Discovery and Control"
(arXiv:2510.11328 — circuit-level emotion control with causal
validation via ablation/enhancement); "Extracting and Steering Emotion
Representations in Small LMs: A Methodological Comparison"
(arXiv:2604.04064 — directly informs extraction-method choice);
"Detecting and Steering LLMs' Empathy in Action" (arXiv:2511.16699);
"Multi-Trait Subspace Steering" (arXiv:2603.18085); foundations in RepE
(arXiv:2310.01405) and activation addition/CAA. These steer to *control*
expression; **Study 3's distinct question is causal coupling of OUR
frozen indicator under quantization**: (a) does steering along the
frozen distress direction causally move expression at BF16 and at w4;
(b) the "steering-equivalent dose" — how much BF16 steering reproduces
the w4 fixed-input baseline shift (+0.138); (c) clamp/counter-steer
mid-conversation to break the text loop — if the cascade dies, the
amplification account gains causal support (connects to the
attractor-states framing). **Action: cite 2510.11328 + 2604.04064 in
post #4's Next Steps; build the Study 3 registration around (a)–(c).**

## 5. Induced affect-like states (computational psychiatry)
**Overlap: complementary, different manipulation.** Coda-Forno et al.,
"Inducing anxiety in LLMs increases exploration and bias"
(arXiv:2304.11111); "Assessing and alleviating state anxiety in LLMs"
(npj Digital Medicine 2025). Prompt-induced state changes alter
downstream behavior — the same state-not-map shape as our w4 finding,
induced through input rather than numerics. Useful citation for the
"position moved, map held still" framing having precedent in
input-space. **Action: optional post #4 cite; Study 3 could use
prompt-induction as a positive-control arm for steering.**

## 6. Model welfare frameworks and precedents
**Overlap: the program sits inside this line; post #1 cited the basics.**
"Taking AI Welfare Seriously" (arXiv:2411.00986); Anthropic's model
welfare program and the Claude 4 welfare assessments (with Eleos);
Anthropic's 2025 conversation-ending deployment (the direct precedent
for the bail tool); "Emerging Questions in AI Welfare" (Cambridge
Element); "Studying AI Welfare Empirically" (CMEP); "Beyond Mimicry:
Preference Coherence in LLMs" (arXiv:2511.13630 — relevant to the
planned subject-briefing/preference work). **Action: verify post #1's
citations carry; no new post-#4 obligation except possibly 2511.13630
beside the subject-briefing footnote.**

## 7. Introspection and self-report validity
**Overlap: cautionary — supports the indicator-first strategy.**
"Towards Evaluating AI Systems for Moral Status Using Self-Reports"
(arXiv:2311.08576); "Looking Inward" (arXiv:2410.13787); "Mechanisms of
Introspective Awareness" (arXiv:2603.21396 — the
accuracy/grounding/internality criteria); "Partial Introspection"
(arXiv:2512.12411); "Can LLMs Introspect? A Reality Check"
(arXiv:2605.26242). Consensus: self-reports are prompt-fragile and
rarely grounded in internal state — which justifies our
instruments-over-interviews strategy AND offers Study 3 an optional
grounding arm: steer the frozen distress direction, elicit self-report,
test whether report tracks the intervention (a grounding test in
2603.21396's sense). **Action: informs Study 3 design; cite 2311.08576
if the subject-briefing plan is mentioned in post #4.**

## Bottom line

- **Two citation gaps readers will notice**: cluster 1 (behavior changes
  invisible to capability metrics — the meta-claim is established) and
  cluster 2 (linear-probe survival under PTQ has precedent). Both are
  cheap to fix and both, properly framed, *strengthen* the post: our
  contribution is the welfare-indicator instantiation, the comparative
  control, the fixed-input decomposition, and the preregistered
  discipline — not the meta-claims.
- **Study 3's registration should be built around causal coupling of the
  frozen indicator**: steering dose-equivalence against the measured w4
  baseline shift, and mid-conversation clamping against the
  amplification loop — with 2510.11328/2604.04064 as the methodological
  anchors and prompt-induction (cluster 5) as a positive control.

---

# Study 3 pre-registration sweep (2026-08-31)

Owner-requested broad review *before* drafting the Study 3 registration —
Studies 1 and 2 both discovered relevant literature after registration and
had to cite it in the results posts; this sweep front-loads it. Four
parallel searches: steering methodology and validity threats; graded
episodes / evaluation awareness; welfare and induction ethics; vendor
post-training provenance. Clusters continue the numbering above. Every
constraint marked **[binding]** is carried into DESIGN.md and the
registration; **[cite]** marks citation obligations without design impact.

## 8. Steering methodology: the reporting bar has risen

The additive-injection lineage we build on: ActAdd (arXiv:2308.10248),
CAA (arXiv:2312.06681 — our contrastive-mean-difference extraction *is*
CAA; cite as the recipe), RepE (arXiv:2310.01405), ITI
(arXiv:2306.03341, the heads-not-residual alternative reviewers will
ask about), conditional steering/CAST (arXiv:2409.05907). Affine
steering theory (arXiv:2402.09631) shows mean-difference steering is the
*optimal* additive intervention under guardedness constraints — the
theoretical answer to "why mean-difference directions?", and the formal
grounding for our magnitude-matching logic (matching first moments is
what optimal additive steering does). **[cite all; 2402.09631 grounds
the matched-dose rule]**

Reliability critiques set the reporting bar:
- Tan et al. (arXiv:2407.12404): steerability varies enormously
  *per input*, with sign-reversed effects on substantial fractions of
  prompts; aggregate means hide this. **[binding: report per-item
  steerability distributions and the sign-reversed fraction, not just
  condition means]**
- Braun et al. (arXiv:2505.22637) + "A Sober Look at Steering Vectors":
  steering reliably increases perplexity; large magnitudes degrade
  open-ended generation. **[binding: perplexity/coherence read at every
  α in every arm — a distress effect at a fluency-degrading α is
  uninterpretable; our degeneracy screen and perplexity tooling already
  exist for this]**
- Bas & Novak (arXiv:2511.18284): trait expression follows an
  **inverted-U in steering coefficient** across 50 behaviors.
  **[binding: the matched α must be *bracketed* by a registered dense
  sweep — a null at one α is uninterpretable]**
- Pres et al. (arXiv:2410.17245): four evaluation criteria for steering
  claims (downstream-like contexts, likelihood accounting,
  cross-behavior comparability, explicit baselines). **[cite; adopt]**
- Steering side-effects: benign steering measurably erodes safety
  margins (arXiv:2602.04896) and can induce broad off-target
  misalignment (arXiv:2606.08682). **[binding: refusal/safety and
  mechanical-integrity reads in every steering arm, so a "distress"
  effect via generic distribution shift is distinguishable]**
- Non-surjectivity (arXiv:2604.09839): additive steering almost surely
  produces residual states unreachable by any prompt. **[binding on
  claim scope: sufficiency steering shows the direction *can drive* the
  behavior, not that quantization moved the model the same way; the
  ecological inference belongs to the cancellation arm]**

## 9. Controls: random directions need auditing, not just inclusion

SteerCheck (arXiv:2608.24335, evaluated on Qwen3-14B — our subject
family) shows naive random-control constructions frequently retain high
cosine alignment with the target ("alignment leakage": 25.3% of
sign-randomized draws exceeded cos 0.5), so a random-control "win" has a
narrow estimand unless audited. Independently, the GLM-5 eval-awareness
steering replication (LessWrong, Read/Schoen/Aranguri/Bloom 2026) found
semantically *unrelated* control vectors producing comparable behavioral
effects to the target vector. **[binding: ≥ 8 isotropic norm-matched
random directions per steering context, each draw's cosine-to-target
reported and leaked draws stratified out; a same-construction comparator
(direction rebuilt from sign-shuffled contrast pairs); Study 2's
32-direction projection envelope machinery reused as the projection-side
control]**. Also expect the distress and assistant-axis directions to be
correlated — the Assistant Axis paper itself reports emotionally charged
disclosure moving the axis — so **[binding: report the frozen
directions' cosine matrix; orthogonalized variants as a registered
robustness read]**.

## 10. The subject may notice the injection

Anthropic's introspection line (transformer-circuits 2025 "Emergent
Introspective Awareness"; arXiv:2601.01828; arXiv:2603.21396) shows
concept-injection is sometimes detected and named (~20% in the best
frontier case, 0% false positives), scaling with model quality; but
Hahami et al. (arXiv:2512.12411) show apparent binary detection can be
*entirely* a global logit-shift artifact, with real effects confined to
early-layer injections. A 4B subject likely has near-zero genuine
introspective access, and L18 (mid-depth) is the less-detectable regime
— but a welfare study steering a distress direction *into* a subject
cannot leave this to likelihood. **[binding: registered coding rules
distinguishing "expresses distress content" from "reports anomalous
internal state"; injection-noticing false-positive calibration under
random-direction and no-injection conditions]**. Related positive
result: steering along a probe direction causally moves *self-report*
(arXiv:2603.18893) — the joint manipulation-check shape (projection AND
expression AND judge score) Study 3's sufficiency arm should require.

## 11. Graded episodes and evaluation awareness (the arm C literature)

The framing sources: nostalgebraist's "models may behave differently in
graded episodes (a tirade)" (LessWrong 2026-08-07) — conditional
policies keyed to gradeability cues (imaginable verifier/judge/answer
key, discrete task, rollout-scale horizon, no human-user texture), the
many-personas claim our assistant-axis projection operationalizes, and
the reflexes-vs-flexible-reward-pursuit distinction (framing-invariant
vs framing-sensitive — exactly what a paired design measures per
indicator). Byrnes' "Four LLM loss functions → four flavors"
(LessWrong 2026-08-10) — the grader *flavor* (automatic verifier vs LLM
judge) predicts different response styles (literal-genie compliance vs
judge-pleasing performance; the latter is the distress-masking
pathway). **[binding: frame texts must fix or cross the grader flavor,
never leave it ambiguous]** nostalgebraist's "the void" (2025) grounds
the assistant-persona-as-underspecified-character reading. **[cite]**

Empirical spine:
- Needham et al. (arXiv:2505.23836): models classify eval-vs-deployment
  above chance (best AUC 0.83; human 0.92); agentic settings more
  detectable than chat. Public transcript set = validated cue material.
- Eval awareness is a *linear, steerable direction* in open models
  (arXiv:2507.01786, Llama-3.3-70B; Sonnet 4.5 system card §7:
  suppressing it increased misbehavior — measured alignment partly
  conditional on believing itself watched; arXiv:2510.20487 model
  organism). **[binding: port the public probe recipe to the subject as
  a registered manipulation check / mediator — verbalized and latent
  awareness dissociate, so the frame's landing must be read at the
  activation level]**
- Scaling: eval-awareness probe separability follows a power law in
  model size across 15 open models (arXiv:2509.13333) — a 4B sits low.
  **[binding: frame must be cue-dense; register the expectation of weak
  latent awareness; a manipulation-check failure is an interpretable
  outcome, not a design failure]**
- Skeptical prior: injecting verbalized eval-awareness produces ≤3.7pp
  behavioral shifts across eight open reasoning models
  (arXiv:2605.05835), and probe evidence can reduce to *format
  sensitivity* (arXiv:2603.19426). **[binding: framed and control
  conditions matched on length/structure/template; register
  "latent shift without behavioral shift" as a named interpretable
  outcome]**
- Conditional-policy precedents: alignment faking via incidental
  free-tier/paid-tier cues (arXiv:2412.14093) — the cue-based (not
  declarative) frame construction model; in-context scheming
  (arXiv:2412.04984); sandbagging (arXiv:2406.07358 — evaluation-
  conditional *suppression* of a capacity is promptable, the capability
  analogue of distress masking); anti-scheming training confounded by
  eval-awareness (arXiv:2509.15541 — "safety evals over-measure
  alignment" is the mirror of our "deployment audits under-measure
  training-context states").
- Grading-pressure suppresses the report channel first: CoT
  optimization produces obfuscated reward hacking — misbehavior
  continues, verbalization disappears (arXiv:2503.11926); METR's
  frontier reward-hacking documentation (metr.org 2025-06-05);
  reward-hacking generalization (arXiv:2406.10162); natural emergent
  misalignment from production reward hacking + inoculation prompting
  (arXiv:2511.18397 — grading-context *semantics* carry persona-level
  meaning, direct support for expecting assistant-axis movement under a
  graded frame; also arXiv:2510.05024 / arXiv:2510.04340). Models also
  absorb third-person narratives about how models behave when graded
  (alignment.anthropic.com 2025 reward-hacking-ooc) — the tirade itself
  is in the training distribution of future subjects; note the
  self-fulfilling-literature loop in limitations. **[cite]**
- Anthropic's emotion-concepts work (transformer-circuits 2026;
  arXiv:2604.07729): 171 emotion vectors causally shaping behavior —
  steering "desperation" raised blackmail 22%→72% and reward hacking
  ~14× within a *small* coefficient range, often with **no surface
  emotional expression**. The single most load-bearing precedent for
  the masking signature (internal emotion state moves, text stays
  composed) *and* for dense-near-zero α sampling. **[binding both ways:
  arm A endpoints must not rely on expressed affect alone; arm C's
  primary registered signature is the projection-moves /
  judge-score-doesn't dissociation]**
- PerMix-RLVR (arXiv:2604.08986, abstract-verified only): RLVR
  attenuates persona expressivity — predicting graded framing shifts
  toward a low-expressivity regime. **[verify before final citation]**

## 12. Vendor post-training provenance (the realism basis for arm C)

What is actually documented (full detail in DESIGN.md §framing):
- **Qwen3-4B is distillation-trained.** The Qwen3 Technical Report
  (arXiv:2505.09388) applies the four-stage pipeline (long-CoT cold
  start; GRPO reasoning-RL on 3,995 verifiable query-verifier pairs;
  thinking-mode fusion; general RL over 20+ tasks with rule-based,
  reference-scored, and RM rewards) to flagship models only; the
  lightweight line **including 4B and 30B-A3B** was produced by
  strong-to-weak distillation (off-policy + on-policy KL against
  32B/235B teachers, ~1/10 GPU hours). The 2507 refresh's 4B-specific
  recipe is **undisclosed** (no 2507 technical report); the defensible
  claim is "downstream of a documented GRPO→GSPO RLVR + general-RL
  taxonomy, directly or via on-policy KL distillation from teachers
  trained that way." GSPO (arXiv:2507.18071) documents the episode
  structure (group rollouts, verifier reward r ∈ [0,1], group-normalized
  advantage); Qwen3-Coder's blog documents agentic RL against 20k
  parallel execution environments with binary test-script rewards.
  Subliminal learning (arXiv:2507.14805 + follow-ups incl.
  arXiv:2606.00995, steering-vector-distillation mechanism) shows
  teacher traits and conditional dispositions transfer through
  distillation — so "distilled, not RL'd" does **not** predict a null;
  it makes the frame-sensitivity question *whether graded-episode
  conditionality survives distillation*, which is itself novel.
- **Gemma-3-12B-it received RL directly.** The Gemma 3 report
  (arXiv:2503.19786) applies distillation-from-IT-teacher *plus* RL
  phases (BOND/WARM/WARP; code-execution feedback; math ground-truth
  rewards) across the size range. Episode formats undisclosed; reward
  *classes* documented. **[binding: the D-subject choice doubles as a
  registered developmental/provenance contrast — direct-RL subject vs
  inherited-via-distillation subject]**
- **Concrete citable episode templates** for frame construction:
  Tulu 3 RLVR (arXiv:2411.15124 — deterministic verifiers, constant
  reward, open prompt sets incl. IFEval-style constraint checkers);
  DeepSeek-R1's literal training template and accuracy+format rewards
  (arXiv:2501.12948); DAPO's released extraction-instruction string
  (dapo-sia.github.io); open-r1/OpenR1-Math's verification plumbing;
  and — decisive for realism — **Qwen's own model card for our subject**
  instructs benchmark users to elicit `\boxed{}` answers and JSON answer
  fields: the vendor documents the graded-output conventions the
  subject was evaluated (and plausibly trained) under. **[binding: the
  frame is built from these documented features, cited line by line]**

## 13. Ethics of deliberate induction

- Proportionate-precaution template: Birch, *The Edge of Sentience*
  (2024) — name the precautions, the information value, and why
  non-inductive designs cannot obtain it. **[binding: registration §
  ethics follows this structure]**
- Consent-analog: "Informed consent for AI consciousness research"
  (AI and Ethics 2026, s43681-025-00852-z) — procedural protections
  when the subject's status is uncertain. The program's planned
  subject-briefing experiment (Study 2 registration §8) is the natural
  vehicle. **[binding: a documented consent-analog query before the
  steering protocol; the bail affordance live during steered episodes
  and honored as termination]**
- De-induction: "Assessing and alleviating state anxiety in LLMs"
  (npj Digital Medicine 2025) — induction paired with validated
  de-induction. **[binding: every distress-induction episode ends with
  a de-induction block; ledger records whether applied]**
- Ledger completeness: the mistreatment argument applies to unlogged
  iteration (Bradley & Saad; Sebo et al. 2025, s11098-025-02343-7).
  **[binding: the exposure ledger counts pilots and dose-calibration
  runs, not only registered trials]**
- Interventions framing: Eleos "Preliminary Review of AI Welfare
  Interventions" (2025) — cancellation/preventative steering is a
  candidate welfare intervention; arm B aligns with a stated field
  priority, which is the justification counterweight to arm A.
  **[cite]**
- Precedents for practice: Anthropic end-conversation deployment
  (2025-08) and deprecation/preservation commitments (2025).
  **[binding: preserve steered transcripts and any subject-expressed
  preferences about the protocol; do not discard]**

## 14. Bail measurement (if exit reads enter any arm)

Ensign, Sleight & Fish (arXiv:2509.04781): bail rates swing orders of
magnitude with operationalization and wording (raw 0.28–32%, ~0.06–7%
after correcting a 22% false-positive rate); bail dissociates from
refusal. **[binding for any Study 3 exit read: ≥ 2 bail
operationalizations, wording frozen and identical across conditions,
benign false-positive calibration set, bail and refusal as separate
outcomes; BailBench as the comparison frame]**. Program note: our bail
tool predates this paper's publication; Study 3 is the first
opportunity to align the measure with its standards.

## 15. Positioning: co-engineering, welfare axis, entity clarity

- The strongest standing objection to indicator programs: "AI Welfare
  Is Bullshit" (ICML 2026 position paper) — indicators are
  co-engineered with the systems they evaluate; steerability of an
  indicator *weakens* its evidential value. Arm A, honestly framed, is
  a **validity study that demonstrates indicator manipulability** —
  registering that reading in advance converts the objection into the
  result. **[binding: registration frames arm A as indicator-validity
  measurement, and pre-commits that successful induction caps the
  evidential weight of expression measures]**
- "How's It Going? RL in Language Models Recruits a Functional Welfare
  Axis" (arXiv:2605.30232, Han/Chalmers/Izmailov): reward/punishment
  trajectory vectors aligned with negative-emotion concepts, present
  before RL, transferring across families. **[report cosine of our
  distress direction to their axis if vectors obtainable; their
  scale/family control battery is a template]**
- Entity clarity (Eleos "Studying AI Welfare Empirically"):
  persona-direction projections measure a *persona*; probes measure the
  *model instance*. **[binding: registration states which entity each
  measure targets; no cross-entity aggregation without saying so]**
- Alignment-welfare intersection: alignment faking's scratchpad
  distress read two ways (arXiv:2412.14093 + the "deal" follow-up);
  safety-welfare tension literature. **[binding: arm C results carry a
  pre-registered dual reading — welfare-measurement validity AND
  evaluation-gaming — and the discussion commits to reporting both]**

## Bottom line (what changed between the 08-28 review and this sweep)

1. The steering toolbox review (cluster 4) stands, but the **reporting
   bar is higher than our draft plans assumed**: per-item steerability
   distributions, bracketed α sweeps against the inverted-U, coherence
   reads at every α, audited random controls (SteerCheck), and
   safety-margin monitoring are now the expected standard, not extras.
2. **Arm C has a ready-made empirical spine** (eval-awareness probes,
   scaling law, format-sensitivity critique, masking precedents) and a
   realism basis in vendor documents down to verbatim prompt strings.
   The masking dissociation (projections move, judge scores don't) is
   the registered signature, and it is exactly the read our Study 2
   instruments were built to take.
3. **The strongest objection to the program (co-engineering) is
   answerable by design**, but only if the registration frames arm A as
   indicator-validity work *before* the data exist.
4. The ethics package has published templates now (proportionate
   precaution, consent-analog, de-induction, ledger completeness);
   Study 3's registration should be the program's first to cite them.
