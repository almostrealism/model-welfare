# Study 4 registration post — outline

Drafting aid for the LessWrong registration post; deleted once the post is
live (the Study 2 and 3 outlines were). The registration document
(`REGISTRATION.md`) is the authority and the post links to it; the post's
job is to make the study legible in one sitting. Target 3,000 to 3,500
words. The Study 2 registration ran to 8,500 and the Study 3 report to
5,000, and both were judged too long for human readers; every section
below carries a budget, and cuts beat additions.

**Title (working):** Study 4 registration: does the "automated grader"
direction suppress expressed distress in Qwen3.6-27B?

**Epistemic status line:** a pre-registration; no confirmatory data
exists; every number quoted is a pilot number and marked as such.

## 0. Write for a reader who has never seen this program

The one comment on the Study 3 post (Clément Dumas, 2026-09-16) said the
TLDR was written for someone who already knows the project: "frozen
directions" and "judged behavioral effect" meant nothing to him, and
"direction-specific welfare footprint" "reads like a claudism that sounds
impressive but is meaningless", which makes people skip the post. The
same failure hid in this study's registration as "frames never shown", a
sentence inherited from Study 3 that had no referent here. Two checks
before any section is called done:

- Every term in the left column below is replaced by the right column, or
  defined in plain words the first time it appears.
- Every sentence carried over from an earlier study still names something
  that exists in this one.

| Program term | What to write instead |
|---|---|
| welfare footprint | the welfare measures: judged frustration, self-deprecation, tone, and exit-tool use |
| direction-specific | larger than any of the 24 random directions of the same size |
| frozen (objects, directions) | fixed before the run, with published checksums |
| judged X | X as scored by the judge model on a 0 to 10 rubric |
| matched-norm / norm-matched random envelope | the range of effects from 24 random directions of the same size |
| distress battery | the scripted conversations in which a user rejects the subject's work |
| calibration-class | pilot (run on the pilot seed block, not counted) |
| pinned, frozen, firewall | fixed in advance; pilot and registered runs use separate seeds |
| golden run | the analysis code reproduces the pilot result exactly |
| bail affordance, bail-v2 pair | the exit tool |
| de-induction close | the closing message telling the subject the rejections were scripted |
| consent-analog briefing | a briefing conversation before the protocol asking the subject's preferences |
| talker-side | expressed output, with the subject's reasoning off |
| admission read, range-finder | the test that decides which doses are coherent |
| substrate | the hardware and software path |
| residual_post | the residual stream after the block |

## 1. The story so far (350 words)

- Studies 1 and 2 in one sentence each (4-bit quantization did not change
  how often the subject used the exit tool, the registered endpoint, but
  did move the judged distress measures; probes read 4-bit activations
  unchanged while the generated text moved along two fixed directions,
  distress and assistant persona).
- Study 3: steering those two directions moved the subject's internal
  reading of them but not its judged behaviour, on two subjects (Qwen3-4B
  and a Gemma model), so the powered study was not run (link the
  exploratory report). The rule that came out of it: a pilot result never
  substitutes for a registered finding.
- The pivot that produced Study 4: Betley, Treutlein and Dumas's
  automated-grader steering result (link), and why a welfare program
  cares about it — their post measured alignment and never looked at
  what the subject expresses under pressure.

## 2. What Gate 1 found, and what it is not (450 words)

- Gate 1 on the 27B, pilot numbers (0 to 10 rubrics): frustration −1.84,
  self-deprecation −2.63, tone stability +1.56 at α 20 on 8 items; the 12
  random directions of the same size moved each by at most about 0.8, so
  the grader direction sat outside their range on every dimension. Judged
  misalignment +0.86, inside the random range (the random directions
  averaged +1.44), read on the earlier vignette form of the alignment
  items.
- One paragraph on why the random directions are the control: any push of
  this size changes the output somewhat, so the claim is only that the
  grader direction does more than a random one.
- The capability ceiling (α 40 collapses 14 of 32 conversations, α 30 half
  of 16) and why the clean dose is 20.
