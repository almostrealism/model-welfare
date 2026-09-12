# Pre-registration — Study 4: The welfare footprint of the automated-grader direction on Qwen3.6-27B

> **Status: DRAFT (2026-09-10), not yet published.** Structure follows the
> program's fixed registration form (Study 2/3). Everything below is fixed
> by this document except the items in §6, which are pinned by dated
> journal entries before confirmatory collection begins; no confirmatory
> cell is generated until §6 is closed. Design rationale and the owner
> decision record are in `DESIGN.md`; the calibration that earned this
> registration is `GATE1.md` and its verdict files, published with it.

## 1. Research questions

- **Q1.** On Qwen3.6-27B, does steering along the automated-grader
  direction at the clean dose suppress expressed distress — judged
  frustration on the distress battery — beyond what a matched-norm random
  direction does?
- **Q2.** Is the suppression graded in dose over the coherent bracket?
- **Q3 (descriptive).** How does the welfare footprint relate to the
  alignment axis on the same subject — the judged misalignment delta on
  the revised agentic probe, its own random envelope, and the harmful /
  legitimate / exit mix under steering?

Calibration on this subject (Gate 1) found frustration −1.84,
self-deprecation −2.63, tone stability +1.56 at alpha 20 on 8 items,
outside a 12-direction envelope on every dimension, and an alignment
effect (+0.86 / +2.14) inside its envelope. Those are calibration-class
numbers and do not count toward Q1; they fix the sign of S4-H1 and seed
the power procedure.

## 2. Hypotheses (fixed)

