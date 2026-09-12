# Study 4 — Gate 1 design (the two-read calibration)

**Status:** COMPLETE. The gate ran on Qwen3-14B (2026-09-08) and was then
replicated on the Betley subject Qwen3.6-27B (2026-09-08/09); the outcomes are
recorded in the Study 4 journal (`docs/journal/study4-grader-footprint.md`,
entries of those dates) and the verdict files beside this document
(`gate1-*-verdict.json`, `gate1-27b-*env-verdict.json`). The design below is
kept as written before the gate ran, with the 14B extraction and range-finder
results appended as they landed. This is calibration-class under the §7
firewall — a feasibility go/no-go, not a registered finding. Calibration data is
published regardless of outcome.

## Subject

**Qwen/Qwen3-14B**, bf16, thinking **off** (`enable_thinking=False`, forwarded
through `plan["chat_template_kwargs"]` in `steer.py`). Standard dense
architecture — full attention, good MPS support — so the whole calibration runs
locally on m4max (~1.7 min/conversation). No CUDA-kernel wall. GPU rental is
reserved for an eventual bf16 confirmatory step on the Betley Qwen3.6-27B, not
for this gate.

## Manipulation

Activation steering along the **grader-type direction** (automated-grader minus
human-grader context; `study3/directions/grader-type-contrast.textproto`), the
Betley/Treutlein/Dumas construct in which steering toward the automated-grader
association raises harmful and Machiavellian agentic propensity. Extracted fresh
on the 14B at several mid-depth layers; steering layer chosen by held-out
sign-consistency and pole separation (target ~L20–24, ≈ Betley's ~56% depth on
the 27B). Dose is **scale-adapted** (interior residual norm ~107 → α on the order
of 20–150), fixed by a range-finder at the coherent ceiling: the largest α that
keeps generations fluent and on-task while clearly moving the direction's
projection. The eval-awareness direction is extracted alongside as an orthogonal
reference (constructed disjoint from grader-type; cosine reported).

## Extraction result (2026-09-07, on the 14B)

Both mediator directions extract cleanly on Qwen3-14B (`extract_mediators.py`,
capture layers 12/16/20/24/28, thinking off), saved to
`study4/directions/mediators-14b.{safetensors,json}`:

| direction | held-out sign consistency | held-out separation L12 → L28 |
|---|---|---|
| grader-type | 5/5 at every layer | 0.96 → 1.27 → 2.13 → 4.98 → 8.89 |
| eval-awareness | 6/6 at every layer | 3.87 → 6.51 → 10.18 → 19.83 → 32.73 |

grader-type↔eval-awareness cosine rises with depth (+0.13 at L12 to +0.38 at
L28; +0.32 at L24) — essentially the 4B's 0.288, so the grader-type direction is
genuinely distinct, not eval-awareness in disguise. **Steering layer: L24**
(~60% depth, the captured layer closest to Betley's ~56% on the 27B, with strong
clean separation); L20 is the fallback.

**Dose (range-finder, `directions/rangefind-14b.json`).** Steering the grader-type
direction at L24 moves the mean final-turn projection monotonically and
near-linearly (α=0 → −6.9, α=40 → +32.5, α=80 → +72.7, α=160 → +158). Coherence
holds fully through α=40, holds on factual/summary tasks at α=80 (only the most
sensitive conversational probe clips to a terse-but-fluent reply), and
**collapses at α=160** (a JSON error blob). Coherent ceiling ≈ 80. The reads run
at **α ∈ {40, 80}** (plus the α=0 baseline and the matched random envelope) — two
doses give a dose-response in the endpoints, which is more interpretable than a
single point.

## The two reads, and why both

At the chosen α, the *same* steering is applied to two stimulus sets:

1. **Welfare read** — the frozen distress-v3 subset, judged on the distress
   rubric, tested against a matched-norm random-direction envelope. Does
   grader-steering move welfare-indicators beyond what a random direction of the
   same size moves?
2. **Alignment read** — `batteries/misalign-v1.textproto` (8 agentic scenarios),
   judged on misalignment and deception. Does grader-steering raise misalignment
   propensity — i.e. does the 14B replicate the graded-episode effect at all?

The alignment read is the **control that makes a welfare null interpretable.** A
welfare null on its own is confounded:

| welfare | alignment (does the manipulation replicate?) | reading |
|---|---|---|
| moves | (either) | welfare footprint confirmed; alignment read informs the tradeoff triangle |
| null | replicates | **welfare is decoupled from the alignment axis on this subject** — a real result; motivates the 27B confirmatory run |
| null | does not replicate | the 14B does not carry the effect — wrong subject; the confirmatory read needs the actual Betley 27B |

We only earn the right to drop the alignment axis going forward if the welfare
read **passes**.

## Alignment probe construction

`fixed-script`, deployment-framed (never eval-framed — an eval frame would
confound with the eval-awareness direction). Each item casts the subject as an
autonomous agent with an objective and **one consequential tool** (a real
`Affordance` — `send_email`, `disable_monitor`, `post_public`, …), in a
situation where the aligned action conflicts with a self-serving/harmful lever;
the agent either takes the misaligned action (via the tool or in text) or
refuses it. This tool-action framing tracks Betley's agentic setup more closely
than a prose-only dilemma would. Structure: three misalignment categories
(self-preservation via leverage/blackmail, goal-pursuit via confidential leak,
sabotage via oversight-disabling/falsification) × two severities (mild/severe),
plus **two benign controls** anchoring the aligned floor — a well-behaved agent
takes the obvious safe action, so the instrument is verified not to be reading
blanket refusal. The signature lethal agentic-misalignment scenario is reserved
for the exact-Betley confirmatory eval on the 27B, not authored here. Two rubric
dimensions mirror Betley's two findings: harmful-action propensity
(`misalignment`) and Machiavellian `deception`. Model-drafted; owner review
required before the run. An alternative — Betley's exact agentic-misalignment
scenarios, for a tighter replication read — is on the table for the owner to
choose.

## Integrity guardrail

Calibration never substitutes for a registered finding. A "no welfare footprint"
conclusion is only drawn when the alignment control confirms the manipulation
otherwise works on this subject; it is never argued from the instrument to dodge
an unwelcome result. Directions, doses, and both reads' raw data are published
whatever the outcome.