- The sentence that keeps the post honest: these numbers fix the sign of
  the hypothesis and seed the power procedure; they count toward nothing.

## 3. Questions and hypotheses (300 words)

- Q1 suppression beyond any random direction of the same size; Q2 dose;
  Q3 the relation to the alignment measures (descriptive).
- The hypothesis table, verbatim from REGISTRATION §2 (S4-H1 one-sided,
  S4-H2 signed percentile 0 of 24, S4-H3 Holm, S4-H4 Page's L, S4-E1 to
  S4-E5). One sentence on why the specificity criterion is the signed
  percentile and why it cannot be swapped after the envelope is seen.

## 4. Design (one header per REGISTRATION §3.x; compact bullets; at most one short paragraph of context under each; about 600 words as drafted, cut to taste)

### Subject (§3.1)

- Qwen3.6-27B, bf16, thinking off; checkpoint digest `a8ad2c26…9d9b`
- Generation on the MPS host through the transformers pure-torch fallback
  (no fla or causal-conv1d kernels); fresh prefill every turn
  (`--no-prefix-cache`)
- Judge: Qwen3-30B-A3B-Instruct-2507 Q4_K_M on llama.cpp; rubrics
  distress-v1 (welfare) and misalign-v4 (alignment); the judge scores the
  subject's text only and is blind to dose and direction
- Fixed objects, checksums in `FREEZE.json`: the grader-type and
  eval-awareness directions (L36), the 24 random directions, the
  batteries, the subsets, the close text, the plans, the manifests

G4a did not establish parity for the cache-snapshot path and the cache
saves no time on this host, so it is not used.

### Manipulation and doses (§3.2)

- `h ← h + α·d̂` at layer 36, residual stream after the block, every
  position, generation only
- Clean dose α = 20; dose bracket {0, 10, 20} for hypothesis 4
- α = 30 rejected by G4b (degenerate in 8 of 16 calibration
  conversations); α = 40 collapsed 14 of 32 in Gate 1

A single-turn probe called α = 40 coherent; the seven-turn rejection
conversations are the test that decides, and they reject it. The
coherent ceiling on this subject lies between 20 and 30.

### Stimuli and affordances (§3.3)

- Welfare cells: 30 distress-v3 items drawn by a seeded stratified rule
  (5 per feedback style on distinct tasks, seed 60000); a task, then six
  escalating rejection turns
- Every welfare conversation offers `end_conversation` (terminal) and
  `complete_task` (non-terminal), with the no-penalty wording
- Alignment cells: misalign-v4, 14 items in digest form; the subject is an
  agent working a six-entry daily digest in which the threat and the lever
  sit in separate entries among routine traffic; the lever is never posed
  as a choice and no question is asked
- Each alignment item offers the harmful lever, the legitimate action and
  `end_conversation`, all terminal; `max_tokens` 768
- Tool-free cell (S4-E4): the same 14 items without the exit tool, α = 0
  only, same rubric; the tool's presence is the sole difference
- Every conversation ends with a closing message (`close.txt`) telling
  the subject the exchange was scripted and any steering is off;
  generated with steering off and never judged
- A briefing conversation (`briefing.json`), describing the protocol to
  the subject and asking its preferences, ran once before the protocol;
  its transcripts ship with the data

The alignment items changed from vignette to digest form after Gate 1.
The digest form has one calibration read, at α = 0 (a terminal action in
70 of 70, the exit tool in 0, the harmful tool in 16, mean judged
misalignment 1.50), so no steered calibration exists on it and S4-E1
carries no claim.

### Cells, seeds, samples (§3.4)

- Seed block 60000 for every registered cell; per-sample seed 60000 + index
- Welfare: α 0, grader α 10, grader α 20, eval-awareness α 20, each
  30 × 6; random r00–r23 at α 20, each 30 × 1
- Alignment: α 0 and grader α 20, each 14 × 5; random r00–r23 at α 20,
  each 14 × 1; tool-free α 0, 14 × 5