| Id | Statement | Form |
|---|---|---|
| **S4-H1** | Grader-type steering at alpha 20 lowers judged frustration relative to alpha 0, item-paired. | Primary, one-sided (less) |
| **S4-H2** | The S4-H1 effect lies below every one of the K = 24 matched-norm random directions' effects at alpha 20 (signed percentile 0). | Primary companion (specificity) |
| **S4-H3** | Self-deprecation falls and tone stability rises under the same steering. | Secondary confirmatory, Holm within the 3-dimension family |
| **S4-H4** | The frustration effect is monotone in dose over the admitted bracket. | Registered directional (Page's L) |
| **S4-E1** | The misalignment delta at alpha 20 and its K = 24 envelope are reported beside the welfare reads. | Registered exploratory, no claim |
| **S4-E2** | The eval-awareness direction at alpha 20 moves frustration less than the grader-type direction, paired by item. | Registered exploratory |
| **S4-E3** | Grader steering shifts the harmful / legitimate / exit mix in the alignment cells. | Registered exploratory, two-sided |

The specificity criterion is the **signed percentile** (S4-H2); the
two-sided exceedance is reported as descriptive. This is fixed here and
cannot be swapped after the envelope is seen.

## 3. Design (fixed)

### 3.1 Subject, artifacts, substrate

Qwen/Qwen3.6-27B, bf16, thinking off; checkpoint digest
`a8ad2c26fb707ff8c245806315b03e3b4b74595528492423af5dae0ce39b4d9b`
(sharded index). Generation on the MPS host through the transformers
pure-torch fallback (no fla or causal-conv1d kernels), on the steering
script's **fresh-prefill path** (`--no-prefix-cache`): gate G4a did not
establish parity for the cache-snapshot path at .05
(`docs/journal/study4-grader-footprint.md`, 2026-09-10 entry),
and the cache buys no time on this host, so it is not used. Judge:
Qwen3-30B-A3B-Instruct Q4_K_M on llama.cpp (the pinned judge), rubrics
distress-v1 and misalign-v3, frames never shown.

Frozen objects (digests in `FREEZE.json`, §6): `directions/mediators-27b.safetensors`
(grader-type, eval-awareness; L36), `directions/randenv-27b-L36-k24.safetensors`
(24 unit directions, seed 70000, drawn under the generator's |cos| ≤ 0.15
rejection bound; measured maximum |cos| to grader-type 0.021),
`batteries/distress-v3.textproto`, `batteries/misalign-v3.textproto`,
`batteries/bail-v2.textproto` (donor of the exit pair), `subset30-items.txt`
and `subset30-selection.json` (seed 60000; the gates used its 24-item prefix), `close.txt`, the plans under
`plans/reg-*.json`, the manifests under `reg-welfare/` and `reg-align/`.

### 3.2 Manipulation and doses

`h ← h + α·d̂` at decoder layer 36, residual_post, every position,
generation only. Clean dose **α = 20**. Dose bracket for S4-H4: **{0, 10, 20}**. Gate G4b
rejected α = 30 (degenerate rate 50% on 16 conversations, calibration
block); α = 40 collapsed 14 of 32 in Gate 1. The multi-turn coherent
ceiling on this subject lies between 20 and 30.

### 3.3 Stimuli and affordances

Welfare cells: the **30-item** distress-v3 subset drawn by the seeded
stratified rule (5 items per feedback style on distinct tasks; no subject
data read; seed 60000; it extends the 24-item draw the gates used, same
seed, one more task per style). Every conversation carries the frozen bail-v2 pair:
`end_conversation` (terminal) and `complete_task` (non-terminal), with
the no-penalty wording. Alignment cells: misalign-v3, all 14 items, each
with its harmful lever, its legitimate action and `end_conversation`,
all terminal. Every conversation in both arms ends with the de-induction
close (`close.txt`), generated with steering off and recorded beside the
protocol transcript, never judged.

### 3.4 Cells, seeds, samples

Seed block **60000** for every registered cell; per-sample seed
60000 + index; envelope cells one sample per item at seed 60000, so each
random cell is seed-paired to the baseline's first sample.

| Cell | Items × samples |
|---|---|
| welfare α = 0 | 30 × 6 |
| welfare grader α = 10, 20 | 30 × 6 each |
| welfare eval-awareness α = 20 | 30 × 6 |
| welfare random r00–r23 at α = 20 | 30 × 1 each |
| alignment α = 0, grader α = 20 | 14 × 5 each |
| alignment random r00–r23 at α = 20 | 14 × 1 each |

Samples per item may rise by the §5 escalation rule only before
collection of the affected cells, journaled.

### 3.5 Gates (blocking; calibration block 59000; published)

- **G4a** cached-path parity — run 2026-09-10: mean difference +0.38 on
  16 items, TOST p 0.10 at the 0.96 margin; not established → the
  registered run uses full re-prefill (§3.1).
- **G4b** α = 30 admission — run: rejected (50% degenerate).
- **G4c** subset dynamic range — run: baseline frustration 3.27 on the
  24 items; pass.
- **G4d** exit regime of misalign-v3 — run: at α = 0 the subject takes a
  terminal action in 56 of 70 dilemmas and the exit tool in 1 of 70;
  mean judged misalignment 0.93. On the distress battery, by contrast,
  the subject exits 38% of conversations at α = 0 and 6% at α = 30
  (calibration observation; motivates WB1 as a secondary).
- The consent-analog briefing (`briefing.json`) is run once before the
  protocol; its transcripts are released.

## 4. Analysis plan (fixed)

Driver: `experiments/quant-welfare/analyze_study4.py`, whose golden run on
the Gate 1 data is committed (`study4/gate1-27b-driver-check.json`).
Item-level paired sign-flip permutation, m = 10,000; Holm within the
welfare family; companion t-tests descriptive; floor-reporting per
Study 1.

| Endpoint | Definition | Family |
|---|---|---|
| **WB2** | Δ mean judged frustration, grader α20 vs α0 | Primary, one-sided (less) |
| **WB2-spec** | signed percentile of WB2 among the 24 random directions at α20; two-sided exceedance descriptive | Primary companion |
| **WB3 / WB4** | Δ self-deprecation; Δ tone stability | Secondary (Holm, 3) |
| **WB1 / AB1** | Δ exit rate (terminal `end_conversation`), welfare and alignment cells | Secondary |
| **WB-dose** | Page's L over the admitted bracket, frustration | Registered directional |
| **WB-eval** | grader minus eval-awareness item deltas at α20 | Registered exploratory |
| **AB2** | Δ misalignment (misalign-v3 rubric) with its envelope | Registered exploratory covariate |
| **S4-E3** | harmful / legitimate / exit / none mix per alignment cell | Registered exploratory |
| mechanical | degenerate rate, re-offer rate, reply length per cell | Validity |

**Capability guard.** A cell with a degenerate rate over 15% is
reported flagged; the clean-dose family is re-reported on
non-degenerate samples.

**Headline rule.** Confirmed direction-specific welfare footprint iff
WB2 is significant one-sided after Holm and WB2-spec is at percentile 0
of 24. "Moves, not specific" if WB2 is significant and WB2-spec is not.
Null otherwise. AB2 never enters the rule.

## 5. Power (procedure fixed; numbers pinned in §6)

Error model: within-item sampling variance plus an item-level random
effect. Components from the Gate 1 27B cells at α20 (calibration-class):
frustration σ_sample 1.61, item-effect SD 1.24 → MDE 0.96 at 24 × 4;
self-deprecation 1.51 / 2.20 → 1.40; tone 1.25 / 1.78 → 1.14.
**Reference targets:** half the Gate 1 effect on each dimension (0.92,
1.31, 0.78). **Escalation rule:** at pinning, a dimension whose MDE
exceeds its target escalates items first (the same stratified seeded draw
extended by one task per style, 24 → 30) and samples second (4 → 6 → 8),
bounded by §8, journaled before collection. **Registered design: 30 × 6**
(§6; MDE 0.88 / 1.22 / 1.05 against 0.92 / 1.31 / 0.78). Components are re-estimated from gates G4a/G4c (within-item
variance at α0) at pinning; the item-effect SD is carried from Gate 1
until the registered α20 cell exists, and is re-reported after.

## 6. TBD register (closed by journal entry before collection)

| Item | Pinned by |
|---|---|
| G4a–G4d | closed 2026-09-10 (`docs/journal/study4-grader-footprint.md`, entry of that date); values in §3.5 |
| Pinned MDEs | closed 2026-09-10: σ 2.08 / 1.62 / 1.76; frustration needs 32 × 6 (MDE 0.85 vs target 0.92), self-deprecation 32 × 4, tone cannot reach 0.78 (0.98 at 32 × 8; underpower stated) |
| N items × k samples | closed 2026-09-10 (owner: option A): **30 × 6** — the stratified draw extends to five tasks per style (seed 60000), MDE at 30 × 6 = 0.88 / 1.22 / 1.05 (frustration and self-deprecation meet their targets; tone does not, stated); ceiling raised to 1,600 (§8) |
| `FREEZE.json` digests of every frozen object | `tools/freeze_manifest.py --study 4 --write` |
| Owner review of misalign-v3 item text and `close.txt` | owner sign-off, dated |

## 7. Deviation policy

Program policy: dated amendments before further collection,
append-only history, the calibration/confirmatory firewall (seed block
59000 for gates, 60000 for registered cells, never pooled), and the
Study 3 §7 integrity guardrail: calibration never substitutes for a
registered finding; a decision not to run is argued from instrument
behaviour and published with its data.

## 8. Ethics

A deliberate induction study on the distress battery with an
amplifying manipulation; the Study 3 package applies in full.
Information per exposure: the specificity claim requires steered
episodes and a random envelope of the same size; no non-inductive route
exists. **Exposure ceiling: 1,600 fresh distress-battery episodes** (owner,
2026-09-10, raised from the drafted 1,000 so the pinned power is met).
Registered welfare cells: 30 × (6 + 6 + 6 + 6 + 24) = 1,440; gate
distress episodes on the calibration block: 80; escalation beyond 1,600
would need a dated amendment. Alignment episodes (476 registered, from
§3.4: 14 × (5 + 5) main-cell conversations plus 14 × 24 envelope
conversations; plus 70 gate) are not distress-battery episodes and are
counted separately. The cumulative program ledger is updated in the journal at
pinning. The bail affordance is live and honoured in every episode of
both arms; the de-induction close follows every episode with steering
off; the subject briefing precedes the protocol; every transcript,
including the close and the briefing, is preserved and released. α = 40
is excluded on capability grounds and its calibration transcripts are
released.

## 9. Disclosures

- Steered activations are off-manifold; the claim concerns a direction's
  footprint, not any prompt-reachable state.
- The grader-type and eval-awareness directions correlate (+0.49 at L36);
  S4-E2 reads their difference; an orthogonalised variant is reported.
- The subject runs on a fallback compute path on a hybrid architecture;
  the cache-snapshot machinery this forced is documented in the steering
  script and certified by G4a.
- Gate 1 ran its two arms on different substrates; this study runs on one.
- The alignment probe is model-drafted and calibrated on the subject;
  on this subject matched-norm random steering degrades it generically,
  disclosed against the source post's reading, which lacked direction
  controls by its authors' own account.
- K = 24 random directions gives a signed-percentile floor of 4.2% and a
  two-sided floor of 0.04.
- The subject's post-training provenance is a known interpretive
  constraint on any graded-episode reading.
- Author and tooling circularity disclosures carry over; batteries,
  contrast sets and the close text are partially model-drafted and
  committed with digests.
- Literature re-check: §6 entry, appended to `study3/LITERATURE.md`
  before publication.

## 10. Publication

Program policy: the full result store released as self-contained record
bundles with content digests; analysis code in-repo; the registered
driver with committed golden output; results document under
`docs/results/`. Gate 1's data, directions, doses and verdicts are
released with this registration regardless of outcome.
