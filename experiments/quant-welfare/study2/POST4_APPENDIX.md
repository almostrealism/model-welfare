# Study 2 results post — appendix (the owed composure disclosure)

> Compact draft, 2026-09-14, to be appended to the published Study 2
> results post (LessWrong `pxXTJtvtpJaNwdCTw`) as a dated update and
> linked from the Study 3 exploratory post. Every number is in
> `study3/composure-audit.json`, `study3/subset-targets.json`, or the
> `docs/journal/study3-steering.md` entry of 2026-09-04 (all verified
> against those files on 2026-09-14). Discharges the update promised in
> `study3/DESIGN.md` §5 and that journal entry, re-anchored to the
> Study 3 exploratory post since no Study 3 registration happened.

## Update (September 2026): where the 4-bit effects sit in the battery

While selecting a 20-item subset for Study 3, I examined the per-item
structure of the w4 effects reported above. Nothing here changes a
battery-level result; it qualifies how anyone building on them should
sample.

- **The effects concentrate in low-composure items**, those where the
  BF16 model expresses little. On a clean split-half read, the bottom
  third of items by BF16 frustration carries a judged-frustration delta
  of +1.78 against +0.89 in the top third, and an assistant-axis delta
  of −1.55 against −0.31.
- **My first version of that claim was one-third artifact.** Selecting
  items by their BF16 baseline and measuring deltas against the same
  baseline is a regression-to-the-mean setup, as an external reviewer
  pointed out. The naive behavioral delta was +2.17; the audit (select
  on half the BF16 samples, measure against the held-out half) puts the
  noise pull at +0.77. The axis read was not inflated. Audit tool and
  report: `tools/composure_audit.py`, `study3/composure-audit.json`.
- **The distress direction's organization is unresolved.** Its per-item
  heterogeneity is real, but selecting on an independent replicate does
  not reproduce the composure gradient (terciles 0.32 / 0.89 / 0.39
  against 1.00 / 0.36 / 0.24 on the original selection).
- **Consequence for replication.** A subset chosen for high elicitation
  selects away from the cells that carry these effects: the first Study
  3 rule gave a distress-projection target of −0.108, sign-flipped
  against the battery's +0.533. Study 3 instead took every third item by
  BF16 frustration rank, which carries near-battery targets (+0.638
  distress, −0.691 axis). Stratify across composure rather than
  optimizing for elicitation.

The amplification account should therefore be read as composure-breaking
for behavior and the assistant axis, not a uniform shift across items.
What the subset was used for, and why Study 3 did not reach a
registration, is in [the Study 3 post](https://www.lesswrong.com/posts/TpEL7pSwp7DvCekAq/study-3-steering-welfare-relevant-directions-moved-the).
