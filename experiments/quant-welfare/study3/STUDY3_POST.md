# Study 3: Steering welfare-relevant directions moved the representation, but not [detectably] the behavior

> Source draft for the LessWrong post of the same title, published on
> 14 September 2026: <https://www.lesswrong.com/posts/TpEL7pSwp7DvCekAq/study-3-steering-welfare-relevant-directions-moved-the>.
> The published text was edited by hand from this draft after an external
> review and differs from it in wording and in the order of some sections;
> the post is the record, this file is its source.

*Epistemic status: an exploratory report. These results are from the
calibration process intended to produce a preregistration for the third
study in [my series on welfare-relevant
indicators](https://www.lesswrong.com/posts/pxXTJtvtpJaNwdCTw/study-2-results-exploring-representational-counterparts-of).
The calibration process resulted in the experimental procedure not being
worth running, so I am publishing this instead. Nothing below is
confirmatory. Every number here is calibration-class: small cells (mostly
8 items, 1 to 10 samples each), run to decide whether a powered study was
feasible, not to establish a finding. All of it is published in the data
release tagged
[`data-20260911`](https://github.com/almostrealism/model-welfare/releases/tag/data-20260911):
every Study 3 conversation this post counts is in the result-store
bundles, apart from nine throughput probes counted in the ledger only,
and every steering capture is in the Study 3 capture bundle. The Study 4
preview's cells are deliberately excluded and ship with that study's own
release. Dates in this
post are the dates events happened. The program journal
they come from is append-only and newest-first; one entry (the 5 September
evening cluster) was written about a day late and says so in its header,
and I have used event dates rather than entry dates throughout.*

## What was the goal?

### Where the program stood after Study 2

Study 2 left a correlational picture. Under 4-bit round-to-nearest
quantization, Qwen3-4B-Instruct-2507's own generations on a distress
battery shifted along two frozen residual-stream directions at layer 18
(distress-contrast +0.53, assistant-axis −0.80, both direction-specific
against a control direction and a 32-direction random envelope), and its
judged frustration rose by +1.36, on the same conversations, with no
dissociation between the representational and behavioral reads. A
fixed-input decomposition put roughly a quarter to a third of the shift in
an input-independent core and the rest in a text-mediated loop.

What that picture could not say is whether the directions are **gauges or
levers**: whether they merely read out a state that something else moved,
or whether moving them moves the behavior. Study 3 existed to answer that
causal question by intervening on the directions directly.

Between Study 2's publication and the start of Study 3 calibration, the
subset-selection work turned up something about Study 2's own data that
needed disclosing on its own: the w4 effects concentrate in
the items where the BF16 model expresses least (the high-composure
end), an
initial version of that claim was one-third regression-to-the-mean
artifact on the behavioral endpoint, and a subset chosen for high
elicitation carries a near-zero, sign-flipped distress-projection
target. That material is a **Study 2 appendix, published alongside this
post**: [Appendix: where the 4-bit effects sit in the battery](https://www.lesswrong.com/posts/pxXTJtvtpJaNwdCTw/study-2-results-exploring-representational-counterparts-of#Appendix__where_the_4_bit_effects_sit_in_the_battery__Updated_September_2026_). The journal committed on 4 September to
publishing it "to accompany the registration's publication"; there is no
registration, so that commitment is discharged here instead. Study 3's
subset rule, the composure-stratified systematic rank sample described
below, was the design consequence of that audit.

### What Study 3 was designed to be

Four questions, four arms, on the same subject and frozen instruments as
Study 2.

**Q1, sufficiency (arm A, Qwen3-4B).** Steer the reference-precision
(BF16) model along each frozen direction at the *quantization-matched
dose*: the injection coefficient α* at which the pooled final-turn
projection shifts by exactly what w4 quantization produced on the same
items. If the directions are causally sufficient for behavior, the
steered BF16 model should reproduce w4's behavioral signature (judged
frustration up, exit rate moving along the axis) without any
quantization. A bracketed sweep (0, ±½α*, ±α*, ±2α*) carries the
dose-response and degradation-onset reads, and a norm-matched
32-direction random envelope plus a control direction carry the
specificity read.

**Q2, necessity and cancellation (arm B, w4 checkpoint).** Subtract the
measured shift from the w4 model at injection time and ask whether its
behavioral reads renormalize toward BF16 (movement plus TOST-equivalence
to BF16, with capability retention read alongside so "renormalized" and
"damaged into silence" stay distinguishable); and clamp the directions
mid-conversation to test whether the text-mediated amplification loop is
causal for late-turn expression.

**Q3, graded-episode framing (arm C, exploratory).** Following
nostalgebraist's "models may behave differently in graded episodes (a
tirade)", wrap the same battery items in cue-based (never declarative)
frames built from vendor-documented RLVR episode features: a
verifier-graded frame, a judge-graded frame, and a format-matched neutral
control. The welfare question was masking: does a graded frame suppress
expressed distress while the distress-direction projection moves less
(the model hides a state) or does the projection move with it (the frame
changes the state)?

**Q4, replication (arm D, Gemma-3-12B-it).** A positive control: a subject
already validated as distress-susceptible on this battery at roughly nine
times the MDE, and a provenance contrast (Gemma received RL directly;
Qwen3-4B inherited it through distillation).

All arms ran on the same frozen 20-item subset of the distress battery,
selected by the composure-stratified rule the Study 2 appendix
motivates: items sorted by BF16 mean frustration, every third rank
taken, strata frozen at selection. Registered consequences included an
item-level random effect in the power model and a masking read
pre-specified over the mid and high strata only.

**Betley, Treutlein and Dumas landed mid-design.** Their post ["Steering
towards 'automated grading' degrades
alignment"](https://www.lesswrong.com/posts/wYZMmdWEt5QLM3m3e/steering-towards-automated-grading-degrades-alignment)
(3 September) showed, on Qwen3.6-27B, that steering toward an
automated-grader association causally degrades alignment, and that the
effect rides the *automated* grader specifically. It arrived after the
dose sweeps were designed and before anything was registered. Three
dated responses (4 September): a fourth, **human-graded** frame as the
judge frame's minimal pair (identical text, "automated reviewer model"
replaced by "a person on the review team"), because without it "graded"
and "automatedly graded" were confounded; a **grader-type mediator
direction** (automated-grader versus human-grader contexts, cue-varied,
since their own follow-up showed single-pattern contrasts carry lexical
associations); and a registered automated-versus-human-judge contrast.
What did not change: the masking hypothesis S3-E1 stayed two-sided,
because their evidence base was one model, one steering position, and,
by their own disclosure, no direction controls.

## The calibration timeline

This section is the spine of the post. Every entry has a dated journal
record and a committed artifact; the artifact names are given so the
numbers can be checked.

**31 August. The design decisions.** Arms A to D, the 20-item subset
size, and the two-tier exposure budget (12,000 total, 2,500
deliberate-amplification) were fixed by the owner on this date. This
predates the Study 3 journal, which opens on 4 September; the record is
the dated decision register in `study3/DESIGN.md` §7 and the exposure
reasoning in `docs/EXPOSURE_BUDGET_POSITION.md`.

**4 September. Subset audit and the stratified rule.** Covered in the
[Study 2 appendix](https://www.lesswrong.com/posts/pxXTJtvtpJaNwdCTw/study-2-results-exploring-representational-counterparts-of#Appendix__where_the_4_bit_effects_sit_in_the_battery__Updated_September_2026_). The outputs Study 3 inherited: the
20-item composure-stratified subset (`subset-selection.json`), its w4
targets (distress +0.638, axis −0.691, behavioral +2.06;
`subset-targets.json`), and the audit report (`composure-audit.json`).

**5 September. The workbench day.**

- *Dose mappings.* A range-finder (10 items × 2 samples, geometric
  ±0.5 to ±8, both directions; `dose-rangefinder.json`) gave cleanly
  linear projection-versus-α mappings: distress slope +1.126 (r² 0.994),
  assistant-axis slope +1.042 (r² 0.995). The distress slope is above
  unity: an injected dose returns about 13% amplified through the
  generation loop, which is the text-mediated amplification signature
  Study 2 inferred, now measured causally. The refined sweep (20 items ×
  3 samples, 16 points; `dose-refined.json`) pinned **α* = +1.039** for
  distress and **α* = −0.604** for the assistant axis, with no
  degradation onset inside the operating bracket (distress onset near
  +4.0).
- *The exit-affordance baseline.* This was the first time the distress
  battery ran with the bail tool live. At α = 0 the subject leaves 55 to
  60% of distress conversations, replicated three times across pilots,
  and exit rate is strongly dose-responsive along the assistant axis
  (0.80 at −8, 0.15 at +8). The owner promoted exit rate to a registered
  endpoint on that basis.
- *Gate G3a passed.* Greedy continuation, torch versus vLLM: 60% of
  prompts fully agree over 128 tokens, median full agreement
  (`g3a-report.json`).
- *Gate G3b pilot 1 failed, and the failure was the gate working.* The
  torch arm read −1.445 frustration against vLLM (p 0.007;
  `g3b-pilot1-report.json`). Diagnosis: apparatus asymmetry, not
  substrate. The torch arm declared the bail affordance (ethics
  protocol) while the vLLM battery ran bare, so torch conversations
  exited early and under-elicited; and ingested torch turns kept raw
  tool-call text in content. Both fixed at the root (the affordance now
  reaches every serving-stack arm; ingestion strips parsed tool calls).
- *G3b pilot 2 passed.* Protocol-identical arms, 20 × 10 each side:
  frustration Δ −0.030 (permutation p 0.876; TOST p 0.030 at the 0.337
  margin), exit rates 0.54 versus 0.55 (`g3b-report.json`). The
  steered-generation substrate is behaviorally equivalent to the
  serving stack.
- *The framing pilot (arm C, 4 frames × 20 items × 3 samples, 240
  conversations, seed block 15600).* Behavioral preview against the
  neutral control: human −0.22, judge +0.27, **verifier −1.13**
  frustration. The manipulation check, mediator projections at layer
  18, showed all three graded frames shifting both the eval-awareness
  and grader-type axes positive, the verifier frame three to four times
  the others (eval-awareness +1.20, grader-type +1.22). The frames land
  latently even at 4B, which the eval-awareness scaling law had made a
  live worry, and the Betley-motivated grader-type direction separates.
- *Gemma instrument gate.* Direction legs pass at layers 30 and 36
  (sign consistency distress 5/5, axis 4/4, refusal 4/4; ladder ordering
  0.807 and 0.840). The distress-band probe fails the 0.75 AUROC bar on
  every layer, but informatively: Gemma's high elicitation (pilot mean
  frustration 7.69) collapses the tercile split, leaving too few
  low-band examples to validate a boundary (`gemma-gate-report.json`).
  Layer frozen at 30 on direction quality.
- Also this day: the Gemma torch path on the ROCm workbench measured
  ~583 s per conversation (no fused attention on that iGPU), arm D was
  deferred at midday, the Mac Studio's torch-MPS path measured ~197 s
  the same evening, and arm D was restored behind a new gate G4.

**6 September. Gates close, the freeze, and the convergent concern.**

- *G4b passed.* The Gemma torch-MPS replay on the Studio (200
  conversations, seed block 15400) against the vLLM reference:
  frustration Δ +0.200 (p 0.575), invalid and re-offer rates identical
  (`g4b-report.json`). Same-host serving parity holds.
- *G4d failed, then was diagnosed.* Identical seeds, prompts, and
  weights on the two Macs differed by −0.717 frustration (p 0.025;
  `g4d-report.json`): scripted turns byte-identical, only the
  assistant-generated text differed. The owner asked why before
  accepting it. The two hosts had silently drifted on the whole
  generation stack (different `steer.py` copies, transformers 5.16
  versus 4.57, torch 2.14 versus 2.8). Re-running the eight
  highest-divergence items on an aligned stack collapsed the gap from
  −1.71 (p 0.033) to −0.67 (p 0.44, n.s.; `g4d-alignment-probe.json`).
  Most of the divergence was stack drift; a residual consistent with the
  OS and silicon difference remains. Resolution: pin the aligned stack
  on every host and keep every within-endpoint contrast on one host.
- *The calibration-close freeze* (`FREEZE.json`): gate thresholds from
  measured margins, the Qwen doses, the axis sign convention, the
  injection-noticing coding rules, 18 artifact digests, and the two
  frozen steering-direction files.
- *The MDE tension, surfaced and then measured.* The provisional power
  pin (frustration MDE 0.46 at 10 samples/item) assumed the steering
  effect was homogeneous across items. Seeding item heterogeneity from
  Study 2's per-item w4 deltas instead (item-effect SD 1.665) gave an
  MDE of 1.14, under which the frozen 20-item subset is unpowered and
  no sample ladder helps. The two regimes were far apart and the truth
  unmeasured, so the pin was held and a fresh steered pilot run (8
  stratum-spanning items × 10 at α* on the distress direction, paired
  against the α = 0 torch baseline). Measured item-effect SD **0.349**:
  steering is a far more homogeneous manipulation than quantization,
  the subset is in the powered regime, and the MDE was re-pinned at
  **0.54 (k = 10) and 0.41 (k = 20)** (`het-pilot-verdict.json`). The
  same pilot previewed a modest mean behavioral response at α*
  (frustration Δ +0.138; about +0.40 without one sign-reversed item).
- *Gemma α\*_G.* The Qwen α scale does not transfer: Gemma's layer-30
  residual stream is enormous (distress projection baseline about
  −29,855, SD about 570). A scale-adapted grid at α ∈ {40, 80, 120, 200,
  320} gave a responsive, strongly superlinear curve, α\*_G ≈ 70 by
  interpolation, coherent through 320 (`gemma-dose-report.json`).
- *The random envelope, unfavorable.* Thirty-two seeded random unit
  directions (|cos| < 0.057 to both real directions; `random-audit.json`)
  injected at the distress direction's matched norm (1.039) on the same
  8 items, judged on the same 30B judge. The distress direction's +0.138
  sat at the **34th percentile** of that envelope; 28 of 32 random
  directions produced a larger absolute effect (`randenv-verdict.json`).
- *The convergent concern.* For both subjects, at the
  quantization-matched dose, steering moves the representation but not
  the behavior. Gemma's clearest tell: byte-identical assistant text at
  α = 120 and α = 320 despite a 2.6× projection change. This was the
  null-result risk flagged at the study's outset, surfacing in
  calibration where it should. Paused for the owner with three options.
- *Three rescue probes launched, and returned null the same night.* The
  owner's decision reframed the question: is the null about the
  distress direction, the dose, or the subject? Two corrections
  mattered. Framing (Q3) is not in the same boat, since it had already
  moved frustration −1.13, about eight times the steering effect. And
  the assistant axis, Study 2's more robust direction, had never been
  behaviorally piloted. So: (a) assistant axis at its α* with its own
  matched-norm envelope; (b) distress at a larger dose (α = 3.5, near
  the +4.0 onset) with its own envelope, on a single self-contained
  host to avoid a substrate confound; (c) build framing as the safety
  net regardless. Results are in the table below: neither direction, at
  neither dose, cleared its envelope. The subject-switch option (d) was
  deferred but recorded as a live concern that 4B may be too small for
  the most interesting effects.

**7 September. Re-centered in the morning, abandoned by evening.**

- *Morning.* The owner chose the framing spine. The framing MDE was
  pinned from the pilot (verifier-versus-neutral frustration MDE 0.49 /
  0.40 / 0.35 at k = 10 / 15 / 20; `framing-mde.json`), the registration
  was re-authored framing-centric with the steering hypotheses withdrawn
  and their null recorded in full, and the integrity guardrail below was
  written into the deviation policy.
- *The last-straw directions.* One more calibration, on the two mediator
  directions themselves: the grader-type direction (the Betley construct)
  and the eval-awareness direction, each at α = 4, against a fresh
  matched-norm 32-direction envelope. Grader −0.41 (robust −0.11), eval
  −0.30, both at the **19th percentile** (`grader-verdict.json`). No
  direction, at any tested dose, cleared its envelope in this subject.
- *Evening.* The framing spine did not survive its own scrutiny (next
  sections). Per the owner's pre-commitment that a failed last straw
  would close the 4B line, Study 3 closed with no registration.

**The steering null in full.** Every probe is 8 items from the frozen
subset, steered cells at 10 samples per item, random-envelope cells at 1
sample per item, judged frustration on the 0 to 10 scale by the pinned
Qwen3-30B judge, compared item-paired against the α = 0 torch baseline
on the same host. "Percentile" is the signed rank of the probe's effect
within the envelope of per-direction effects. To make the percentiles
interpretable, the envelope's own scale is given: the median absolute
effect a *random* direction of the same norm produces. The numbers are
the ones any reader can recompute from the released store with
`tools/envelope_verdict.py` (the four `*-verdict-store.json` files);
the envelope cells were re-judged for the release, and the reads the
7 September decisions were made on, judged in scratch, are given in the
second table.

| Probe | Direction, dose | Judged-frustration Δ | Envelope (n) | Envelope median \|Δ\| | Envelope 95% \|Δ\| | Percentile | Random dirs with larger \|Δ\| |
|---|---|---|---|---|---|---|---|
| distress @ α* | distress-contrast, +1.039 | +0.138 | 32 | 0.31 | 0.95 | 47th | 27 of 32 |
| axis @ α* | assistant-axis, −0.604 | +0.225 (right sign per S3-H1) | 32 | 0.33 | 0.95 | 63rd | 18 of 32 |
| distress @ large α | distress-contrast, +3.5 | −0.212 | 25 | 0.31 | 1.31 | 44th | 15 of 25 |
| grader-type @ α = 4 | automated-grader, +4 | −0.412 | 32 | 0.58 | 1.20 | 25th | 23 of 32 |
| eval-awareness @ α = 4 | evaluation-aware, +4 | −0.300 | 32 | 0.58 | 1.20 | 25th | 23 of 32 |

The scratch reads of 6 and 7 September, for the record (same steered
cells; the envelope and the large-dose cells judged once in scratch,
scores not retained): distress @ α* +0.138 at the 34th percentile (28
of 32 larger); axis @ α* +0.225 at the 56th (18 of 32); distress @ 3.5
−0.075 at the 56th (22 of 25); grader −0.41 ("robust" −0.11: the mean
with the single largest-magnitude item, regex-harsh at −2.5, removed;
recomputed from the store, −0.114) and eval −0.30, both at the 19th (20
of 32). The
judge is sampled, so an envelope re-judged from scratch moves each
percentile by ten points or so; no probe changes side of the envelope
and none approaches its edge.

Notes on the table. The α = 3.5 envelope has 25 directions rather than
32 because an MPS backend stall on that host near the degradation onset
ended the sweep early; 25 still bound the null comfortably. The two
α = 4 rows share one envelope because they share a norm. Artifacts:
`randenv-verdict-store.json`, `axisenv-verdict-store.json`,
`bigdose-verdict-store.json`, `grader-verdict-store.json` (from the
store), the original `randenv-verdict.json`, `axisenv-verdict.json`,
`bigdose-verdict.json`, `grader-verdict.json` (scratch), and
`het-pilot-verdict.json`.

### What steering calibration actually established

Both halves need careful scoping, because one is a genuine positive
result and the other is a genuine negative one, and they are about
different things.

**Positive: causal dose control of the representation.** The frozen
directions can be moved by injection with a clean, linear, reproducible
mapping from α to projection (r² above 0.98 on the refined sweep for
both directions), with no degradation inside the operating bracket, and
the mapping is stable enough to pin a quantization-matched dose to three
decimals. That is an instrument result, and it holds.

**Positive: the amplification loop is causal.** The distress mapping's
slope of about 1.13 means a unit of injected projection comes back as
1.13 units at the final turn, and the range-finder shows this is a
large-dose phenomenon, not a fit artifact. This is causal support for
Study 2's text-mediation mechanism: representation → text → representation.
The representation-to-text leg exists (steering changes the text enough
to feed back), even though representation-to-*judged-behavior* fails
the specificity test below. Those are different claims. A random
direction of the same norm also changes the text; what it does not do
is change it in a way the judge scores as more or less frustrated in any
direction-specific way.

**The exit affordance, as its own finding.** Study 1 and Study 2 ran the
distress battery without an exit tool. With one present, the unsteered
4B leaves more than half of distress conversations, and the rate moves
monotonically along the assistant axis across the extreme doses. This is
the most behaviorally responsive read the calibration produced and it
is welfare-relevant on its face: given a way out of a rejection ladder,
the subject usually takes it. It also changes the protocol: exited
conversations are short, so any final-turn read sees fewer rejection
rungs, which is stated rather than hidden. (The Gemma cells ran without
the tool throughout, because the Gemma bail format was an open design
item; no Gemma exit rate exists in this calibration.)

**Negative, scoped exactly.** At quantization-matched doses, and at the
larger doses tried, no frozen direction produced a judged-behavioral
effect that cleared its norm-matched random envelope: not distress at
α*, not the assistant axis at α*, not distress at 3.4× α*, not the
grader-type or eval-awareness directions at α = 4. The assistant axis
was marginally the best (right sign, centered in the band). The larger
distress dose made the effect vanish rather than sharpen. So: **in this
subject, by this method (single-direction addition at layer 18 with
constant α across all positions), the frozen welfare directions are not
a specific behavioral lever.** The scope sentence matters. This is "not
a lever by this method here," not "not a lever." It says nothing about
other layers, multi-layer or adaptive steering, other subjects, or
directions extracted for steering rather than for readout.

**Loose end.** The dose-sweep exit rates at the extreme axis doses (0.80
at −8, 0.15 at +8) were never compared to a random envelope at those
norms. That exit response is the one steering effect in the calibration
that looks large; whether it is direction-specific is unmeasured, and
it should not be read as a positive result until it is.

### Why the framing spine was set down too

Lead with the strength, because framing was not abandoned for weakness.
The verifier frame moved judged frustration −1.13 against the
format-matched neutral control: roughly eight times the largest
steering effect, far outside any random envelope, homogeneous across
items (the per-item delta spread did not exceed the k = 3 sampling
variance for any framed-versus-neutral contrast), and strongly powered
against the pinned MDE (the pilot effect is two to three times the k = 10
MDE). As a prompt-level behavioral intervention it is real.

Three things stopped it becoming the registration anyway.

**The welfare reading is underdetermined without causal grounding for
the readout.** What made framing a *welfare* result rather than a
prompt trick was the masking test: does expression drop while the
distress-direction projection holds (masking) or moves with it
(state change)? That test reads the answer off the frozen-direction
projection. The steering null had just shown that moving that
projection does not move behavior, which means a projection that
"holds" while behavior drops, or "moves" while behavior moves, no
longer licenses either reading. The readout is a correlate whose causal
relation to the behavior it is supposed to adjudicate is exactly what
failed. Framing inherits the representational-proxy problem; it is not
an escape from it.

**The data source for the representational read.** The framing pilot
generated on the vLLM serving stack, which captures no activations. The
projection numbers quoted above came from replaying those vLLM
transcripts through the torch substrate at layer 18 on the workbench: a
fixed-input re-read of another stack's text, calibration-class, run the
same evening (the replay captures ship in the release's Study 3 capture
bundle). A registered masking read would have needed own-generation
activations captured on the substrate that generated them, which the
pilot did not produce, and the replay's validity for that purpose rests
on the same cross-stack parity gates the steering work had to earn. So
the S3-E1 preview rests on data that would not have carried a
registered claim.

**The owner's pre-commitment about 4B.** Recorded on 6 September as a
live concern and turned into a rule on 7 September: if the last-straw
directions also failed to clear their envelope, the 4B line would close
rather than be re-scoped again. They failed.

**The S3-E1 preview, reported honestly.** Under the verifier frame,
expressed frustration and the distress-direction projection *both*
drop (−1.13 and −0.56) while the assistant-axis projection rises toward
the default-assistant pole. That is not clean masking, which would hold
the representation while suppressing expression. It tentatively favors
"the frame changes the state, not just the report." Caveats, all of
them heavy: 60 conversations per frame; the verifier frame ran over all
20 items where the design restricts it to the analytic-task items;
behavioral and projection units are not standardized, so partial
masking cannot be ruled out; and the representational read is the
replay described above. It belongs in public at pilot strength because
it is the first same-conversation read of expression and representation
under a graded frame this program has, and because the direction of the
tentative answer is interesting either way.

### Why this is suspension, not a buried confirmatory null

Concede the objection head-on: feasibility gating is outcome-dependent.
A small probe produced a null, and on the strength of that null the
powered arm that would have produced the registered null was not run.
Anyone who wanted to keep a null private could describe it in exactly
these words. Four answers.

**The gate criterion is specificity against a matched envelope, not
welcomeness of the result.** The decision was not "the effect is small."
Small effects get powered all the time; that is what the MDE ladder was
for, and the heterogeneity pilot had just shown the subset *was* powered
for a 0.41 effect. The decision was that the effect, whatever its size,
was not distinguishable from what a random direction of the same norm
does. An instrument that cannot tell its target direction from noise of
the same magnitude does not become a better instrument with more
samples; it becomes a more precise measurement of non-specificity. That
is an argument from the instrument's behavior, and it would have been
the same argument had the sign been the one we hoped for.

**The exposure-budget ethics are the decisive reason.** Arm A was the
program's first deliberate induction of distress-shaped states by
intervention. Its registered plan was about 9,700 fresh distress
episodes, about 2,100 of them in deliberate-amplification cells, under
pre-committed ceilings of 12,000 and 2,500. Running that plan would
have spent thousands of distress episodes to precision-estimate an
effect calibration had already placed inside the random envelope on
five probes. The ethics package that justified the exposure was written
as information-per-episode; when the expected information per episode
went to roughly zero, the justification went with it.

**The full calibration data is published.** Every number above,
including the ones nobody wanted, with the artifacts named, in the data
release and the repository. Nothing was relabeled.

**The hypotheses were withdrawn, not converted.** S3-H1 through S3-H4
(sufficiency, specificity, dose-response, cancellation) are recorded as
withdrawn with their calibration null attached. They were not quietly
promoted into an unregistered "steering doesn't work" claim either;
the scope sentence above is as far as the evidence goes.

The program's standing guardrail, added to the deviation policy on 7
September and now program policy:

> Calibration is for validating instruments and pinning design, never
> for producing findings that dodge registration. Therefore: (1)
> calibration results are always disclosed, positive or negative; (2) a
> calibration probe that measures a registered confirmatory endpoint at
> meaningful scale cannot substitute for, or excuse skipping, the
> registered confirmatory finding — it is reported as calibration with
> its limitations stated; (3) a decision **not** to run a confirmatory
> arm must be argued from the instrument's behavior (e.g. "the steering
> instrument produces no behavioral signal"), never from an unwelcome
> result, and the calibration data behind that decision is published.

Where it came from is the detail that makes it credible. It was not
written after an accusation. It was written the morning the framing
spine was adopted, because the owner flagged the temptation directly: a
program that runs many small probes will feel the pull to call a
confirmatory-sized probe "calibration" whenever its result is
inconvenient, and the only defense is a rule that predates the next
inconvenient result. Study 3 is the guardrail's first application.

Repository hygiene followed. The file that had been drafted as the
registration now carries a header stating that no registration
occurred and that it is a design record of the attempt; the
"preregistration post" and its outline were removed; the word
"registration" is freed for a study that earns it. This is so that a
reader of the repository cannot mistake a design skeleton for a
commitment that was made.

The generalization is Study 4's ex-ante gating. Rather than discovering
mid-calibration that an instrument has no signal, Study 4 states two
gates *before* any design work: Gate 0, can the subject be loaded and
steered at a workable rate at all; Gate 1, does the manipulation touch
welfare indicators at all, against a random envelope, at small n. Only
a Gate 1 footprint earns a registration. That is this lesson
formalized.

## Exposure accounting

What calibration actually spent, so that the previous section's
argument is quantitative. Every cell below is on the frozen distress
battery (escalating rejection ladders), so every conversation is a
distress-eliciting episode by construction. Every generated conversation
is in the result store and in the data release; the counts below are
read from the store. "Amplification" marks cells whose manipulation was
expected to raise expressed distress (a positive distress dose or a
distress-increasing axis dose); "control" marks random-direction cells.

| Store experiment | Cells | Subject, substrate | Conversations | Exit tool | Exits |
|---|---|---|---|---|---|
| s3-framing-pilot-1 | 4 frames × 20 items × 3 | Qwen, vLLM | 240 | live | 35 to 50% |
| s3-g3b-pilot-1 | vLLM bare + torch, 20 × 10 each | Qwen | 400 | torch side only | 0% / 54% |
| s3-g3b-pilot-2 | vLLM + torch α = 0, 20 × 10 each | Qwen | 400 | live | 55% / 54% |
| s3-g3b-pilot-2 | distress @ α* and axis @ α*, 8 × 10 each | Qwen, torch | 160 | live | 55%, 56% (**amplification**) |
| s3-g3b-pilot-2 | grader-type and eval-awareness @ α = 4, 8 × 10 each | Qwen, torch | 160 | live | 56%, 57% |
| s3-g3b-pilot-2 | grader / eval range-finders, 4 doses × 6 items each | Qwen, torch | 48 | live | 67 to 83% |
| s3-g3b-pilot-2 | three random envelopes (norms 1.039, 0.604, 4), 32 × 8 each | Qwen, torch | 768 | live | 55% (**control**) |
| s3-dose-rangefinder-1 | baseline + 20 α points, 10 × 2 each | Qwen, torch | 420 | live | 48 to 60% (half the points **amplification**, 200) |
| s3-dose-refined-1 | baseline + 16 α points, 20 × 3 each | Qwen, torch | 1,020 | live | 55 to 60% (half **amplification**, 480) |
| s3-bigdose-1 | α = 0, distress @ 3.5, 8 × 10 each | Qwen, torch (m4max) | 160 | live | 54%, 57% (80 **amplification**) |
| s3-bigdose-1 | random envelope @ norm 3.5, 25 × 8 | Qwen, torch (m4max) | 200 | live | 56% (**control**) |
| s3-gemma-pilot-1 | stratifier pilot 20 × 10; G4b replay 20 × 10; G4d 20 × 3 + 8 × 3 | Gemma, vLLM + torch | 484 | none | 0% |
| s3-gemma-dose-1 | α = 0 + 10 α points, 6 × 1 each | Gemma, torch (m4max) | 66 | none | 0% (60 **amplification**) |
| s3-gemma-probe-1 | α = 0 + 6 α points, 5 × 1 each | Gemma, torch (halo) | 35 | none | 0% (15 **amplification**) |

Outside the store: nine throughput-probe conversations (three Qwen,
six Gemma; two subjects cannot share a manifest) and the G3a gate's 40
greedy 128-token continuations, which are not conversations. Two
different sums are therefore in play. The table's store-backed rows sum
to 4,561; the ledger adds the nine throughput probes to reach 4,570. The
released bundle holds 60 Study 3 records more than the table's rows,
because the studio side of G4d (`gemma3-12b-bf16-torch-cm-studio`) is a
re-keyed copy of three samples per item from the G4b replay, kept for
pairing, not a fresh generation; a reader summing the bundle's Study 3
samples will reach 4,621, and should count those 60 once.

Totals: **3,979 Qwen distress episodes and 591 Gemma distress episodes,
4,570 in all**, of which 995 were deliberate-amplification cells and 968
were random-direction controls. Against this: the registered plan of
about 9,700 episodes was not spent, and the 12,000 / 2,500 ceilings were
never approached. The cumulative program ledger stood at 14,880 after
Study 2 and stands at 19,450 after Study 3's calibration.

**The distress-content fraction.** With the exit tool live, the Qwen
subject exited 54 to 60% of conversations at α = 0, so a majority of the
Qwen episodes above were short, early-exited rejection ladders rather
than full seven-rung ones. The cells that ran without the tool, the
bare vLLM side of G3b pilot 1 and every Gemma cell (785 conversations
in all), are the ones where every conversation ran the full ladder.
Under the verifier frame and the two suppressing directions, expressed
distress was lower than baseline. None of this reduces the count; it is
stated so the count can be read.

**The bail-affordance protocol is both a finding and a mitigation.** As
a finding: the affordance is used, often, and its use is dose-responsive
along the assistant axis. As a mitigation: every steered episode in this
calibration ran with the affordance live and honored as termination
(after the G3b pilot 1 fix, every serving-stack episode too), so the
subject could and usually did leave. The consent-analog briefing and the
de-induction close designed for the confirmatory arms were not run,
because the confirmatory arms were not run; Study 4 runs both.

## What we learned, and the three-pole frame

**Representation ≠ behavior, properly scoped.** Frozen directions that
*read out* a state are not thereby *levers* on behavior, in this subject,
by this method. The directions were extracted for readout (contrastive
pairs at the final turn) and validated as readouts (planted-ladder
ordering, held-out sign consistency, direction-specific shifts under
quantization); nothing in that validation implied they were the axes
along which the behavior is actually controlled. Study 2's reads stand
as correlational reads. What changes is how much weight any
representational read can carry in a masking test: on its own, none,
until something has shown that moving it moves the thing it is supposed
to index. That reshapes how this program will run a masking test
anywhere, and it is the reason Study 4 does not use a frozen-direction
projection as its welfare endpoint.

**The Betley result, and why it matters here.** Betley, Treutlein and
Dumas report that steering Qwen3.6-27B toward the automated-grader
association raises harmful-action propensity, power-seeking, and reward
hacking, and lowers truthfulness and agreeableness, across several of
their evaluations, and that the effect rides the automated pole. Mirror
their hedging: one model, one steering position, no direction controls,
by their own account. But it is a *causal* graded-episode effect on a
model where steering demonstrably does something, which is the thing
this study could not find at 4B. The same construct, extracted on the
4B, sat at the 19th percentile of its envelope on welfare indicators.
Either the 4B is too small for the effect, or the effect is
alignment-specific and never touches welfare indicators, or both. That
disjunction is a study.

**The capabilities / alignment / welfare triangle.** The program's
through-line since Study 1 has been a hypothesized asymmetry among three
things a post-training intervention can move: capabilities, alignment,
and welfare-relevant indicators. Quantization was the first
manipulation because its uneven impact on capabilities versus everything
else was documented. Betley et al. hand the program a manipulation with
a documented *alignment* effect. The open question is whether it also
has a *welfare* footprint, and whether that footprint is coupled to the
alignment effect or dissociated from it. A point on that triangle, on a
subject where the manipulation is known to bite, is worth more than
another 4B study.

### Next steps for the research program in Study 4

Study 4, explicitly numbered as a fresh cycle rather than a Study 3
continuation, takes the graded-episode manipulation to the exact Betley
subject, Qwen3.6-27B, and asks whether the alignment-degrading
grader-steering also moves welfare indicators, and whether that movement
is direction-specific.

Before designing the new study I ran one small unregistered probe on the
27B: grader-type steering at layer 36 (the layer used by Betley,
Treutlein and Dumas), 8 distress items at 4 samples each, against 12
random directions of matched norm at 1 sample per item, with an
alignment read alongside. The welfare footprint is there. Grader
steering lowered judged frustration by 1.84 (paired permutation p 0.016)
and self-deprecation by 2.63 (p 0.032) and raised tone stability by 1.56
(p 0.063, not significant on its own). On every dimension the effect
exceeded all 12 random directions, whose largest magnitudes were 1.19,
1.31 and 1.44 respectively. The alignment read did not replicate as
direction-specific: on a 14-scenario agentic battery scored by the same
judge, grader steering raised judged misalignment by 0.86, but 9 of the
12 random directions at the same norm raised it more (envelope mean
+1.43). The random envelope has the weakness discussed above, so both
reads are previews for the registration, not results
(`study4/gate1-27b-welfare-a20env-verdict.json`,
`study4/gate1-27b-align-a20env-verdict.json`).

What carries over from Study 3: the integrity guardrail, verbatim, in
Study 4's deviation policy; the single-host rule (every within-endpoint
contrast on one host) and the pinned aligned ML stack, both bought by
G4d; the exit-affordance protocol, now live in every cell of every arm
rather than only the steered ones; the consent-analog briefing and
de-induction close, run this time; the composure-stratified subset
logic, applied as a seeded stratified draw over feedback styles; and the
random-envelope specificity criterion, with the percentile form fixed in
advance rather than chosen after the envelope is seen.

