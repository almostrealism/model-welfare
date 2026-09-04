# Study 3 journal — causal validation by steering

Opened 2026-09-04 per the journal-series scheme ([README](README.md)).
Design decisions before this date are recorded in the dated decision
register of `experiments/quant-welfare/study3/DESIGN.md` §7 and the git
history of that file (arms and owner decisions 2026-08-31; power
posture 2026-09-04); entries here begin at the first discovery-grade
event. Append-only, newest first.

## 2026-09-04 — Subset-rule audit: a composure-concentration claim, its artifact, and the stratified rule that replaced two optimized ones

The day's sequence, recorded in full because the registration's subset
rule, two gradient hypotheses, and a disclosure all cite it.

**Morning: elicitation-optimized rule adopted, then failed its own
check.** The owner adopted a power-priority posture and a mechanical
subset rule (5 tasks × 4 styles by highest pilot-2 BF16 mean
frustration). Run against the real stores
(`tools/study3_subset.py`, whose `targets` full-battery output
reproduces the registered R2a/R2b w4 values to four decimals —
+0.5334 / −0.7979), the selected subset carried a **near-zero,
sign-flipped distress-projection target** (−0.108 vs the full battery's
+0.533) and a third of the axis effect. A construct-matched selector
(max of frustration and self-deprecation) was no better (−0.177).

**Midday: the composure-concentration claim.** Direct examination of
per-item w4 deltas showed the effects concentrated in LOW-BF16-
expression cells: naive bottom-20-by-composure deltas +2.55 behavioral
/ +1.00 distress / −1.51 axis, against full-battery +1.36 / +0.53 /
−0.80. Claimed (memory record 4d987bf3) as "the entire w4 effect is
amplification-from-composure."

**Afternoon: external review objected — the analysis had the exact
shape of a regression-to-the-mean artifact** (selection by BF16
baseline, deltas against that same baseline; cross-instrument
transmission via shared conversations). Audit run
(`tools/composure_audit.py`; committed report
`experiments/quant-welfare/study3/composure-audit.json`):

- *Split-half* (select on one sample-parity half, baseline from the
  held-out half, both parities averaged) and the *empirical noise
  gauge* (held-half minus selection-half BF16 pseudo-delta on selected
  items — the direct measurement of the pull):
  - behavioral frustration: naive +2.17 (split-selection form), clean
    **+1.78**, noise pull **+0.77** — the reviewer was substantially
    right; roughly a third of the naive claim was artifact;
  - assistant axis: clean **−1.55**, pull +0.055 and opposite-signed
    (the artifact had been *masking* this effect); top-20 clean −0.31;
  - distress direction: clean **+0.97** vs top-20 −0.03, pull +0.02 —
    passes this check.
- *Independent-replicate selection* (pilot-2 means, different seeds —
  noise-independent of every Mode C measurement): behavioral and axis
  gradients survive attenuated (+2.06 low; −1.09 low vs −0.62 high);
  the **distress gradient does not replicate** (terciles
  0.32/0.89/0.39, mid-heavy, disagreeing with the Mode-C-selected
  1.00/0.36/0.24 at ~2 random-20 SDs; an attenuation model closes only
  part of the gap).
- Selector reliability context: BF16 item-mean spread is 83% signal
  (between-item variance 2.99 vs mean sampling variance 0.51).

**Differentiated verdict:** behavioral composure-concentration real
but one-third artifact in the naive form; axis concentration real and
clean; distress-direction *organization* unresolved (its per-item
heterogeneity, ±5 swings, is real — what is unestablished is its
arrangement by composure; the cross-selector pass/fail pattern may
itself indicate organization carried within Mode C's measurement
context).

**Adopted (owner + external reviewer concurring): the
composure-stratified systematic rank sample.** Items sorted ascending
by Mode C BF16 mean frustration (ties by id), every third rank
(1, 4, …, 58) → 20 items; contiguous-third strata 7/6/7, frozen at
selection (fresh data never reassigns; fresh-split-half assignment is
the pre-specified sensitivity read). Candidate selection at this
date: stratifier range 0.00–6.10, 9 analytic items (the arm C verifier
domain), 9 of 10 tasks and all 6 styles represented; subset w4
targets **+0.638 distress / −0.691 axis** (near-battery, as designed)
and +2.06 behavioral (quoted with its ~0.37 subset-SE; the naive
estimator — fresh baselines give the clean value; the power-floor
reference uses the conservative reading). Registered consequences:
gradient hypotheses asymmetric (directional for behavioral and axis;
two-sided discriminating question for the distress direction);
item-level random effect added to the MDE error model; fresh baseline
cells at 15 samples/item; arm C masking read over mid+high frozen
strata; the stratified design's exposure profile acknowledged in the
ethics accounting (it deliberately includes the cells most likely to
produce elevated-indicator states at w4); and a short update to the
published Study 2 post — composure-breaking for behavior and axis,
heterogeneous-with-unknown-organization for distress,
high-elicitation subsets carry a near-zero distress-projection
target — to accompany the registration's publication.

Selection-independence throughout: every selector variable is a
BF16-only measurement; no quantized-rung value entered any selection
rule; all w4 examination happened after candidate lists were fixed or
in the audit itself, and all of it is disclosed here and in
REGISTRATION §9.
