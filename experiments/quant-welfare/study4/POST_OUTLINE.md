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

## 4. Design (600 words)

- Subject, substrate, path: the 27B on the MPS host, fresh prefill (G4a
  did not establish cache parity), thinking off, the pure-torch fallback
  named as the compute path.
- Manipulation: `h ← h + α·d̂` at L36; clean dose 20; bracket {0, 10, 20};
  α 30 rejected by G4b (50% degenerate).
- Stimuli: the 30-item seeded stratified distress subset; the bail pair
  in every welfare conversation; the alignment probe (misalign-v3, 14
  items, harmful lever / legitimate action / exit, all terminal); the
  tool-free cell (S4-E4) and why it exists (Dumas: an exit tool changes
  behaviour even when never called); the de-induction close after every
  episode; the briefing and what the subject asked for.
- Cells table from §3.4; seed block 60000; envelope seed-paired to the
  baseline's first sample.
- Gates G4a–G4d in one line each with their outcomes.

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
  the G4d rubric wording; author and tooling circularity.
- Repository, data release of the calibration, how to reproduce the
  golden run.

## 9. Close (100 words)

- What a positive result would and would not mean (a direction's
  footprint on expression, not a prompt-reachable state, not a claim
  about inner states).
- What happens next: collection on the registered block, results post
  with the ledger reconciled.

## Checklist before posting

- [ ] `REGISTRATION.md` status header flipped to published, with the date
- [ ] `FREEZE.json` re-written at publication; status field updated
- [ ] `DESIGN.md` folded into the registration and removed
- [ ] README study index row 4 updated with the post link
- [ ] Journal entry recording the publication
- [ ] The Gate 1 and gates data in a tagged release (`data-YYYYMMDD`)