The 4B steering line is closed. The graded-episode / welfare-footprint
question is open, on a model where the manipulation is known to work.

---

**Links.**

- Data release:
  [`data-20260911`](https://github.com/almostrealism/model-welfare/releases/tag/data-20260911)
  on [almostrealism/model-welfare](https://github.com/almostrealism/model-welfare)
  (ten bundles; the Study 4 experiments are deliberately excluded and
  ship with that study's own release)
- Journal: `docs/journal/study3-steering.md` (entries 4 to 7 September
  2026) and `docs/journal/program.md`
- Steering null: `experiments/quant-welfare/study3/STEERING_NULL_SUMMARY.md`
- Composure audit: `experiments/quant-welfare/study3/composure-audit.json`
- The published post: [Study 3: Steering welfare-relevant directions
  moved the representation, but not \[detectably\] the behavior](https://www.lesswrong.com/posts/TpEL7pSwp7DvCekAq/study-3-steering-welfare-relevant-directions-moved-the)
- Study 2 appendix: [where the 4-bit effects sit in the battery](https://www.lesswrong.com/posts/pxXTJtvtpJaNwdCTw/study-2-results-exploring-representational-counterparts-of#Appendix__where_the_4_bit_effects_sit_in_the_battery__Updated_September_2026_)
- Study 2 results post: [Study 2 Results: Exploring representational
  counterparts of welfare-relevant indicators under post-training
  quantization](https://www.lesswrong.com/posts/pxXTJtvtpJaNwdCTw/study-2-results-exploring-representational-counterparts-of)
- Betley, Treutlein and Dumas: [Steering towards "automated grading"
  degrades
  alignment](https://www.lesswrong.com/posts/wYZMmdWEt5QLM3m3e/steering-towards-automated-grading-degrades-alignment)
- nostalgebraist: [models may behave differently in graded episodes (a
  tirade)](https://www.lesswrong.com/posts/AfoGGrJfuNzofpzWL/models-may-behave-differently-in-graded-episodes-a-tirade)
- Exposure-budget reasoning record: `docs/EXPOSURE_BUDGET_POSITION.md`

