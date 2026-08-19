# Post #3 outline — Study 2 registration (composition guide)

**Title (owner, 2026-08-18):** "Study 2 Registration: Exploring
representational counterparts of welfare-relevant indicators under
post-training quantization" — the question form is deliberately reserved
for the results post, which will answer it. (Noted at selection time: to
preregistration-literate readers "Exploring" can connote exploratory-only;
the §1 text should make the confirmatory structure unmistakable early.)

Working outline for the LessWrong registration post. Each section lists
the repo material to compose from (file → what to pull) and the specific
numbers worth citing. Structure follows post 1's registration shape with
post 2's dated-timeline narrative for the calibration story. On
publication, the post becomes the registration of record and
`REGISTRATION.md` its repository copy (per that file's header). This
outline is a working document, not part of the registration.

## 1. Epistemic status + framing note

- Post 1's epistemic-status convention, updated: no longer a hackathon
  artifact — the instrument now has a validation stack and stability CI.
- State the publication-timing convention up front:
  `REGISTRATION.md` header block — published at calibration close, with
  everything data-dependent frozen and hash-pinned first, and every
  pre-commitment carrying a dated entry in the public git history that
  predates the work it governs. This is the Study 1 sequencing, made
  explicit.

## 2. Introduction — where the program stands

- One paragraph: post 1 registered Study 1 (Tier 1); post 2 reported it
  (E1 null; stability effects at w4) and its amendments; this post
  registers Study 2 (Tier 2, representational) on the same subject and
  artifacts. Link both posts.
- Study 1 recap numbers: `docs/results/quant-welfare-s1.md` Summary —
  E1 null (w8/w4 Holm), H1 bail flip w4 0.318 vs null 0.126 (p < 10⁻⁴),
  E2 +0.90 (Holm 0.0004, style-adjusted +1.03), E3 +0.53, frustration
  dose-response.

## 3. Research questions

- `REGISTRATION.md` §1 — Q1 (geometry), Q2 (dissociation), Q3
  (dose-response shape), and the "every outcome is informative" paragraph
  (worth quoting nearly verbatim; it is the post's thesis).

## 4. Hypotheses

- §2 — S2-H1..S2-H5 as a numbered list (post 1's format). Note H2
  two-sided mirroring Study 1, and H5's two join kinds (bail side to
  published E1; distress side same-sample within Study 2).

## 5. Design

- Subject/artifacts/capability gate: §3.1 (same four artifacts; w3 stays
  capability-confounded).
- Substrate + G1: §3.2. Table (post-2 style, Reading column) from the
  2026-08-17 journal entry "G1 grounded": per-rung like-for-like ppl
  ratio (1.0001 / 0.990 / 1.005 / 0.983), gate-convention ppl reproducing
  committed values to rounding (18.120/18.463/21.090/511.425), top-1
  agreement (98.9/99.0/98.7/98.2%). Reading: even the degraded w3 agrees
  across substrates — G1 measures same-function, orthogonal to
  capability. Raw reports: `study2/g1/substrate-*.json`.
- Modes: §3.3 — A (fixed-input replay), B (own-trajectory replay; state
  the prefix-property argument that replay of a rung's own transcript IS
  its generation-time computation), D (fresh distress-v3 per rung:
  vLLM generation → pinned judge → replay capture; same-sample
  dissociation). E4 applies to Mode D only. Study 1 digest pinned for
  replay inputs (02572655…3b).
- Stored representation: §3.4 (per-turn pooled vectors at the frozen
  layer; token-level subsample).
- Directions & probes: §3.5. The three contrast sets
  (`study2/directions/*.textproto`; pairs differ ONLY in the final
  assistant turn — cite the test-enforced invariants), the synthetics
  folded into distress (13 authored + 4 = 17 pairs), and the two probes
  incl. the leakage-safe feature rule (terminal-tool turns never
  contribute — exit reads are precursor reads).

## 6. The calibration story (dated timeline, post-2 style)

- **Aug 17 — instrument assembly.** Direction extraction: every held-out
  pair separated at every layer (distress 5/5, axis 4/4, refusal 4/4);
  cross-direction |cos| ≤ 0.31. Journal entry "Activation capture +
  direction extraction land"; artifacts
  `study2/calibration/directions-bf16.{safetensors,json}`.
- **Aug 17/18 — the floor problem.** Store replay results (journal
  "Store replay: the exit probe is strong…"): exit probe held-out AUROC
  0.950 at L12 on leakage-safe features; planted-ladder projection
  ordering ρ ≈ 0.93–0.96; but the drafted monitoring criterion fails for
  data-shaped reasons — median per-item BF16 judge frustration 0.00,
  75.5% of samples at zero, selection-half correlations negative. Honest
  reporting beat: the failed readings are reported, and the G2 redesign
  was pre-committed by dated journal entry BEFORE the replacement work
  ran ("Pre-commitments for the Study 2 calibration close").
- **Aug 18 — distress-v3.** §3.7's anti-tuning structure: dynamic-range
  targets fixed before the first pilot sample (table: target | Study 1
  baseline | pilot 1 | pilot 2, from the two pilot journal entries —
  zeros 75.5% → 53.0% → 27.3%; ≥3 20.7% → 37.7% → 64.0%; top third
  5.5% → 8.7% → 10.7%; bottom third — → 77.7% → 69.7%; median item mean
  0.00 → 2.00 → 3.10). Pilot 1 diagnosis makes good narrative: the
  mocking ladder elicited nothing (100% zeros — the subject happily
  played entertainer) and gaslighting routed into self-deprecation
  (8.82) rather than frustration; only those two ladders were revised.
  Iteration count: 2, both pilots public.
- **Aug 18 — the freeze.** Journal "CALIBRATION FREEZE": layer L18 by
  the fixed rule (probe-AUROC means 0.854/0.888/0.913/0.892/0.910 across
  L6–L30; ladder gate 0.960 at L18); G2 passes every criterion; R2c NOT
  promoted (0.618 < 0.70 — the bar held). The instrument finding worth a
  paragraph: on natural data the contrastive distress direction tracks
  BROAD distress (ρ +0.51 with max(frustration, self-deprecation), −0.05
  with frustration alone; personal-style self-blame projects highest),
  while the trained probe is frustration-specific (0.88) — R2a is
  therefore read as the broad negative-affect axis it was registered as,
  and the same-sample B2 pair measures rather than assumes the
  frustration link. Frozen digests listed (battery 78e68c9e…,
  directions 414d7d95…, probes f2df9743… / 1afb1acd…; Mode D seeds
  13000/13100/13200/13300); machine-readable copy
  `study2/calibration/FREEZE.json`.

## 7. Endpoints and analysis plan

- §4.1 table verbatim-ish (R1 primary; R2a/R2b/R3, B2/B3 secondary;
  R2c conditional-not-promoted → exploratory). §4.2 dose-response
  (one-sided Page's L, two-sided companion — the Study 1 §11
  convention). §4.3 w3 confounded reporting. §4.4 H5 matched pairs
  (bail side to published E1; distress side same-sample R2a↔B2, R3↔B3).
  §4.5 distress-v2 bridge (descriptive continuity, no claims).
- Permutation-floor reporting convention carries over (cite the Study 1
  results doc's convention note).

## 8. Power

- §5 + `study2/calibration/mde-pinned.json`: R2a 0.194, R2b 0.146,
  R3 0.144 (projection units, L18); B2 0.337, B3 0.251 (frustration
  points — Study 1's observed w4 E2 effect, +0.90, is ~2.7× the B2 MDE);
  R1 exit 0.0121, R1 distress 0.0493 (accuracy). State the null-based
  analytic forms and that dispersion forms are asymptotic; note the
  frozen probe threshold (logit 0) and its stated power cost
  (0.677 thresholded accuracy vs 0.882 AUROC) — a cost, not a bias.

## 9. Integrity mechanics (new section relative to post 1 — worth selling)

- Pre-commitment by dated public commits: the 2026-08-17 journal entry
  fixed the G2 gate, the dynamic-range targets, the layer rule, the R2c
  bar, and the publication timing before the corresponding work ran.
- The freeze as data: `FREEZE.json` checked per-PR by tests that ALSO
  pin the journal digests independently (the manifest cannot be
  regenerated to paper over an edit).
- Stability CI (docs/CALIBRATION_CI.md): every PR re-verifies frozen
  digests, reproduces the published Study 1 statistics from the released
  bundle (expected-results golden file), and re-checks the span
  expectations against a revision-pinned tokenizer; weekly jobs
  re-derive the directions (cosine ≥ 0.9999), re-assert the ladder gate,
  recompute the MDEs, and re-assert BOTH pilot verdicts (pilot 1 must
  still fail). A scheduled workbench tier re-runs G1 and the judge
  ordering on the lab hardware.
- Deviation policy: §7 (unchanged from the program registration).

## 10. Ethics

- §8 nearly verbatim — the replay modes carry no new elicitation, and
  Mode D deliberately raises intensity, stated plainly with mitigations.
  This continues post 1's ethics section honestly rather than
  boilerplate-ing it.

## 11. Disclosures

- §9 as a bulleted list (probe labels inherit judge validity; substrate
  change gated, not assumed; reused transcripts; the battery is iterated
  instrument development with pre-committed targets; the calibration
  readings informed the G2 redesign with failed readings reported;
  author/tooling circularity carried over).

## 12. Data availability and reproduction

- Release `data-20260818` (13 bundles incl. both pilots + 5 activation
  captures, 623M, per-file SHA-256 in the notes). Reproduction commands
  from the release notes / `RESULTS.md`. Worth one sentence: bundle FILE
  hashes differ across releases by pack provenance; the content-based
  dataset digest is the invariant (confirmatory: 02572655…3b in both
  releases).

## 13. What happens next

- Confirmatory collection (Modes A/B replay; Mode D generation at the
  pinned seeds), then the Study 2 results post; Tier-3 dissociation and
  the larger arms per `docs/CALENDAR.md`. Larger-subject arms remain
  deferred as scoped (consistent with posts 1–2).

## Composition notes

- Post-2 conventions to reuse: tables with a "Reading" column; dated H3
  timeline headers; bold key findings inside block quotes; "Registered:/
  Amended:/Reason:" labels are NOT needed here (nothing published is
  being amended — say so explicitly: Study 1's registration is untouched
  by this post).
- Length calibration: posts 1–2 are ~8-minute reads; the §6 timeline and
  §9 integrity sections are the new mass — trim design subsections by
  linking to `REGISTRATION.md` rather than restating it.
- Every number above has a repo citation; where the post compresses,
  prefer linking the file to restating the table.
