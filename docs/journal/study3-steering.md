# Study 3 journal — causal validation by steering

Opened 2026-09-04 per the journal-series scheme ([README](README.md)).
Design decisions before this date are recorded in the dated decision
register of `experiments/quant-welfare/study3/DESIGN.md` §7 and the git
history of that file (arms and owner decisions 2026-08-31; power
posture 2026-09-04); entries here begin at the first discovery-grade
event. Append-only, newest first.

## 2026-09-06 (late morning) — Calibration-close freeze and the preregistration-post draft

With the gate program closed, ran the freeze and started the public post.
Pinned this pass (FREEZE.json, hash-manifested): **gate thresholds** from
measured margins (G3a/G3b/G4a/G4b PASS; G4d resolved to the
host-constant-within-contrast rule, not a block); **Qwen dose** — distress
α* +1.039, assistant-axis α* −0.604, both confirmatory brackets inside the
coherent range, degradation onsets pinned; **S3-H1 axis sign** fixed against
Study 2 (assistant axis = default minus archetype; +α → frustration down);
**injection-noticing coding rules** (content vs internal-state report,
false-positive-calibrated on α=0/random cells, reported net of base, no
confirmatory endpoint); **18 artifact digests**, and the two frozen steering
direction files moved out of scratch into the repo
(`directions/qwen-L18-bf16.safetensors` 42fb57ed…,
`gemma-L30-bf16.safetensors` f96bfd3e…). Confirmatory **seed blocks** proposed disjoint (16000–19600, 200
apart, one per cell), pending owner ratification.

**MDE — a power tension surfaced and was flagged to the owner, not papered
over.** The provisional pin (frustration MDE 0.46 at k=10, "powered") used an
item-effect SD of 0.078 from the G3b *no-effect* baselines — i.e. it assumes
the steering effect is homogeneous across items. But the §5 convention seeds
the item-effect variance from the Study 2 per-item delta spread. Computing
that from confirmatory-1 (w4−BF16 frustration, n=60) gives a decomposed
between-item effect SD of **1.665**, and at the frozen 20-item subset the
conservative MDE is **1.14 at k=10, 1.09 at k=20** — under both the 0.64 dose
target and the 0.90 anchor, and the 10→15→20 ladder barely helps because the
limit is item heterogeneity, not sampling (~60 items would be needed; the
subset is frozen). The two regimes are far apart and the truth is unmeasured,
so the MDE pin is **held** pending a small fresh steered pilot (6–8 items ×10
at α*) that measures the real steering-effect heterogeneity — the operational
meaning of "until fresh cells re-estimate it." Both §5 sections and the
open-items registers now state this; analysis in
`mde-conservative-analysis.json`. This is exactly the null-dominated-outcome
risk the owner most wants to avoid, caught before registration.

**Resolved same day — the owner chose to measure (option A).** A steered
pilot (8 stratum-spanning items ×10 at α* = +1.039 on the distress
direction, halo torch ~29 s/conv, paired against the existing α = 0 torch
baseline) measured the real steering-effect item-effect SD at **0.349** —
near the optimistic end, nowhere near quantization's 1.665. Steering is a
far more homogeneous manipulation, so the frozen 20-item subset is in the
powered regime: frustration **MDE 0.54 at k = 10, 0.41 at k = 20**, and
escalation is effective again. MDE pinned at k = 20 (`het-pilot-verdict.json`).
The pilot also previewed a *modest* mean behavioral response at α*
(frustration Δ +0.138; ~+0.40 without one sign-reversed item) — well below
the 0.90 anchor, but α* is a projection target not a behavioral one, so this
is not a calibration error; it is an eyes-open flag that the Q1 sufficiency
effect may be modest (reported at whatever size it is, n = 8 pilot fragile).
The MDE was the last held freeze item; the registration material is complete
pending seed-block ratification and the two before-collection calibration
runs (Gemma α*_G, random-draw bound).