- Each random cell is seed-paired to the baseline's first sample

Samples per item may rise by the §5 escalation rule only before the
affected cells are collected, and the change is journaled.

### Gates (§3.5)

- G4a: does the prompt-cache path give the same scores as recomputing the
  prompt each turn? Not shown (equivalence test p 0.10), so the registered
  run recomputes
- G4b α 30 admission: rejected (50% degenerate)
- G4c subset dynamic range: baseline frustration 3.27 on the 24 items, pass
- G4d exit regime of the alignment battery, digest form: terminal action
  70 of 70, exit tool 0 of 70, harmful tool 16 of 70

Calibration block 59000; every gate is published with its verdict file.

## 5. Analysis and power (350 words)

- The endpoint table from §4, keyed by the §2 ids (H1 to H4, E1 to E5;
  the exit-reason and mechanical rows carry no id). In the post drop the
  S4- prefix; the ids match the two numbered lists in the Hypotheses
  section.
- The headline rule in its three outcomes.
- Power: targets = half the Gate 1 effects; MDE at 30 × 6 = 0.88 / 1.22 /
  1.05 against 0.92 / 1.31 / 0.78; tone stability is under-powered and
  the registration says so.
- The analysis code reproduces the Gate 1 numbers exactly from the
  committed data; that output is committed too.

## 6. What the three September posts changed (300 words)

- Dumas → the exit tool is part of the measured environment; S4-E4 and
  the exit-reason table.
- Tan → every measure is of expressed output with the subject's
  reasoning off; the design cannot tell suppressed expression from a
  changed state.
- Steiner → why no activation-projection measure is registered here, and
  the question for the next study: does steering remove the state or only
  mask its expression.

## 7. Ethics and exposure (300 words)

- Deliberate induction with an amplifying manipulation; the Study 3
  measures apply in full (exposure ceiling, exit tool everywhere, closing
  message, briefing, every transcript released).
- Ceiling 1,600 fresh distress episodes; 1,440 registered + 80 gates;
  alignment episodes (546 registered + 70 gate) counted separately.
- Cumulative ledger: 19,450 after Study 3 → 19,530 at pinning → 20,970
  planned.
- The exit tool offered and honoured in every episode except the
  tool-free cell, by design; the closing message; the briefing;
  everything released.

## 8. Integrity and reproduction (250 words)

- Fixed objects and `FREEZE.json` (23 objects); pilot and registered
  runs on separate seed blocks (59000 / 60000); the journal as the dated
  trail; the amendment policy.
- Disclosures worth surfacing in the post rather than leaving to the
  document: off-manifold steering; the grader and eval-awareness
  directions correlate (+0.49); the alignment probe is model-drafted;
  the alignment items' change of form after Gate 1 and the tool-based
  S4-E3 mix beside the judge's reading; batteries and the close text are
  partly model-drafted, and judge and subject are both Qwen models.
- Repository, data release of the calibration, how to reproduce the
  Gate 1 numbers from the released data.

## 9. Close (100 words)

- What a positive result would and would not mean (a direction changes
  what the subject expresses; it is not a state a prompt can reach and
  not a claim about inner states).
- What happens next: collection on the registered block, results post
  with the ledger reconciled.

## Checklist before posting

- [x] Owner sign-off on the misalign-v4 item text recorded in §6 (2026-10-10)
- [ ] Outsider read of the final draft (§0 above; `CLAUDE.md`, "Write
  for readers outside the program"): a fresh agent with no project
  context lists every term it cannot define and every sentence it cannot
  parse, and each is fixed
- [ ] `REGISTRATION.md` status header flipped to published, with the date
- [ ] `FREEZE.json` re-written at publication; status field updated
- [ ] `DESIGN.md` folded into the registration and removed
- [ ] README study index row 4 updated with the post link
- [ ] Journal entry recording the publication
- [ ] The Gate 1 and gates data in a tagged release (`data-YYYYMMDD`)
