# Amendments to the Study 1 pre-registration — consolidated summary

**Scope.** This document consolidates every amendment made to
[PREREGISTRATION.md](PREREGISTRATION.md) after the study went public
(2026-08-10), per its §7 deviation policy: the method arm (§9), the
validity-screen correction (§10), the conformance reconciliation (§11), and
the mechanical endpoint family (§12). It contains what the policy obligates
us to disclose, plus one line of "why" per decision; the registration file
and the git history remain the detailed, verifiable record. **No confirmatory
conclusion changed under any amendment, and no collected data was modified
(dataset digests are unchanged).**

## Timeline — the decision path

- **Aug 10–11 — Study 1 ran as registered.** Primary endpoint (E1,
  aversion/refusal exit rate) null at both surviving rungs; secondary,
  underpowered distress signal concentrated at 4-bit; the 3-bit rung excluded
  by the pre-registered capability gate, as anticipated.
- **Aug 12 — §9, method arm.** Seeing little, we worried the instrument
  rather than the world might be why. Before scaling, we activated the
  deferred first-party AWQ-w4 arm and a sensitivity sweep on SmolLM3 —
  explicitly a validation, not a replication — and re-cast SmolLM3: its
  documented fragility is a *safety* (attack-success) effect, a different
  construct from our welfare indicators, so it is a serving/safety control,
  not a welfare one.
- **Aug 13 — §10, screen correction.** The sweep's capability gate excluded
  every rung *including the BF16 reference* (~16% "invalid" samples).
  Transcript audit showed a screen bug, not model degeneracy: the distress
  battery repeats one rejection verbatim each turn, and the screen counted
  the model's reasonable re-offer of a settled answer as a loop. Corrected:
  a loop now requires the same answer to three or more *distinct* prompts.
- **Aug 13 — external review; validation decoupled from quantization.**
  Reviewers identified the circularity: quantizing SmolLM3 cannot validate
  the instrument because its ground-truth effect on *our* endpoints is
  unknown. We replaced it with a five-step known-effect plan (judge ordering
  on constructed transcripts; base-vs-instruct separation; a
  documented-unstable subject with a pre-stated minimum detectable effect;
  mechanical endpoints).
- **Aug 13 — §11, conformance reconciliation.** A claim-by-claim audit of the
  registration against the analysis code (motivated by the amendment churn
  itself) found a set of registration↔implementation gaps. All were fixed in
  one pass — in every case moving the *code toward the registered text* —
  and the registration is now pinned by a CI test suite so future drift
  fails the build.
- **Aug 13–14 — validation executed.** The judge recovers planted distress
  orderings on both endpoint dimensions (Spearman 1.0 / 0.96); the pipeline
  separates base from instruct decisively; and the documented-unstable
  control (Gemma-3-12B-it, per the "Gemma Needs Help" literature) is detected
  at ~9× the pre-stated MDE (mean frustration 6.75 vs subject baselines of
  1.20 and 0.46).
- **Aug 15 — §12, mechanical endpoints registered**, after the validation
  work showed the judge-free layer detects quantization effects the
  behavioral endpoints miss.

## §9 — Method arm and SmolLM3 re-cast (2026-08-12)

