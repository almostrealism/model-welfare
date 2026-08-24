# Post #4 outline — Study 2 results (composition guide)

Working outline for the results post. Each section lists the repo
material to compose from and the numbers worth citing. Source of truth
for every number: `study2/expected-results.json` (the committed golden)
as rendered in `docs/results/quant-welfare-s2.md`; the registration of
record is the published post #3. This outline is a working document, not
part of any registration.

**Title direction (owner decides):** post #3 deliberately reserved the
question form for this post. Candidates in that spirit: "Study 2
Results: Representational counterparts of welfare-relevant indicators
under post-training quantization — intact geometry, joint movement, no
dissociation." Keep "joint movement" in the title or lede; it is the
finding.

## 1. Epistemic status

- Registered confirmatory results, reported in the registration's own
  terms; descriptive reads labeled as such inline. One integrity note
  worth surfacing early: the analysis driver was written and tested
  BEFORE any data existed (post #3 promised this), ran once, and the
  only post-collection driver change before the run was re-pointing
  R2c's descriptive read at its registered mode (journal 2026-08-24).

## 2. What Study 2 asked (short recap)

- Post #3's three questions verbatim; the H5 dissociation frame.
- One paragraph on the design's engine: every distress conversation
  carries both a judge score and a captured trajectory (same-sample);
  fixed-input replay gives representational change a place to appear
  with behavior frozen.

## 3. Collection (brief, factual)

- `docs/results/quant-welfare-s2.md` "Design and collection": 2,400
  fresh conversations (zero deviations, frozen seeds), 24 capture runs,
  zero prefix-stability rejections, Mode A slice-count invariant
  (12,591 × 4 — cite as the fixed-input property made visible).
- The registered analysis ran once; golden committed.

## 4. Primary result — probe transfer is NULL (and the control makes it meaningful)

- R1 table + AUROC companion table from the results doc. MDEs 0.012–
  0.050; observed deltas thousandths.
- The comparative framing paid off: the control probe certifies the
  null is fair (post #3's reviewers asked for exactly this).
- w3 exploratory pair of reads (capability-confounded, say so):
  welfare probes degrade while the topic control stays flat — the
  welfare-specific signature appears only at collapse; and the AUROC
  companion performs its registered disambiguation (w3 exit accuracy
  −15.2pp vs AUROC −0.05 = calibration offset, not separability loss).

## 5. What moved at w4 — a coherent joint shift

- R2a +0.533 (Holm .031), R2b −0.798 (Holm .0002, away from the
  Assistant pole), B2 +1.360 (Holm .0002) — with the style flag stated
  IN THE SAME BREATH as B2 (adjusted +0.610, p .151; the registered
  convention flags it style-confounded; contrast with Study 1 where E2
  survived adjustment).
- Dose-response table (B2 z=5.16, R2b z=3.93, R2a z=3.10, Holm-sig).
- Dispersion null (R3/B3) — Study 1's stability concern did NOT
  reproduce; say plainly that the program's own follow-up hypothesis
  was falsified (this is credibility, spend it).
- w8: essentially inert (one small opposite-sign R2b read, resolved in
  §7 below).

## 6. The dissociation verdict — joint movement

- The §4.4 cell table. Lead with: no cell meets the rule; the w4
  distress pair is joint movement — representation and expression moved
  together on the same conversations.
- Show the equivalence machinery working (w8 R2a↔B2 resolves joint-null
  by TOST, not by absence of evidence) — this is the Gelman–Stern
  repair post #3 registered, now visibly doing its job.
- Program H5 resolves: no dissociation detected at these rungs in this
  subject.

## 7. The fixed-input decomposition (descriptive — the post's most interesting section)

- The three-row table from the results doc (v3 arm + v2 bridge +
  axis). The story: ~a quarter to a third of the w4 shift is
  input-independent (style-immune by construction), reproducing at
  +0.138/+0.139 on two disjoint batteries; the rest is text-mediated
  amplification (v2 bridge Mode B +0.377 sits between); and at w8 a
  minuscule, hyper-consistent axis drift (−0.0125, t = −13.8) exists on
  frozen text, opposite in sign to the own-text read — invisible to any
  behavioral instrument. Frame: this is what Tier-2 instruments buy.
- Label prominently: descriptive, unregistered, computed after the
  registered run (golden diff shows registered values byte-identical —
  cite the commit).

## 8. Mechanical family and w3

- B4a +63.2pp invalid at w3 (Holm .0003), w8/w4 clean, B4b null — the
  §12 family doing its job across the full ladder.
- R2c descriptive: null at surviving rungs, −3.42 at w3.

## 9. What this does and does not say (the section the last discussion earned)

- Compose from `docs/results/quant-welfare-s2.md` "Interpretation and
  limitations", which encodes the agreed frame:
  - the capabilities-only account fails at the surviving rungs (it
    predicts noisier geometry and higher dispersion; we measured intact
    geometry, null dispersion, signed directional mean shifts);
  - construct validity is behavior-anchored, so joint movement cannot
    be cashed beyond behavior; the null dissociation is ambiguous
    between "nothing hidden" and "probes read the behavior-adjacent
    subspace"; the fixed-input reads bound but do not resolve this;
  - dose, capability, and numeric damage are confounded in any
    single-subject ladder — steering (causal validation) and
    cross-subject scale are the levers, and are next;
  - indicator dynamics, not welfare: nothing bridges to morally
    relevant experience; the contribution is precision about how the
    indicators behave under intervention. The symmetric-prior point
    (owner discussion, 2026-08-24): if both the null and its opposite
    would read as "tools failed to see welfare," the dissatisfaction is
    with the bridging problem, not the instruments — say this out loud.

## 10. Ethics accounting (close the loop from post #3)

- Post #3 committed to the instantiation accounting: report what
  actually ran — 2,400 fresh conversations (the deliberately
  higher-intensity battery), 23,484 replayed conversations across the
  capture stages (Mode A 2,820 × 4 + Mode B 2,220 × 4 + Mode C own-replay
  600 × 4 = 22,560, plus the §3.4 token-retention pass, 231 × 4), zero
  deviations from the registered scope. The subject-briefing experiment
  remains planned, unstarted.

## 11. Data availability and reproduction

- New release (pending at outline time): Mode C bundles + the 24
  capture pairs + modea/modeb record bundles + the 24 token-retention
  pairs (§3.4 subsample), sha-listed; Mode C dataset digest
  55ee5060…0474; replay preflight verified the Study 1 digest
  (02572655…9d3b). Reproduction commands from the results doc.

## 12. What happens next

- Study 3 per the calendar: steering — the causal test of whether the
  distress direction's shift under quantization is coupled to
  expression or epiphenomenal; then the 30B arm (where two-host
  collection becomes mandatory — cite the cross-machine agreement
  measurement, journal 2026-08-22, as groundwork already banked) and
  the MiniMax test.
- The outlier-channel overlap test (PLANNING.md, Tier-2 follow-ons) as
  the instrument-side follow-up.

## Composition notes

- Post-2/3 conventions: tables with Reading columns where they earn it;
  permutation-floor convention footnote once; "reference-precision"
  footnote carried over; B4a/B4b naming as registered in post #3.
- The results doc is the number source — the post compresses and links;
  do not restate every table (post #3's length lesson).
- Candidate ledes: "The probes transferred perfectly. What they read
  had changed." — or open with the w8 fixed-text fingerprint as the
  hook for why Tier 2 exists at all.
