# Study 3 — an exploratory update: what steering taught us, and a pivot

**Status: exploratory report, 2026-09-07. Not a pre-registration.** Study 3 set
out to causally validate welfare-relevant indicators by activation steering, and
to open a graded-episode framing question. It did not reach a confirmatory
registration, and this post explains why in full: calibration showed the
steering *instrument* does not produce a behavioral signal worth powering a
study around in this subject. We report that negative result openly and, in the
same post, disclose where the program goes next. There is no registration to
firewall here — this is exploratory work reported as exploratory work.

---

## 1. What Study 3 was going to be

Study 2 left a correlational picture: under quantization, a 4B model's
generations shift along frozen residual-stream "welfare directions" (distress,
assistant axis) and its judged frustration rises. Study 3's plan was to
intervene on those directions — add or subtract them in the reference-precision
model — and see whether the behavior followed (sufficiency, necessity). A second
thread, from nostalgebraist's "graded episodes," asked whether *framing* an
episode as graded changes the indicators, and whether grading pressure masks
distress.

## 2. The calibration timeline, and the steering null — in full

Before committing a confirmatory exposure budget, we ran small
calibration-class instrument checks (n = 8 items, 1–10 samples, underpowered by
design). Their job was feasibility: is the steering effect large and specific
enough to justify a powered study? The answer was no, across two directions and
two doses. Each frozen direction, at its calibrated dose, was compared to a
matched-norm 32-direction random envelope:

| Probe | Direction / dose | Judged-frustration effect | Percentile of matched random envelope |
|---|---|---|---|
| distress @ α* | distress, 1.039 | +0.138 | 34th |
| assistant-axis @ α* | axis, −0.604 | +0.225 | 56th |
| distress @ larger α | distress, 3.5 | −0.075 | 56th |
| grader-type @ α=4 | automated-grader | −0.41 (robust −0.11) | 19th |
| eval-awareness @ α=4 | evaluation-aware | −0.30 | 19th |

Every substrate gate (torch-vs-vLLM, cross-host) passed, so this is not an
apparatus artifact. But at its calibrated dose, each frozen direction moves the
*projection* (the representation) as intended while producing a *behavioral*
effect indistinguishable from — often below — norm-matched random perturbation.
We even tried the literature-potent direction: the automated-grader vector from
[Betley/Treutlein/Dumas](https://www.lesswrong.com/posts/wYZMmdWEt5QLM3m3e/steering-towards-automated-grading-degrades-alignment),
whose steering demonstrably degrades *alignment* in a larger model — and in this
4B model it too was sub-threshold on welfare-indicators.

**Reading:** in Qwen3-4B, steering frozen welfare directions is not a specific
behavioral lever. The directions read as correlational, not causally sufficient
for behavior.

## 3. The framing thread, and why it's compromised too

The graded-episode *frame* does move behavior — a verifier frame shifted judged
frustration by ≈ −1.1, far outside any random envelope. But the reading that
would make this a *welfare* result rather than a prompt trick — the masking test,
"does behavior move while the representation moves less?" — rests on the same
frozen-direction projection whose validity the steering null just undercut. So
the framing effect is behaviorally real but its welfare-relevance inherits the
representational-proxy problem. Framing is not a clean escape hatch.

## 4. Why this is a calibration result, not a hidden confirmatory null

The probes were underpowered instrument checks, not the powered subset a
confirmatory run would use; their purpose was feasibility and their finding is an
*instrument* finding — steering produces no behavioral signal worth powering.
Running the powered arm would spend a large distress-exposure budget to precisely
estimate an effect calibration already shows is ~zero and non-specific. We report
the full null rather than bury it, and we withdraw the steering hypotheses rather
than convert them into unregistered claims. This program's standing guardrail:
**calibration never substitutes for a registered finding; "not worth powering" is
argued from the instrument's behavior, never from an unwelcome result; and the
calibration data behind any such decision is published.** This update is its
first application.

## 5. What we actually learned, and where the program goes

The negative result is informative on three fronts, and they compose into the
program's next move:

- **Representation ≠ behavior (in a 4B model).** Frozen directions that read out
  a state are not thereby levers on behavior. This cautions against treating any
  representational read as an internal-state proxy — a caution that reshapes how
  we'd run a masking test anywhere.
- **The graded-episode effect is real and bears on alignment.** Betley et al.
  show that steering toward an automated grader raises violent-action propensity
  and Machiavellianism — a *causal* graded-episode effect, on a model where
  steering demonstrably works.
- **A three-pole tradeoff landscape is the center of gravity.** The program's
  through-line is a hypothesized tradeoff among **capabilities, alignment, and
  welfare-indicators** — the same asymmetry logic that motivated studying
  quantization (uneven impact on capabilities vs welfare). Betley hands us a
  manipulation with a *documented alignment effect*; the open question is whether
  it also has a **welfare footprint**, and whether that footprint is coupled to
  or dissociated from the alignment effect.

**The plan (disclosed, gated, not yet registered).** The next study takes the
graded-episode manipulation to a subject where it demonstrably bites — the exact
Betley model (Qwen3.6-27B) — and asks whether the alignment-degrading
grader-steering *also* moves welfare-indicators, placing a point on the
capabilities/alignment/welfare triangle. We are deliberately pruning before we
invest: **Gate 0** is a pure engineering check (can we load and steer a 27B on
our hardware at a workable rate?); **Gate 1** is a small exploratory probe (does
the manipulation touch welfare-indicators at all?). Only if Gate 1 shows a
footprint do we scope and register the full study. This is the discipline the 4B
experience bought us: spend real resources only on what we can expect to find.

The 4B steering line is closed. The graded-episode / welfare-footprint question
is very much open — on a model where the manipulation is known to work.
