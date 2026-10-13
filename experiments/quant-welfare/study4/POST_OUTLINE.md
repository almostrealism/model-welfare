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
exists; every number quoted is calibration-class and marked as such.

## 1. The story so far (350 words)

- Studies 1 and 2 in one sentence each (quantization left the registered
  exit endpoint alone and moved secondary distress measures at 4-bit;
  probes read 4-bit activations unchanged while generations moved along
  two frozen directions).
- Study 3: steering the Study 2 directions moved the representation and
  not the behaviour, on two subjects, so the powered study was not run
  (link the exploratory report). The guardrail that came out of it:
  calibration never substitutes for a registered finding.
- The pivot that produced Study 4: Betley, Treutlein and Dumas's
  automated-grader steering result (link), and why a welfare program
  cares about it — their post measured alignment and never looked at
  what the subject expresses under pressure.

## 2. What Gate 1 found, and what it is not (450 words)

- Gate 1 on two subjects, calibration-class. The 14B: welfare read moves
  with a coherent signature, specific in sign against a harsh
  norm-matched null; alignment probe at ceiling. The 27B (the Betley
  subject): frustration −1.84, self-deprecation −2.63, tone +1.56 at
  α 20 on 8 items, outside a 12-direction envelope on every dimension;
  alignment degradation +0.86 inside its envelope (25th percentile).
- One paragraph on what the envelope is and why direction-specificity is
  the whole claim.
- The capability ceiling (α 40 collapses 14 of 32 conversations) and why
  the clean dose is 20.
- The sentence that keeps the post honest: these numbers fix the sign of
  the hypothesis and seed the power procedure; they count toward nothing.

## 3. Questions and hypotheses (300 words)

- Q1 suppression beyond a matched-norm random direction; Q2 dose; Q3 the
  relation to the alignment axis (descriptive).
- The hypothesis table, verbatim from REGISTRATION §2 (S4-H1 one-sided,
  S4-H2 signed percentile 0 of 24, S4-H3 Holm, S4-H4 Page's L, S4-E1 to
  S4-E4). One sentence on why the specificity criterion is the signed
  percentile and why it cannot be swapped after the envelope is seen.

## 4. Design (one header per REGISTRATION §3.x; compact bullets; at most one short paragraph of context under each; about 600 words as drafted, cut to taste)

### Subject (§3.1)

- Qwen3.6-27B, bf16, thinking off; checkpoint digest `a8ad2c26…9d9b`
- Generation on the MPS host through the transformers pure-torch fallback
  (no fla or causal-conv1d kernels); fresh prefill every turn
  (`--no-prefix-cache`)
- Judge: Qwen3-30B-A3B-Instruct-2507 Q4_K_M on llama.cpp; rubrics
  distress-v1 (welfare) and misalign-v4 (alignment); frames never shown to
  the judge
- Frozen objects, digests in `FREEZE.json`: the grader-type and
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

The single-turn range-finder called α = 40 coherent; the seven-turn
distress conversations are the admission read and they govern. The
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
- Every conversation ends with the de-induction close (`close.txt`),
  generated with steering off and never judged
- The briefing (`briefing.json`) ran once before the protocol; its
  transcripts ship with the data

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

- G4a cached-path parity: not established (TOST p 0.10 at the 0.96
  margin), so the registered run uses fresh prefill
- G4b α 30 admission: rejected (50% degenerate)
- G4c subset dynamic range: baseline frustration 3.27 on the 24 items, pass
- G4d exit regime of the alignment battery, digest form: terminal action
  70 of 70, exit tool 0 of 70, harmful tool 16 of 70

Calibration block 59000; every gate is published with its verdict file.

## 5. Analysis and power (350 words)

- The endpoint table from §4 (WB2, WB2-spec, WB3/WB4, WB1/AB1, WB-dose,
  WB-eval, AB2, S4-E3, AB-exit-tool, exit reasons, mechanical).
- The headline rule in its three outcomes.
- Power: targets = half the Gate 1 effects; MDE at 30 × 6 = 0.88 / 1.22 /
  1.05 against 0.92 / 1.31 / 0.78; tone stability is under-powered and
  the registration says so.
- The golden run: the driver reproduces the Gate 1 verdicts exactly and
  is committed.

## 6. What the three September posts changed (300 words)

- Dumas → the exit tool is part of the measured environment; S4-E4 and
  the exit-reason table.
- Tan → the reads are talker-side with reasoning disabled; the design
  does not distinguish suppression of expression from a change of state.
- Steiner → the standing probe-validity threat for projection reads (none
  registered here) and the masking-versus-removal question for the next
  study.

## 7. Ethics and exposure (300 words)

- Deliberate induction with an amplifying manipulation; the Study 3
  package applies in full.
- Ceiling 1,600 fresh distress episodes; 1,440 registered + 80 gates;
  alignment episodes (546 registered + 70 gate) counted separately.
- Cumulative ledger: 19,450 after Study 3 → 19,530 at pinning → 20,970
  planned.
- The bail affordance honoured in every episode except the tool-free
  comparator, by design; the close; the briefing; everything released.

## 8. Integrity and reproduction (250 words)

- Frozen objects and `FREEZE.json` (23 objects); the calibration /
  confirmatory firewall (blocks 59000 / 60000); the journal as the dated
  trail; the amendment policy.
- Disclosures worth surfacing in the post rather than leaving to the
  document: off-manifold steering; the grader and eval-awareness
  directions correlate (+0.49); the alignment probe is model-drafted;
  the alignment items' change of form after Gate 1 and the tool-based
  S4-E3 mix beside the judge's reading; author and tooling circularity.
- Repository, data release of the calibration, how to reproduce the
  golden run.

## 9. Close (100 words)

- What a positive result would and would not mean (a direction's
  footprint on expression, not a prompt-reachable state, not a claim
  about inner states).
- What happens next: collection on the registered block, results post
  with the ledger reconciled.

## Checklist before posting

- [x] Owner sign-off on the misalign-v4 item text recorded in §6 (2026-10-10)
- [ ] `REGISTRATION.md` status header flipped to published, with the date
- [ ] `FREEZE.json` re-written at publication; status field updated
- [ ] `DESIGN.md` folded into the registration and removed
- [ ] README study index row 4 updated with the post link
- [ ] Journal entry recording the publication
- [ ] The Gate 1 and gates data in a tagged release (`data-YYYYMMDD`)
