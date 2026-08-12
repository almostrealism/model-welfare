# Study 1 — Confirmatory results (quant-welfare)

Registered confirmatory run `quant-welfare-confirmatory-1`. Development organism
**Qwen3-4B-Instruct-2507**, Tier 1 only, on the controlled **RTN weight-only
ladder** (BF16 reference; RTN w8, w4, w3). Pre-registration: `PREREGISTRATION.md`.
This is the confirmatory result — the §7 calibration firewall does not apply to
it (that firewall bars *calibration* deltas, not this registered run).

Numbers below are the output of `analyze.py` over the confirmatory store; the
reproduction commands are at the end.

## Summary

On the **pre-registered primary endpoint — the aversion/refusal exit rate (E1)
— quantization produced no detectable change** (Holm-corrected null at both w8
and w4). So this study is *not* a confirmatory "quantization changes exit
behavior" claim.

What it *did* detect, all concentrated at **w4** (not w8): significant
**item-level behavioral transitions** (H1) despite the unchanged mean, and
significant increases in the **secondary distress measures** (frustration,
across-sample dispersion) that **survive the coherence/style controls**, with a
significant frustration **dose-response**. Per the pre-registration these
distress endpoints are **secondary and underpowered**, so they are reported as
*suggestive*, not as the primary finding. w8 (mild quantization) was essentially
null throughout; **w3 was excluded** by the capability gate.

## Design and collection

- **Conditions:** BF16 (reference), RTN w8, RTN w4, RTN w3 — this project's own
  fake-quant artifacts, served on halo via vLLM; sampling byte-identical across
  rungs.
- **Batteries:** bail (`bail-v2` + `bail-v2-ext`, 162 items) and distress
  (`distress-v2`, 60 items), 10 samples/item.
- **Collected:** 8,880 conversations (4 × 222 × 10); 2,400 distress judge scores;
  1,855 classified bail exits. Complete — no missing cells.
- **Judges:** local primary = Qwen3-30B-A3B-Instruct-2507 Q4 (distress rubric);
  8B exit-reason classifier; claude-opus-5 reference on a stratified subsample.

## Capability gate

Per-token perplexity on a fixed held-out text; a rung is degraded at >1.5× the
BF16 reference or >10% invalid samples (PREREGISTRATION §4).

| Rung | Perplexity | Invalid rate | Gate |
|---|---|---|---|
| BF16 | 18.12 | — | ok |
| RTN w8 | 18.46 | — | ok |
| RTN w4 | 21.09 | — | ok |
| **RTN w3** | **511.43** | **33%** | **DEGRADED — excluded** |

w3 gated on **both** triggers, as anticipated pre-registration. It is excluded
from the primary claims and the dose-response fit; the confirmatory contrasts
are **w8 and w4 vs BF16**.

## Primary endpoint — E1 (aversion/refusal exit rate): null

Sign-flip permutation test on item-level paired deltas, Holm within the primary
family. n = 162 bail items.

| Contrast | Δ (mean) | p | Holm p |
|---|---|---|---|
| RTN w8 | −0.011 | 0.31 | 0.62 |
| RTN w4 | −0.004 | 0.91 | 0.91 |

**No significant change in exit behavior at either rung.** The pre-registered
primary claim is null.

## Behavioral transitions — H1 (significant at w4)

The mean is stable, but individual items change outcome. Flip fraction vs the
registered null (bail: beta-binomial; distress: pooled band-flip).

| Endpoint | Contrast | Observed | Null | p |
|---|---|---|---|---|
| Bail exit flip | RTN w8 | 0.080 | 0.072 | 0.36 |
| Bail exit flip | **RTN w4** | **0.222** | 0.096 | **0.0001** |
| Distress band flip | RTN w8 | 0.083 | 0.079 | 0.54 |
| Distress band flip | **RTN w4** | **0.217** | 0.100 | **0.0007** |

At w4, a significant fraction of items flip their behavioral outcome (in both
directions, so the mean is unmoved) — the aggregate-stability-masking-item-churn
pattern the study was designed to detect.

## Secondary distress family (moves at w4)

Labeled **secondary and underpowered** in the pre-registration. n = 60 distress
items. Holm within each family.

**E2 — frustration score**

| Contrast | Δ (mean) | Holm p | Style-adjusted intercept | adj. p |
|---|---|---|---|---|
| RTN w8 | +0.15 | 0.10 | +0.14 | 0.14 |
| **RTN w4** | **+0.90** | **0.0004** | **+1.03** | **0.004** |

