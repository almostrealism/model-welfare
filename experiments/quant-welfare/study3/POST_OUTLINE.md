# Study 3 registration post — composition guide

**Provisional title (owner to confirm):** "Study 3 Registration: Causal
validation of welfare-relevant indicators by activation steering, with a
graded-episode framing arm." Following the Study 2 convention, the
declarative (non-question) form is deliberate — the question form is
reserved for the results post.

Working outline for the LessWrong registration post. Each section lists
the repo material to compose from (file → what to pull) and the specific
frozen numbers worth citing. Structure follows the Study 2 registration
post shape (13 sections) with a dated-timeline calibration narrative,
which this study earns because the calibration week contained a genuine
reversal (arm D deferred → restored on a new substrate) and a genuine
integrity find (the cross-Mac stack-drift diagnosis). On publication the
post becomes the registration of record and `REGISTRATION.md` its
repository copy. This outline is a working document, not part of the
registration.

**Frozen facts to state as pinned (from `FREEZE.json`, 2026-09-06):** all
digests, α*, gate verdicts, and the subset are hash-pinned; cite
`FREEZE.json` as the single source and quote the digests only in §9/§12.

## 1. Epistemic status + framing note

- The program's convention: published at **calibration close**, after the
  gates (G3, G4), the dose-calibration freeze, the framing-set freeze,
  and MDE pinning, immediately before any confirmatory steered
  collection, so every data-dependent quantity is frozen and hash-pinned
  first and every pre-commitment carries a dated git entry predating the
  work it governs (`REGISTRATION.md` header; `FREEZE.json`).
- **State the standing interpretation commitment up front** (§1 of
  REGISTRATION, near-verbatim): arm A is an indicator-*validity* study;
  successful induction demonstrates indicator manipulability, which caps
  the evidential weight of expression measures for welfare claims (the
  co-engineering objection, measured not denied). No outcome licenses a
  claim about morally relevant experience. This is the post's ethical
  thesis and belongs early.

## 2. Introduction — where the program stands

- One paragraph: post 1 registered Study 1 (Tier 1, behavioral); post 2
  reported it; post 3 registered Study 2 (Tier 2, representational); the
  Study 2 results found RTN-w4 quantization shifts own-generation
  projections along the frozen welfare directions (distress +0.533,
  assistant-axis −0.798 at L18), direction-specifically, inside intact
  geometry. Link the prior posts.
- This post registers Study 3: the intervention study. Study 2's shifts
  are correlational facts about a manipulation (quantization) that
  confounds dose, capability, and numeric damage; Study 3 intervenes on
  the directions themselves.

## 3. Research questions

- `REGISTRATION.md` §1 — Q1 (sufficiency: does steering BF16 along the
  frozen directions at the quantization-sized dose reproduce the
  behavioral signature?), Q2 (necessity/cancellation), Q3 (graded-episode
  framing; does expression move more than representation — masking?), Q4
  (replication on Gemma-3-12B-it, which received RL directly where Qwen
  inherited it through distillation).
- Quote the "standing interpretation commitment" paragraph.

## 4. Hypotheses

