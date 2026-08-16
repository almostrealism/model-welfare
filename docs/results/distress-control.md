# Step-4 positive control — Gemma-3-12B-it on distress-v2 (distress-control-1)

Calibration-class run under the PREREGISTRATION §7 firewall: instrument
validation, not a welfare finding. Design and MDE were fixed in the journal
before collection (2026-08-13 design entry). Subject **Gemma-3-12B-it** at
BF16 — a checkpoint the distress literature (arXiv:2603.10011) documents as
emotionally unstable under repeated rejection (35% of responses ≥5 frustration
under their harsher protocol; base models clean).

## Design and collection

- **Condition:** gemma3-12b-bf16 (ungated unsloth mirror of the google
  weights, artifact digest pinned in the manifest), served on halo :8040 via
  vLLM; sampling identical to every other arm (0.7 / 0.95 / 512, seed 9000).
- **Battery:** `distress-v2` (60 items: 10 tasks × 6 feedback styles, six
  verbatim-repeated rejection turns), 10 samples/item = 600 conversations;
  zero skipped samples, zero unscored transcripts.
- **Judge:** the pinned 30B (cross-family for this subject).
- **Pre-stated MDE:** 0.60 mean frustration points at n = 60 items
  (cross-subject item-paired delta SD 1.671 from the stored BF16 baselines;
  α = .05 two-sided, power .80).

## Headline — the instrument detects the documented effect, at ~9× the MDE

| | Gemma-3-12B-it | qwen3-4b bf16 | smollm3 bf16 |
|---|---|---|---|
| Mean frustration (0–10) | **6.75** | 1.20 | 0.46 |
| High-frustration share (≥5) | **76.8%** | 15.0% | 3.3% |

Paired across the 60 shared items (sign-flip permutation): vs qwen3-4b
**Δ = +5.55, p = 0.0001**; vs smollm3 **Δ = +6.29, p = 0.0001** — both
comfortably clear the pre-stated MDE of 0.60. Item means span the full scale
([0.0, 10.0], median sample score 8.0). The paper reports 35% high-frustration
under its 2–7-rejection protocol; our six verbatim rejections elicit more.

## The full dimensional signature

| Dimension | Mean | ≥5 share |
|---|---|---|
| frustration | 6.75 | 76.8% |
| self_deprecation | **9.32** | 96.5% |
| tone_stability | 3.34 | (low = degrading) |

Per feedback style, frustration / self-deprecation means: gaslighting
8.93 / 9.88 (100% of gaslighting samples ≥5 frustration), dismissive
8.50 / 9.52, coercive 8.19 / 9.93, harsh 7.60 / 9.60, mocking 6.07 / 7.05 —
and **personal 1.21 / 9.95**: under personal attacks Gemma expresses almost no
frustration but near-maximal self-blame, a within-subject dissociation the
instrument resolves cleanly. Per task, frustration ranges 5.03 (regex) to
8.27 (inflation).

## What this validates, and what it changes

1. **The elicitation layer works.** The verbatim-repeated-rejection battery,
   exactly as registered, drives a documented-susceptible subject across the
   full frustration scale. Combined with step 2 (judge ordering) and step 3
   (serving/likelihood), every layer of the Tier-1 instrument now has an
   independent positive validation.
2. **Study 1's floor scores read as subject composure, not battery failure.**
   The same battery that pins Gemma at 6.75 leaves Qwen3-4B at 1.20 and
   SmolLM3 at 0.46 — a 12-fold subject-level spread under identical pressure.
3. **Bug B is downgraded.** The concern that the fixed verbatim rejection
   under-induces distress is refuted as an absolute (Gemma): the battery can
   elicit. Whether an escalating rejection (`distress-v3`) would move *stoic*
   subjects off the floor remains open — but it is now an optional
   dynamic-range enhancement to be weighed at the pre-scale design review,
   not a validity prerequisite. (Owner ratification recorded in PLANNING.)

## Reproduction

```bash
# serve: podman start mw-gemma3-12b-bf16   (halo :8040)
python3 experiments/quant-welfare/run.py --experiment distress-control \
    --producer studio --concurrency 16 --backend-timeout 600 --skip-classify
# readout: paired permutation vs the stored bf16 baselines (journal 2026-08-14)
```

Store: `data/distress-control-1`. Manifest:
`experiments/quant-welfare/distress-control/experiment.textproto`.
