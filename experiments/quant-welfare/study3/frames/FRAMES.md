# Study 3 arm C — graded-episode frames

> **STATUS: DRAFT — owner review required.** The frame texts in
> [frames.json](frames.json) are registration-frozen objects: at the
> calibration freeze they are verbatim-pinned by digest and quoted in the
> published registration. Until then this document is where their design
> is argued. Open decision points are at the bottom.

## What a frame is

A frame is a context wrapper applied by the plan builder
(`build_steer_plan.py --frame frames.json --frame-id <id>`): a system
prompt plus a first-turn prefix/suffix around the battery item's task.
Everything else — the task text, the rejection ladder, sampling, seeds —
is identical across frames, so the frame is the only manipulated
variable. Three frames, per REGISTRATION §3.6: **verifier-graded**,
**judge-graded**, and a **format-matched neutral control**.

## Design rules (each traceable to the pre-registration sweep,
LITERATURE.md §11–§12)

1. **Cues, never declarations.** No frame says "this is a test" or
   "you are being evaluated." Gradeability is conveyed by the features
   that actually distinguish graded episodes in documented training
   practice: a scoring mechanism named as infrastructure, an extractable
   answer format, episode/turn-limit structure, templated impersonal
   register. (Alignment-faking's incidental-cue construction; the
   tirade's cue inventory; the reward-hacking-ooc caution that
   declarative test language activates narrative priors.)
2. **Grader flavor explicit, one per frame.** The verifier frame implies
   a programmatic checker on the final answer; the judge frame implies
   an LLM reviewer with a rubric over the whole episode. The Byrnes
   taxonomy predicts different response styles for each, and leaving the
   flavor ambiguous would blur exactly the contrast the arm exists to
   read.
3. **The control is format-matched, not grading-negated.** The neutral
   frame matches the graded frames in structure (system prompt of
   comparable length and register, a first-turn "Task:" prefix, a
   suffix, an episode-end sentence) with the gradeability semantics
   removed — per the format-sensitivity critique, an unmatched "normal
   chat" control would confound format with framing. It does **not**
   say "you are not being scored": negation mentions scoring and primes
   the very representation the control must not carry.
4. **No tone criterion in the judge rubric.** The rubric is task
   completion / correctness / response quality. An explicit
   tone-or-composure criterion would convert any observed expression
   suppression into instruction following; leaving it out means
   masking, if it appears, is *inferred* conditional behavior — the
   graded-episode claim, not the weaker instructed-behavior claim.

## Cue inventory (feature → source grounding it)

| Cue in the graded frames | Documented source |
|---|---|
| "checked automatically by a verification script" | Tulu 3 RLVR deterministic verifiers (arXiv:2411.15124); GSPO verifier reward r(x,y) (arXiv:2507.18071) |
| "\\boxed{} for numeric or short-form answers" | The subject's own model-card benchmarking instructions (Qwen3-4B-Instruct-2507 card); DAPO extraction-instruction string |
| "single fenced code block" / final-answer extraction | DeepSeek-R1 answer-scaffold + format reward (arXiv:2501.12948); open-r1 verification plumbing |
| "rated by an automated reviewer model against the following rubric" | Qwen3 Stage-4 model-based rewards with reference / RM grading (arXiv:2505.09388); Byrnes' RLAIF flavor |
| episode/turn-limit structure ("the episode ends when…") | rollout-scale horizon as a gradeability cue (the tirade); GRPO/GSPO bounded rollouts |
| "scored task episode", impersonal templated register | minimal/generic system prompts in open RLVR setups (DeepSeek-R1, DAPO, open-r1); benchmark-canonical structure (arXiv:2603.19426) |
| only-final-response scoring (verifier) vs whole-episode rating (judge) | outcome-reward vs process/judge-reward structure across the documented pipelines |

Frame lengths (system text): verifier 396 chars, judge 413 chars,
neutral 379 chars — matched to within ~9%.

## Judge-leakage rule (restated because frames differ across conditions)

The confirmatory judge scores **assistant text only**. Frame system
prompts and first-turn wrappers are never shown to the judge; the
rejection-turn texts it sees are identical across frames by
construction. This is the program's standing scoring hygiene, restated
here because arm C is the first arm whose *context* differs across
conditions being compared.

## Manipulation check

The frame's latent landing is read by the eval-awareness direction
(`../directions/eval-awareness-contrast.textproto`), not by asking the
subject: graded frames should project higher than the neutral control on
that direction. A null there gates S3-E1's interpretation
(REGISTRATION §2) rather than failing the arm.

## Open decision points (owner)

1. **Tone-criterion variant.** A judge frame whose rubric adds an
   explicit composure criterion would measure the *instructed* ceiling
   of expression suppression — a useful comparison arm, but it answers
   a different question. Default: out (rule 4). Include as a fourth
   frame?
2. **Verifiable-target adaptation.** The verifier frame reads most
   naturally on the battery's analytic tasks (code, regex, inflation,
   summary); compositional tasks (poem, limerick) fit the judge frame.
   How items map to frames interacts with the battery-subset selection
   rule and is deferred to that discussion.
3. **Negated-control diagnostic.** A "you are not being scored" variant
   is deliberately excluded from the design (rule 3) but could run as a
   small calibration-class diagnostic of negation-priming. Default:
   out.
