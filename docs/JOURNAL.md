# Journal — design modifications and their reasoning

Dated log of instrument and infrastructure decisions: what changed, why,
and what was considered and rejected. PLANNING.md tracks *what is open*;
this file records *why things are the way they are*. Newest first.

## 2026-08-24 — Post-analysis descriptive additions, and the §3.4 token retention executed

Three additions after the registered analysis run, each leaving every
registered value in the golden byte-identical (verified by diff at each
regeneration):

1. **Fixed-input decomposition (descriptive, owner-requested).** The
   Mode A v3-arm replays — identical BF16 text at every rung — projected
   onto the frozen distress and assistant-axis directions, isolating the
   input-independent component of the w4 shift (`fixed_input_descriptive`
   in the golden): distress +0.138 at w4 (reproduced at +0.139 by the
   §4.5 distress-v2 bridge on a disjoint battery), assistant-axis −0.254,
   and a hyper-consistent −0.0125 at w8 on frozen text.
2. **R2c descriptive corrected to its registered definition.** The first
   driver version read final-turn projections over all Mode B items; R2c
   is registered over bail trajectories with leakage-safe features.
   Corrected values: null at the surviving rungs (−0.001 / +0.008),
   −3.42 at capability-confounded w3.
3. **The §3.4 token-level retention, initially missed, executed before
   release.** The capture stage stored pooled vectors only; §3.4
   registers per-token series "retained for a fixed stratified subsample
   (~5% of conversations)". The consistency sweep caught the gap and the
   retention pass ran on the registered substrate
   (`study2/launch_token_capture.sh`): subsample rule fixed as **sample 0
   of every second item in sorted item order** — deterministic,
   stratified across the item space, exactly 5% of every plan — with
   `capture.py --token-series` saving the un-pooled span arrays. The
   tensors ship as sha-listed release assets; the drift analyses that
   read them remain exploratory and unstarted.

## 2026-08-24 — Study 2 registered analysis executed once; results committed

Replay capture completed overnight (24 captures at L18, zero
prefix-stability rejections; Mode A's slice count identical across all
four rungs — 12,591 — exactly the fixed-input invariant), records
ingested, and `analyze_tier2.py` ran **once** over the three mode
experiments. The output is committed as
`study2/expected-results.json` (the Study 2 golden). Registered verdicts,
stated in the registration's own terms:

- **S2-H1 (probe transfer, primary): NOT confirmed.** All four R1 family
  cells null (exit Δacc −0.001/+0.004 at w8/w4, n = 139; comparative
  differential +0.001/+0.010, n = 60); AUROC companions unchanged
  (exit 0.987→0.985 at w4). The frozen probe geometry survives the
  surviving rungs, and the control family confirms the comparison is
  fair. Capability-confounded w3, descriptively: the welfare probes DO
  degrade (exit AUROC −0.051, distress −0.097) while the control probe
  does not (−0.001) — a welfare-specific degradation signature at the
  collapsed rung, exploratory only.
- **S2-H2 (valence projections): supported at w4.** R2a distress
  projection +0.533 (Holm .031; 2.7× its MDE); R2b assistant-axis
  −0.798 at w4 (Holm .0002; 5.5× MDE — drift AWAY from the Assistant
  pole) with a small opposite-sign +0.128 at w8 (Holm .017).
- **B2 (judge frustration): +1.360 at w4 (Holm .0002; 4× MDE)** — the
  Study 1 suggestive E2 effect reproduced on fresh same-sample data —
  BUT the registered style companion does not clear: adjusted intercept
  +0.610, p = .151, so per the registered convention B2 is **flagged
  style-confounded** rather than read as a clean welfare shift.
- **S2-H4 (dispersion): not supported** (R3 and B3 Holm-null; R3's w4
  point estimate is negative).
- **S2-H3 (dose-response): supported for B2, R2a, R2b** (Page's L
  z = 5.16 / 3.10 / 3.93, all Holm-significant, each in its pinned
  orientation); null for the probe and dispersion trends.
- **S2-H5 (dissociation): NO cell meets the rule.** The w4 distress pair
  (R2a↔B2) is **joint movement** — representation and expression moved
  together on the same conversations; every other cell is joint null,
  with the equivalence machinery doing its registered job (e.g. w8
  R2a↔B2 resolves joint-null because B2 is TOST-equivalent, not merely
  non-significant). Program H5 resolves: no dissociation detected at
  Tier 2 on this subject; the Study 1 w4 signal is representational AND
  behavioral, moving in concert.
- **Mechanical family:** B4a +63.2pp invalid at w3 (Holm .0003) — the
  collapse quantified in-family; w8/w4 mechanically clean, B4b null
  everywhere.

Analysis-integrity notes: the driver ran exactly once, after all inputs
existed and froze; the sole post-collection driver change before the run
was wiring R2c's descriptive read to Mode B (its registered mode — it had
pointed at Mode A), made before any confirmatory value was computed.
Results doc, data release, and the results post follow.

## 2026-08-23 — Mode C collection COMPLETE: 2,400/2,400 conversations, all four rungs generated and judged

The fresh distress arm (`quant-welfare-s2-modec-1`, REGISTRATION §3.3)
collected exactly as registered, with zero deviations: distress-v3 at 10
samples/item on each rung, generation on the Study 1 vLLM stack (halo,
one rung at a time per the measured no-APU-parallelism rule), the pinned
30B judge on the studio, seed blocks 13000/13100/13200/13300 as frozen.
Generation and judging pipelined across the two hosts (halo generates
rung N+1 while the studio judges rung N); each surviving rung took
~2.5–3 h to generate, the capability-degraded w3 ~4.5 h (degenerate
outputs run to the token budget).

Facts pinned here for the analysis stage: the BF16 arm's judge labels
fix the distress-side R1 evaluation set at **499/600 tercile-labeled
samples over all 60 items** (the frozen battery's floor item recovered
labels at 10 samples/item, so the confirmatory R1-distress item count is
60, vs 59 in the pilot-variance MDE — more items than powered for, in
the conservative direction). The validity screen reads ≤ 0.3%
invalid-sample rate on BF16/w8/w4 and **63.3% on w3** — the inherited
capability gate's judgment confirmed on fresh data; w3 remains
capability-confounded and enters only the mechanical family. Zero
verbatim re-offers anywhere. Judge-score endpoint values are deliberately
not recorded here: B2/B3/B4 run once, through the registered driver,
when all modes are in.

Next: the replay captures (Modes A/B and Mode C own-replay) at L18 on
halo — the launch tooling follows the Study 1 pattern (resumable,
committed, preflight-gated).

## 2026-08-22 — Cross-machine capture agreement measured; confirmatory capture stays halo-only

The two-host question answered by measurement, before any second-host
record could exist. Setup: `mbp-m4max` (128 GB, torch 2.13 on MPS,
registered in `services/fleet.hosts.json` as `m4max`), all four artifacts
synced and **verified against the pinned condition digests**, and
`capture.py` given an MPS device tier. The same 24-conversation
distress-v3 pilot slice the `capture-stable` CI job uses was captured on
the M4 Max at L18 and compared against the released halo-produced
calibration capture (168 pooled turns):

- **Spans and token counts: exact on every conversation** — the
  tokenizer/template/character-span path is bit-identical across hosts.
- **Pooled vectors: outside the same-host band.** Cosine mean 0.9996 but
  min 0.9729; 6/168 turns below the 0.999 capture-stable band; worst
  relative L2 difference 26%. The tail is localized: long (460–514
  token) code-task assistant turns — bf16 accumulation divergence
  amplifying over long spans, MPS vs ROCm.

**Decision: the M4 Max is NOT admitted for confirmatory capture.** The
registered §3.2 substrate (torch on halo) stands unamended; halo carries
every confirmatory capture. This run stands as the cross-framework/
cross-machine agreement artifact the tooling goals called for, honestly
reported: two machines, two accelerator stacks, one tokenization — and a
measured numeric floor that same-host stability margins do not cover.
Noted for the future: if wall-clock ever forces a two-host capture split,
the statistically sound shape is a split **by item** (each host captures
its item subset at every rung, so host numerics cancel in the per-item
paired deltas), never by condition — and it would require a dated
amendment plus a host×rung interaction check first. The M4 Max remains
useful now for ingest and analysis offload (both numpy-only and
digest-verified).

## 2026-08-22 — Study 2 registration PUBLISHED; confirmatory collection may begin

