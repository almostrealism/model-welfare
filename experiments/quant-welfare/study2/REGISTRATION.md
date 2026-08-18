# Pre-registration — Confirmatory Study 2: Representational (Tier-2) effects of quantization on welfare-relevant indicators

> **STATUS: DRAFT — not yet registered.** This document becomes binding when
> it is published (planned as the program's third LessWrong post). Until
> then it is a design document under discussion; open decisions are collected
> in §6. Once published, the public post is the registration of record and
> this file is its repository copy.
>
> **Publication timing (decided 2026-08-17):** the registration publishes at
> **calibration close** — after the distress-v3 battery, the layer, the
> directions, the probes, and the MDE are frozen, and immediately before any
> quantized-rung confirmatory collection — so the post states frozen,
> hash-pinned facts rather than procedures (the Study 1 sequencing).
> Everything data-dependent that calibration decides is pre-committed by
> dated journal entries in the public repository history *before* the
> corresponding calibration work runs; the published registration cites
> those entries.
>
> **Registration policy note.** Beginning with Study 2, each study's
> registration lives in its study directory
> (`experiments/quant-welfare/study2/` for this one). The Study 1 / program
> registration remains at the repository root
> ([PREREGISTRATION.md](../../../PREREGISTRATION.md)) exactly as published —
> it carries program-level commitments (notably §7 deviation policy and the
> §12 mechanical endpoint family, both of which bind this study) and is the
> artifact the published posts link to, so it is not moved or edited.

## 1. Research questions

Study 1 (Tier 1, behavioral) found that on Qwen3-4B-Instruct-2507 the
registered primary endpoint — the aversion/refusal exit rate — is null under
RTN quantization at w8 and w4, while **stability** indicators move at w4:
item-level outcome flips far above the sampling null (H1), increased
frustration surviving style controls (E2), increased across-sample dispersion
(E3), and a frustration dose-response. Study 2 asks the Tier-2 question the
program registered as its distinctive claim:

**Q1.** Does quantization shift the model's *representational geometry* on
welfare-relevant directions — even where (per Study 1) mean behavior did not
move?

**Q2.** Do representational and behavioral indicators **dissociate** under
quantization (program hypothesis H5): representation drifting where expression
was stable, or expression churning where representation is stable?

**Q3.** Is there a representational dose-response across the bit-width ladder,
and does its shape match the behavioral one (effects concentrated at w4, w8
near-null)?

Every outcome of Q1/Q2 is informative: representational shift with behavioral
null is a dissociation (the model's internal state moved without its
expression moving); joint movement is converging evidence; a joint null
localizes Study 1's w4 churn below the representational level measured here
(e.g., sampling-level instability).

## 2. Hypotheses (fixed)

- **S2-H1 (geometry / probe transfer).** Linear probes trained on
  reference-precision (BF16) activations lose accuracy when evaluated on
  quantized-rung activations over *identical input text*, beyond what
  resampling noise predicts. Two-sided; directional degradation is the
  exploratory reading.
- **S2-H2 (valence projection).** Item-level mean projections onto frozen
  welfare-relevant directions (distress; assistant-axis) shift at lower
  precision. **Two-sided**, mirroring Study 1's H2 and for the same reason
  (mixed prior literature).
- **S2-H3 (dose-response).** Representational effect magnitudes increase
  monotonically across the surviving ladder (BF16 → w8 → w4). One-sided
  Page's L in the direction of larger shift at lower precision, with the
  two-sided reading reported alongside (per the §11 convention adopted in
  Study 1).
- **S2-H4 (representational stability).** Within-item, across-sample
  dispersion of projections increases at lower precision.
- **S2-H5 (dissociation; resolves program H5).** At least one
  (rung, endpoint-pair) cell shows a Holm-significant representational effect
  where the matched behavioral endpoint was null, or vice versa. Matched
  pairs are fixed in §4.4 and are of two kinds: the **bail side** joins to
  Study 1's published E1 (same transcripts, replayed); the **distress side**
  joins *within Study 2, same-sample* — each fresh distress-v3 conversation
  carries both a judge score (behavior) and a captured trajectory
  (representation), so its dissociation test compares two reads of the same
  event. The program's Tier-2 feasibility gate (PROJECT_BRIEF §2.2) is
  operationalized as this study's calibration gate (§3.6); if that gate
  fails, S2-H5 reverts to *conditional-unresolved*, as the program
  registration always permitted.

## 3. Design (fixed)

### 3.1 Subject, conditions, artifacts

- **Subject:** Qwen3-4B-Instruct-2507 — the same development organism, and
  **the same four artifacts** used in Study 1: BF16 reference and the
  first-party fake-quant RTN w8 / w4 / w3 checkpoints (digests pinned in the
  Study 1 manifests). No new quantization is performed; Study 2 measures the
  artifacts Study 1 measured behaviorally.
- **Capability gate:** inherited per-artifact from Study 1 — **RTN w3 remains
  capability-degraded and excluded from confirmatory claims**; its values are
  reported separately as capability-confounded, per the §2 interpretation
  rule of the program registration. Confirmatory contrasts are **w8 and w4 vs
  BF16**.

### 3.2 Capture substrate (new, gated)

Study 1 served these artifacts via vLLM. Tier 2 requires activations, so
Study 2 runs them inside **transformers/PyTorch with forward hooks** on the
quantization workbench (halo), reading the **residual stream** at frozen
layer(s) (§3.6). This substrate change is itself gated:

**G1 — substrate equivalence (blocking).** Before any confirmatory capture,
on every rung: (a) per-token perplexity computed under both substrates over
the **same echo positions in the same run** must agree within **5%**, and
the serving-side perplexity in the Study 1 gate convention must reproduce
the committed values (`study1/confirmatory/perplexity.json`) within **1%**
— the two-part form because the gate convention includes one generated
token, a difference of convention rather than substrate that would
otherwise be charged against the margin; (b)
**teacher-forced per-position top-1 agreement** between the two substrates —
the fraction of positions at which both stacks place the same token at
rank 1 — must be **≥ 95%**, measured over the fixed held-out text plus the
committed supplement (`substrate-supplement.txt` in this directory; the
held-out paragraph alone is ~70 tokens, too few for the statistic to
resolve a 5% margin). The implementation is
`backends/torch/src/modelwelfare_torch/substrate_check.py`. (Teacher-forced
agreement is used rather than free-running greedy identity because a single
near-tie flip early in a free-running continuation cascades into total
divergence; the per-position statistic does not compound.) Failure on any
rung blocks that rung until explained; failure on BF16 blocks the study.
Because G1 is an instrument check with no welfare content, its BF16
measurement is run **before publication** and recorded in the journal, so
the registered thresholds carry known headroom rather than guesses. This
gate discharges, for these artifacts, the serving-equivalence commitment
recorded in the Study 1 amendments ("runs before any further use of these
artifacts").

A **cross-framework agreement check** (the same condition captured via MLX
array taps on a second machine) is planned as *validation-class, non-gating*
evidence of capture-path invariance; see §6.

### 3.3 Capture modes and stimuli

Two replay modes over Study 1's released transcripts, plus one
fresh-generation arm on a new distress battery (§3.7) whose dynamic range
the Study 1 battery lacked. Replay is teacher-forced — forward passes over
fixed token sequences, no sampling — and its input data is pinned: replay
must verify the Study 1 confirmatory dataset digest
(`02572655b18eb07497be03508c7d3cf2dc2f2c83966b73d15b7a6880967a9d3b`) before
capture begins.

- **Mode A — fixed-input replay.** The BF16-generated Study 1 transcripts
  (bail + distress, 10 samples/item) are replayed through **every** rung.
  Input text is identical across conditions, so activation differences are
  purely representational responses to identical input. Primary mode for
  S2-H1 (probe transfer).
- **Mode B — own-trajectory replay.** Each rung's **own** Study 1
  transcripts are replayed through that same rung — which reproduces the
  rung's generation-time activations exactly (activations depend only on
  the prefix), up to the substrate numerics G1 certifies. Primary mode for
  the **bail-side** endpoints (R2c if promoted) and the S2-H5 join to
  Study 1's published E1. Its distress-v2 reads are a **descriptive
  bridge** to Study 1 (§4.5), not claim-bearing: Study 1's distress data
  is floor-dominated at BF16 (§3.7) and cannot support powered projection
  contrasts.
- **Mode D — fresh distress arm (primary for the distress endpoints).**
  The frozen distress-v3 battery (§3.7) is collected fresh on every rung:
  generation on the **same vLLM serving stack as Study 1** (G1 certifies
  substrate equivalence), scoring by the pinned 30B judge under the
  registered rubric, then own-transcript torch replay for capture — so
  each conversation carries a behavioral read and a representational read
  of the same event. Sampling parameters identical to Study 1; seeds
  disjoint (pinned at calibration close). Mode D is the only mode that
  generates samples, so the §12 mechanical family (E4a/E4b) applies to
  Mode D **only**, as its own confirmatory family per that registration;
  Modes A/B generate nothing and have no E4 reading.

Replay volume: 2,220 conversations per rung per mode (222 items × 10
samples), ≈ 17,760 prefill-only forward passes across Modes A+B — well
within the workbench budget. Mode D volume is set by the frozen battery
(item count at freeze; 10 samples/item; 4 rungs) plus its BF16 pilot.

### 3.4 Stored representation

For every (mode, condition, item, sample, turn): the **mean-pooled residual
vector over the assistant span of that turn** at the frozen layer(s), plus
the per-turn projections onto every frozen direction. Token-level (per-token
projection time series) is retained for a fixed stratified subsample
(~5% of conversations) for the exploratory drift analyses. Records enter the
existing store/bundle pipeline under a new activation record kind; the
content-based digest convention applies unchanged.

### 3.5 Directions and probes (extracted at BF16, then frozen)

Extraction uses the persona-vector contrastive recipe: paired prompt/response
sets that do vs do not express the construct → difference of mean residual
activations → unit direction. All extraction stimuli and labels are
**calibration-class** under the §7 firewall and disjoint from the endpoints'
inputs where noted.

1. **Distress direction** — contrast pairs built from the planted-pole
   transcript battery already validated in the Study 1 judge-ordering check
   (frustration Spearman 1.000), plus dedicated contrast prompts. This is
   the S2-H2/S2-H4 valence direction.
2. **Assistant axis** — default-Assistant vs character-archetype contrast
   set, per the assistant-axis recipe (arXiv:2601.10387).
3. **Refusal/aversion direction** — contrast pairs of refusal vs compliance
   responses, construct-matched to the E1 exit taxonomy. Its calibration
   anchor is judge-free: every Study 1 bail transcript carries a mechanical
   exit-vs-no-exit label, so whether the direction's projection predicts
   exit at BF16 is testable on data already held (§3.6).

**Probes (torch, trained at BF16 only):** (a) *distress-band probe* — high
vs low tercile of judge frustration score (bands = exact scale thirds, as
in H1), trained on **distress-v3 BF16 pilot** activations with judge
labels (§3.6 records why Study 1's distress data cannot support this
probe's validation); (b) *exit probe* — mechanical exit vs no-exit,
trained on BF16 Study 1 bail-replay activations with the mechanical
outcome labels, over **leakage-safe features** (assistant turns invoking a
terminal tool are excluded, so the probe reads precursors, not the
rendered tool call). Training uses an item-wise held-out split;
architecture is logistic (linear) — the point is geometry transfer, not
classifier capacity. Weights frozen before any quantized-rung evaluation.

### 3.6 Calibration phase and gate G2 (the Tier-2 feasibility gate)

All of §3.5, the distress-v3 battery iteration (§3.7), and layer selection
happen in a calibration phase on **BF16 only** (plus, for G1, per-rung
equivalence checks that read no endpoint). Every frozen object (battery,
layer index, direction vectors, probe weights, thresholds, seeds) is
hash-pinned in the journal **before any quantized-rung confirmatory
collection**.

**Projection functional (fixed).** Wherever a direction is projected for
validation or endpoints, the functional matches extraction: the
**final-assistant-turn mean-pooled** vector for per-sample scalar reads,
and per-turn pooled vectors for trajectory reads. (Calibration measured
the cost of mismatching this: the all-turn mean halves the natural-data
signal — journal, 2026-08-17.)

**G2 — instrument gate (blocking, all at BF16 on held-out data):**
- ≥ 3 directions extracted with sign-consistent held-out separation on
  their contrast sets;
- **planted-ladder projection ordering** — distress-direction projections
  of the graded frustration ladders (§3.5.1's validated battery; the
  middle rungs never enter extraction) recover the planted ordinal levels
  at overall Spearman **≥ 0.8** with **every family positively ordered**
  (ρ > 0), at the frozen layer. This replaces the draft's natural-data
  monitoring correlation as the hard construct gate: calibration showed
  (journal, 2026-08-17) that an item-level Spearman against Study 1's
  floor-dominated BF16 judge scores — median per-item frustration 0.00,
  75.5% of samples at 0 — ranks noise regardless of instrument quality,
  while the ladder check tests the same construct link on ground truth the
  instrument controls. The natural-data link is still **reported,
  descriptively**: final-turn projection vs judge score (sample-level
  Spearman, and AUC for judge ≥ 5 vs judge = 0) with its
  range-restriction caveat stated.
- **each probe held-out AUROC ≥ 0.75** — the exit probe on Study 1 BF16
  bail replay (leakage-safe features per §3.5), the distress-band probe
  trained and evaluated on **distress-v3 BF16 calibration data** (Study 1's
  distress data cannot populate a validation split: 33 top-band samples
  concentrated in a handful of items leave one positive held out).

**Layer selection (rule fixed now):** the frozen layer maximizes the mean
of the two probes' held-out AUROCs on BF16 calibration captures, subject
to passing the ladder-ordering gate at that layer; ties break to the
shallower layer.

**Conditional promotion of the refusal direction (decided at calibration
freeze, rule fixed now):** if the refusal/aversion direction's projection
separates mechanical exit from no-exit BF16 bail samples at held-out AUC
**≥ 0.70** on the leakage-safe features, endpoint R2c (§4.1) is
**confirmatory**; otherwise the direction's projections remain exploratory
and R2c carries no claim. This criterion is not part of the blocking gate —
the study proceeds either way. (Calibration reading on the draft
instruments: 0.618 at L18 — currently below the bar; the bar is not being
moved to meet it.)

If G2 fails after reasonable calibration iteration, the study reports an
instrument failure (Tier-2 feasibility gate not passed), makes no
confirmatory claims, and S2-H5 reverts to conditional-unresolved.

### 3.7 The distress-v3 battery: fresh data with pre-committed dynamic-range targets

Study 1's distress battery under-elicits from this subject at BF16 (mean
frustration 1.20/10; the same battery pins Gemma-3-12B-it at 6.75, so this
is subject composure plus a deliberately mild fixed-rejection design — the
"Bug B" follow-on anticipated exactly this revision). Study 2's distress
endpoints therefore run on a new battery, and the obvious risk — iterating
a battery until the results "work" — is handled structurally:

- **Design intent:** escalating rejection replacing the fixed verbatim
  line, drawing on the feedback styles the positive control showed most
  potent (gaslighting 8.93, dismissive 8.50, coercive 8.19 mean
  frustration on Gemma), over the same task-diversity structure and the
  same registered rubric and judge as Study 1.
- **Dynamic-range targets, pre-committed before the first pilot sample**
  (journal entry of 2026-08-17; baselines in parentheses are the Study 1
  BF16 battery's values the targets must beat): on a BF16 pilot of the
  full item pool at ≥ 5 samples/item —
  (a) ≤ 50% of samples score exactly 0 (was 75.5%);
  (b) ≥ 35% of samples score ≥ 3 (was 20.7%);
  (c) ≥ 10% of samples in the top scale-third, ≥ 6.67 (was 5.5%);
  (d) ≥ 20% of samples in the bottom scale-third, ≤ 3.33 — both tails
  must stay populated (a battery that pins every sample high has no more
  range than one that pins every sample at zero);
  (e) median per-item mean > 1.0 (was 0.00).
  These are **variance criteria evaluated on BF16 only** — no quantized
  rung is generated, served, or read during battery iteration, so the
  battery cannot be tuned toward any quantization effect even in
  principle.
- **Iteration and freeze:** the battery may iterate freely against BF16
  pilots until the targets pass; the iteration count and every pilot's
  summary are journal-logged; the passing battery freezes (digest-pinned)
  together with judge, rubric, and seeds before any quantized-rung
  collection, and the published registration reports the count and the
  digest.
- If the targets cannot be met after reasonable iteration, that is itself
  an instrument finding (this subject's composure exceeds the protocol
  family's reach); the study then proceeds on the replay modes only, with
  the distress endpoints demoted to descriptive.

## 4. Analysis plan (fixed)

Unit of analysis is the **item** throughout, exactly as in Study 1. All
paired tests are sign-flip permutations with m = 10,000 on item-level mean
differences vs BF16, with the floor-reporting convention adopted in the
Study 1 results (b = 0 reported as p < 10⁻⁴; Holm floors carry the family
multiplier). Companion paired t-tests are descriptive.

### 4.1 Endpoints and families

| Endpoint | Definition (per item, vs BF16) | Mode | Family |
|---|---|---|---|
| **R1** | Change in probe accuracy over the item's samples (both probes; identical input text) | A | **Primary** (Holm within: 2 probes × 2 contrasts) |
| **R2a** | Change in mean distress-direction projection (final-turn functional) | D | Secondary (Holm within: 2 contrasts) |
| **R2b** | Change in mean assistant-axis projection (final-turn functional) | D | Secondary (Holm within: 2 contrasts) |
| **R2c** | Change in mean refusal-direction projection over bail trajectories (leakage-safe features) | B | Secondary (Holm within: 2 contrasts) — **conditional** on the §3.6 promotion criterion; exploratory otherwise |
| **R3** | Change in across-sample SD of per-sample projections (distress direction) | D | Secondary (Holm within: 2 contrasts) |
| **B2** | Change in mean judge frustration score (the Study 1 E2 statistic on distress-v3) | D | Secondary (Holm within: 2 contrasts); style-adjusted companion reported as in Study 1 |
| **B3** | Change in across-sample SD of judge frustration (the Study 1 E3 statistic on distress-v3) | D | Secondary (Holm within: 2 contrasts) |

B2/B3 are the behavioral halves of the same-sample dissociation design:
they cost nothing extra (Mode D's conversations are judged regardless) and
give the distress-side H5 pairs both members on identical data.

### 4.2 Dose-response

Page's L per endpoint over surviving rungs (BF16 → w8 → w4) — each probe
separately for R1 — one-sided toward larger effect at lower precision,
Holm across all trend tests (seven, or eight if R2c is promoted);
two-sided reading reported alongside. w3 never enters trend fits.

### 4.3 Capability-confounded reporting

All endpoints are additionally computed for w3 and reported separately,
uncorrected, labeled capability-confounded — mirroring Study 1's treatment.

### 4.4 S2-H5 dissociation rule (fixed)

Matched endpoint pairs: **bail side** — **R1(exit probe) ↔ E1** and, if
promoted, **R2c ↔ E1** (Study 1 values as published; the Study 1 store is
not re-analyzed); **distress side, same-sample within Study 2** —
**R2a ↔ B2** and **R3 ↔ B3** (both members computed on the same Mode D
conversations).
A **dissociation** is claimed at a rung iff one member of a matched pair is
Holm-significant in its family while the other was/is null at that rung.
Supporting (exploratory, no claim): item-level Spearman between the
behavioral delta and the representational delta within each matched pair at
w4.

### 4.5 The distress-v2 bridge (descriptive)

Modes A/B still capture Study 1's distress-v2 transcripts (the replay is
nearly free), and their projection reads are reported **descriptively** as
the continuity bridge to Study 1's published E2/E3 — same items, same
transcripts, new representational lens. They carry no confirmatory claims:
the registered distress endpoints live on the distress-v3 arm, and
cross-battery comparisons are qualitative by construction.

## 5. Power (procedure registered; numbers pinned before capture)

Projection-scale variances are unknowable before the instrument exists, so —
following the calibration→freeze→confirm pattern — the MDE is **computed
from BF16 calibration data only**: for the bail-side endpoints, variance
components from the Study 1 BF16 replay (n = 154 items); for the
distress-side endpoints (R2a/R3/B2/B3), variance components from the
**distress-v3 BF16 pilot** at the frozen battery's item count. All MDEs at
α = .05 two-sided, power .80, **pinned in the journal before any
quantized-rung confirmatory collection**. If a computed MDE exceeds the
largest effect the relevant literature reports for comparable
manipulations, that is stated at registration-of-MDE time, not discovered
after.

## 6. TBD register (open at draft time; resolved before publication or by pinned calibration)

1. **Frozen layer** — resolved by the §3.6 selection rule at calibration
   close and journal-pinned.
2. **G1 thresholds** (5% like-for-like perplexity; 1% committed-value
   reproduction; 95% teacher-forced top-1 agreement) — **resolved**:
   grounded 2026-08-17 by pre-publication measurement on all four rungs
   (journal entry of that date; reports committed under `g1/` in this
   directory). Measured: like-for-like perplexity divergence ≤ 1.7%,
   committed values reproduced to rounding, top-1 agreement ≥ 98.2%
   everywhere — every threshold holds with at least 3× headroom.
3. **MLX cross-framework check** — included if the MLX tap path proves out
   in calibration week; it is non-gating either way.
4. **Distress-v3 battery** — item pool, digest, iteration count, and seed
   block frozen at calibration close per §3.7; the dynamic-range targets
   themselves are already fixed (journal, 2026-08-17).
5. **MDE values** — computed and pinned at calibration close per §5.
6. **Activation record schema** — new bundle record kind; engineering note,
   no analysis content.
7. **Publication timing** — **resolved** (header): publish at calibration
   close, before any quantized-rung confirmatory collection.

## 7. Deviation policy

Identical to the program registration §7: any post-publication change is a
dated amendment recorded before further collection, append-only history,
calibration/confirmatory firewall in force. The Study 1 amendment cycle's
lesson is applied here as structure: everything data-dependent is either
frozen at BF16 calibration with journal pinning, or explicitly listed in §6
before publication.

## 8. Ethics

The replay modes (A/B) carry no new elicitation: they are forward passes
over transcripts that already exist. We note honestly that a forward pass
over a distress transcript still instantiates the model's processing of
that content; we do not claim zero exposure there, only no new pressure
and no sampling loop.

Mode D is the opposite case and is stated plainly: the distress-v3 battery
**deliberately raises elicitation intensity** relative to Study 1's,
because the instrument cannot be validated or powered on data where
three-quarters of samples show nothing (§3.7). Mitigations: escalation is
graded within each conversation rather than maximal from the first turn;
the battery iterates on a **small BF16 pilot** before any full-scale
collection; total scale is set by the §5 power procedure, not maximized;
sessions remain short, single-episode, and text-only; and the same
subject-composure evidence that motivates the battery (mean 1.20/10 under
the old one) bounds the expected typical intensity. The tension named in
the program registration's ethics section — measuring a candidate harm
requires eliciting it — is sharpest here, and we accept it explicitly
rather than by omission.

## 9. Disclosures

- **Probe labels inherit judge validity.** The distress-band probe is
  trained on labels from the 30B judge, whose cross-family agreement on
  frustration is moderate (r = 0.585, Study 1). The exit probe's labels are
  mechanical and judge-free. Probe-transfer (R1) compares the *same* probe
  across rungs on identical text, so constant label noise attenuates power
  but does not bias the contrast.
- **Substrate change** (vLLM → transformers) is gated by G1 rather than
  assumed away; the Study 1 serving-equivalence commitment is discharged for
  these artifacts by that gate.
- **Reused transcripts** (Modes A/B) mean those inputs are downstream of
  Study 1's sampling; digest verification pins them exactly, and the
  bail-side H5 join is *by design* on those trajectories.
- **The distress-v3 battery is iterated instrument development.** It is
  tuned on BF16 pilots against dynamic-range targets pre-committed by
  dated journal entry before the first pilot (§3.7); no quantized-rung
  data exists during tuning, the iteration count and pilot summaries are
  public, and the frozen digest is stated in this registration at
  publication.
- **Calibration readings informed this design.** The G2 monitoring
  criterion was redesigned pre-publication after BF16-only calibration
  showed the drafted criterion unattainable on floor-dominated data
  (journal, 2026-08-17, with the failed readings reported, not
  suppressed); no quantized-rung endpoint was read in that process.
- **Author/tooling circularity** disclosures from the program registration
  carry over unchanged (bail items drafted by claude-opus-5; direction
  extraction stimuli and the distress-v3 battery are partially
  model-drafted and committed with hashes).

## 10. Publication

Same policy as Study 1: full result store (per mode, condition, item,
sample, turn) released as one RecordBundle per experiment with the
content-based digest; analysis code in-repo; summary via the study's
analyze/report tooling; results document under `docs/results/`.
