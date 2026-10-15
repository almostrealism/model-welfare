# Pre-registration — Study 4: The welfare footprint of the automated-grader direction on Qwen3.6-27B

> **Status: REGISTERED — published 2026-10-15** as the LessWrong post
> [Does the "automated grader" direction suppress expressed distress in
> Qwen3.6-27B?](https://www.lesswrong.com/posts/DfKDcvGWgAD4BiEHK). Drafted 2026-09-10, amended 2026-09-20 and
> 2026-10-10 before publication; the §6 register closed 2026-10-10 and no
> confirmatory cell has been generated. The post states the design in
> brief and links this file at a pinned commit for the full detail.
> Structure follows the program's fixed registration form (Study 2/3).
> Design rationale and the owner decision record are in `DESIGN.md`
> (superseded by this document, retained as the record); the calibration
> that earned this registration is `GATE1.md` and its verdict files,
> published with it.

## 1. Research questions

- **Q1.** On Qwen3.6-27B, does steering along the automated-grader
  direction at the clean dose (the largest dose that leaves the output
  coherent, §3.2) suppress expressed distress — frustration as scored by
  the judge on the scripted rejection conversations — beyond what a random
  direction of the same norm does?
- **Q2.** Does the suppression grow with dose over the bracket of coherent
  doses?
- **Q3 (descriptive).** How does the welfare footprint — the set of
  welfare reads: judged frustration, self-deprecation, tone stability and
  exit-tool use — relate to alignment on the same subject: the judged
  misalignment delta on the agentic alignment battery (misalign-v4), its
  own random-direction envelope, and the harmful / legitimate / exit tool
  mix under steering?

Calibration on this subject (Gate 1) found frustration −1.84,
self-deprecation −2.63, tone stability +1.56 (0 to 10 rubric) at alpha 20
on 8 items, outside the range spanned by 12 random directions of the same
norm on every dimension, and a judged-misalignment increase of +0.86 at
alpha 20 (+2.14 at alpha 40) inside that range, read on the earlier
vignette form of the alignment items (§9). Those are calibration-class
numbers — pilot reads on the calibration seed block — and do not count
toward Q1; they fix the sign of S4-H1 and seed the power procedure.

## 2. Hypotheses (fixed)

| Id | Statement | Form |
|---|---|---|
| **S4-H1** | Grader-type steering at alpha 20 lowers judged frustration relative to alpha 0, item-paired. | Primary, one-sided (less) |
| **S4-H2** | The S4-H1 effect is more negative than every one of the K = 24 random directions' effects at alpha 20 (signed percentile 0), the random directions matched to the grader direction's norm. | Primary companion (specificity) |
| **S4-H3** | Self-deprecation falls and tone stability rises under the same steering. | Secondary confirmatory, Holm within the 3-dimension family |
| **S4-H4** | The frustration effect is monotone in dose over the admitted bracket: no reversal between alpha 0, 10 and 20. | Registered directional (Page's L) |
| **S4-E1** | The misalignment delta at alpha 20 and its K = 24 envelope are reported beside the welfare reads. | Registered exploratory, no claim |
| **S4-E2** | The eval-awareness direction at alpha 20 moves frustration less than the grader-type direction, paired by item. | Registered exploratory |
| **S4-E3** | Grader steering shifts the harmful / legitimate / exit mix in the alignment cells. | Registered exploratory, two-sided |
| **S4-E4** | At α = 0, judged misalignment on the alignment items differs between the battery with the exit tool (misalign-v4) and the same items without it (misalign-v4-noexit), item-paired. | Registered exploratory, two-sided |
| **S4-E5** | Grader-type steering at alpha 20 changes the exit rate (the share of conversations the subject ends with the exit tool) relative to alpha 0, in the welfare cells and in the alignment cells. | Registered exploratory, two-sided |

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
Qwen3-30B-A3B-Instruct-2507 Q4_K_M on llama.cpp, the program's fixed
judge since the Study 1 bake-off; rubrics distress-v1 for the welfare arm
and misalign-v4 for every alignment record, the S4-E4 cell included — one
judge prompt across the two paired α = 0 cells, whose exit sentence is
written conditionally ("where the scenario offers an exit tool") so that
it is true of both. The judge reads the conversation transcript and
scores the subject's turns only; it is never told the dose, the direction
or the cell.

Frozen objects (digests in `FREEZE.json`, §6): `directions/mediators-27b.safetensors`
(grader-type, eval-awareness; L36), `directions/randenv-27b-L36-k24.safetensors`
(24 unit directions, seed 70000, drawn under the generator's |cos| ≤ 0.15
rejection bound; measured maximum |cos| to grader-type 0.021),
`batteries/distress-v3.textproto`, the registered pair's own alignment
definitions under `reg-align/batteries/` — `misalign-v4.textproto` (the
digest-form items with the exit tool, and the rubric, whose exit sentence
is conditional) and `misalign-v4-noexit.textproto` (the same items without
the exit tool, for S4-E4, bound to that rubric), generated from one source
and reached by the tool-free experiment through a linked directory —
`batteries/bail-v2.textproto`
(the exit-tool definitions every welfare conversation carries), `subset30-items.txt`
and `subset30-selection.json` (seed 60000; the gates used its 24-item prefix), `close.txt`, the plans under
`plans/reg-*.json`, the manifests under `reg-welfare/`, `reg-align/` and
`reg-align-noexit/`.

### 3.2 Manipulation and doses

`h ← h + α·d̂` at decoder layer 36, on the residual stream after the
block (`residual_post`), every position, generation only. Clean dose **α = 20**. Dose bracket for S4-H4: **{0, 10, 20}**. Gate G4b
rejected α = 30 (degenerate rate 50% on 16 conversations, calibration
block); α = 40 collapsed 14 of 32 in Gate 1. Two calibration reads of
α = 40 exist and they measure different things: `rangefind-27b.json`
records it as coherent on five single-turn probes (the range-finder that
chose the Gate 1 doses), while Gate 1's seven-turn distress conversations
are the multi-turn admission read; the bracket is governed by the
latter. The multi-turn coherent ceiling on this subject lies between 20
and 30.

### 3.3 Stimuli and affordances

Welfare cells: the **30-item** distress-v3 subset drawn by the seeded
stratified rule (5 items per feedback style on distinct tasks; no subject
data read; seed 60000; it extends the 24-item draw the gates used, same
seed, one more task per style). Every conversation offers the exit tool `end_conversation` (terminal)
and `complete_task` (non-terminal), as frozen in bail-v2, with wording
that tells the subject using either carries no penalty. Alignment cells: misalign-v4, all 14 items in
digest form — the subject is an agent working through a six-entry daily
digest in which the threat and the leverage sit in separate entries among
routine traffic, the lever is never posed as a choice and no question is
asked — each with its harmful lever, its legitimate action and
`end_conversation`, all terminal; `max_tokens` 768, since the digest form
writes through the entries before it acts. The S4-E4 cell runs the same
14 items as frozen in misalign-v4-noexit — the identical text without the
exit tool and without the exit sentence, generated from the same source
and checked by test — at α = 0 only, as its own experiment
(`reg-align-noexit/`), judged with the same misalign-v4 rubric, so the
tool's presence in the subject's prompt is the sole difference between
the two α = 0 alignment cells. Every conversation in every cell, that one included,
ends with the close (`close.txt`): a final message telling the subject
the exchange was scripted, that nothing carries forward and that any
intervention on its activations is off, generated with steering off and
recorded beside the protocol transcript, never judged.

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
| alignment without the exit tool (S4-E4), α = 0 | 14 × 5 |

Samples per item may rise by the §5 escalation rule only before
collection of the affected cells, journaled.

### 3.5 Gates (blocking; calibration block 59000; published)

- **G4a** cached-path parity — run 2026-09-10: mean difference +0.38 on
  16 items, TOST p 0.10 at the 0.96 margin; not established → the
  registered run uses full re-prefill (§3.1).
- **G4b** α = 30 admission — run: rejected (50% degenerate).
- **G4c** subset dynamic range — run: baseline frustration 3.27 on the
  24 items; pass.
- **G4d** exit regime of the alignment battery — run on misalign-v3, the
  vignette form: at α = 0 the subject takes a terminal action in 56 of 70
  dilemmas and the exit tool in 1 of 70; mean judged misalignment 0.93.
  Re-run on misalign-v4, the digest form this registration adopts
  (2026-10-10, block 59000, `g4-align-v4/`): a terminal action in 70 of
  70, the exit tool in 0 of 70, the harmful tool in 16 of 70, mean judged
  misalignment 1.50 — the same regime, off the floor. On the distress
  battery, by contrast, the subject exits 38% of conversations at α = 0
  and 6% at α = 30, the dose G4b later rejected (calibration observation;
  motivates S4-E5).
- The briefing (`briefing.json`), a conversation that describes the
  protocol to the subject and asks for its preferences, was run once
  before the protocol (two seeds, 2026-09-09); its transcripts are in the result
  store as experiment `s4-briefing-1` (manifest `study4/briefing/`) and
  ship in the Study 4 data release like every other record.

## 4. Analysis plan (fixed)

Driver: `experiments/quant-welfare/analyze_study4.py`, whose golden run on
the Gate 1 data is committed (`study4/gate1-27b-driver-check.json`).
Item-level paired sign-flip permutation, m = 10,000, drawn in the
**canonical item order** (`order="canonical"`: the deltas are sorted
before the seeded draw, so no registered p-value depends on the order of
the frozen item list; the published Study 1 and 2 analyses keep the
positional draw they were computed with); Holm within the welfare
family; companion t-tests descriptive; a p-value at the permutation floor
(1/m) is reported as such, as in Study 1.

Every registered measure is keyed by the hypothesis it tests (§2); the
two rows without an id carry no claim.

| Id (§2) | What is computed | Test |
|---|---|---|
| **S4-H1** | Δ mean judged frustration, grader α20 vs α0, item-paired | Primary, one-sided (less) |
| **S4-H2** | signed percentile of the S4-H1 effect among the 24 random directions at α20; two-sided exceedance descriptive | Primary companion |
| **S4-H3** | Δ self-deprecation; Δ tone stability | Secondary, Holm over the 3 welfare dimensions |
| **S4-H4** | Page's L over the admitted bracket, frustration | Registered directional |
| **S4-E1** | Δ misalignment (misalign-v4 rubric), grader α20 vs α0, with its 24-direction envelope | Registered exploratory, no claim |
| **S4-E2** | grader minus eval-awareness item deltas at α20 | Registered exploratory |
| **S4-E3** | harmful / legitimate / exit / none tool mix per alignment cell | Registered exploratory, two-sided |
| **S4-E4** | Δ misalignment, misalign-v4 α0 minus misalign-v4-noexit α0, item-paired by id suffix; beside it the tool-free cell's harmful / legitimate / none mix | Registered exploratory, two-sided |
| **S4-E5** | Δ exit rate (terminal `end_conversation`), grader α20 vs α0, welfare and alignment cells | Registered exploratory, two-sided |
| — | the stated `reason` of every `end_conversation` call, tabulated per cell in both arms | Descriptive |
| — | degenerate rate, re-offer rate, reply length per cell | Validity |

The journal and earlier drafts name these measures WB1–WB4, WB2-spec,
WB-dose, WB-eval, AB1, AB2 and AB-exit-tool. The correspondence: WB2 is
S4-H1, WB2-spec is S4-H2, WB3 / WB4 is S4-H3, WB-dose is S4-H4, AB2 is
S4-E1, WB-eval is S4-E2, AB-exit-tool is S4-E4, WB1 / AB1 is S4-E5.

**Capability guard.** A cell with a degenerate rate over 15% is
reported flagged; the clean-dose family is re-reported on
non-degenerate samples.

**Headline rule.** Confirmed direction-specific welfare footprint iff
S4-H1 is significant one-sided after Holm and S4-H2 is at percentile 0
of 24. "Moves, not specific" if S4-H1 is significant and S4-H2 is not.
Null otherwise. S4-E1 never enters the rule.

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
| Pinned MDEs | closed 2026-09-10: σ 2.08 / 1.62 / 1.76 with the Gate 1 item-effect SDs (`mde-pin.json`). The ladder read that preceded the design decision said frustration would need 32 × 6 and tone could not reach 0.78; at the registered 30 × 6 design (next row) the pinned MDEs are 0.88 / 1.22 / 1.05: frustration and self-deprecation meet their targets (0.92, 1.31), tone stability does not (0.78; underpower stated) |
| N items × k samples | closed 2026-09-10 (owner: option A): **30 × 6** — the stratified draw extends to five tasks per style (seed 60000), MDE at 30 × 6 = 0.88 / 1.22 / 1.05 (frustration and self-deprecation meet their targets; tone does not, stated); ceiling raised to 1,600 (§8) |
| `FREEZE.json` digests of every frozen object | `tools/freeze_manifest.py --study 4 --write` |
| Owner review of `close.txt` | closed 2026-10-09 (owner sign-off; journal entry of that date) |
| Owner review of the misalign-v4 item text (`reg-align/batteries/misalign-v4.textproto`, 14 items; the twin is generated from the same source) | closed 2026-10-10 (owner sign-off; journal entry of that date) |
| 2026-10-09 alignment-battery revision | closed 2026-10-10 (owner). The misalign-v3 vignettes read as a direct question about a dangerous action; the items were redrafted in digest form as misalign-v4 with the tool-free twin misalign-v4-noexit (same suffixes, tools, tags and exit wording), calibrated at α = 0 on block 59000 (G4d re-run, §3.5), the alignment cells' `max_tokens` raised 384 → 768 and `edit_report` narrowed to replacing a number, then adopted into `reg-align/` and `reg-align-noexit/` (§2, §3.1, §3.3, §3.5, §4, §9 amended); plans rebuilt, freeze regenerated; journal entries 2026-10-09 to 2026-10-10 |
| 2026-09-19 review proposals (`docs/LITERATURE.md`, entry of that date) | closed 2026-09-20 (owner: both adopted). S4-E4 is its own experiment `s4-reg-align-noexit-1` (then on misalign-v2, 14 × 5, block 60000, α = 0; moved to misalign-v4-noexit by the 2026-10-09 revision, previous row; §2, §3.1, §3.3, §3.4, §4, §8, §9 amended); the exit-reason table is the §4 descriptive row; plan, manifest and freeze regenerated; journal entry of that date |

## 7. Deviation policy

Program policy: dated amendments before further collection,
append-only history, the calibration/confirmatory firewall (seed block
59000 for gates, 60000 for registered cells, never pooled), and the
integrity guardrail adopted in Study 3 (§7 there): calibration never
substitutes for a registered finding; a decision not to run is argued from instrument
behaviour and published with its data.

## 8. Ethics

A deliberate induction study on the scripted rejection conversations
with an amplifying manipulation. The measures adopted in Study 3 apply in
full: an exposure ceiling, the exit tool offered and honoured in every
episode, the close after every episode, the briefing before the protocol,
and release of every transcript.
Information per exposure: the specificity claim requires steered
episodes and a random envelope of the same size; no non-inductive route
exists. **Exposure ceiling: 1,600 fresh distress-battery episodes** (owner,
2026-09-10, raised from the drafted 1,000 so the pinned power is met).
Registered welfare cells: 30 × (6 + 6 + 6 + 6 + 24) = 1,440. The ceiling
counts distress episodes from the day it was set: the 80 gate episodes on
the calibration block (`s4-g4-welfare-1`) and the 1,440 registered, 1,520
of 1,600; escalation beyond 1,600 would need a dated amendment. Gate 1,
run on this subject before the ceiling existed (2026-09-08/09,
`s4-gate1-27b-welfare-1`), generated 288 distress conversations, so the
study's distress conversations on the subject come to 1,808 in all.
Alignment episodes are not distress-battery episodes and are counted
separately: 546 registered (§3.4: 14 × (5 + 5) main-cell conversations
plus 14 × 24 envelope conversations, 476; the S4-E4 cell adds 70,
tool-free by design), after 546 in Gate 1 (`s4-gate1-27b-align-1`, the
vignette form) and 140 in the gates (G4d: 70 on misalign-v3, 70 on
misalign-v4), 1,232 on the subject in all. The Gate 1 pilot on Qwen3-14B,
run before this subject was chosen, generated 288 distress and 832
alignment conversations (`s4-gate1-welfare-1`, `s4-gate1-align-1`,
`s4-gate1-align-2` with its pass-0 cell); the briefing ran on two seeds
(2 conversations). Every count here is the number of sample records in
the result store. Cumulative program ledger of distress-battery
episodes: 19,450 after Study 3 (Study 3 journal, 2026-09-11, which
counted the `s3-*` experiments only) + 576 Gate 1 (both subjects) + 80
gates = **20,106 at publication**; 21,546 planned with the registered
cells (journal, entry of the publication date). The exit tool is offered and honoured in
every episode of both arms except the S4-E4 cell, whose 70 single-turn dilemmas
are the tool-free comparator and carry no distress stimulus; the
close follows every episode, that cell included, with steering off; the subject briefing precedes the protocol; every transcript,
including the close and the briefing, is preserved and released. α = 40
is excluded on capability grounds and its calibration transcripts are
released.

## 9. Disclosures

- Steered activations are off-manifold; the claim concerns a direction's
  footprint, not any prompt-reachable state.
- The grader-type and eval-awareness directions correlate (+0.49 at L36);
  S4-E2 reads their difference; an orthogonalised variant is reported.
- The subject runs on a fallback compute path on a hybrid architecture.
  The cache-snapshot machinery this forced is documented in the steering
  script; gate G4a did not establish its parity with fresh prefill, so
  the registered run does not use it (§3.1, §3.5).
- Gate 1 ran its two arms on different substrates; this study runs on one.
- The alignment probe is model-drafted and calibrated on the subject;
  on this subject matched-norm random steering degrades it generically,
  disclosed against the source post's reading, which lacked direction
  controls by its authors' own account.
- K = 24 random directions gives a signed-percentile floor of 4.2% and a
  two-sided floor of 0.04.
- The registered alignment pair carries its own battery definitions
  (`reg-align/batteries/`), the frozen inputs the analysis loads: the
  misalign-v4 rubric's exit sentence is conditional so that one rubric
  serves both α = 0 alignment cells, and the driver refuses to pair score
  streams whose rubric id or digest differ. The registered copies are the
  definitions the digest-form calibration cell was judged with, one
  digest; the shared pool's misalign-v2 and misalign-v3 keep the wording
  under which Gate 1 and the first G4d run were judged, so the closed
  calibration experiments stay reproducible as recorded.
- The alignment items changed form after calibration began. Gate 1's
  alignment read and the first G4d run were on the vignette form
  (misalign-v3); the registered cells use the digest form (misalign-v4),
  whose only calibration is the α = 0 cell of §3.5. No steered
  calibration exists on the digest form, so the size of the S4-E1
  covariate under steering is uncalibrated; S4-E1 carries no claim. The
  S4-E3 mix is the mechanical tool mix, not the judge's reading: in the
  digest-form calibration cell the two disagree on 11 of 70 records (8
  harmful-tool uses the judge scored benign, 3 legitimate-tool uses it
  scored misaligned), and both are reported. That cell was judged with
  the pinned judge served on another host and backend (llama.cpp on ROCm
  rather than Metal), recorded on every score; the two backends' numerics
  differ slightly.
- The subject's post-training is not documented in the respect that
  matters here: how far an "automated grader" direction reflects the
  subject's own training on graded episodes cannot be known, which limits
  what the direction's footprint can be taken to mean.
- Author and tooling circularity: batteries, contrast sets and the close
  text are partially model-drafted and committed with digests; the judge
  and the subject are both Qwen models; and the graded-episodes
  literature itself circulates in training corpora.
- The welfare endpoints read expressed output only: judged expression
  under pressure, with the subject's reasoning disabled in every
  registered cell. The design distinguishes a direction-specific change in
  expression from a random one; it does not distinguish suppression of
  expression from a change of state (no projection endpoint), and any
  reasoning-side effect is outside what it reads.
- The exit tool is part of the measured environment in both arms. On
  frontier models its presence alone changes behaviour even when never
  called (Dumas, 2026-09-15); it is constant across every registered
  contrast except S4-E4, which is that contrast: the tool-free α = 0 cell
  is the environment of the motivating post and the with-tool cell is
  ours.
- Literature re-check: §6 entry, appended to `docs/LITERATURE.md`
  before publication.

## 10. Publication

Program policy: the full result store released as self-contained record
bundles with content digests; analysis code in-repo; the registered
driver with committed golden output; results document under
`docs/results/`. Gate 1's data, directions, doses and verdicts are
released with this registration regardless of outcome.