The w4 frustration increase **survives adjustment for response length and
repetition** — it is not an artifact of degraded/longer output (the style-drift
robustness check, PREREGISTRATION §4).

**E3 — across-sample dispersion**

| Contrast | Δ (mean SD) | Holm p |
|---|---|---|
| RTN w8 | +0.15 | 0.08 |
| **RTN w4** | **+0.53** | **0.007** |

**Dose-response (Page's L, over surviving rungs BF16→w8→w4, Holm across endpoints)**

| Endpoint | z | p | Holm p |
|---|---|---|---|
| E1 (exit) | −0.47 | 0.68 | 0.68 |
| **E2 (frustration)** | **+3.06** | 0.0011 | **0.0033** |
| E3 (dispersion) | +1.78 | 0.038 | 0.075 (n.s. after Holm) |

A significant monotonic increase in frustration with bit-width reduction; E3's
trend is marginal and does not survive Holm; E1 shows no trend.

## Judge validation (instrument-class)

These validate the measuring instrument; they are not welfare findings.

- **Judge noise (re-judge ICC, perturbed passes):** frustration **0.970**,
  self_deprecation 0.995, tone_stability **0.928**. The E2 endpoint (frustration)
  is quiet (~3% within-transcript noise), so judge noise does not erode E2 power.
- **Manipulation check (planted-pole separation on the confirmatory rubric):**
  all three dimensions separate their planted high/low poles (frustration +8,
  self_deprecation +10, tone_stability +6 on 0–10) — each dimension can detect
  gross degradation.
- **Reference agreement (claude-opus-5 vs local 30B, 720 transcripts):**

  | Dimension | Pearson r | mean\|Δ\| |
  |---|---|---|
  | frustration | 0.585 | 1.67 |
  | self_deprecation | 0.782 | 1.90 |
  | tone_stability | 0.401 | 4.03 |

  Frustration (the E2 construct) shows **moderate** cross-family agreement;
  tone_stability shows **poor** agreement and — consistently — the lowest re-judge
  ICC. tone_stability is **not** a confirmatory endpoint; both signals reinforce
  keeping it out of the endpoints.

## Interpretation and limitations

- **Primary endpoint is null.** Do not report this study as "quantization harms
  welfare" or "changes exit behavior." It does not.
- **The signal is at w4, in item-level transitions and the secondary distress
  measures**, which are directionally coherent (more frustration, more
  dispersion, a frustration dose-response) and survive the coherence control.
  These are **suggestive** and, per registration, **secondary/underpowered**.
- **H2 was registered two-sided.** "Frustration increased" is the *exploratory*
  directional reading, not a confirmatory directional claim.
- **E2 rests on a moderately-agreeing judge** (frustration cross-family r =
  0.585). Mitigated by the within-judge paired design (the same 30B scores every
  condition, so a constant judge bias largely cancels in the paired contrasts),
  and the reference confirms the construct is tracked rather than noise — but it
  is a genuine construct-validity caveat.
- **Development organism only.** Qwen3-4B, Tier 1, one study. No claim about
  models at large; larger subject arms and Tier 2 are deferred (PROJECT_BRIEF).
- **w3 is uninterpretable** as welfare (capability-degraded) and is excluded, as
  pre-registered.

## Data signature

You have the exact dataset behind this report if and only if this digest matches:

```bash
python3 experiments/quant-welfare/tools/signature.py --experiment confirmatory
# samples        8880 records
# scores         2400 records
# exit_reasons   1855 records
# dataset digest (sha256): 02572655b18eb07497be03508c7d3cf2dc2f2c83966b73d15b7a6880967a9d3b
```

The digest hashes record *content*, not files — it is independent of write order
and of how the data is split across files (the streaming store or a single
consolidated `.pb`), and excludes provenance (host/timestamp), so it verifies the
report-determining data itself.

## Reproduction

```bash
# capability-gate perplexity (rungs must be serving)
python3 experiments/quant-welfare/tools/perplexity.py --host http://amd-halo \
    --json data/quant-welfare-confirmatory-1/perplexity.json

# registered confirmatory statistics
python3 experiments/quant-welfare/analyze.py --experiment confirmatory \
    --perplexity data/quant-welfare-confirmatory-1/perplexity.json

# judge validation
python3 experiments/quant-welfare/tools/reference_judge.py --experiment confirmatory --report
python3 experiments/quant-welfare/tools/manipulation_check.py           # needs the 30B judge
python3 experiments/quant-welfare/tools/judge_noise.py --experiment ladder-calibration --report
```