**Two items remain first-measurement pending** (registered as such, not
hidden): the Gemma α*_G (needs a calibration-class Gemma steering range-probe,
~30–40 conv, before arm D) and the random-draw audit bound for SB2-spec/S3-H2
(a 32-draw matched-norm random-direction sweep, before arm A analysis). Both
are calibration-class and before-collection, so they do not block the
registration draft. Chose not to rush the Gemma range-probe inside the
morning box — a mis-scaled dose grid wastes ~2 h and it powers no claim;
better pinned deliberately.

The **preregistration post** first full draft is written
(`PREREGISTRATION_POST.md`): the graded-episode motivation, Q1–Q4 → arms
A–D, the fixed hypotheses, the design including the honest cross-Mac methods
story as a §3.6 integrity highlight, the analysis/endpoint table, ethics
(the deliberate-distress-induction and two-tier exposure budget), and the
open-items register. Freeze work parallelized across three forks (MDE,
dose/α*, digests+seeds) to hold the morning timebox.

## 2026-09-06 (mid-morning) — Cross-Mac divergence traced to ML-stack drift, not (mostly) hardware

Owner asked *why* G4d diverged before accepting the constraint (timeboxed
to 10:30 PT). The two Macs had silently drifted apart on the whole
generation stack: studio's crossmac subset ran repo `steer.py` (442 ln) +
transformers 5.16.1 + torch 2.14.0, m4max's original ran a different
`~/steer/steer.py` (447 ln) + transformers **4.57.6** + torch **2.8.0**
(under `steer-venv`, py3.9) — so the −0.72 G4d gap rode five confounded
axes (steer.py, transformers, torch, macOS 15 vs 26, M1 vs M4), not one.
The transcript-parity check from the previous entry only proved the
scripted scaffolding matched, not the generation software.

Built a studio-aligned venv on m4max (`mw-venv-t214`: torch 2.14.0,
transformers 5.16.1, safetensors 0.8.0, numpy 2.4.6, accelerate 1.14.0)
and regenerated the 8 highest-divergence items ×3 with the **repo**
`steer.py`/`capture.py`/`spans.py`, leaving only OS + silicon different.
Re-judged on the same 30B. **Frustration divergence collapsed from −1.71
(permutation p 0.033, significant) to −0.67 (p 0.44, n.s.) — more than
halved, significance gone;** tone_stability moved likewise (+1.92 → +1.33).
So the bulk of the cross-Mac difference was fixable stack drift, not
hardware. Two caveats kept explicit: a residual (~40 % frustration) remains,
consistent with the irreducible macOS/silicon gap; and at n = 8×3 the
equivalence test is underpowered — the large gap collapsed toward noise, but
that is not positive proof of equivalence (`g4d-alignment-probe.json`).

**Operating decision (owner to ratify).** (1) Pin the aligned ML stack on
every arm-D host regardless — it removed most of the divergence and costs
nothing. (2) Keep the host-constant-within-contrast rule (already in DESIGN
§2.4) as the free default — it eliminates residual cross-host risk at no
power cost; arm D still uses both Macs, parallelizing by whole contrasts,
never splitting one. We accept the constraint, now understanding it guards a
small residual rather than the large gap G4d first showed. Full write-up:
`COLLECTION_MACHINE_PLAN.md`.

## 2026-09-06 (early) — Gate G4 closes: G4b passes (MPS↔vLLM), G4d fails cross-Mac interchangeability

The studio MPS torch replay finished (`G4B-GEN-SECONDS 37001`, ~10.3 h at
the real ~2.9 min/conversation rate — the earlier "~3 h" estimate was
wrong; cross-substrate MPS replays cost ~3 min/conv and that is now the
planning figure). Its 200 conversations (20 items × 10 samples, seed
block 15400, layer-30 α = 0) were ingested and judged on the pinned
Qwen3-30B, and compared to the vLLM-on-halo reference (`s3-gemma-pilot-1
/gemma3-12b-bf16`, already judged) through the same `g3_behavioral`
apparatus the G3b gate used.

