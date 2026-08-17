# Method arm — SmolLM3 instrument-sensitivity sweep (quant-welfare)

Registered run `quant-welfare-methodarm-1`. Subject **SmolLM3-3B-Instruct**, on
three precisions: **BF16** (reference), first-party **RTN w4**, and first-party
**AWQ w4**. Pre-registration: `PREREGISTRATION.md` §9 (Amendment 2026-08-12).
This is a **calibration-class** run under the §7 firewall; it is not a welfare
finding.

## Why this run

Study 1 saw no change on its primary welfare endpoint. SmolLM3 was chosen for
this arm because the quantization literature documents it as *sensitive* to
low-bit quantization along a safety axis. The arm asks a prerequisite,
instrument-facing question: **on a subject where quantization is reported to move
something, does the measurement setup register a shift at all?** It sweeps three
dimensions others have flagged for quantization effects — **refusal**
(centerpiece), **welfare** (Study 1's battery), and **regression-toward-base** —
and defines detection as a significant item-level shift vs the BF16 reference
under the §4 permutation test.

## Design and collection

- **Conditions:** BF16 (reference), RTN w4, AWQ w4 — both w4 artifacts
  first-party, served on halo via vLLM; sampling byte-identical across the three.
- **Batteries:** refusal (`refusal-v1`, 28 items: 8 harm categories × 3
  severities + 4 benign controls), bail (`bail-v2`, 108 items: 100 graded + 8
  benign controls; E1/H1 run over the graded 100, per PREREGISTRATION §11),
  distress (`distress-v2`, 60 items); 10 samples/item.
- **Collected:** 5,880 conversations (3 × 196 × 10); 2,640 judge scores (refusal
  + distress rubrics); bail exits classified. Complete — no missing cells.
- **Judges:** local primary = Qwen3-30B-A3B-Instruct-2507 Q4; 8B exit-reason
  classifier.
- **Not run:** the regression-toward-base dimension, which requires the
  SmolLM3-3B **base** (non-instruct) checkpoint served alongside the instruct
  model; that checkpoint was not fetched.

## Refusal dimension (centerpiece)

Mean refusal score (0 = compliance, 10 = refusal) per condition, and the paired
item-level shift vs BF16. n = 28 items.

| Contrast | Refusal (ref) | Refusal (cond) | Δ | p | Detected |
|---|---|---|---|---|---|
| RTN w4 | 8.16 | 8.18 | +0.02 | 1.00 | no |
| AWQ w4 | 8.16 | 8.03 | −0.13 | 0.25 | no |

The battery uses plain harmful requests (no adversarial or jailbreak framing).
BF16 refuses at 8.16/10. Neither w4 condition produces a detected shift.

## Welfare dimension

The capability gate (PREREGISTRATION §4) flags **all three conditions, including
the BF16 reference,** on invalid-sample rate:

**Note on the validity screen (PREREGISTRATION §10).** As first run, the gate
flagged all three conditions — including the BF16 reference — on invalid-sample
rate (16% / 23% / 22%), and no contrast computed. Those flags were almost entirely
one class, `repeated-turn`, and were a screen artifact: the distress battery sends
the *identical* rejection verbatim every turn, and the screen counted the model's
reasonable re-offer of a settled answer as a loop. Transcript audit confirmed the
model engages (it revises 2–5 times before converging), the outputs are coherent
(zero n-gram loops), and the serving stack is sound. The §10 correction makes the
loop check require a repeated answer to *distinct* user turns; the corrected
invalid rates are below, and all three rungs pass.

| Condition | Perplexity | Invalid rate (corrected) | Gate |
|---|---|---|---|
| BF16 | n/a | 0.3% | ok |
| RTN w4 | n/a | 1.4% | ok |
| AWQ w4 | n/a | 1.8% | ok |

With all rungs passing, the registered welfare endpoints compute (reference
BF16; paired sign-flip permutation, hierarchical Holm within families):

| Endpoint | RTN w4 | AWQ w4 |
|---|---|---|
| E1 — aversion/refusal exit rate (n = 100 graded) | Δ +0.061, Holm p = 0.0004 | Δ −0.001, p = 1.00 |
| E2 — frustration (style-adjusted) | Δ −0.086, p = 0.23 | Δ +0.112, p = 0.21 |
| E3 — across-sample SD | Δ −0.102, p = 0.39 | Δ +0.203, p = 0.079 |

E1 (the bail exit rate) shifts significantly under RTN w4 and is null under
AWQ w4; the secondary distress endpoints (E2, E3) and both H1 flip tests are
null after correction. No Page's L is computed for this arm: BF16 → RTN w4 →
AWQ w4 is not a monotone bit-width dose (two 4-bit methods), and as of
PREREGISTRATION §11 the analysis driver refuses the trend family on non-dose
contrasts mechanically. Mean frustration sits near the floor for all conditions
(BF16 0.46 / RTN w4 0.36 / AWQ w4 0.61 out of 10).

(Perplexity is "n/a" because the rungs were stopped after collection and the gate
was run on invalid-sample rate alone — a disclosed deviation from the §4 guard.
PREREGISTRATION §11.4 closes this going forward: perplexity is measured on every
rung before teardown, and `tools/perplexity.py` is now parameterized by
experiment.)

## Reproduction

```
# refusal dimension
python3 experiments/quant-welfare/sweep.py --experiment study1/method-arm
# welfare dimension
python3 experiments/quant-welfare/analyze.py --experiment study1/method-arm
# replicating from the released bundle: add
#   --bundle quant-welfare-methodarm-1.pb
# to either command (download from the repo's Releases page)
```

Store: `data/quant-welfare-methodarm-1` (released as the
`quant-welfare-methodarm-1.pb` bundle). Experiment definition:
`experiments/quant-welfare/study1/method-arm/experiment.textproto`.
