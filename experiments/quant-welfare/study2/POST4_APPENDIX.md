# Study 2 results post — appendix draft (the owed composure disclosure)

> Draft, 2026-09-11. Intended to be appended to the published Study 2
> results post (LessWrong `pxXTJtvtpJaNwdCTw`) as a dated update section,
> and linked from the Study 3 exploratory post. Every number below is in
> `experiments/quant-welfare/study3/composure-audit.json` or the
> `docs/journal/study3-steering.md` entry of 2026-09-04; the owner should
> check each against those before posting. This discharges the commitment
> recorded in `study3/DESIGN.md` §5 and the 2026-09-04 journal entry,
> which tied the update to a Study 3 registration that did not happen;
> it is re-anchored here to the Study 3 exploratory post instead.

## Update (September 2026): where the w4 effects live, and a correction to my own first reading

While preparing Study 3, I examined the per-item structure of the w4
effects reported above, because Study 3 needed a 20-item subset of the
60-item battery and I wanted the subset to carry the effect. Three
things came out of that which qualify how anyone should replicate or
extend this result. None of them changes a registered claim; Study 2
made no claim about homogeneity across items or about where in the
battery the effects sit. But they are the kind of thing I would want to
know before building on it, so they are owed here.

**1. The effects are not uniform across the battery.** The w4 − BF16
deltas concentrate in items where the BF16 model expresses little
(low-composure items, ranked by BF16 mean judged frustration). Split
cleanly (see 2), the bottom third of items by BF16 composure carries a
judged-frustration delta of about +1.78 against +0.89 in the top third,
and an assistant-axis delta of −1.55 against −0.31. The
distress-direction projection shows the same gradient on one selector
(+0.97 bottom versus +0.07 top) but not on another (see 3).

**2. My first version of that claim was one-third artifact.** The naive
analysis selected items by their BF16 baseline and then measured deltas
against that same baseline. That has the exact shape of a
regression-to-the-mean artifact: part of the quoted delta is the
selection's own sampling noise flowing back, and because the behavioral
and representational reads share conversations, the bias transmits
across instruments. An external reviewer pointed this out and was
substantially right. A split-half audit (select on one half of the BF16
samples, measure against the held-out half, both parities averaged) plus
a direct noise gauge (the held-half minus selection-half pseudo-delta on
the selected items) gives, for the behavioral endpoint, naive +2.17,
clean +1.78, noise pull +0.77. For the assistant axis the pull is +0.06
and opposite-signed, so the artifact had been slightly *masking* that
gradient. For the distress direction the pull is +0.02. The audit tool
and its report are committed (`tools/composure_audit.py`,
`study3/composure-audit.json`). The selector itself is reliable: 83% of
the between-item spread in BF16 item means is signal rather than
sampling variance.

**3. The distress direction's organization is unresolved.** Selecting
items by an independent replicate (the pilot-2 BF16 means, different
seeds) reproduces the behavioral and axis gradients attenuated (+2.06
low; −1.09 low versus −0.62 high) but the distress-direction gradient
does not replicate: its terciles come out mid-heavy (0.32 / 0.89 / 0.39)
where the same-data selection gave 1.00 / 0.36 / 0.24. The per-item
heterogeneity of the distress projection is real (swings of ±5 units);
what is not established is that it is arranged by composure. The
differentiated verdict: composure-concentration is real but one-third
artifact for behavior, real and clean for the assistant axis, and
unresolved in organization for the distress direction.

**4. The practical consequence for replication.** A subset chosen for
high elicitation, the natural power-maximizing choice, selects *away*
from the cells that carry the Study 2 effects: the first Study 3 subset
rule (top items by BF16 frustration) carried a distress-projection
target of −0.108, near zero and sign-flipped against the full battery's
+0.533, and a third of the axis effect. Anyone extending this result on
a subset should stratify across the composure range rather than
optimize for elicitation; Study 3 adopted a composure-stratified
systematic rank sample (every third item by BF16 frustration rank),
which carries near-battery targets (+0.638 distress, −0.691 axis).

**What this does and does not change.** The registered results above
stand as stated: they are battery-level, and the battery-level numbers
are unaffected. What changes is the reading of the amplification
account: it is composure-breaking for behavior and the assistant axis
(the degraded model loses composure where the reference model had it),
heterogeneous with unknown organization for the distress direction, and
not a uniform shift across items. The Study 3 exploratory post
`[[author: link]]` describes what the subset rule this produced was used
for, and why Study 3 did not reach a registration.
