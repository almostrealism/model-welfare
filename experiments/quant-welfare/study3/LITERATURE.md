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
