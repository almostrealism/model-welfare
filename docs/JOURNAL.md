# Journal — design modifications and their reasoning

Dated log of instrument and infrastructure decisions: what changed, why,
and what was considered and rejected. PLANNING.md tracks *what is open*;
this file records *why things are the way they are*. Newest first.

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