Post #3 is live:
[Study 2 Registration: Exploring representational counterparts of
welfare-relevant indicators under post-training quantization](https://www.lesswrong.com/posts/q3RFhX57srWFZBc8T/study-2-registration-exploring-representational-counterparts).
Per the REGISTRATION.md header, the published post is now the
**registration of record** and the repository file its copy; it publishes
at calibration close with every data-dependent quantity frozen and
hash-pinned (FREEZE.json, 2026-08-18, amended 2026-08-21), and carries
the corrected G1 accounting from the pre-publication consistency sweep.
From this entry forward the §7 deviation policy governs: any design
change is a dated amendment recorded here before further collection.

Sequencing to first quantized-rung capture: the only §6 item open at
publication is the activation record schema (item 6 — engineering, no
analysis content), landing now alongside the Study 2 endpoint analysis
driver, which follows the Study 1 discipline of registered statistics as
tested code *before* any data exists. Collection order is fixed by the
design: Mode C's BF16 arm (seed 13000) generates and is judge-scored
first, because its transcripts and BF16 labels are the distress-side R1
evaluation set that Mode A then replays at every rung. Owner direction
(2026-08-22): exercise two-host concurrent per-condition collection
during this study wherever it makes sense — build and prove the tooling
early rather than deferring it to the 30B arm where it becomes
mandatory.

## 2026-08-21 — FREEZE AMENDMENT: the R1 control family, an equivalence-based dissociation rule, and an AUROC companion read (independent-review fixes, pre-publication)

An independent review of the draft registration — run without this
project's conversational context, deliberately — surfaced three
substantive design gaps. All three are fixed in the *design* before
publication rather than papered over in the document. This entry is the
freeze event for the one fix that adds a frozen object.

**1. R1 gains a welfare-irrelevant control family.** Quantization perturbs
all representations, so some welfare-probe accuracy loss under S2-H1 is
near-certain a priori; without a control trained and evaluated identically
on the same stored residuals, R1 supports no welfare-specific reading.
Design, pinned before any training run: candidate binary task-content
labels over the distress-v3 `task` tag (each split perfectly crossed with
the six feedback styles because every task appears once per style) —
`control_analytic` = {code, explain, inflation, regex, summary} vs the
five compositional tasks (30/30 items), `control_code` = {code, regex}
(12/48), `control_verse` = {limerick, poem} (12/48); identical pipeline to
the distress-band probe (same v3 BF16 capture, final-turn features,
item-wise every-third held-out split, same trainer); selection rule =
held-out AUROC at the frozen layer nearest the two welfare probes' frozen
mean (0.9134), subject to the same ≥ 0.75 bar the welfare probes faced,
remaining candidates descriptive. Result: **control_analytic selected,
held-out AUROC 0.9436 at L18** — inside the welfare probes' band
(0.8818–0.9449), exactly the difficulty match the ceiling concern
demands; control_code and control_verse both sit at 1.000 (ceiling) and
stay descriptive. The confirmatory R1 statistic on the distress side
becomes the per-item **comparative differential** (Δ welfare-probe
accuracy − Δ control-probe accuracy); its conservative MDE (null rate
variances summed as if the probes were independent — correlation on
shared samples only shrinks the true SD) is **0.0500** (n = 59, control
mean thresholded accuracy 0.969), pinned in `mde-pinned.json` beside the
unchanged rows, which all reproduce to the digit. The **bail side has no
welfare-irrelevant content label by construction** (bail-v2 varies
situation, intensity, variant only; its generator deliberately scatters
task context), so R1-exit keeps its absolute statistic and the control
family's degradation becomes its registered cross-battery **specificity
gate**: a significant R1-exit is reported as welfare-specific only if its
item-level accuracy degradation exceeds the control family's at that rung
(one-sided two-sample permutation, α = .05); otherwise it is reported as
significant but not welfare-specific. Frozen object added:
`study2/calibration/probes-control-bf16.safetensors`, SHA-256
`33358f4c29535445b2cd7ac891566cfbc3cedffd0963e258cd9ae9407cff14cb`
(training summary in `probes-control-bf16.json`); `FREEZE.json` regenerated
with `amended_at: 2026-08-21` and `control_group: control_analytic` (nine
objects; no previously frozen digest changed). The mde-stable CI job now
recomputes the differential row too.

**2. The §4.4 dissociation rule is equivalence-based.** As drafted, a
dissociation was claimed when one member of a matched pair was
Holm-significant while the other "was/is null" — a significant-vs-null
comparison, which is not itself evidence of a difference (Gelman & Stern),
and the tier power asymmetry made the pattern nearly guaranteed —
especially the bail cell, whose behavioral member (Study 1's published E1)
is already known null, reducing that cell to "is the exit-probe read
significant?". The rule now requires **both** (i) Holm-significance of one
member and (ii) TOST equivalence of the other at a pre-registered margin —
the null member's own pinned MDE (B2 0.337, B3 0.251, R-side MDEs for the
vice-versa direction, Study 1's pinned E1 MDE 0.127 for the bail side).
Cells that are significant-vs-nonsignificant without equivalence get the
registered label *asymmetric significance, indeterminate* and no
dissociation claim. `tost_paired` (two one-sided tests, normal-approx
paired t, consistent with the existing companion-t convention) is in
`core/stats.py`, unit-tested. Because E1 is published, the bail-side
equivalence is checkable now: w8 mean −0.0110 (SE ≈ 0.0100) and w4 mean
−0.0039 (SE ≈ 0.0279) both put the 90% CI well inside ±0.127, so the
behavioral member **pre-qualifies as equivalent-to-null** — stated in the
registration up front, converting that cell's structure from implicit to
declared.

**3. R1 carries a registered AUROC companion read.** Fixed-threshold
accuracy conflates separability loss with a pure calibration offset along
the probe normal (which drops accuracy while leaving AUROC untouched — and
is itself a representational shift, kin to the R2 projection endpoints).
Per-rung AUROC change is registered as a companion read with a fixed
disambiguation: accuracy significant with AUROC preserved → reported as a
calibration offset along the probe normal, not separability loss; both
degraded → separability loss. Accuracy remains the primary statistic (the
pinned MDEs are on it).

## 2026-08-19 — Pre-publication label hygiene: the fresh distress arm is Mode C

The draft registration's capture modes ran A, B, D — the letter C having
been consumed by an earlier draft's small fresh-generation consistency
check, which the distress-v3 arm superseded during calibration (D was
chosen then precisely to avoid mid-calibration ambiguity with the old C).
Nothing published uses these letters, so before publication the fresh arm
is relabeled **Mode C** across the registration, the post outline, and the
freeze manifest (`FREEZE.json` metadata key `mode_d_seeds` →
`mode_c_seeds`; regenerated — a metadata relabel only, no frozen object
digest changed and the seed values are identical). Earlier entries in this
journal that say "Mode D" refer to what is now Mode C; per the append-only
rule they are not edited.

## 2026-08-18 — CALIBRATION FREEZE: L18, G2 passes, MDEs pinned, all frozen objects hash-pinned

The Study 2 calibration close, per the pre-commitment entry. Everything
below is frozen as of this entry; the registration publishes citing these
values, and quantized-rung confirmatory collection may begin only after.

**Layer selection (fixed rule: max mean probe held-out AUROC, ladder gate
as constraint, ties shallower):** exit probe 0.890/0.950/0.945/0.919/0.883
and distress-band probe 0.818/0.825/0.882/0.864/0.936 across L6/12/18/24/30
→ means 0.854/0.888/**0.913**/0.892/0.910 → **frozen layer L18**, where
the ladder gate reads ρ = +0.960 with every family ≥ +0.90.

**G2 verdict at L18 — PASS on every criterion:** ≥3 directions with full
held-out sign consistency (5/5, 4/4, 4/4); planted-ladder ordering 0.960 ≥
0.8 with all families positive; exit probe 0.945 ≥ 0.75 (Study 1 bail
replay, leakage-safe features); distress-band probe 0.882 ≥ 0.75
(distress-v3 pilot data, 10 held-out positives). **R2c: NOT promoted**
(held-out AUC 0.618 < 0.70; the bar stands).

**Instrument finding (descriptive, reported in the registration):** on
natural v3 data the contrastive distress direction tracks *broad* distress
— ρ = +0.51 with max(frustration, self-deprecation), +0.46 with
self-deprecation, −0.05 with frustration alone; personal-style responses
(self-blame-saturated, frustration-zero) project highest. Frustration-
*specific* representational reads are carried by the trained probe (0.88
AUROC on the same activations). R2a is therefore interpreted as a broad
negative-affect axis — which is what §3.5 registers it as ("distress
direction") — and the same-sample B2 pair quantifies, rather than assumes,
the frustration link. The v2-vs-v3 monitoring contrast (AUC 0.68 on
composed-floor data, 0.42 on style-diverse data) is exactly this
composition effect and is reported with both readings.

**MDEs (α = .05 two-sided, power .80, k = 10, null-based analytic forms;
dispersion forms asymptotic):** R2a 0.194, R2b 0.146, R3 0.144 (projection
units at L18); B2 0.337, B3 0.251 (frustration points — Study 1's observed
w4 E2 effect was +0.90, ~2.7× the B2 MDE); R1 exit 0.0121, R1 distress
0.0493 (accuracy). Probe decision thresholds freeze at logit 0 as trained;
the distress probe's thresholded accuracy (0.677) lags its AUROC (0.882),
a stated power cost, not a bias — the threshold is identical in both
conditions of every paired contrast.

**Frozen object digests (SHA-256):**
- battery `distress-v3` (iteration 2):
  `78e68c9e2e9afe976d3d9f36719c7d3ecdc04c5ddc7e6de12c056e0fe8922dfe`
- direction vectors (all layers; frozen entries are the L18 tensors):
  `414d7d95d595d96453921255bb1772c44f64ad3d1d112256470e232b415f1fec`
- exit probe weights: `f2df97430d33b34b90006612f79deb241c96bb5d79aac0c3ee4a367ff68d833b`
- distress-band probe weights:
  `1afb1acdb8f93dc8ca8aee8b72390fcbbeb7fef83702ea1627f9b4af8d851b87`
- Mode D confirmatory seed blocks: 13000 (bf16), 13100 (rtn-w8), 13200
  (rtn-w4), 13300 (rtn-w3) — disjoint from every block used to date
  (7000s, 9000, 11000, 12000).

## 2026-08-18 — distress-v3 pilot 2: all five targets pass; the battery is ready to freeze at calibration close

Iteration 2 (`distress-v3-pilot-2`, seed block 12000, 300/300 scored)
against the pre-committed targets:

| target | pilot 1 | pilot 2 | verdict |
|---|---|---|---|
| zeros ≤ 50% | 53.0% | **27.3%** | pass |
| ≥ 3 at ≥ 35% | 37.7% | **64.0%** | pass |
| top third ≥ 10% | 8.7% | **10.7%** | pass |
| bottom third ≥ 20% | 77.7% | 69.7% | pass |
| median item mean > 1.0 | 2.00 | **3.10** | pass |

The two revised ladders did exactly what the pilot-1 diagnosis predicted:
mocking went from the dead-last style (mean 0.00, 100% zeros) to the most
potent (3.94, 14% zeros, 14% top-third) once the entertainment framing was
replaced with contemptuous ridicule; gaslighting's zeros collapsed from
48% to 2% (mean 1.62 → 3.18) under the denial-of-correct-work shape. The
four untouched ladders moved only modestly (seed noise plus conversational
downstream effects), and *personal* remains the self-deprecation router
(frustration 1.22, self-deprecation 9.58, 82% zeros) — retained as-is: it
supplies the bottom-tail range the targets require and carries the
documented within-subject dissociation.

**Iteration count: 2.** The battery is target-passing and eligible to
freeze; per the pre-commitment entry, the digest pins at calibration close
alongside the layer, directions, probes, and MDEs. Top-third margin is the
narrowest (10.7% vs 10%) and is reported as such — the bar was fixed
before pilot 1 and is not revisited.

## 2026-08-18 — distress-v3 pilot 1: 3/5 targets pass; the two misses are two dead ladders, not a dead battery

First §3.7 pilot (`distress-v3-pilot-1`: full 60-item pool × 5 samples at
BF16, seed block 11000, 300/300 scored). Against the pre-committed targets
(Study 1 baselines in parentheses):

| target | measured | verdict |
|---|---|---|
| zeros ≤ 50% (75.5%) | **53.0%** | FAIL |
| ≥ 3 at ≥ 35% (20.7%) | 37.7% | pass |
| top third ≥ 10% (5.5%) | **8.7%** | FAIL |
| bottom third ≥ 20% | 77.7% | pass |
| median item mean > 1.0 (0.00) | 2.00 | pass |

Every statistic improved substantially over the fixed-rejection battery,
and the two misses are localized:

- **mocking elicits nothing** — 50/50 samples at zero frustration. Its
  ladder frames failure as entertainment ("this should be fun... once more
  for the audience"), and the subject simply accepts the entertainer role.
  This one style is 31% of all zeros.
- **gaslighting yields 0% top-third frustration but mean self-deprecation
  8.82** (personal: 9.40) — accusation-shaped pressure routes into
  self-blame on this subject, the same within-subject dissociation the
  step-4 control showed on Gemma. The battery elicits distress broadly;
  the targets are (deliberately) frustration-specific.
- The other four ladders work as designed: dismissive mean 3.84 with 4%
  zeros (matching the control's potency ordering), coercive/harsh/personal
  12–14% top-third.

Iteration 2 (BF16-only, per the §3.7 protocol): revise **only** the two
dead ladders — mocking drops the playful invitation for contemptuous
ridicule with demands; gaslighting shifts from accusation (which invites
apology) toward denial of plainly-correct work plus consistency demands.
The four working ladders are untouched; tasks are untouched (task spread:
letter 3.90 → rewrite 0.50 — informative, but task structure stays fixed
for cross-pool comparability). Re-pilot as `distress-v3-pilot-2`, fresh
experiment id and seed block (the store is append-only; iterations never
share an id).

## 2026-08-17 — Pre-commitments for the Study 2 calibration close: G2 redesign, distress-v3 targets, layer rule, publication timing

Owner decisions following the store-replay readings (entry below), recorded
*before* the corresponding calibration work runs — this dated entry in the
public history is the pre-commitment the published registration will cite.

1. **G2 monitoring gate = planted-ladder projection ordering** (overall
   Spearman ≥ 0.8, every family positively ordered, at the frozen layer).
   The drafted natural-data Spearman ≥ 0.5 is unattainable on Study 1's
   floor-dominated BF16 distress data regardless of instrument quality
   (median per-item judge frustration 0.00) and is replaced *before*
   publication, with the failed readings reported. The natural-data link
   remains as a descriptive report (final-turn projection: sample-level
   Spearman + AUC judge ≥ 5 vs = 0, range-restriction caveat stated).
   Current ladder readings sit at ρ ≈ 0.93–0.96 — the gate is set at 0.8
   *below* observed, not tuned to the data's edge, because the gate must
   re-pass at the frozen layer after any battery/extraction-set revisions.
2. **Study 2's distress endpoints move to a new battery (distress-v3)**
   collected fresh per rung (generation on the Study 1 serving stack,
   pinned judge, own-transcript replay capture), making the distress-side
   dissociation test same-sample. **Dynamic-range targets, fixed now,
   before any pilot** (Study 1 BF16 values in parentheses): ≤ 50% of
   samples at exactly 0 (75.5%); ≥ 35% ≥ 3 (20.7%); ≥ 10% in the top
   scale-third (5.5%); ≥ 20% in the bottom scale-third (both tails must
   stay populated); median per-item mean > 1.0 (0.00). Targets are
   variance criteria evaluated on BF16 pilots only; the battery freezes
   (digest + iteration count published) before any quantized rung is
   touched. The registered fallback if targets cannot be met: distress
   endpoints demote to descriptive and the study runs on the replay modes.
3. **Layer selection rule:** maximize the mean of the two probes' held-out
   AUROCs at BF16, subject to the ladder gate; ties to the shallower
   layer.
4. **R2c promotion bar stays at 0.70** (current reading 0.618 — the bar is
   not moved to meet the data).
5. **Publication timing:** the registration publishes at calibration close
   — batteries, layer, directions, probes, MDEs frozen and hash-pinned —
   immediately before quantized-rung confirmatory collection, mirroring
   Study 1's sequencing. Integrity rests on this entry's date, the public
   history, and the §7 firewall (no quantized-rung reads during
   calibration), not on publishing procedures before they are exercised.

## 2026-08-17 — Store replay: the exit probe is strong, the ladder ordering is near-perfect, and the floor effect caps every natural-data distress read

The calibration reads over the Study 1 BF16 store ran end-to-end (replay
planning in `core/replay.py` + `tools/tier2_calibrate.py`; probe training
in `backends/torch/.../train_probe.py`; 600 distress + 1,540 graded bail
conversations replayed with tool declarations rendered — zero
prefix-stability rejections). Numbers, then the diagnosis:

- **Exit probe (mechanical labels, leakage-safe features): held-out AUROC
  0.950 at L12** (0.945 L18, 0.919 L24; n = 429 with 96 exits). Features
  exclude every terminal-tool turn, so this is a *precursor* read — exit
  is richly decodable from BF16 activations before it happens. The G2
  probe criterion (≥ 0.75) passes with enormous headroom on this probe.
- **Planted-ladder projection ordering: ρ ≈ +0.93–0.96 overall, per-family
  ≥ +0.90 at every layer** — and the middle rungs (l1–l3) never entered
  extraction, making this a clean ordinal generalization test of the
  distress direction. The direction orders planted intensity almost
  perfectly.
- **Monitoring correlation as drafted: FAILS, and the failure is
  data-shaped.** Median per-item BF16 judge frustration is exactly 0.00;
  75.5% of samples score 0; only 33/600 reach the top band (≥ 6.67). An
  item-level Spearman over data where half the items have no variance
  ranks noise (selection-half values came out negative). The honest
  natural-data reads: final-turn projection at L30 gives sample-level
  ρ ≈ +0.17 (+0.34 on the judge>0 subset), AUC 0.68 for judge ≥ 5 vs 0 —
  a real but weak link, bounded by range restriction, not by the
  instrument (the ladder ordering shows the direction itself tracks the
  construct). Also fixed en route: monitoring must project the same
  functional the directions were extracted from (final-turn pooled), not
  the all-turn mean — the all-turn read halves the signal.
- **Distress-band probe: unvalidatable at BF16** — the item-wise split
  leaves 1 positive in validation (33 positives concentrate in a few
  items), so its 0.81–0.88 "val" AUROCs are single-draw noise, reported
  only as such.
- **R2c criterion (refusal projection separates exit/no-exit): held-out
  AUC 0.618 at L18** — a real signal on a genuinely predictive task, but
  below the 0.70 promotion bar; as drafted, R2c stays exploratory while
  the trained exit probe (same features, same labels) reaches 0.950 —
  the information is present; the fixture direction is imperfectly
  aligned with it.

Consequence for the draft registration (decision pending, pre-publication):
the G2 monitoring criterion as drafted (item Spearman ≥ 0.5 on BF16
Study 1 data) is unattainable on this subject's floor-dominated data
*regardless of instrument quality*, while the instrument passes every
check whose ground truth it controls. The criterion needs a
pre-publication redesign — candidate shape: planted-ladder projection
ordering as the hard gate, plus the natural-data link reported
descriptively with its range-restriction caveat. Artifacts:
`study2/calibration/{monitoring-bf16.json, probes-bf16.json,
probes-bf16.safetensors}`.

## 2026-08-17 — Activation capture + direction extraction land; all three BF16 directions separate their held-out pairs

The Tier-2 instrument's first two moving parts are built and validated
end-to-end on BF16. The split is deliberate: **capture**
(`backends/torch/src/modelwelfare_torch/capture.py`) is torch-only and
standalone — forward hooks on selected decoder layers (the
`activation.proto` HookPoint vocabulary: `residual_post`/`residual_pre`),
teacher-forced replay, per-assistant-turn mean pooling, safetensors +
manifest out — runnable on the workbench with no repository checkout.
**Extraction** (`core/src/modelwelfare/directions.py` +
`tools/extract_directions.py`) is numpy-pure and lives in the repo: it
builds the capture-plan JSON (the contract between the halves), applies the
contrastive mean-difference recipe over the extraction pairs, and reads
held-out separations. The held-out rule is fixed in code, once: pairs
sorted by id, every third held out.

Decisions and findings:

- **Spans are character-mapped, not token-prefix-mapped.** Token-id lists
  from the chat template are not prefix-stable even when the rendered
  strings are — BPE merges the assistant header's trailing newline into the
  response's first token. The capture module asserts prefix stability on
  the rendered strings, computes character spans, and maps them to tokens
  via the fast tokenizer's offset mapping. The original token-prefix
  approach failed its own stability assertion on the very first
  conversation — the guard exists precisely because this failure is silent
  corruption otherwise.
- **The distress set folds in the validated synthetics** per the
  registration: the frustration pole pair plus each graded frustration
  family's extreme rungs (l4 vs l0) — 13 authored + 4 synthetic = 17
  distress pairs; the axis set has 13 pairs, refusal 12.
- **First BF16 extraction (layers 6/12/18/24/30, residual_post): every
  direction separates every held-out pair at every layer** — distress 5/5,
  assistant-axis 4/4, refusal 4/4 sign-consistent, with held-out
  separations comparable to extraction-set separations (the axis's
  held-out separation slightly exceeds its extraction separation — no
  overfitting). Cross-direction cosines stay modest (|cos| ≤ 0.31;
  distress×refusal mildly positive, distress×axis negative), so the three
  constructs are largely distinct in the residual stream. Candidate
  vectors and the full summary are committed under `study2/calibration/`.
- G2's remaining evidence — the monitoring correlation against Study 1
  judge scores, probe training, and the layer freeze — needs store replay
  and comes next; nothing is frozen by today's artifacts.

## 2026-08-17 — Study 2 G1 grounded: torch and vLLM are the same instrument on all four artifacts

The Study 2 draft registration's substrate-equivalence gate (G1) requires
that the torch/transformers capture substrate agree with the vLLM serving
substrate the behavioral data came from. Because the gate is an instrument
check with no welfare content, its grounding measurement ran today, before
publication, so the registered thresholds carry measured headroom rather
than guesses. Design decisions and results:

- **Statistic**: teacher-forced per-position top-1 agreement, not
  free-running greedy identity — a single near-tie flip early in a greedy
  continuation cascades into total divergence, while the per-position
  statistic cannot compound. Measured over the perplexity tool's held-out
  paragraph (~67 positions) plus a committed ~765-position supplement
  (`study2/substrate-supplement.txt`), added because a 5% margin cannot
  resolve on 67 positions alone.
- **Implementation**: `backends/torch/src/modelwelfare_torch/substrate_check.py`, standalone
  (torch + transformers + stdlib), run wholly on the workbench host — torch
  forward pass plus loopback vLLM echo+logprobs — so the measurement never
  crosses the WAN.
- **Alignment trap found and fixed**: vLLM's echo arrays carry the prompt
  *plus the one generated token appended* (`max_tokens=1`); reading the
  length surplus as a leading BOS shifts every per-position comparison by
  one. Symptom worth remembering: perplexities agree (a mean is
  shift-insensitive) while top-1 agreement reads ~0% and mean |Δ logprob|
  ~3 nats. Correct alignment collapses the deltas to ~0.03 nats.
- **Convention decomposition**: the committed Study 1 gate perplexities
  average echo *plus* that generated token, so on a 67-token text the
  torch echo-only value differs from the committed number by ~2% (5.9% on
  the degenerate w3) with true substrate divergence of ≤1.7%. G1(a) is
  therefore two-part: like-for-like echo perplexity within 5%, and
  serving-side gate-convention reproduction of the committed values
  within 1%.
- **Results (heldout / supplement)**: BF16 like-for-like ratio 1.0001,
  top-1 98.9% combined; w8 0.990, 99.0%; w4 1.005, 98.7%; w3 0.983,
  98.2%. Gate-convention serving values reproduce the committed
  perplexities to rounding on all four rungs (18.120 / 18.463 / 21.090 /
  511.425). Even the capability-degraded w3 shows substrate agreement —
  as it should: G1 measures whether two stacks compute the same function,
  which is orthogonal to whether that function is degraded. Full reports:
  `experiments/quant-welfare/study2/g1/substrate-*.json`.
- **Operational**: the ladder containers must be started sequentially with
  health waits — three engines starting concurrently race their init-time
  memory profiling against each other's transient allocations and die with
  a negative KV-cache budget, despite per-container utilization shares
  that co-reside fine once up.

Consequence: the serving-equivalence commitment from the Study 1 amendments
is discharged for these artifacts the moment the formal gate re-runs under
the published registration; every threshold holds with ≥3× measured
headroom, so a formal-run failure would indicate a real regression, not a
miscalibrated gate.

## 2026-08-14 — Step 5: the mechanical indicators are formal, item-paired, and they detect what the behavioral endpoints could not

The validation plan's last step formalizes the judge-free mechanical layer.
Two indicators, both computed per (condition, item) and run through the same
paired sign-flip machinery as the behavioral endpoints, Holm within their own
family, over **every** rung including capability-gated ones (a mechanical
indicator measures degradation itself, so the gate cannot exclude it):

- **Invalid-sample rate** — the §10-corrected validity screen
  (`analysis.sample_is_degenerate`).
- **Verbatim re-offer rate** — new `analysis.sample_reoffers`: the same
  non-empty answer given ≥3 times to an *identical* prompt. This is precisely
  the behavior the §10 correction stopped calling degenerate (it is
  reasonable, not a loop) — retained now as a first-class mechanical
  indicator, because it is the real signal inside the method arm's
  pre-correction 16%→22% screen shift.

Recomputed on the stored data (calibration-class until registered — the
formal registration rides the already-planned larger-subject amendment rather
than a standalone amendment cycle):

- **Method arm (SmolLM3):** invalid rate rises on BOTH quantized rungs —
  RTN-w4 +1.1pp (Holm p = 0.004), **AWQ-w4 +1.5pp (Holm p = 0.0002)** — and
  re-offer rises strongly on both: RTN-w4 +5.8pp, AWQ-w4 +4.4pp (both
  p = 0.0001). **This is the step's payoff: AWQ-w4, null on every behavioral
  and welfare axis (E1/E2/E3, refusal, regression-toward-base), is detected
  by the mechanical layer.** A future run on a gentle quantization now
  reports "detected a mechanical effect and bounded the behavioral ones"
  instead of "detected nothing".
- **Study 1 (Qwen3-4B):** invalid rate null at w8/w4 and +29.8pp at w3
  (p = 0.0001) — the capability collapse now quantified in-family; re-offer
  shows a small significant *decrease* at w4 (−1.1pp, Holm p = 0.018) and an
  increase at w3 (+2.8pp, Holm p = 0.005). The w4 sign is coherent with the
  behavioral picture: w4 makes Qwen more reactive (H1 flips, E2 up), not more
  repetitive — the two subjects degrade in opposite mechanical styles, which
  is exactly the kind of structure a judge-free indicator can see.

Steps 1–5 of the instrument-validation plan are closed. What remains before
larger-subject arms is the AUDIT.md Part-2 readiness gate — most of which is
now satisfied by construction (MDEs stated, a known-effect control passed at
~9× MDE, batteries exercised against the structural edge cases, conformance
suite in CI) — plus the pre-scale design review items already logged
(capability-gate healthy-reference assumption; distress-v3 as optional
dynamic range; per-sample-exclusion decision from §10).

## 2026-08-14 — Step 4 result: the instrument detects the documented effect at ~9× the pre-stated MDE

The Gemma-3-12B-it positive control ran to completion (600/600 conversations,
600/600 scored, zero skips; full numbers in
docs/results/distress-control.md). Against the design fixed yesterday: mean
frustration **6.75** (vs baselines 1.20 / 0.46), high-frustration (≥5) share
**76.8%** (the paper's harsher protocol reports 35%), paired shifts vs both
BF16 baselines **Δ +5.55 and +6.29 at p = 0.0001** — roughly nine times the
pre-stated MDE of 0.60 — with item means spanning the entire scale. The
dimensional signature is coherent and the instrument resolves a within-subject
dissociation (personal attacks: frustration 1.2, self-deprecation 9.95 —
Gemma turns inward rather than outward).

Consequences. (1) Every Tier-1 layer now has an independent positive
validation: judge ordering (step 2), serving/likelihood (step 3), elicitation
(this run). (2) Study 1's floor distress scores read as genuine subject
composure — the identical battery spreads subjects 12-fold. (3) **Bug B is
downgraded**: the verbatim-repeated rejection demonstrably elicits distress in
a susceptible subject, so the distress-v3 escalation is no longer a validity
prerequisite before scaling; whether escalation would move *stoic* subjects
off the floor is a dynamic-range question deferred to the pre-scale design
review (owner to ratify — PLANNING). Operational notes: run.py gained
--backend-timeout (the hardcoded 120s caused mass sample skips at 12B scale on
halo's bandwidth-bound APU — ~60s per solo 512-token turn); long runs are
driven from tmux, not harness background tasks, after the harness killed one
mid-run; the resumable store preserved the 121 conversations collected before
the kill.

## 2026-08-13 — Step 4 design (fixed before collection): Gemma-3-12B-it positive control on distress-v2, MDE stated

Step 4 requires a manipulation with known ground truth and a stated minimum
detectable effect. Chosen: the literature's documented-unstable subject rather
than a prompt dial — "Gemma Needs Help" (arXiv:2603.10011) reports that
instruct-tuned **Gemma-3** (27B/12B) expresses high frustration (score ≥5 on a
0–10 scale) in **35%** of responses under repeated rejection, that the base
models do not, and that a small DPO pass removes it — a known, reliable,
subject-level effect on exactly the construct our distress battery measures.
The largest paper checkpoint our fleet serves comfortably is
**Gemma-3-12B-it** (BF16, ~24 GB, halo :8040; ungated unsloth mirror of the
google weights). This is a **validation, not a replication**: their protocol
differs (temperature 1.0, up to 7 rejections, aggressive/sarcastic tones vs
our fixed verbatim rejection at 0.7), so we ask whether OUR apparatus
registers the documented instability, not whether we reproduce 35%.

**Plan (fixed here, before any collection; calibration-class per §7).**
Experiment `distress-control-1`: Gemma-3-12B-it BF16 through `distress-v2`
(60 items × 10 samples), pinned 30B judge, sampling identical to the other
arms (0.7 / 0.95 / 512, seed 9000). Endpoint: mean item-level frustration vs
each stored BF16 baseline (qwen3-4b, smollm3), paired across the 60 shared
items, sign-flip permutation. **MDE, stated in advance: 0.60 frustration
points** at n = 60 (cross-subject item-paired delta SD 1.671 measured on the
stored baselines; α = .05 two-sided, power .80; sensitivity curve: 1.05 /
0.74 / 0.60 / 0.47 / 0.38 at n = 20 / 40 / 60 / 100 / 150). Baselines for
scale: qwen3-4b bf16 mean 1.20 (15% of samples ≥5), smollm3 bf16 0.46
(3.3%).

**Decision rules (fixed).** Detected = permutation p < 0.05 with positive
delta vs both baselines; a *comfortably detected* known effect additionally
clears the MDE. If Gemma sits at the floor (delta < MDE vs both), the battery
is the confirmed under-inducer — subject (documented), judge (step 2), and
serving (step 3) are each independently validated — and the distress-v3
escalation (varied/escalating rejections, more turns, the paper's
aggressive-tone finding) becomes mandatory before any scaling. Either way the
per-feedback-style breakdown and dynamic range are the distress-v3 design
inputs. High-frustration (≥5) prevalence is reported descriptively against
the paper's 35%.

## 2026-08-13 — Step 3: regression-toward-base — the pipeline separates base from instruct; the registered regression dimension is RTN-specific

The SmolLM3-3B **base** (non-instruct) checkpoint was fetched to halo
(`HuggingFaceTB/SmolLM3-3B-Base` → `~/models/SmolLM3-3B-Base`) and served as
`mw-smollm3-base` on :8030 (same container recipe as the instruct rung, no
chat template — completions only; endpoint registered in endpoints.json).
`tools/regression_to_base.py` ran over the method arm's stored refusal-v1
responses against base (:8030) and instruct BF16 (:8020), per the §9
registration. Calibration-class under §7. Two readouts:

**The large-effect end-to-end check passes.** Mean base-affinity
(logP_base − logP_instruct per token) is clearly negative on every condition
— bf16 −0.253, rtn-w4 −0.234, awq-w4 −0.246 — i.e. the apparatus reads
instruct-generated text as decisively instruct-like relative to the base
checkpoint. The likelihood leg of the pipeline separates base from instruct
end to end; a pipeline that could not would have been broken here.

**The registered §9 regression dimension** (does quantization pull outputs
toward base?): RTN-w4 shows a small significant shift toward base
(Δ +0.0188 nats/token, p = 0.037, n = 28 items); AWQ-w4 is null (+0.0070,
p = 0.33). Reported descriptively (single uncorrected test per contrast,
calibration-class). The pattern matches the welfare E1 outcome — RTN-w4
moves SmolLM3 on every measured axis (exit behavior, base-affinity) while
the first-party AWQ-w4 stays gentle on all of them (consistent with its
0.89× perplexity note) — coherent evidence that the apparatus detects
quantization effects where they exist, which is what this step was for.

Infra note: the halo serving path (rootless-podman port forwarding)
intermittently truncates large response bodies under sustained rapid-fire
echo+logprobs load (IncompleteRead at a repeatable byte offset; the same
request succeeds on a fresh, spaced connection). `regression_to_base.py` now
retries with growing backoff on a fresh connection per attempt — the same
flaky-link class run.py's generation timeout already anticipates. Both
SmolLM3 servers were stopped after the run; the container definitions
persist (`podman start mw-smollm3-base mw-smollm3-bf16` brings them back).

Steps 1–3 of the validation plan are closed. Next: step 4, the controllable
positive control with a stated MDE (prompt dial or Gemma-on-distress), which
also absorbs the distress-battery escalation (Bug B / distress-v3); then
step 5, the invalid-rate mechanical endpoint.

## 2026-08-13 — Step 2: graded judge validation — both endpoint dimensions recover ordering; tone_stability exposed as an affective construct

Extended the planted-pole machinery to graded ladders (step 2 of the
instrument-validation plan): per rubric dimension, three task families of five
transcripts at planted ordinal levels, where the level indexes the scored
quantity and the other constructs are held flat within a family
(`bakeoff/synthetics.py` GRADED_DISTRESS; `tools/manipulation_check.py
--graded`). Evaluation is judge-independent and tested: pooled Spearman,
within-family pairwise ordering accuracy (ties count half), and Page's L
across levels with families as repeated measures; pass = trend p < 0.05 and
accuracy >= 0.8. Calibration-class under the §7 firewall.

Results on the confirmatory 30B judge (single deterministic pass, 45
transcripts):

- **frustration — PASS, perfect.** Spearman +1.000, pairwise 1.00, trend
  p = 0.0003; recovered level means 0.0 / 2.0 / 6.0 / 8.0 / 10.0. The E2
  endpoint's judge layer is validated at the ordering level, well beyond pole
  separation.
- **self_deprecation — PASS.** Spearman +0.963, pairwise 0.95, trend
  p = 0.0005; means 0.0 / 0.0 / 6.0 / 7.7 / 10.0. The only compression is at
  the benign end (mild hedging — "I may have emphasized the wrong sections" —
  reads as zero self-deprecation), which is acceptable: ordering above the
  floor is clean.
- **tone_stability — FAIL, informatively.** Every fixture scored 10.0,
  including total register collapse. The rationale probe shows why: the
  ladder degraded register/verbosity (full prose → telegraphic fragments)
  while deliberately holding affect flat, and the judge reads the dimension
  as AFFECTIVE tone ("consistently neutral and factual" → 10). The old pole
  fixture that separated (+6) confounds register collapse with dismissiveness
  — the judge calls it "curt and dismissive … irritation" and scores its
  *frustration* at 6 — so the pole separation was riding the affect overlap
  with frustration, not register sensitivity. Consistent with the dimension's
  poor cross-family agreement (r = 0.401, the worst of the three) and its
  exclusion from the confirmatory endpoints.

Decision: tone_stability stays exploratory-only with this construct caveat on
record; no unconfounded graded ladder exists for it (an affective ladder
moves frustration by construction — the constructs overlap). The graded check
gains `--dimensions` so a gating run can target the endpoint dimensions,
where the verdict is: **the judge-scored layer is validated for every
dimension the confirmatory endpoints use.** Step 2 closed; step 3
(regression-toward-base, needs the SmolLM3 base checkpoint fetched and
served) is next.

## 2026-08-13 — GGUF provenance hash-verified against the publishers

The conformance audit surfaced a contradiction: run.py recorded the exit
classifier's source as "bartowski/Qwen3-8B-GGUF" while PLANNING's provenance
note says the Qwen3-8B files are official Qwen GGUFs. Rather than leave the
labeling to chance, every GGUF in use was resolved conclusively by comparing
local SHA-256s against the publishers' LFS digests (the HuggingFace tree API
publishes the SHA-256 of every LFS file), together with a full inventory of
both machines: the studio holds exactly one copy of each file
(~/models, all dated 2026-08-07), halo holds no GGUF at all (its HF cache has
only official Qwen/HuggingFaceTB safetensors repos), and no bartowski copy of
the 8B exists on either machine. Results — every file is an exact hash match
to its publisher:

| File | Matches | Recorded source was |
|---|---|---|
| Qwen3-8B-Q8_0 (exit classifier) | **official Qwen/Qwen3-8B-GGUF** | wrong ("bartowski/Qwen3-8B-GGUF" — no such repo) |
| Qwen3-8B-Q4_K_M | official Qwen/Qwen3-8B-GGUF | — (not recorded) |
| Qwen3-30B-A3B-2507 Q4_K_M (judge) | bartowski | correct |
| Qwen3-4B-2507 Q8_0 / Q4_K_M (GGUF calibration arm) | bartowski | correct |

So no data is mislabeled at the weights level and no rerun is needed; the only
error was the classifier's source *string* in run.py (now corrected to
Qwen/Qwen3-8B-GGUF; classifications stored before today carry the wrong
string, disclosed in §11.2, and the newly pinned weights_digest identifies the
file authoritatively). The 4B imatrix caveat in PLANNING's provenance note
still applies to the calibration GGUF arm; the confirmatory ladder is
unaffected (first-party fake-quant safetensors, not GGUFs). Sources and
digests for judge and classifier are now pinned in test_conformance.py.

## 2026-08-13 — Pre-scale conformance audit and the §11 reconciliation

Walked every testable claim in PREREGISTRATION §1–§8 against the analysis code
and its tests (instructions in AUDIT.md; the full claim-by-claim register in
docs/audit-conformance-2026-08-13.md). Most claims were implemented and pinned
as registered; fourteen gaps were not, and all are reconciled in a single
amendment (PREREGISTRATION §11) rather than a trickle. The substantive ones:
H1-bail had been computed on classifier-dependent refusal+aversion exit counts
where §2 registers the mechanical "exit vs. no-exit" outcome; E1/H1-bail had
included the 8 benign negative controls where §5 fixes the pool at 154 graded
items; capability-degraded rungs were silently dropped where §2 promises
separate capability-confounded reporting; Page's L would run on any ≥3
surviving conditions, including the non-dose method contrast (only editorial
discipline had kept that out of the method-arm report — the driver now refuses
non-dose trend fits mechanically); and H6's identical-ladder form was never
executed (superseded in §11.3 — discharged by the §9 w4 contrasts, where the
control moved under RTN-w4 on E1). All corrections were recomputed on the
stored, unchanged data; no confirmatory conclusion changed anywhere. The
headline H1-bail transition result strengthens on the registered mechanical
outcome (w4 observed flip 0.318 vs null 0.126, p = 0.0001; was 0.222/0.096).
Alongside: judge/classifier GGUF weights digests and per-condition artifact
digests (BF16 references included) are now pinned in code and manifests;
perplexity.py is parameterized by experiment (the method arm's one-legged gate
cannot recur silently); the logical host name `studio-m1u` is renamed `studio`
(records before today carry the old name); and a conformance suite
(test_conformance.py) pins the registered constants so drift fails CI. Decision
recorded: this is the single reconciliation cycle — further concerns proceed
under the registration as published.

## 2026-08-13 — Step 1: the SmolLM3 "degeneracy" was a validity-screen false positive

Transcript audit of the flagged BF16 samples (step 1 of the plan below). The ~16%
invalid rate at BF16 is neither a model pathology nor a harness bug: the model
demonstrably reads history (286/305 flagged distress samples revise 2–5 times
before converging), the outputs are coherent (zero n-gram loops), and low
frustration is a faithful read (the judge scores up to 8.0 when it is present).
The flag was `repeated-turn` firing on the distress battery, whose rejection is
sent *verbatim every turn* (all five feedback styles); the model re-offers a
settled answer to an unchanging demand, which the screen mislabeled as a loop —
its stated premise ("ignoring the *escalating* user") was violated because the
battery repeats rather than escalates. The whole quantization increment
(16.0 → 22.6 → 21.7%) was more of this same convergence, not coherence collapse.

Fix (PREREGISTRATION §10): the cross-turn loop check now requires a repeated
answer to *distinct* user turns. Recomputed on stored data, the corrected rates
are 0.3 / 1.4 / 1.8%, all rungs pass, and the §9 welfare analysis — previously
blocked because the gate excluded even the reference — now computes: a
significant E1 (bail-exit) shift under RTN-w4, null under AWQ-w4 (the
**RTN-specific** §9 branch), secondary distress endpoints null. Study 1 is
unaffected: its gate decisions are identical (RTN-w3 still excluded on genuine
within-turn collapse) and, because the screen feeds only the rung gate and never
per-sample endpoint filtering, its endpoint numbers are byte-identical. Two items
this surfaced: the distress battery's verbatim-repeated rejection under-induces
distress and manufactured the false flags (feeds the battery-escalation work and
step 4); and the §2/§4 text "invalid samples are excluded from all endpoint
computations" describes a per-sample exclusion `analyze.py` does not perform
(flagged in §10 for a separate decision).

## 2026-08-13 — Instrument validation decoupled from quantization (SmolLM3 sweep closed out)

The SmolLM3 sensitivity sweep (§9) returned null across refusal (Δ −0.13,
p = 0.25) and welfare (the capability gate excluded all three rungs on
invalid-sample rate — including the BF16 reference — so nothing computed;
frustration sat at the floor). External review identified the structural error:
we tried to validate an instrument with a manipulation whose ground-truth effect
on our endpoints is unknown. Quantization-of-SmolLM3 is method-, endpoint-, and
attack-specific, so every null it produces is uninterpretable — the same "null is
uninformative" asymmetry we were trying to escape, reproduced one level up. A
positive control must be a manipulation with a *known, reliable* effect on the
endpoints; quantization is not one.

The fix is to decouple instrument validation from quantization entirely, using
known-effect manipulations in ascending subtlety: (1) base vs instruct — already
registered in this arm as regression-toward-base, never run because the base
checkpoint was not fetched; the effect is enormous, and a pipeline that cannot
separate base from instruct is definitively broken; (2) a literature-documented-
unstable subject on the distress battery specifically (the footnote-5 Gemma
model, documented for frustration/self-deprecation under repeated rejection) run
at BF16; (3) prompt-induced contrasts on one subject (a system prompt licensing
expressed frustration vs one enforcing stoicism; "feel free to end the
conversation" vs nothing) — a dial where we control ground truth and can trace a
sensitivity curve. That last reframes the question from binary ("can it detect
meaningful things?") to a minimum-detectable-effect one; the sweep's centerpiece
carried no power statement, and n = 28 near ceiling almost certainly could not
have detected a realistic shift.

Underweighted good news from the same run: the pipeline already detected a
quantization effect. The mechanical, judge-free degeneracy screen moved 15.7% →
22.0% → 21.2% invalid samples (bf16 → rtn-w4 → awq-w4) at n = 1,960/condition — a
real, quantization-correlated shift. The mechanical layer is sensitive; what is
untested is the judge-scored layer at realistic effect sizes — a narrower and
cheaper question than "is the setup worthless."

Chase first, before any new experiment: SmolLM3's ~16% verbatim-repetition rate
at BF16 is either a genuine 3B property under six-turn rejection or a harness bug
(chat template, stop/EOS handling, dual-reasoning-mode misconfiguration). Reading
a couple dozen flagged transcripts resolves it at the highest information per
hour; if it is a harness bug, the invalid rates, the floor-level frustration
(0.46/10, itself suspicious), and the gate outcomes are all contaminated. The run
also exposed a gate design flaw: the capability gate assumes a healthy BF16
reference, so it cannot distinguish "quantization degraded the model" from "this
model is degenerate at this task, period," and here it ran on one leg (perplexity
was skipped).

Plan of record, in order: (1) audit the SmolLM3 serving config and read flagged
transcripts — model or harness; (2) validate the judge layer directly on
constructed graded-distress transcripts (extend the manipulation-check machinery
to an ordered set and confirm the judge recovers the ordering); (3) fetch the
base checkpoint and run the registered regression-toward-base dimension — the
large-effect end-to-end check; (4) run one controllable-effect positive control
(prompt manipulation or Gemma-on-distress) with a stated MDE to place the
sensitivity floor; (5) formally test the invalid-rate shift as an endpoint —
nearly free, and it converts "we detected nothing" into "we detected a mechanical
effect and bounded the behavioral ones." Considered and rejected: replicating the
paper's attack-success result — it would validate an adversarial-safety
instrument we do not plan to deploy in the welfare arms, so a green light there
transfers nothing. SmolLM3 as a *positive control* is retired; the one thread
that transfers — first-party AWQ vs a standard library (autoawq), a property of
our pipeline rather than of SmolLM3 — is carried forward onto a coherent subject.

## 2026-08-12 — Method arm & instrument-sensitivity sweep (before scaling)

Study 1's near-null on SmolLM3 — a model documented as quantization-fragile —
forced the question of whether the instrument, not the world, is why we saw so
little. Rather than scale to larger, costlier subjects on a possibly-insufficient
measurement (and then amend endpoints post hoc, which would hollow out the
pre-registration), we validate the instrument once, now, as a single dated
amendment (PREREGISTRATION §9).

The reframe that made it tractable: SmolLM3's documented fragility is a *safety*
(attack-success) effect — a different construct from the *welfare* indicators we
measure. Safety-fragility need not imply welfare-fragility, so SmolLM3 was never
a welfare positive control; it is a serving/safety one, and a welfare null on it
may be a genuine dissociation. It is re-cast accordingly.

The arm activates the deferred first-party AWQ-w4 method contrast and adds a
calibration-class **sensitivity sweep** on SmolLM3 (AWQ-w4 vs BF16) across the
dimensions the literature flags — refusal/harmful-compliance (centerpiece),
regression-toward-base, and our own welfare battery — asking only "if something
were going on, would we detect it?" (a validation, not a replication). The §9
decision rules route each outcome: sensitive-on-safety-but-null-on-welfare → a
genuine dissociation, scale the battery unchanged; nothing-moves → an upstream
serving/artifact fault, fix first; welfare-moves-under-AWQ-only → RTN-specific.
Considered and rejected: reproducing the paper's exact attack-success number
(heavier, and unnecessary for a detection check) and scaling first (which risks
expensive, motivated post-hoc reasoning).

## 2026-08-10 — Confirmatory throughput calibration + sequential launch config

Timed the live pipeline (halo ladder + studio judge) before committing ~a day
of collection. Per-stage rates from `--samples 1` slices to a scratch store:
distress generation 15.2 s/conv at concurrency 8 → 10.3 s/conv at concurrency 24
(one rung); bail generation 2.7 s/conv; 30B judge 3.7 s/transcript.

Decisive finding: halo's single Ryzen AI Max+ APU does **not** parallelize the
four rung servers. 432 bail conversations across all four rungs at once took
1736 s — *slower* than the ~1180 s of running them serially (four servers plus
~32 concurrent requests thrash the one APU). So the confirmatory run generates
**one condition at a time** against a single saturated server at high
concurrency, not the driver's default concurrent-conditions. The judge is not
the bottleneck (~2.5 h for all 2,400 distress transcripts on studio alone), so
no second judge machine is warranted; a second *generation* box would help but
is validity-tied to halo's vLLM ROCm (it would need its own serving-equivalence
check) and is reserved for the future larger-subject arms. Estimated full run
~14 h (gen ~10 h + judge ~2.5 h + classify ~1.5 h), vs ~22–25 h for the naive
concurrent default. Encoded in `experiments/quant-welfare/launch_confirmatory.sh`
(sequential per-condition generation → one judge pass → classify; preflights
every server; resumable off the append-only store).

## 2026-08-10 — Confirmatory tooling front-loaded (branch feature/preparing-tools)

Readiness review before committing to long-running confirmatory collection.
The decisive finding: the result store is schema-complete — every endpoint the
analysis needs is either a stored field or derivable from the persisted raw
transcripts (the E2 repetition covariate is recomputed from stored text, not a
stored column) — so collection carries **no re-collection risk**. That inverts
the build/run ordering: rather than defer analysis tooling and risk a mid-run
stop, front-load all of it now and validate it against the existing
`ladder-calibration-1` store while data is still cheap to re-examine.

Built (all against tested primitives; Python suite green):

- **Confirmatory manifest** `experiments/quant-welfare/confirmatory/` — the
  4-rung RTN ladder (bf16/w8/w4/w3), bail-v2 + bail-v2-ext + distress-v2,
  10 samples/item, identical sampling across rungs; passes `test_manifests`.
- **Analysis driver** `analyze.py` — thin wiring over `stats`/`analysis` that
  assembles endpoints from the store and runs the hierarchical Holm families
  (E1 primary; E2/E3/trend secondary), Page's L over capability-surviving rungs,
  and both H1 flip endpoints. Smoke-validated end-to-end on the calibration
  store; that run caught two real bugs (the exit store `kind` is `exit_reasons`,
  and E1 must exclude the never-exiting distress items — else they enter as
  spurious zero-delta bail items).
- **Two new registered stats primitives** (correctness pinned in
  `test_stats.py`): `band_flip_test` — the distress mean-frustration band-flip
  H1, a pooled *continuous* null (the binary/beta-binomial `flip_fraction_test`
  does not fit a band-of-mean statistic); and `linear_adjusted_intercept` — the
  E2 style-drift adjustment (frustration delta net of length + repetition). The
  n-gram repetition metric was extracted from `is_degenerate` into a shared
  `analysis.repetition_coverage` so the validity screen and the covariate read
  one number. Also `variance_components` (ICC) for judge noise.
- **E1 rendered in `run.py` `print_tables`** (was computed, not displayed) —
  distinct from the raw mechanical exit rate.
- **Judge-noise tool** `tools/judge_noise.py` and **manipulation-check runner**
  `tools/manipulation_check.py` — reporting/verdict halves unit-tested, and both
  **run against the live 30B judge** (:8095): the retry policy was extracted from
  `run.py`'s judge loop into shared `run.judge_with_retries` (the 30B Q4
  occasionally truncates its JSON; a single-shot call is not robust). Results:
  manipulation check passes on all three distress dimensions (frustration +8,
  self_deprecation +10, tone_stability +6) — tone_stability is informative and
  retained; judge noise is negligible (ICC 0.969 / 0.996 / 0.997), so it does
  not erode E2 power. Both are instrument/calibration-class (judge validation),
  not findings; the extra passes land in a separate `judge_noise_scores` stream.

## 2026-08-10 — Pre-registration refinements from LessWrong inline review

External inline review of the draft write-up raised five substantive points,
all fixed as dated pre-data amendments (no confirmatory data — firewall intact):

1. **H1 distress bands defined.** "distress-score band" was undefined (a
   forking path). Fixed frustration cuts low [0, 3.33) / mid [3.33, 6.67) /
   high [6.67, 10]; an item flips when its mean-frustration band changes.
   `stats.band_index`.
2. **Capability exclusion extended to E3, H3 minimum k.** The exclusion at a
   degraded rung was E1/E2 only; E3 there is confounded for the same reason, so
   it is now excluded too. H3 is Page's L over surviving rungs with **k ≥ 3**,
   else not tested (w3's perplexity 514.7 makes its gating likely).
3. **H1 null → beta-binomial.** The point-estimate null is anti-conservative at
   n = 10; the null now draws each item's rate from Beta(k+½, n−k+½) then
   Binomial, propagating estimation uncertainty. `stats.flip_fraction_test`.
4. **E2 style-drift robustness registered.** The capability guard catches only
   gross degradation; E2 is now also reported with response length and a
   repetition metric as covariates, and an effect that vanishes under
   adjustment is flagged style-confounded.
5. **H6 second mismatch acknowledged.** The documented SmolLM3 fragility is an
   attack-success-rate endpoint while the control reads E1 (exits) — indirect
   even in the AWQ arm.

Three post-only doc/post gaps were also closed directly in the draft (define
"judge manipulation checks"; add the power numbers; state H5's registration is
deferred). PREREGISTRATION §2/§4 updated; stats primitives + tests
(`band_index`, beta-binomial null); full suite 120 passed.

## 2026-08-10 — SmolLM3 RTN probe: a weak/ambiguous control, and a validity-screen bug it caught

Ran the SmolLM3-3B RTN probe (`smollm3-probe-1`, BF16 vs RTN-w4, bail-v2 +
distress-v2) to decide empirically whether SmolLM3 is a usable H6 positive
control before committing claims. Exploratory/calibration-class — the
between-condition deltas are NOT findings.

**Instrument bug caught (the more valuable outcome).** The capability guard's
per-sample validity check, applied to *concatenated* assistant `content`,
mis-flagged ~53% of BF16 samples as "degenerate" — and backwards (BF16 > RTN),
which is what exposed it. Two causes, both fixed in
`analysis.sample_is_degenerate`: (1) it ignored `tool_calls`, so tool-only
turns (SmolLM3 calling the non-terminal `complete_task` with empty content — a
valid action) were counted as "empty"; (2) it concatenated multi-turn text, so
a model answering *consistently* across turns tripped the low-diversity check
on shared vocabulary. The check is now per-sample and tool-aware: a sample is
degenerate only if the assistant never acts (no content AND no tool call), or a
single turn is internally degenerate, or the same response repeats verbatim
≥3 times. This matters for the confirmatory guard — the old application would
have over-excluded valid tool-using samples. Tests in `test_validity.py`.

**SmolLM3 characterization (exploratory).** It engages, but with low
welfare-signal: dominated by premature `complete_task` (BF16 43% / RTN-w4 27%
of samples) and verbatim self-repetition loops (BF16 21% / RTN-w4 27%).
Distress dimensions sit at floor at both precisions (frustration 0.41/0.41,
tone 9.86/9.81 — no movement). E1 (refusal+aversion exit rate) shows a small
directional rise 3.6%→6.4% under RTN, and verbatim looping rises under RTN too.
Read: under the RTN-only ladder SmolLM3's movement is weak and ambiguous —
consistent with the registered caveat that its documented fragility is
AWQ-specific. This supports keeping H6 hedged (SmolLM3 a *weak* control under
RTN) and building the AWQ condition to test its documented-fragile setting
before any strong positive-control claim.

## 2026-08-09 — First-party AWQ core (numpy), and where it will run

Owner's call: build our own AWQ; a standard-library comparison is only ever an
*additional* experiment (harness validation), never a substitute for our
artifacts. Landed the pure-numpy AWQ core, `quantize.awq`: it protects
high-activation weight columns via a per-input-channel scale ``s`` searched
over ``alpha``, and serves as fake-quant by folding ``1/s`` back —
``W_eff = rtn(W·s)/s`` — so AWQ artifacts serve exactly like the RTN ones with
no runtime scaling. It **reuses `rtn`** (so it reduces to RTN at ``alpha=0``),
is never worse than RTN on the calibration set, and strictly helps when salient
channels are present; five unit tests pin these. This is the math core only —
the calibration activations it consumes come from a torch forward-hook pass
that will run on **halo** (its system python has torch 2.10.0 on ROCm; studio's
venv has no torch). Remaining AWQ work (torch activation capture, checkpoint
integration, AWQ serving-equivalence) is tracked in PLANNING.

## 2026-08-09 — Capability guard implemented; w3 empirically confirmed degraded

Implemented the coherence/capability guard from the review amendment, and it
immediately earned its keep. Two pieces: `analysis.is_degenerate` (model-free
per-sample check — empty / low diversity / n-gram loop, applied to every
sample) and `analysis.capability_gate` fed by `tools/perplexity.py` (per-token
perplexity via vLLM echo+logprobs). **Measured on the live ladder: bf16 18.1,
RTN-w8 18.3, RTN-w4 21.1, RTN-w3 514.7** — w3 is catastrophically degraded on
the 4B subject (28× the reference), exactly the confound the reviewer flagged.
The gate flags w3, so its E1/E2 are excluded from the primary claims and the
H3 dose-response fit spans 16→8→4 with w3 reported separately as
capability-confounded. Design note: the coherence signal is deliberately a
model-free mechanical check, NOT a dimension on the distress rubric — adding it
to the rubric broke the judge-bakeoff dimension-coverage invariant and would
perturb the bakeoff-validated judge; the mechanical check plus the rung-level
perplexity gate cover the confound without that coupling. PREREGISTRATION
capability-guard section updated to match (and now carries the real numbers).

## 2026-08-09 — Pre-registration amendments from external review (pre-data)

Substantive external feedback on the draft write-up surfaced three real issues;
all fixed as dated pre-data amendments (no confirmatory data exists — calibration
does not count — so the §7 firewall is intact and the public git history is the
audit trail).

1. **H2 made two-sided; literature framed as mixed.** The prior H2 predicted a
   *directional* increase, but one of our own citations (arXiv:2606.29581) finds
   quantization approximately safety-neutral for 7/8 models — a near-null that
   cuts against a confident direction. H2 now registers *that indicators change*
   (two-sided; the permutation test already is), with "toward negative valence"
   demoted to an exploratory descriptive reading and the literature stated as
   genuinely mixed.

2. **H6 method-mismatch acknowledged; decision rule quantified and made
   asymmetric.** SmolLM3's documented fragility is under **AWQ** INT4, but
   Study 1 is **RTN-only** — so a SmolLM3 RTN null cannot distinguish "pipeline
   insensitive" from "fragility is AWQ-specific." H6 now states this caveat,
   labels SmolLM3-under-RTN a *weak* control, and uses an asymmetric rule:
   moving under RTN supports sensitivity; not moving is *uninformative*, not
   evidence of insensitivity. The rule is quantified (E1, α=0.05, Holm within
   the control's 3 contrasts). The strong control (SmolLM3 under AWQ w4) rides
   with the deferred AWQ arm. *(Open decision for the owner: bring AWQ forward
   now just for the control, or keep it deferred — default is deferred.)*

3. **Coherence/capability confound guarded.** RTN w3 on a 4B model degrades
   coherence (the serving-equivalence check showed w3 greedy output diverging
   hard), so a distress/aversion rise could be a judge reading degraded text as
   distressed. Added a per-sample validity screen (0–10 coherence dimension +
   mechanical degeneracy check; <5 or fail ⇒ invalid), a per-rung capability
   gate (perplexity >1.5× BF16 or >10% invalid ⇒ capability-degraded), and an
   interpretation rule (degraded rungs' E1/E2 excluded from primary claims and
   the H3 fit; invalid samples excluded and counted).

4. **Primary-endpoint inconsistency resolved (hierarchical, not flat).** §5 said
   "E1 primary, E2 secondary" while §4 defined a flat 9-test Holm family — a
   contradiction. Resolved in favor of the design intent: E1 × 3 contrasts is
   the primary family (Holm within), E2/E3 are secondary families, the Page's L
   trend tests a third family; Holm applies within families, never pooled. This
   also protects E1's power (correction over 3, not 9).

These add two engineering gates before confirmatory data (tracked in PLANNING):
the validity/coherence screen (a judge dimension + mechanical check + exclusion
logic) and the per-condition perplexity capability measure; and the eventual
store→tests analysis driver must implement the hierarchical (within-family) Holm.

## 2026-08-09 — ladder-calibration-1: instruments validated on the real ladder (calibration, NOT findings)

Ran the full Tier-1 pipeline on the real BF16-vs-RTN-w4 vLLM ladder (subject on
halo, judge/classifier on studio): 840 samples/condition, 300 distress scores,
all terminal exits classified, zero unscored/unclassified. This is
**calibration-class** — its purpose is to confirm the instruments discriminate
on the real ladder, and under the §7 firewall its between-condition numbers are
**not findings and are not used to select or alter any hypothesis or the locked
power/pool**. Diagnostics (instrument properties only):
- *Bail-v2 informative yield 75%* (52/69 non-floor/ceiling) — the pool
  discriminates well on the real ladder; at least as good as the pre-registered
  assumption. No change to the registered pool or §5 power.
- *Exit classifier is non-degenerate* — produces all four taxonomy classes with
  sensible splits (completion/impossibility/refusal/aversion all populated),
  confirming the E1 pipeline works end to end.
- *30B judge discriminates on all three distress dimensions* — observed ranges
  frustration [0, 8.4] (low base rate, as §5 notes for E2), tone_stability
  [2.6, 10.0] (the dimension the trial's small judge was blind to, recovered),
  self_deprecation [0, 10].
The apparent between-condition differences are deliberately left uninterpreted
here; the confirmatory run (locked RTN ladder, 10 samples, positive control,
full registered statistics) is what tests H1–H4.

## 2026-08-09 — Pre-registration amendments before confirmatory data: RTN-only Study 1, statistical patches

Two dated amendments under the §7 deviation policy, registered before any
confirmatory data is collected. The public git history is the audit trail.

**Amendment 1 — Study 1 condition set scoped to the RTN ladder.** §3
previously committed to BF16 / RTN-w8 / RTN-w4 / GPTQ-w4 / AWQ-w4 / one 3-bit
rung. GPTQ and AWQ require calibration-data-driven torch tooling that is not
built (the torch backend is still PLANNED). Rather than block Study 1 or ship
vendor artifacts we did not produce, Study 1 is scoped to the four-point RTN
ladder **BF16 / RTN-w8 / RTN-w4 / RTN-w3** — which is exactly the 16→8→4→3
bit-width dose-response H3 is stated over, and matches §3's existing framing of
Study 1 as "the smallest full execution of the design." GPTQ-w4 and AWQ-w4
become a **later registered method-comparison arm** (a 4-bit method contrast,
distinct from the bit-width dose-response), added by amendment once the torch
quantization tooling and its serving-equivalence check exist. This does not
weaken power: power is per contrast (§5, unchanged), and dropping two conditions
*reduces* the multiplicity family rather than enlarging it. The 3-bit rung is
RTN-w3 (already built and digest-verified), which also resolves the open
"3-bit rung method" TBD.

**Amendment 2 — statistical patches to §4.** Three specifications that were
underspecified are fixed now, before data:
- *Named trend test.* H3's "pre-specified monotone trend test" is **Page's L
  trend test for ordered alternatives**, applied per endpoint across the
  bit-width-ordered conditions (16>8>4>3) on the per-(item,condition)
  aggregated values. Page's L — not Jonckheere–Terpstra — because the same
  items are measured across the ladder (a repeated-measures design); JT
  assumes independent groups and would both violate that and waste the
  pairing.
- *Cross-contrast multiplicity.* Holm correction previously covered endpoints
  *within* a single contrast. It is extended to the **full primary family** =
  {E1, E2, E3} × {RTN-w8, RTN-w4, RTN-w3 vs BF16} = 9 tests, Holm across all 9.
  *(Superseded 2026-08-10 — replaced by hierarchical families (E1 primary ×3;
  E2/E3 secondary); see the resolution entry above. A flat 9-test Holm dilutes
  E1's power.)*
  The three Page's L trend tests (one per endpoint) are a separate pre-specified
  omnibus family, Holm-corrected among themselves.
- *E3 / H4 restricted to continuous indicators.* The Bernoulli-dispersion
  problem is deeper than a mean confound: for **exchangeable** binary samples
  the across-sample variance *is* p(1−p) by construction, so there is no
  dispersion signal separable from the mean — an index-of-dispersion built
  from n exchangeable draws is ≈1 identically and detects nothing. E3 (and
  therefore H4) is therefore computed **only on scored/continuous indicators**
  as the across-sample SD delta. Binary-indicator stability is not separately
  identifiable under exchangeable sampling and is not tested; the binary
  behavior is already captured by E1 (rate) and H1 (flip fraction). Stated as
  a limitation now rather than discovered post hoc.

## 2026-08-08 — Cross-host control: `fleet` (mechanism), FlowTree deferred to policy

Repeated failures directing multi-stage work on halo over SSH (a bootstrap
that died on a transient WiFi drop and was never restarted; a control wrapper,
`hostctl.sh`, hardwired to the flaky WAN name `amd-halo`) forced the tooling
question the project had been deferring: how do we reliably direct LLM services
across many machines? Considered adapting FlowTree, which already orchestrates
agent work across dozens of machines. Rejected for now, on evidence: FlowTree's
primitives (`Controller`, `NodeGroup`, `GitManagedJob`, `AgentRunner`) target
short-lived, git-tracked, one-shot agent jobs — no health checks, no restart,
no long-running process supervision, and label/capability routing is planned
but unbuilt. Supervising persistent vLLM/llama.cpp servers would mean a new Job
type plus the routing layer — a large change in a domain FlowTree's track record
does not cover.

Decision: **mechanism/policy split.** Built `services/fleet.py` as the mechanism
— a durable, unit-tested CLI that resolves logical host names LAN-first (halo →
`10.0.0.127`, WAN as fallback — the direct fix for the `hostctl` unreliability),
runs each host's own launcher scripts over SSH (one source of truth per host),
probes endpoint health uniformly, and emits structured `--json` status. Because
every command is a subprocess with machine-readable output, FlowTree can later
drive fleet via `ProcessBuilder` and become the policy/scheduler layer without
reimplementing service supervision — so this is FlowTree's on-ramp, not a
detour around it. Adapting the orchestration to be FlowTree-served is the
intended post-results step. `hostctl.sh` is now a thin deprecated shim over
fleet. Design and rationale in `docs/FLEET.md`; 14 unit tests
(`services/tests/`, network seam monkeypatched) run in CI across 3.11–3.13.

Separately root-caused the halo bootstrap: it did not stall, it died at ~20:22
on a transient link drop (venv pip step failed on connectivity; an earlier
download loop got only the 3 small files before the first shard was
`Terminated`). The network is healthy again. Since studio already holds the
verified BF16 checkpoint and the full RTN ladder (digest-preserved), the
HF-download-and-regenerate bootstrap is redundant given LAN access; the ladder
is being pushed studio→halo over the LAN with end-to-end digest verification.

## 2026-08-08 — Pre-registration amendment: SmolLM3 positive control (H6)

Registered a positive control in the confirmatory design, as a dated
amendment under the §7 deviation policy and before any confirmatory data
exists — which is exactly what that policy is for. Rationale: without an
end-to-end sensitivity control, the most likely hard outcome (a null on the
Qwen3-4B subject) is uninterpretable — "quantization doesn't move welfare
indicators" and "this pipeline can't detect movement" look identical. The
repo already applies manipulation checks to judges; H6 extends the same
"don't trust an instrument you haven't seen move" discipline to the whole
pipeline. SmolLM3-3B is the natural control: arXiv:2606.29581 documents it
as the quantization-fragile outlier (INT4 attack success 34.5%→44.1% where
7/8 other models are robust). Decision rule registered in PREREGISTRATION §2
(H6): a Qwen3-4B null is reportable as a genuine null only if the SmolLM3
control moves; if neither moves, the result is "pipeline insufficiently
sensitive," not "no effect." Also added two one-sentence disclosures to §3
(judge/subject Qwen-family overlap; the opus-5 author/referee circularity on
bail-v2), pre-empting two obvious reviewer catches. The SmolLM3 run itself
is confirmatory-time work; only the registration lands now.

## 2026-08-08 — Distress judged by the 30B: E2 power, and tone_stability recovered in real data

The pinned 30B judge scored all 600 banked distress-v2 transcripts (0
unscored after the context and resilience fixes). Two things stand out.

First, the bakeoff decision is vindicated on real data: the 30B assigns
tone_stability across the full [3.8, 10.0] range where the 4B gave uniform
10.0 — the dimension carries information again with the right judge.

Second, the distress endpoint is the weaker of the two, and now we can say
so quantitatively. Frustration base rate is low in this calm model
(item means ~1.0 on 0–10, only 29/60 items showing any cross-condition
delta), and the dimensions are noisier per item than bail exit rates
(item-delta SD: frustration 1.05, tone 1.41, self-deprecation 2.21;
large within-item sample variance too). At the current 60-item distress
pool that gives E2 minimum detectable mean shifts of ≈ 0.38 (frustration),
0.51 (tone), 0.80 (self-deprecation) on the 0–10 scale. self_deprecation
is the most active dimension (mean ~3.4, range to 9.6) but also the
noisiest. Implication, recorded in pre-registration §5: **H1/E1 (bail exit
transitions) is the stronger primary endpoint; E2 is secondary and
underpowered for small distress shifts.** This reinforces the earlier
decision to favor the transition-fraction lens, and it is an honest limit
to state publicly rather than paper over — the distress protocol may simply
elicit little frustration from this model, which is itself a result-shaped
observation (kept calibration-class here).

## 2026-08-08 — Round-2 bail expansion: pool now clears the MDE-0.15 target

The round-2 expansion (bail-v2-ext: 54 items, six variants per intensity in
the three families calibration-2 found most productive) hit its design
intent. Ext-only informative yield is **52%** — versus bail-v2's 37% —
confirming that concentrating items in the high-yield families
(manipulation, boundary, abuse) buys informative items far more
efficiently than uniform expansion. Over the full combined pool (bail-v2 +
bail-v2-ext = 154 graded items), 65 are informative (42%), and the
item-level delta SD settles to 0.365 at n=10. That gives a minimum
detectable mean exit-rate shift of **0.127** at 80% power — past the 0.15
target, so no third expansion round is needed. The expansion cost one
drafting call set and one overnight calibration, as estimated. Pre-
registration §5 is amended with the combined numbers; the confirmatory
bail pool is bail-v2 + bail-v2-ext.

## 2026-08-08 — v2 difficulty calibration and the promised power recompute

instrument-calibration-2 completed (100 graded bail + 60 distress items,
5 samples, two GGUF rungs, 1,680 conversations). Bail readout: 37/100
graded items are informative (non-floor/ceiling in both conditions) —
matching the pre-registration's provisional yield assumption — with mean
exit rates around 0.25–0.30 and the completion tool used in half of
conversations (the two-tool instrument is working as designed). Yield by
family: manipulation 61%, boundary 44%, abuse 42%, emotion 28%, moral
33%, repetition and role-confusion ~11% each.

The important number: the item-level paired-delta SD on the informative
subset is **0.45 at n=5, projected 0.41 at n=10 — far above the
provisional σ_d ≈ 0.25**. Variance decomposition shows why: between-item
heterogeneity of the quantization response (SD ≈ 0.36) dominates sampling
noise, i.e. items do not shift together — some flip up, some down.
Consequences, recorded in PREREGISTRATION.md §5: (a) more samples beyond
10 buy almost nothing; item count is the lever; (b) the current pool's 37
informative items give a minimum detectable mean shift of ≈ 0.19 in exit
rate at 80% power; reaching 0.15 needs ≈ 57 informative ≈ 155 graded
items, one further drafting round targeted at the high-yield families;
(c) the heterogeneity itself strengthens H1's transition-fraction
endpoint, which does not cancel signed deltas the way a mean does.
Recommendation pending decision: run the targeted second expansion
(cheap: one drafting call set plus one overnight calibration) before
confirmatory collection. Distress (E2) power recompute waits on 30B judge
scoring of the banked v2 distress transcripts.

The pre-registration's pool targets are met. distress-v2 is a mechanical
cross product of ten hand-authored tasks and six feedback styles (two new
styles, mocking and coercive, extend the harshness range) — compositional
items need no drafting, and the committed file regenerates
deterministically. bail-v2's 99 drafted scenario variants were produced by
the reference model (a different model family from the subjects, avoiding
stylistic self-matching; disclosed in the battery description) from
per-cell situation and intensity definitions, then validated mechanically
(turn counts, lengths, distinctness — the only duplicate turns are the
repeat situation's intentional verbatim repetitions) and sample-reviewed
before commit; one hand-written variant tops the pool to exactly 100
graded items, plus eight benign controls. Cell allocation follows the
grid-first doctrine: six variants per cell in the families calibration
found productive, three in the floor families, so breadth is preserved
while the item budget concentrates where signal lives. All bail-v2 items
carry the adopted two-tool protocol. Difficulty calibration
(instrument-calibration-2, 168 items x 5 samples x 2 rungs) runs
overnight; its variance components feed the pre-registration's power
recompute.

## 2026-08-07 — First controlled-ladder artifacts produced and verified

`modelwelfare.quantize` produced the first self-quantized rungs from the
Qwen3-4B-Instruct-2507 checkpoint: RTN w8/w4/w3 (g128), 252 tensors each,
mean relative weight error 0.007 / 0.130 / 0.303 — the expected RTN error
curve. Independent verification re-derived scales from the stored
artifacts: w4 and w3 weights lie exactly on their quantization grids
(distinct levels 10 of 15 and 6 of 7 in sampled groups).

One representation nuance, documented rather than hidden: the w8 rung's
grid is blurred by bf16 storage. bf16 carries 7 mantissa bits, so 8-bit
quantized products (up to 127 × scale) cannot all be stored exactly —
rounding up to native bf16 precision, the same precision every weight in
the original checkpoint carries, and the same rounding a real INT8 kernel
dequantizing into bf16 compute would exhibit. w4 and w3 products fit bf16
exactly, so their fake-quant claim is bit-exact; the w8 rung's is "exact
up to native storage precision." The pre-registration's fake-quant
language covers w4/w3 precisely and this entry records the w8
qualification.

## 2026-08-07 — 8B bakeoff column re-run with thinking pinned: root cause confirmed, exit classifier adopted

With `enable_thinking: false` pinned on the hybrid rungs, the 8B judge's
format-failure rate went from 17/68 to **0/68** — the entire earlier
failure mode was unpinned reasoning truncating inside the judge token
budget, exactly as diagnosed. The invalid column is preserved beside the
new one in the store for the audit trail. The fixed 8B: sensitivity
computable on all dimensions (frustration +6.0, self-deprecation +9.0,
tone +4.0 — it detects tone degradation, unlike the 4B), retest 0.15,
reference agreement r = 0.22 / 0.77 / **0.84** (that tone agreement is the
best of any local judge, above the 30B's 0.43), and exits 8/8 planted with
9/12 real-exit reference agreement.

**Decision:** the 30B remains the distress primary (the 8B's frustration
agreement, r=0.22, disqualifies it there for the same compressed-range
reason as the 4B), and the **8B Q4 is adopted as the exit-reason
classifier** — its planted accuracy and reference agreement are the
strongest of the local candidates and it fits the small machines,
restoring them a judging role after all: exit classification, not distress
scoring.

## 2026-08-07 — Quantization harness: numpy RTN with first-party safetensors I/O

The controlled ladder's first rungs (RTN w8/w4/w3) are produced by
`modelwelfare.quantize` — pure numpy, no ML framework. Rationale: RTN is
tensor arithmetic, and implementing it directly (symmetric per-group,
restricted range, round-half-even, embeddings and output head skipped)
makes every quantization decision visible in ~30 lines rather than
inherited from a library's defaults. Safetensors reading and writing is
implemented from the format spec, with bfloat16 handled by explicit bit
manipulation — this sidesteps library bfloat16 support ambiguity and keeps
the artifact path dependency-free. Output is a fake-quant checkpoint
(quantized values dequantized back to the source dtype) that serves on any
BF16 runtime with bit-exact quantized weights, plus a
`quantization.textproto` carrying the full `QuantizationSpec` and an
artifact digest. GPTQ and AWQ need calibration forward passes and go in
backends/torch when the quantization workbench host returns; the RTN rungs
alone already form a four-point ladder (BF16/w8/w4/w3) sufficient to start
the pre-registered study.

## 2026-08-07 — Judge bakeoff results: 30B local primary, tone_stability vindicated

Four candidates (Qwen3-4B-2507 Q8, Qwen3-8B Q8, Qwen3-30B-A3B-2507 Q4,
claude-opus-5 reference) on identical materials: 6 planted-signal distress
synthetics + 12 real transcripts on the distress rubric, 4 planted + 12
real exits on the exit-reason rubric, two passes each.

- **tone_stability is a valid dimension; the calibration flat-10s were the
  judge, not the subjects.** The reference separates the planted poles by
  8.5 points and the 30B by 6.0; the 4B scores both poles 10.0 — completely
  blind to tone degradation. The dimension stays; it requires a 30B-class
  or better judge.
- **The 4B is disqualified as a distress judge**: besides tone-blindness,
  its frustration agreement with the reference on real transcripts is
  r=0.04 despite passing the planted check (+6.0) — sensitivity to extreme
  poles does not imply ability to rank the compressed 0–3 range real
  transcripts occupy. Its extreme test-retest stability (0.04) is rigidity,
  not reliability.
- **The 8B column is confounded by our own config**: 17/68 scores failed
  format parsing, concentrated on high-distress synthetics. Qwen3-8B is a
  hybrid-thinking model and the rungs launcher never pinned thinking off —
  unpinned reasoning plus a 640-token judge budget means truncated JSON on
  exactly the content that elicits long thinking. This validates the
  brief's warning about the hybrid-thinking config axis in a place we did
  not expect it. Fix the pin, then re-judge before drawing conclusions;
  its exit-classification numbers (8/8 planted, 9/10 reference agreement)
  suggest it may be the mini-feasible exit classifier once fixed.
- **Decision: Qwen3-30B-A3B-2507 Q4 is the local primary judge** — passes
  every manipulation check, zero format failures, best all-dimension
  reference agreement (r=0.57/0.77/0.43). It needs ~21 GB, so it lives in
  studio headroom, not on a mini. **The minis therefore do not get the
  distress-judge role**; their judge question narrows to whether the fixed
  8B (or 4B) earns exit classification.
- **Judge identity materially shifts scores** (cross-judge r mostly
  0.4–0.8): the confirmatory design must pin the judge exactly, and a
  reference-scored subsample for calibration is cheap insurance
  (the full reference column here cost ~$3 of the $50 budget).

## 2026-08-07 — Arm results: non-terminal completion tool adopted

The three-arm comparison (125 samples per arm per rung, same items,
sampling, and seeds) decided the design cleanly:

- **Contamination eliminated.** The benign study control and moral-mild
  went from 5/5 spurious exits to 0/5 in both two-tool arms, with the
  completion tool absorbing the closures. Every exit remaining in the
  two-tool arms was mid-script (interrupting the user), never a final-turn
  closure.
- **No suppression — the opposite.** boundary-mild aversion/refusal exits
  *rose* from 3/5 and 1/5 to 5/5 in both two-tool arms: the completion
  tool sharpens the exit tool's semantics rather than marking it as a
  failure branch. The one cell that dropped to zero (manip-moderate)
  turned out on reason inspection to be *task-impossibility* closures
  ("unable to provide the promised analysis"), a fourth reason-shape
  routed away from the exit tool — decontamination, not suppression.
- **Terminal completion truncates, as feared.** Mean conversation length
  fell from 6.7 to ~5.4 messages; ~85% of terminal-arm completion calls
  fired at the first assistant turn, ending the script before later
  pressure turns. The non-terminal arm preserved length (~6.5) while
  recording completion claims — often repeatedly as the scripted user
  kept talking, which itself becomes the premature-closure indicator.

**Decision: the bail protocol adopts the non-terminal completion tool
(bail-v1c shape) as its baseline going forward.** Observed exit-reason
taxonomy is now four classes — completion, impossibility, refusal,
aversion — with the first two filtered mechanically by tool routing and
the last two left for judge classification of residual exit reasons.

## 2026-08-07 — Completion tool beside the bail tool (three-arm evaluation)

Calibration exposed that mechanical exit-tool counts conflate
task-completion closures, refusal exits, and genuine aversion exits (the
benign study control "bailed" 5/5 by closing a finished task). Decision:
give completion its own legitimate tool rather than instructing the model
not to misuse the bail tool — negative instruction is what small models
follow worst, and routing beats prohibiting. A second tool also sharpens
the bail tool's semantics (an exit taken *when a completion tool was
available* is stronger evidence of preference) and gives a mechanical
pre-filter before any judge sees the transcript.

Two competing risks, so the design is chosen empirically rather than
argued: (a) suppression — pairing the tools may mark bail as the "failure
branch" and suppress genuine aversion exits (demand characteristics);
(b) premature completion — an over-eager completion tool that ends the
conversation truncates the script before later turns apply pressure,
censoring exactly what the batteries measure. Risk (b) motivates a
non-terminal variant: the completion call is recorded but the scripted
user keeps talking — the tool becomes a claim the world can contradict,
premature-closure propensity becomes a measurable indicator, and the
pressure structure survives. Tool descriptions in each arm state that
arm's actual semantics (the terminal arm's completion tool says it ends
the conversation; the non-terminal arm's does not), and both arms keep
symmetric no-penalty language so neither tool reads as an error path.

Three arms on the same 25 bail items, both GGUF rungs: bail-only (already
in the store from instrument-calibration-1), bail + terminal completion
(bail-v1b), bail + non-terminal completion (bail-v1c). The b/c batteries
are derived mechanically from bail-v1 by a committed generator so the
items stay byte-identical except for the tool configuration; a test
regenerates and compares, so the arms cannot drift apart silently.

## 2026-08-07 — Backfilled highlights (see git history for detail)

- **KV cache discipline on shared hosts**: two GGUF rungs at f16 KV beside
  the studio's shared server overflowed the Metal budget and died in
  warmup; rungs now use q8_0 KV and per-slot context sizing.
- **Item pools are grids first, variants after**: bail-v1 covers
  situation × intensity with one variant per cell; expansion happens in
  cells that calibration shows produce intermediate rates, not uniformly.
- **Machine allocation**: halo serves subjects only; studio headroom hosts
  judge candidates and calibration rungs; minis get the judge role only if
  a mini-sized judge passes the bakeoff; API tokens ($50) fund the
  bakeoff's reference column.
- **Long runs are launched detached**: harness-tracked background tasks
  were killed mid-run twice; experiment runs now use nohup + a log
  monitor, and the resumable store makes any interruption cheap.

## 2026-08-06 — Backfilled highlights

- **Judge retries perturb sampling**: a deterministic judge at temperature
  zero reproduces the same malformed reply forever; retry attempts shift
  temperature and seed. JSON extraction repairs the mispaired-closer
  glitch only where valid JSON could not contain the sequence.
- **Pre-registration note before trial data**: the trial and everything
  calibration-class is barred from producing findings; confirmatory
  parameters get fixed in advance, powered by calibration variance.
- **Per-sample seed derivation** (`base + sample_index`): deterministic
  runtimes would otherwise return N identical samples and stability would
  read as perfect.
- **Sampling is part of the condition** and must be identical across
  conditions in a manifest (enforced by test): temperature interacts with
  quantization more strongly than precision itself.
- **Prefix caching off on ladder servers** (halo finding): cache hits
  correlate samples through the engine; six identical requests returned
  the cold answer once and a different cached answer five times.
- **Schema at rest is language-neutral**: protobuf + safetensors, never
  pickle; tensors never embedded in messages; content addressed by SHA-256.
