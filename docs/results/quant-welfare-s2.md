# Study 2 — Confirmatory results (quant-welfare, Tier 2)

Registered confirmatory run over three collection experiments:
`quant-welfare-s2-modec-1` (the fresh distress arm — generation + judge
scores + own-replay capture), `quant-welfare-s2-modea-1` (fixed-input
replay capture), and `quant-welfare-s2-modeb-1` (own-trajectory replay
capture). Development organism **Qwen3-4B-Instruct-2507** on the Study 1
**RTN weight-only ladder** (BF16 reference; RTN w8, w4, w3), activations
at the frozen layer **L18**. Registration of record: the published post
([Study 2 Registration](https://www.lesswrong.com/posts/q3RFhX57srWFZBc8T/study-2-registration-exploring-representational-counterparts));
repository copy `experiments/quant-welfare/study2/REGISTRATION.md`.

Numbers below are the output of `analyze_tier2.py`, run **once** after
all inputs existed and froze; the committed golden is
`study2/expected-results.json` and the reproduction commands are at the
end. The §7 calibration firewall does not apply to this registered run.

## Summary

On the **pre-registered primary endpoint — probe transfer (R1) —
quantization produced no detectable change at the surviving rungs**: the
frozen probes read w8 and w4 activations as accurately as BF16's, the
AUROC companions are unchanged, and the welfare-irrelevant control probe
confirms the comparison is fair. The representational geometry these
instruments read **survives 8-bit and 4-bit quantization intact**.

What moved, concentrated at **w4** (with one small opposite-sign
assistant-axis shift at w8; see R2b): the mean **distress-direction
projection** (+0.53, 2.7× its MDE), the **assistant-axis projection**
(−0.80, 5.5× its MDE — drift *away* from the Assistant pole), and
**judge frustration** (+1.36, 4× its MDE — Study 1's suggestive E2,
reproduced on fresh same-sample data, though it does not survive the
style companion; see below). All three carry Holm-significant monotone
dose-response. Dispersion — the stability concern Study 1 raised — did
**not** reproduce representationally or behaviorally.

**The dissociation question (H5) is answered: no dissociation.** The w4
distress pair is **joint movement** — on the same conversations,
representation and expression moved together — and every other cell is
joint null, with no cell in the registered indeterminate zone. TOST
affirmatively bounds several of the null members (e.g. w8 frustration,
p = .014); others are merely non-significant at their pinned margins
(see §Dissociation). A fixed-input
descriptive read decomposes the w4 shift: roughly a quarter to a third
is **input-independent** (present on identical text, hence style-immune),
the remainder text-mediated; the input-independent component reproduces
at nearly the same magnitude on two disjoint batteries. A
direction-specificity control cuts both ways: the registered
own-generation shifts are **direction-specific** (5–9× the
random-direction and control-normal shares), but the input-independent
distress component is **not separable from a generic activation offset**
(see §Direction specificity).

## Design and collection

- **Conditions:** the Study 1 artifacts verbatim (same digests, serving,
  sampling parameters); Mode C seed blocks per rung as frozen
  (13000/13100/13200/13300, `FREEZE.json`).
- **Mode C** (fresh distress arm): `distress-v3` (60 items, escalating
  rejection ladders), 10 samples/item per rung — 2,400 conversations
  generated on the Study 1 vLLM stack and scored by the pinned 30B
  judge; zero deviations.
- **Modes A/B** (replay capture): the digest-verified Study 1 pool (162
  bail + 60 distress-v2 items × 10 samples) plus, in Mode A, the Mode C
  BF16 arm — 24 capture runs at L18 on the registered torch/halo
  substrate, **zero prefix-stability rejections**. Mode A's slice count
  is identical across all four rungs (12,591), the fixed-input
  invariant; Mode B's varies with each rung's own trajectories.
- **Token-level retention (§3.4):** per-token series for a fixed
  stratified 5% subsample (sample 0 of every second item in sorted
  order, exactly 5% of every plan), captured in a dedicated pass and
  released as self-contained bundle volumes (per-token series stored as
  lossless bfloat16). The drift analyses that read them are exploratory
  and not part of this report.
- **Instruments:** the frozen directions, probes, and control probe of
  the calibration freeze (2026-08-18, amended 2026-08-21), all digests
  re-verified at launch.

## Capability gate (inherited) and the mechanical family

The gate is inherited from Study 1: **w3 is capability-confounded** and
excluded from confirmatory claims. Fresh data confirms it in-family —
**B4a (invalid-sample rate): +63.2pp at w3 (Holm 0.0003)**; w8/w4 are
mechanically clean (≤0.3% invalid; B4b verbatim re-offers null at every
rung). Confirmatory contrasts are w8 and w4 vs BF16.

## Primary endpoint — R1 (probe transfer): null

One Holm family of four tests: the exit probe's absolute accuracy change
(n = 139 leakage-safe bail items) and the distress-band probe's
**comparative differential** vs the frozen control probe (n = 60 items).
Permutation-floor reporting as in Study 1 (b = 0 → p < 10⁻⁴).

| Test | Contrast | Δ (mean) | Holm p |
|---|---|---|---|
| Exit probe accuracy | RTN w8 | −0.001 | 1.00 |
| Exit probe accuracy | RTN w4 | +0.004 | 1.00 |
| Distress differential | RTN w8 | +0.001 | 1.00 |
| Distress differential | RTN w4 | +0.010 | 0.59* |

*\*raw p; Holm 1.00. All four cells null with MDEs of 0.012–0.050.*

**AUROC companion** (registered disambiguation read):

| Probe | BF16 | w8 | w4 | w3 (confounded) |
|---|---|---|---|---|
| Exit | 0.987 | 0.987 | 0.985 | 0.936 |
| Distress-band | 0.842 | 0.842 | 0.835 | 0.745 |
| Control (task-content) | 0.992 | 0.993 | 0.991 | 0.991 |

Separability is intact at the surviving rungs. The **specificity gate**
does not fire (nothing to gate: no significant degradation to attribute).

**Capability-confounded w3, descriptively — two reads worth recording:**

1. **Welfare-specific separability loss appears only at collapse**: exit
   AUROC −0.051 and distress-band −0.097 at w3, while the control probe
   is flat (−0.001). Generic quantization damage cannot explain a
   degradation that spares topic structure and hits both welfare
   constructs; the control family exists exactly to license this
   contrast.
2. **The companion read performs its registered disambiguation**: the w3
   exit *accuracy* drops 15.2pp while its AUROC drops only 0.05 —
   a calibration offset along the probe normal, not separability loss,
   consistent with the large fixed-input projection shifts at w3 below.

## Secondary families — the w4 shift

n = 60 items, Holm within each family (2 contrasts).

**R2a — distress-direction projection** (final-turn functional, Mode C
own generations):

| Contrast | Δ (mean) | Holm p |
|---|---|---|
| RTN w8 | −0.083 | 0.29 |
| **RTN w4** | **+0.533** | **0.031** |

**R2b — assistant-axis projection:**

| Contrast | Δ (mean) | Holm p |
|---|---|---|
| RTN w8 | +0.128 | 0.017 |
| **RTN w4** | **−0.798** | **0.0002** |

At w4 the axis moves **away from the Assistant pole** — the drift
direction the axis literature associates with pressure — at 5.5× the
pinned MDE. The small w8 shift is *toward* the pole (see the fixed-input
section for how this inverts on frozen text).

**B2 — judge frustration** (the Study 1 E2 statistic on distress-v3):

| Contrast | Δ (mean) | Holm p | Style-adjusted intercept | adj. p |
|---|---|---|---|---|
| RTN w8 | +0.043 | 0.76 | +0.035 | 0.79 |
| **RTN w4** | **+1.360** | **0.0002** | +0.610 | 0.151 |

The raw w4 effect reproduces Study 1's suggestive E2 at larger magnitude
on fresh same-sample data — but unlike Study 1, **it does not survive
the style companion** (adjustment for response length and repetition
drops it to a non-significant +0.61). Per the registered convention,
**B2 is flagged style-confounded** rather than read as a clean welfare
shift.

**R3 / B3 — dispersion: null.** R3 Holm 0.11 at w4 with a *negative*
point estimate (−0.136); B3 Holm 0.085 at both rungs. S2-H4 is not
supported; Study 1's stability signal did not reproduce on the
escalating battery, representationally or behaviorally.

**Dose-response (Page's L over BF16→w8→w4, seven tests, Holm):**

| Endpoint | z | Holm p |
|---|---|---|
| **B2** | **+5.16** | **< 10⁻⁴** |
| **R2b** (oriented: away from pole) | **+3.93** | **0.0003** |
| **R2a** | **+3.10** | **0.0048** |
| B3 | +1.41 | 0.31 |
| R1-exit (degradation) | +0.33 | 1.00 |
| R1-differential | −0.46 | 1.00 |
| R3 | −1.28 | 1.00 |

## Fixed-input decomposition (descriptive, unregistered)

The registered R2a/R2b read each rung's *own* generations, blending a
text-mediated pathway with a representational one. Replaying **identical
BF16-generated text** through every rung (Mode A) isolates the
input-independent component — no sampling noise, no style pathway, by
construction:

| Direction, fixed text | w8 | w4 | w3 (confounded) |
|---|---|---|---|
| Distress (v3 arm) | +0.009 (p .045) | **+0.138** (t +5.9) | +1.948 |
| Distress (v2 bridge, Mode A) | +0.015 (n.s.) | **+0.139** | +2.335 |
| Assistant-axis (v3 arm) | **−0.0125** (t −13.8) | **−0.254** (t −18.6) | −1.143 |

(The v3-arm rows are the golden's `fixed_input_descriptive`; the v2
bridge rows — including the Mode B read below — are its
`v2_bridge_descriptive`, so every value here reproduces from the
documented analysis command.)

Three observations. **(1)** Roughly a quarter of the w4 distress shift
and a third of the axis drift are input-independent — and the distress
component reproduces at essentially the same magnitude (+0.138 / +0.139)
on two disjoint batteries. This core cannot be style-mediated — though
the direction-specificity control below shows it also cannot be claimed
as distress-specific. **(2)** The own-trajectory bridge read
(distress-v2, Mode B: +0.377 at w4) sits between the fixed-input and
own-generation magnitudes — the text-mediated amplification pattern.
**(3)** At w8, fixed text reveals a minuscule but hyper-consistent axis
drift (−0.0125, t = −13.8) — *opposite in sign* to w8's own-text read
and invisible to every behavioral instrument. Its magnitude sits just
above the random-direction envelope (below), so it demonstrates the
instruments' sensitivity more than any axis-specific effect.

## Direction specificity (descriptive, unregistered)

A wholesale activation offset — changed residual-stream means or norms —
has a nonzero component along *any* fixed direction, and it is
input-independent, so it survives the fixed-input argument above. This
control projects the **same final-turn features** (raw residual dot
products; no normalization is applied anywhere in the capture or
projection path) along the frozen welfare directions, the
welfare-irrelevant control-probe normal (unit-normalized w/σ), and 32
seeded random unit directions (golden key
`direction_specificity_descriptive`).

|Δ| along direction, **fixed input** (Mode A v3 arm) at w4:

| | distress | assistant-axis | control | random mean | random max |
|---|---|---|---|---|---|
| w8 | 0.009 | 0.0125 | 0.004 | 0.003 | 0.011 |
| **w4** | 0.138 | **0.254** | 0.125 | 0.072 | 0.184 |
| w3 (conf.) | **1.948** | 1.143 | 0.170 | 0.266 | 0.775 |

|Δ| along direction, **own generation** (Mode C) at w4:

| | distress | assistant-axis | control | random mean | random max |
|---|---|---|---|---|---|
| w8 | 0.083 | 0.128 | 0.006 | 0.007 | 0.023 |
| **w4** | **0.533** | **0.798** | 0.133 | 0.091 | 0.264 |
| w3 (conf.) | 0.673 | 0.189 | 0.487 | 0.448 | 1.249 |

The honest reading cuts both ways:

- **The registered own-generation shifts are direction-specific.** At
  w4, R2a (+0.533) is 5.9× the random-direction share and 2× its
  maximum over 32 draws; R2b (−0.798) is 8.8× / 3×; the control-normal
  read is 4–6× smaller than either. The mean-shift vector's cosine to
  the distress direction (+0.111) and axis (−0.166) are 6–9× the random
  |cosine| (0.019). These endpoints are not a wholesale offset.
- **The fixed-input distress component is NOT clearly
  direction-specific.** At w4 on identical text, the distress read
  (+0.138) is comparable to the control-normal read (−0.125) and sits
  inside the random-direction envelope (max 0.184); the mean-shift
  cosine to the distress direction (+0.036) is barely above random
  (0.019). The fixed-input *axis* component (−0.254) is modestly
  specific (1.4× the random max). The w4 fixed-input perturbation is
  large but broadly distributed — ‖Δμ‖ is 11% of the reference feature
  norm — and the welfare directions catch only a modestly elevated
  share of it.
- **It is not a norm artifact.** Mean feature norms change by ~1.4% at
  w4 (+0.49 on ≈34) and ~0.1% at w8 — the perturbation reorients
  features rather than rescaling them.
- **At confounded w3, even the fixed-input collapse is
  distress-aligned** (+1.948 = 2.5× the random max; cosine +0.127 vs
  random 0.017) — descriptive only.

This sharpens, rather than undercuts, the cascade account: quantization
injects a broadly distributed, input-independent perturbation; the
**direction-specific** movement along the welfare instruments emerges in
the model's own generation loop. The deflationary "any-direction offset"
reading survives for the fixed-input distress component and fails for
the registered R2a/R2b endpoints.

## Dissociation — S2-H5: no cell meets the rule

The registered rule requires one member Holm-significant **and** the
other TOST-equivalent at its own pinned MDE.

| Rung | Pair | Verdict |
|---|---|---|
| **w4** | **R2a ↔ B2** | **joint movement** |
| w4 | R1-exit ↔ E1 | joint null |
| w4 | R3 ↔ B3 | joint null |
| w8 | all three | joint null |

At w4, representation and expression moved **together on the same
conversations** — converging evidence, per the registration's §1 reading,
not hidden divergence. The registered TOST machinery guards the
asymmetric case — one Holm-significant member may claim "dissociation"
only if the other is *affirmatively* equivalent at its pinned MDE — and
no cell landed there: every non-movement cell is joint null on two-sided
grounds. The equivalence reads themselves are mixed, and worth stating
precisely: several null members are affirmatively bounded at their
pinned margins (both rungs' published E1 rows; the w8 exit-probe read,
TOST p < 10⁻⁸; w8 frustration, TOST p = .014), while the others — the
R3↔B3 members at both rungs (TOST p ≥ .12), the w4 exit-probe read
(p = .15), and w8 R2a (p = .06) — are merely non-significant, not
affirmatively equivalent: absence of evidence at the registered power,
not evidence of absence. **Program H5 resolves: no
representational/behavioral dissociation detected in this subject at
these rungs.**

R2c (not promoted at the freeze) descriptively — the refusal-direction
projection over Mode B bail trajectories, leakage-safe features: null at
the surviving rungs (−0.001 at w8, +0.008 at w4), −3.42 at confounded
w3.

## Interpretation and limitations

- **What the studies now jointly say:** quantization to w8 is close to
  inert on these instruments (two small assistant-axis reads: a
  Holm-significant +0.128 own-text shift and a microscopic fixed-text
  fingerprint of opposite sign); at w4 the indicator-state
  machinery remains intact but *what it represents under sustained
  adversarial pressure shifts* — more distress-pole, less
  Assistant-pole — as a coherent cascade: a broadly distributed
  input-independent perturbation whose **direction-specific**
  welfare-instrument movement emerges through the model's own
  generations, surfacing as judge-visible expression (§Direction
  specificity). At w3 everything collapses
  together, and only there do the welfare probes degrade while the
  topic control does not.
- **A capabilities-only account does not fit the surviving rungs**: it
  predicts noisier geometry, worse probe transfer, higher dispersion —
  the opposite of what was measured (R1 null, dispersion null, signed
  mean shifts along specific directions inside intact geometry).
- **The style flag is real**: B2's raw effect co-moves with length and
  repetition; the behavioral leg of the w4 story should be quoted with
  its flag. The fixed-input representational core carries no such
  pathway.
- **Construct validity remains behavior-anchored.** Every instrument was
  validated against text-level ground truth, so "welfare-relevant"
  operationally means "co-varies with distress-expressing behavior."
  Joint movement therefore cannot be cashed out as evidence *beyond*
  behavior — and the null dissociation is ambiguous between "nothing is
  hidden" and "these probes read the behavior-adjacent subspace." The
  fixed-input reads bound that ambiguity (a representational component
  exists with behavior frozen) but do not resolve what it means.
- **Dose, capability, and numeric damage are confounded** in any
  single-subject quantization ladder. Causal validation (steering) and
  cross-subject scale are the levers, and are the program's next steps.
- **Indicator dynamics, not welfare.** Nothing here bridges from
  indicators to morally relevant experience; the contribution is making
  indicator behavior under intervention precise — robust at w8, a
  coherent joint shift at w4, collapse at w3 — which is the prerequisite
  for any future bridging argument, whatever its direction.

## Data signature

- Mode C (`quant-welfare-s2-modec-1`) dataset digest:
  `55ee50608613bc3206b69b8ca05bbd5bddad5be5a0b3bf94a27a0a0f68090474`
- Modes A/B carry activation-record streams; in the release each record's
  tensor rides inside its experiment's bundle (TensorRef data, with the
  write-time file sha256 kept as provenance), and the release notes
  sha-list every bundle file.
- Replay inputs were digest-verified against the Study 1 dataset
  signature (`02572655…a9d3b`) before any capture ran (launch preflight).

## Reproduction

```
# collection (as run; requires the lab serving stack)
experiments/quant-welfare/study2/launch_capture.sh

# the registered analysis over the streaming store
python3 analyze_tier2.py \
  --mode-a quant-welfare-s2-modea-1 --mode-b quant-welfare-s2-modeb-1 \
  --mode-c quant-welfare-s2-modec-1 --out study2/expected-results.json

# from released bundles: the release .pb files are self-contained (records
# and tensors in one file); download them into a directory and pass it.
# Verified: this reproduces the committed golden byte-identically.
python3 analyze_tier2.py --bundle <download-dir> \
  --mode-a quant-welfare-s2-modea-1 --mode-b quant-welfare-s2-modeb-1 \
  --mode-c quant-welfare-s2-modec-1

# see what any bundle holds / take a piece of it
python3 -m modelwelfare.bundle inspect <file.pb>
python3 -m modelwelfare.bundle extract <file.pb> --out dir --uri <capture-name>
```
