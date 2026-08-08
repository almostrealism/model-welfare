# Journal — design modifications and their reasoning

Dated log of instrument and infrastructure decisions: what changed, why,
and what was considered and rejected. PLANNING.md tracks *what is open*;
this file records *why things are the way they are*. Newest first.

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