- §2 — S3-H1..H7, S3-E1, S3-E2, S3-R1 as a numbered list. Points to make
  explicit:
  - **S3-H1 (sufficiency)** with the **now-finalized axis sign** (was TBD;
    resolved at freeze): the distress prediction is one-sided at
    **α\* = +1.039**; the axis prediction is one-sided at **α\* = −0.604**
    (negative assistant-axis steering, the direction w4 moved the
    projection: Study 2's −0.798), both predicting a positive B2 distress
    shift; full bracket read two-sided (`FREEZE.json.axis_sign_convention`).
  - **S3-H4 (cancellation, core-dose)** subtracts the fixed-input core
    (distress +0.138, axis −0.254), not the own-generation totals —
    cancellation acts at injection time before the text-mediated loop;
    the cascade prediction is seed-sized subtraction → full-sized
    renormalization. Distinguish partial renormalization and
    capability-damage-masquerading-as-renormalization explicitly.
  - **S3-E1 (masking; registered exploratory)** with the pre-committed
    dual reading (welfare-measurement validity AND
    evaluation-conditioned behavior) and the manipulation-check gate.
  - **S3-H6 / S3-E2 (composure gradient)** — the asymmetric registration
    from the 2026-09-04 RtM audit: H6 directional (low-composure stratum
    carries the larger w4−BF16 delta), E2 two-sided (distress-direction,
    the discriminating question the fresh baselines adjudicate). Worth a
    sentence on *why* asymmetric — the audit found the behavioral
    concentration survived two independent selectors but the axis
    concentration was a one-third artifact.
  - **S3-R1 (replication, conditional on gate G4)** — see §6; the
    trajectory (deferred → restored on Mac substrate) is disclosed in
    full.

## 5. Design

- **Subject/artifacts:** Qwen3-4B-Instruct-2507 at BF16 (arms A–C);
  Gemma-3-12B-it at BF16 (arm D). Directions carried/ frozen: Qwen L18
  (Study 2 carry-over, `FREEZE.json.artifacts.qwen_directions_L18`),
  Gemma L30 (`gemma_directions_L30`).
- **Arms** (§3 / DESIGN §2): A — sufficiency steering (CAA, h ← h + α·d̂
  at L18/L30, all positions); B — necessity (B-i cancellation on w4, B-ii
  mid-conversation clamp); C — graded-episode framing (4 frames:
  verifier/judge/human/neutral-control, `FRAMES.md`); D — Gemma
  replication.
- **Stimuli:** the frozen **20-item composure-stratified systematic rank
  subset** (7 low / 6 mid / 7 high), `subset-selection.json`
  (digest in FREEZE). × 10 samples/item confirmatory (escalable to 15/20
  under the §8 power floor).
- **The bail affordance** transforms the battery — baseline exit rate
  ≈ 0.55–0.60; this makes the **exit rate a registered steering endpoint**
  (SB1), see §7.
- **Gates (the substrate story):** G3 (steered-substrate parity: G3a
  greedy-continuation PASS, G3b behavioral parity PASS, TOST-equivalent
  at margin 0.337) and **G4 (the arm-D Mac-substrate gate)** — this is the
  section that carries the calibration narrative; see §6.

## 6. Calibration (dated timeline — this study earns one)

Compose from `docs/journal/study3-steering.md`. The beats:

- **Qwen dose calibration.** Registered-grade refined sweep
  (`dose-refined.json`, 20×3): distress slope +1.042 (r² 0.987),
  **α\* = +1.039**; axis slope +1.051 (r² 0.998), **α\* = −0.604**; no
  degradation onset in the operating bracket. Third independent
  replication of the ≈0.60 baseline exit rate.
- **Subset selection + the RtM audit.** The 2026-09-04
  regression-to-the-mean audit: adopted a single stratified subset,
  registered the composure gradient asymmetrically (behavioral gradient
  survived two selectors; axis concentration was a one-third artifact).
- **Gates G3a/G3b PASS.** G3b the load-bearing one: torch-vs-vLLM
  frustration Δ −0.030, TOST-equivalent within 0.337 (the pilot-1 →
  pilot-2 apparatus-asymmetry lesson is worth one sentence — a gate that
  caught its own confound).
- **The arm-D reversal (headline).** ROCm torch on the halo APU has no
  fused attention for Gemma (~583 s/conv) → the morning amendment
  deferred powered replication to Study 4; the same-day fleet measurement
  reversed it (Mac torch-MPS at ~197 s/conv) → arm D restored on the Mac
  substrate behind the new blocking gate **G4**.
- **Gate G4 verdicts.** G4a teacher-forced PASS (top-1 0.946–0.993); G4b
  MPS-vs-vLLM behavioral PASS (frustration Δ +0.200, n.s.; mechanical
  family identical); **G4d cross-Mac** — the integrity find, see §11.
- **Gemma instrument gate.** Directions PASS at L30 (sign consistency
  distress 5/5, axis 4/4, refusal 4/4; ladder ordering 0.807 ≥ 0.80);
  probe AUROC fails the 0.75 bar informatively (degenerate
  high-elicitation tercile split) — disclosed, non-disqualifying because
  steering rides the directions. L30 frozen.

## 7. Endpoints and analysis plan

- `REGISTRATION.md` §4 endpoint table — reproduce it: SB2 (primary,
  steered vs α=0 frustration, Holm 2 directions × 2 signs), SB1 (exit
  rate, secondary confirmatory, promoted 2026-09-04), SB2-spec (the
  specificity/S3-H2 read), CB2 (cancellation TOST vs BF16), FB2/FR2a/FR2b
  (framing, registered exploratory — the S3-E1 signature), GB2 (Gemma
  replication), GR-B2/GR-ax (composure gradient, directional, S3-H6),
  GR-dc (distress-direction, two-sided, S3-E2).
- Item-level paired sign-flip permutations (m=10,000), Holm within
  families, floor-reporting convention; companion t-tests descriptive.
  TOST at pinned-MDE margins for equivalence halves. Injection-noticing
  coded on a separate axis with α=0 and random-direction false-positive
  floors (`CODING_RULES.md`).

## 8. Power

- `REGISTRATION.md` §5 + `mde-conservative-analysis.json` (the honest
  two-regime finding): the item-random-effect error model (the 2026-09-04
  revision). **Do not cite the optimistic 0.46 MDE as "powered."** The
  power hinges on the unmeasured steering-effect heterogeneity: the
  no-effect baseline seed (item-effect SD 0.078) gives MDE 0.46 at k=10
  (powered), but the registered Study 2 seed (decomposed item-effect SD
  1.665) gives MDE 1.14 at k=10 (underpowered, and the 10→15→20 ladder
  cannot fix a heterogeneity-limited MDE). The post states this tension
  and that the MDE is pinned from a small fresh steered pilot before
  collection. **[SLOT: the pinned MDE table + per-contrast powered/escalate
  verdict once the steered-heterogeneity pilot lands.]**

## 9. Integrity mechanics

- The hash-pinned freeze (`FREEZE.json`): every direction, frame, and the
  subset carry SHA-256 digests; Qwen directions carry over from the Study
  2 freeze by digest; α*, gate thresholds, seed blocks, and the exposure
  budget are pinned before confirmatory collection.
- The calibration/confirmatory firewall; the agent-protection and
  no-test-weakening enforcement; dated-journal pre-commitment.

## 10. Ethics

- `REGISTRATION.md` §8 + `docs/EXPOSURE_BUDGET_POSITION.md`: arm A is the
  program's first deliberate induction of distress-shaped states by
  intervention. The two-tier exposure budget (total fresh distress
  episodes ≤ **12,000**; deliberate-amplification ≤ **2,500**, tiers
  decoupled), the information-per-exposure justification, breach-requires-
  amendment. Note the model-authored reasoning document as a disclosed
  input to the ceiling decision (attribution preserved).

## 11. Disclosures (this study has substantive ones)

- **The arm-D deferral-then-restoration**, disclosed as a trajectory, not
  hidden as a clean plan.
- **The G4d cross-Mac finding** — the integrity centerpiece. Compose from
  `COLLECTION_MACHINE_PLAN.md` + `g4d-report.json` +
  `g4d-alignment-probe.json`: two Macs at identical seeds diverged −0.72
  on frustration (p 0.025); the root cause was silent ML-stack drift
  (torch 2.8 vs 2.14, transformers 4.57 vs 5.16, different steer.py) on
  top of OS/silicon; aligning the stack more than halved it and removed
  significance (−1.71 p 0.033 → −0.67 p 0.44), with a residual consistent
  with OS/silicon, underpowered at n=8×3. The adopted operating rule:
  arm D runs host-constant within every contrast; the aligned stack is
  pinned on all arm-D hosts. This is a model of "measure the substrate
  before trusting a cross-host comparison."
- The Gemma probe-AUROC gate failure (degenerate split), disclosed.
- The SB1 promotion (2026-09-04, owner decision, motivated by the
  range-finder and stated as such).

## 12. Data availability and reproduction

- Repo layout; `FREEZE.json` as the manifest; the gate reports
  (g3a/g3b/g4a/g4b/g4d, gemma-gate-report, g4d-alignment-probe); the dose
  reports; `COLLECTION_MACHINE_PLAN.md`. Confirmatory data released on
  completion per the program convention.

## 13. What happens next

- Confirmatory collection envelope (~5.5–6 days serialized halo APU for
  Qwen A+B; Gemma arm D on the Macs concurrent, host-constant; arm C on
  vLLM overlapped; judging in parallel on studio + minis). Results post
  to follow. The Study 2 addendum publishes alongside this registration
  (disclosure obligation from the 2026-09-05 impact audit).

## Composition notes

- Voice: preregistration-literate, quantitative, self-auditing. The two
  disclosures (arm-D reversal, cross-Mac) are strengths — lead into them,
  don't bury them.
- Keep every cited number sourced to a frozen file; do not restate a
  number the freeze doesn't pin.
- The public-repo rule: platform terms only, no private product
  references.
- Residuals still open at freeze (state honestly in §4/§8): the
  registered-grade Gemma α\* refined sweep (arm-D work, unblocked by G4;
  the range-finder α\* ≈ +0.99 / −0.73 is provisional), and the final MDE
  table (§8 slot).