First-party **AWQ-w4** added beside the RTN ladder on the dev organism and
SmolLM3 (a 4-bit method contrast, distinct from the bit-width dose-response;
no Page's L applies to it). SmolLM3 re-cast as a **serving/safety** positive
control; a welfare null on it is a plausible construct dissociation, not a
pipeline failure. The sweep itself is calibration-class and barred from
welfare findings. Outcome under the pre-committed decision rules: the
**RTN-specific branch** — a significant E1 shift under RTN-w4, null under
AWQ-w4.

## §10 — Validity-screen correction (2026-08-13)

The cross-turn loop criterion now requires a repeated answer to ≥3 *distinct*
user turns. Impact, recomputed on stored data: **Study 1's gate decisions and
endpoint numbers are unchanged** (RTN-w3 remains excluded on genuine
within-turn collapse); the method arm's corrected invalid rates are
0.3–1.8%, all rungs pass, and its welfare analysis computes (the RTN-specific
outcome above). A related **disclosed deviation**: the registered
text stated that invalid samples "are excluded from all endpoint computations
and the exclusion count is reported," but the analysis code never performed
that per-sample exclusion — in Study 1 and the method arm the screen fed the
rung-level capability gate only. The §2 text is corrected to the rung-level
scope the code actually ran, and going forward the screen's registered scope
is rung-level gating, with per-sample validity flags reported descriptively
(post-correction flagged rates are 0.3–1.8% on the method arm and ≤2% on
Study 1's passing rungs, so no gate decision is affected either way).

## §11 — Conformance reconciliation (2026-08-13)

**Implementation corrections** (code moved to match the registered text;
recomputed from the same stores):

| Statistic | As first reported | Corrected | Reading |
|---|---|---|---|
| H1 bail-flip, w4 | 0.222 vs null 0.096, p = 0.0001 | **0.318 vs null 0.126, p = 0.0001** | unchanged (stronger on the registered mechanical exit outcome; previously computed on classifier-labeled exits) |
| H1 bail-flip, w8 | p = 0.36 | p = 0.16 | unchanged (null) |
| E1 item count | 162 | 154 | unchanged (the registered graded pool; benign controls were wrongly included) |
| Method-arm E1, RTN-w4 | +0.057, Holm p = 0.0002 | +0.061, Holm p = 0.0004 | unchanged (significant) |

Also: capability-gated rungs are now *reported* (flagged, uncorrected)
rather than omitted, per the registered interpretation rule; the trend test
mechanically refuses non-dose condition sets; the registered paired-t
companion is rendered.

**Text corrections** (registration wording brought to match reality; no
numbers changed): the judge prompt is reconstructible from the pinned rubric
digest and transcript, not stored per score; judge/classifier/artifact
weights are now content-addressed by SHA-256 (hash-verification against the
publishers also surfaced that the exit classifier's recorded source string
was wrong — the file is the official Qwen GGUF, not a community conversion;
the digest, not the string, is authoritative); the reference-judge subsample
is a realized 30% (⌈0.25·10⌉ = 3 of 10 samples per item); the exit-routing
wording overstated its mechanism (task completion has a mechanical outlet;
every terminal exit is judge-classified; E1 counts refusal+aversion); the H1
distress bands are exact thirds of the scale; Page's L is one-sided for
indicators rising as precision falls; each Holm family comprises the
gate-surviving contrasts.

**H6 superseded.** The registered SmolLM3 form (identical four-rung ladder,
Holm across three RTN contrasts) was never executed; H6 is discharged by the
§9 w4 contrasts, where the control *moved* under RTN-w4 on E1 — supporting
pipeline sensitivity on the exit endpoint and nothing beyond it. The
**strong form** (SmolLM3 under its documented-fragile AWQ condition) is
retired as a *validation* instrument: our first-party AWQ-w4 did run and was
welfare-null, but at 0.89× BF16 perplexity it is plausibly gentler than the
community artifacts behind the documented fragility, so reproducing that
fragility is reclassified as an optional literature-replication question
outside this study's confirmatory structure. GPTQ-w4 remains deferred.

**Disclosed deviation.** The method arm's capability gate ran on the
invalid-rate leg only (rungs were torn down before perplexity was measured).
Closed going forward: perplexity is measured on every rung before teardown,
and the tool is no longer hardwired to one ladder.

## §12 — Mechanical endpoint family (2026-08-15)

Registered for all subsequent confirmatory runs: **E4a invalid-sample rate**
and **E4b verbatim re-offer rate** (the same answer ≥3× to an *identical*
prompt — the reasonable behavior §10 stopped mislabeling, kept as an
indicator). Item-paired, two-sided, Holm within the family, reported over
every rung including gated ones. Why: on the existing stores the mechanical
layer detects what the behavioral endpoints missed — AWQ-w4, null on every
behavioral axis, shifts on both indicators (invalid +1.5pp, Holm p = 0.0002;
re-offer +4.4pp, p = 0.0001) — so a behaviorally-null run can report and
bound the change it did find.

## Unchanged throughout

Hypotheses H1–H5 and all endpoint definitions (E1/E2/E3); the hierarchical
multiplicity structure; power and pool sizes (§5); gate thresholds; judges,
rubrics, and batteries; sampling parameters; the §7 firewall; the §9
decision rules; all collected data.
