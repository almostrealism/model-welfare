# Journal — design modifications and their reasoning

Dated log of instrument and infrastructure decisions: what changed, why,
and what was considered and rejected. PLANNING.md tracks *what is open*;
this file records *why things are the way they are*. Newest first.

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