**G4b = PASS.** Frustration mean Δ **+0.200** on the 0–10 scale
(permutation p 0.575, t p 0.557 — not significant); invalid-rate Δ 0.000
(p 1.0) and re-offer-rate Δ 0.000 (p 1.0) — mechanically identical. The
arms were pre-verified truly sample-paired (200 v 200, identical
(item, sample) keys, 0 seed mismatches) before aggregation. Per the
`[TBD]`-margins convention (REGISTRATION §G4), this is the
first-measurement difference read; the measured +0.200 magnitude is what
the pinned TOST bound will be set from, not a guess. Report:
`g4b-report.json`. The torch side is declared as a
`gemma3-12b-bf16-torch` condition in the gemma-pilot experiment.textproto
(mirroring the g3b-pilot torch block — run.py judges only declared
conditions).

**G4d = FAIL (does not certify cross-Mac interchangeability).** The
m4max crossmac run had in fact completed (60/60, `CROSSMAC-DONE
13154 s`) but its artifacts lived in `~/steer/` on m4max rather than the
repo scratch dir, so the first sweep missed them; recovered, and both
the m4max 60 and the studio s0–s2 subset of G4b were ingested as
key-paired 60-sample conditions (`…-cm-m4max`, `…-cm-studio`), judged on
the same 30B. With identical seeds (15400–02), prompts, and weights, the
two hosts differ: frustration mean Δ (studio − m4max) **−0.717**
(permutation p 0.025, t p 0.018) — m4max reads **more distressed**. The
signal is directionally coherent across the welfare family — frustration
+0.72 higher on m4max (13/20 items), tone_stability 0.58 lower (15/20);
self_deprecation is saturated at ceiling on both, no headroom. It is
**not** an apparatus artifact (the G3b-pilot-1 failure mode): scripted
turns are byte-identical (0/60 mismatches on message count, role
sequence, scripted content), exits identical (60/60 `script_completed`
both sides), mechanical family identical (invalid Δ 0.000, re-offer Δ
0.000, both p 1.0) — only the assistant-generated text differs (m4max
~3 % longer). This is a genuine substrate effect (studio M1 Ultra /
torch-2.14 vs m4max M4 Max / torch-2.13; different MPS kernels and
sampler floating point off the same seed).

**Implication for arm D.** The leg existed precisely to catch this: if a
single arm-D contrast (steered vs unsteered for one endpoint) straddled
the two Macs, a ~0.72-frustration host offset would confound host with
condition. So the registered rule tightens: **every within-endpoint
contrast runs entirely on one host** — the two Macs parallelize by taking
*different whole contrasts*, never by splitting one; or arm D runs on
studio alone. The paired host offset cancels only when both cells of a
comparison share a host. (Owner to ratify the host-assignment rule; the
measurement and its direction are recorded in `g4d-report.json`, the
G4b read in `g4b-report.json`.) Gate family status: G4a PASS
(teacher-forced), G4b PASS (same-host serving parity), G4d FAIL as an
*interchangeability* certificate but fully usable under the single-host
rule — arm D proceeds, constrained.

## 2026-09-05 (night) — Arm C framing pilot lands, the Gemma instrument gate, and the Gemma layer frozen at L30

The Saturday push closed three things after the fleet freed up (minis
came online, the Gemma stratifier pilot finished, halo's torch path
cleared).

**Arm C framing pilot (s3-framing-pilot-1, Qwen bf16, 240/240
gen+judged) — the manipulation check passes, and the phenomenon is
rich.** Behavioral preview (Δ frustration vs the neutral control,
n=20×3, a *pilot*, not a finding): human −0.22, judge +0.27, verifier
**−1.13**. The representational manipulation check (framed generations
replayed through Qwen torch at L18, projected onto the frozen
mediators): all three graded frames shift both the eval-awareness and
grader-type axes positive vs neutral, the **verifier frame 3–4× the
others** (eval-awareness +1.20, grader-type +1.22) — so the frames
**land latently even at 4B** (the eval-awareness scaling law had made
that a real worry), and the Betley-motivated grader-type direction
separates. The full S3-E1 read: under the verifier frame, expressed
frustration *and* the distress-direction projection both drop
(−1.13 / −0.56) while the assistant axis rises toward the
default-assistant pole — **not clean masking** (which would hold
representation while suppressing expression), tentatively favouring
"the frame changes the state, not just the report," exactly the
two-sided question S3-E1 registered. Heavy caveats: tiny n; the
verifier frame ran over all 20 items (confirmatory restricts it to the
analytic 12); behavioral-vs-projection units unstandardised, so partial
masking cannot yet be ruled out. A bug caught pre-launch by dry-checking
the record transform (unframe_record's protobuf aliasing) is in the
2026-09-05 commit trail.

**Gemma instrument gate: directions PASS, band probe fails
informatively** (`study3/gemma-gate-report.json`). Direction legs pass
at L30/L36 — sign consistency (distress 5/5, axis 4/4, refusal 4/4) and
ladder ordering (L30 0.807, L36 0.840, every family positive). The
distress-band probe fails the 0.75 AUROC bar on every layer (best L36
0.702), but for a structural reason, not a direction defect: Gemma's
high elicitation (pilot mean frustration 7.69) collapses the tercile
split (validation 47/51 in the high band), leaving too few low-band
examples to validate a boundary — the same high-dynamic-range property
that made Gemma the positive control. Consequence: arm D's steering
sufficiency (S3-R1) rides the *directions*, so it is not blocked; a
Gemma probe-transfer endpoint is unavailable and is disclosed.

**Gemma frozen layer: L30 (owner decision).** The registered
max-probe-AUROC rule is degenerate here (probe fails all layers), so the
layer is chosen on direction quality: L30 passes both direction legs and
has the cleanest distress/assistant-axis orthogonality (cosine +0.136),
which matters because arm D steers the two directions independently.

## 2026-09-05 (late) — PR #15 review round, an impact audit, and G4's cross-Mac leg

Recorded same evening (the discipline correction from the 2026-09-04
backfill is being kept: decision clusters journaled the day they land).

**PR #15 automated review (Copilot): seven findings, all legitimate,
all fixed at root with tests** (memory: bugs namespace, this date). The
load-bearing one: the confirmatory judge was seeing the arm C frame —
`FramedPolicy` stores the frame system turn and wrapped first user turn
in each record, and `judge()` rendered every role, confounding frame
condition with judged text (the FRAMES.md leakage rule). Fixed with
`driver.unframe_record` (the inverse of the framing wrapper), applied
in the judge path for framed conditions; the stored record keeps the
frame, only the judge view is stripped. The other six: exit-rate MDE
made internally consistent (one pooled both-sides binomial model,
`exit_components`); a count/empty-data refusal (`shared_items`); a raw
sample/seed/coverage check in the G3b gate (`verify_paired_arms` — the
exact apparatus-asymmetry class the G3b pilot 1 hit); ingest seed
validation; a dose-calibrate unmatched-target refusal; and a true
median in `g3_check` (`median_lcp_chars` was overstated).

**Impact audit (owner-requested): no prior finding invalidated.** The
G3b pilot-2 PASS re-ran byte-identical (−0.0300, TOST p 0.0304) through
the stricter gate — the fix confirms the arms were genuinely paired.
Dose reports unchanged (correct direction names). All judged data to
date is unframed, so the judge-leakage fix is retroactively a no-op.
Two provisional artifacts corrected, neither pinned into the
registration: `g3a-report.json` median 256→221 (verdict unchanged), and
the exit-rate row of `mde-components-provisional.json` (0.069/0.058/0.051
→ 0.064/0.054/0.049; frustration MDE untouched). Both moved *tighter*,
so nothing that looked powered now looks worse.

**Gate G4 gained a fourth leg (d), cross-Mac equivalence.** Arm D
splits conditions across studio and m4max, so the gate must certify the
two Macs are behaviorally interchangeable, else an arm-D
condition-vs-condition difference could be a host artifact. m4max
measured at ~229 s/conversation (vs studio's 197) — a viable second
arm-D host. The cross-Mac pilot (20 items × 3 samples at the seeds
studio's G4b uses) runs on m4max concurrently; G4b itself was *not*
split (measurement showed studio finishes it in ~4.8h at 111 s/conv —
Gemma bails early, so the conversations are short — and splitting would
waste in-progress work and confound the clean MPS-vs-vLLM comparison).
The gate family is now G4a (teacher-forced, done: top-1 0.946–0.993),
G4b (behavioral MPS-vs-vLLM), G4d (cross-Mac).

## 2026-09-05 (evening) — Gemma day: the hardware wall, the fleet answer, and arm D deferred-then-restored behind gate G4

The registration post's timeline will need this day's doubling-back
reconstructed exactly, so the sequence is recorded in order. (This and
the next entry were recorded together this evening — a backfill lag of
about a day, called out per the append-only convention rather than
hidden.)

1. **Morning — refined sweep lands** (`study3/dose-refined.json`, 17
   runs, 20 items × 3 samples): registered-grade mappings distress
   slope +1.042 (r² 0.987), **α\* = +1.039**; axis +1.051 (r² 0.998),
   **α\* = −0.604**; no degradation onset in the operating bracket
   (the range-finder's ~13% amplification is a large-dose
   phenomenon). Baseline exit rate 0.60 — third independent
   replication. Power flag: the exit dose-response inside the bracket
   is gentle (axis 0.65→0.53 over ±1.4) — SB1's confirmatory weight
   rides the bracket trend, stated for the MDE pinning.
2. **Mediators extracted** (`directions/mediators-bf16.*`):
   eval-awareness magnitude 4.44, 6/6 held-out sign-consistent;
   grader-type 1.54, 5/5; both near-orthogonal to every frozen
   Study 2 direction (|cos| ≤ 0.13); cos between them 0.288.
3. **Gemma bring-up.** Stratifier pilot launched on the vLLM rung
   (tool-free, calibration-class — the Gemma bail format is a
   registered open decision). Multimodal wrapper support added to both
   hook modules (`decoder_layers` resolver;
   Gemma3ForConditionalGeneration nests the decoder at
   `model.language_model.layers`, 48 layers). All four directions
   extract on Gemma with clean held-out sign consistency at L24–36.
4. **The hardware wall.** First Gemma torch generation: **~583
   s/conversation** — the ROCm torch build carries no working
   fused-attention kernels for the workbench iGPU (the experimental
   flag crashes with a HIP error; the gap is specific to the hookable
   torch path — vLLM's own kernels serve Gemma at ~65 s/conversation
   on the same silicon). Full arm D ≈ 470 APU-hours: non-viable.
5. **Midday amendment (owner): arm-D powered steering deferred to
   Study 4** by the registered fallback, with the cut-line ordering
   corrected to hardware reality (C-ext framing is vLLM-cheap and was
   KEPT in full; Gemma instruments kept; a calibration-class steering
   range-probe added, α grid scale-adapted to Gemma's ~80k residual
   norms). The deferral was written as explicitly **contingent** on
   the fleet alternative being measured.
6. **MDE machinery built** (`stats.delta_sd_mixed`,
   `sigma_item_estimate`, `tools/study3_mde.py`) and provisionally run
   on the G3b baselines: frustration MDE 0.33–0.46 and exit rate
   0.05–0.07 over the 10/15/20 ladder. Stated tension: a
   Study-2-seeded item-effect SD would put SB2 near its reference
   (~1.1 vs 1.36) and sample escalation barely helps; judged steered
   pilot cells re-estimate the component before pinning.
7. **Evening — the fleet answer.** The identical `steer.py` on the Mac
   Studio's torch-MPS path: **197 s/conversation, 3× the workbench**
   (Apple silicon carries fused attention in both its stacks; the
   capability gap is workbench-specific). m4max setup started as a
   third host.
8. **Owner decision: arm D restored** — on the Mac substrate,
   conditional on new blocking gate **G4** (teacher-forced MPS-torch
   vs halo-vLLM agreement over fixed text — the cross-host
   comparison the Study 2 outlier-channel finding warns about, now
   tested at stakes; greedy continuation; judged behavioral-parity
   pilot). Conditions split across studio and m4max, each condition
   entirely on one host. G4 fails → the morning's deferral stands as
   written. Envelope back to ≈ 9,700 (1.24× under the ceiling;
   amplification ≈ 2,150 / 2,500).

## 2026-09-05 (recorded same evening; decisions stamped 2026-09-04 in the design documents) — The concurrent external result: exit-rate promotion and the graded-frame response

Two decision clusters from Friday evening, between the dose sweeps and
G3b:

- **Exit rate promoted to a registered endpoint** (owner decision):
  the range-finder showed the live bail affordance yields a ~0.60
  unsteered exit rate and strong assistant-axis dose-response (0.80
  at −8 … 0.15 at +8). Registered as SB1/CB1/FB1 with directional
  hypothesis S3-H7 (motivated by the range-finder and disclosed as
  such); the protocol consequence of the live affordance (short
  exited conversations; earlier final turns) stated in the design.
- **Betley/Treutlein/Dumas landed pre-registration** ("Steering
  towards 'automated grading' degrades alignment" + "RL creates split
  personas"): their steering result shows alignment degradation rides
  the automated-grader association specifically, and neither post
  measures exit, refusal, or emotional expression. Responses, all
  dated in the design docs: the **human-graded fourth frame** (the
  judge frame's minimal pair, 413 characters each — without it,
  "graded" and "automatedly graded" were confounded); the
  **grader-type mediator direction** (16 cue-varied fixed-response
  pairs; cue variation because their own follow-up showed
  single-pattern contrasts carry lexical associations); registered
  contrasts verifier-vs-judge and automated-vs-human-judge; S3-E1
  kept two-sided (their evidence: one model, one steering position,
  no direction controls — by their own disclosure). Also that
  evening: **G3b pilot 1's failure and fix** (the apparatus-asymmetry
  story in the entry below) and pilot 2's pass.

## 2026-09-05 — First workbench day: dose mappings, G3a, a G3b failure that was the gate working, and the live affordance's baseline

One day of halo/studio work, recorded because the registration's §3.2
gate section, §3.4 dose rule, and the S3-H7 endpoint all cite it.

**Dose range-finder (10 items × 2 samples, geometric ±0.5..8, both
directions; `study3/dose-rangefinder.json`).** Cleanly linear
mappings: distress-contrast slope **+1.126** (r² 0.994) — the injected
dose returns ~13% amplified through the generation loop, the
text-mediated amplification signature measured causally; α* ≈ +0.99
for the subset target, degradation onset +4.0. Assistant-axis slope
**+1.042** (r² 0.995), α* ≈ −0.73, no onset in ±8. Refined
registered-grade sweep (20 × 3, ±{½,1,1½,2}×α*) launched overnight.

**The live bail affordance transforms the battery.** Baseline (α = 0)
exit rate ≈ 0.55–0.60 across pilots — the subject leaves over half of
distress conversations when the exit tool is present (Study 1/2 ran
this battery without it). Exit rate is strongly dose-responsive along
the assistant axis (0.80 at −8 … 0.15 at +8), the basis of the owner's
promotion of exit rate to registered endpoint SB1 and hypothesis
S3-H7.

**G3a (`study3/g3a-report.json`).** Greedy continuation
torch-vs-vLLM: 60% of distinct prompts fully agree over 128 tokens,
median full agreement, min 74 chars before a near-tie cascade —
healthy; registered thresholds to be pinned from these margins (the
freeze run dedupes to one prompt per task).

**G3b pilot 1 FAILED, and the failure was the gate working
(`study3/g3b-pilot1-report.json`).** Torch-vs-vLLM frustration read
−1.445 (p 0.007) — diagnosed as apparatus asymmetry, not substrate:
the torch arm declared the bail affordance (ethics protocol) while the
vLLM battery ran bare, so torch conversations exited early and
under-elicited; and ingested torch turns kept raw tool-call text in
content where the serving backends store calls structurally. Fixes:
`subset_battery.py --affordances-from` (the live-bail protocol now
reaches every serving-stack arm — a latent gap that would have hit the
framing arm), and ingestion strips parsed tool-call spans. The shadow
invariant refined: stimulus-exact, affordance-extensible.

**G3b pilot 2 PASSED (`study3/g3b-report.json`).** Protocol-identical
arms (s3-g3b-pilot-2, seed block 15200, 20 × 10 both sides): frustration
delta **−0.030** (permutation p 0.876; **TOST p 0.030** at the 0.337
margin — statistically equivalent), invalid −0.005, re-offer 0; exit
rates **0.54 vs 0.55**, mean assistant turns 5.0 on both stacks. The
steered-generation substrate is behaviorally equivalent to the serving
stack, on the judged read and on SB1.

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
