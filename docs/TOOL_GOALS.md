# Tooling surface goals — PyTorch and multi-machine

Working inventory of the engineering surfaces the remainder of the program
should exercise, recorded 2026-08-16 at the Study 1 → Study 2 pivot. Two
project-level goals sit alongside the scientific ones: the final state of the
repository should demonstrate (1) substantial, load-bearing **PyTorch** work
and (2) experiment setups that **require multiple machines operating
together**. This document lists the candidate surfaces for each, their current
status, and where the [calendar](CALENDAR.md) picks them up. It is a planning
inventory, not a commitment device — registrations commit; this document
orients.

The guiding principle: every surface listed here must be **confirmatory-path
or validation-path** — code the registered analyses actually depend on — not
decoration added to exhibit a technology.

## PyTorch surfaces

| Surface | What it is | Status | Planned home |
|---|---|---|---|
| **Activation capture module** | Forward hooks over configurable layers of transformers models, streaming per-(condition, item, sample, turn) records into the existing store/bundle schema. Works identically across BF16 and fake-quant checkpoints. | **Built** (2026-08-17): `backends/torch/.../capture.py` — forward hooks, per-assistant-turn pooling, safetensors + manifest; produced every calibration capture; G1-gated | Study 2, capture substrate (calendar wk 1–2) |
| **Contrastive direction extraction** | Persona-vector recipe: paired prompt batches → mean residual-stream activation difference → frozen unit direction. Includes the assistant-axis variant. Validated by reproducing the published projection-predicts-expression correlation on Qwen at BF16. | **Built** (2026-08-17): `core/.../directions.py` + `tools/extract_directions.py`; three directions frozen 2026-08-18, 13/13 held-out pairs sign-consistent, weekly stability CI | Study 2 calibration phase (wk 2) |
| **Linear probe suite** | Probes trained in torch at reference precision (real training loop: minibatching, optimizer, held-out early stopping), transfer-evaluated on each quantized rung's activations. Probe-transfer degradation is a registered Study 2 endpoint, so this is confirmatory-path torch. | **Built** (2026-08-17): `backends/torch/.../train_probe.py` (Adam, minibatched, val-AUROC early stop); exit + distress probes frozen 2026-08-18, control family added at the 2026-08-21 freeze amendment | Study 2 (wk 2–3) |
| **Steering validation** | Causal check of extracted directions: write-path hooks add ±α·direction during generation; judge-scored expression must move in the predicted direction. Upgrades "we found a direction" to "the direction is causally implicated." | Not started | Study 3 validation layer (wk 4) |
| **First-party GPTQ** | Hessian-based quantization (blocked Cholesky updates) mirroring the RTN/AWQ harness, completing the deferred method-comparison arm with a third first-party artifact. Heaviest torch numerics on the list. | Not started; AWQ + RTN harnesses exist | Optional method-arm slot (wk 6 buffer) |
| **On-the-fly fake-quant modules** | Quantized forward via torch modules instead of pre-written checkpoints, enabling per-layer ablations (which layers' quantization drives an observed shift). | Not started | Stretch; only if a Study 2/3 finding motivates the ablation |

## Multi-machine surfaces

| Surface | What it is | Status | Planned home |
|---|---|---|---|
| **Role-split pipeline** | halo (ROCm torch) as hooked capture/generation host; studio llama.cpp services as judge/classifier tier; orchestrator machine drives runs and pulls results into the central store. | In use since Study 1 (generation on halo, judges on studio :8095/:8092, orchestration from the Mac) | All studies; Tier 2 makes it structurally necessary (activations too large, capture host saturated) |
| **Concurrent per-condition collection across hosts** | Different conditions of one experiment collected simultaneously on different machines (e.g., halo captures w4/w3 while the M4 Max captures BF16/w8), merged through the per-producer streaming store with the content-based digest proving losslessness. | Store supports per-producer streams and digest-verified merge; Study 2 pipelined generation (halo) with judging (studio) across hosts, and measured cross-machine capture agreement (2026-08-22: spans exact, vectors outside the same-host band) — confirmatory capture stays halo-only, with the item-split design reserved for the larger arms | Study 2 (exercised as pipeline + measurement); essential at 30B scale (wk 5–6) |
| **Cross-framework agreement check** | The same condition captured on two machines with two frameworks (torch hooks on halo vs MLX array taps on a Mac); registered as a capture-path-invariance instrument validation. The clearest "two machines, two stacks, one result" artifact available. | **Resolved out of Study 2** (2026-08-18 freeze; REGISTRATION §6 item 3): never gating, not exercised; MLX capture remains a program-level goal for the larger-subject arms | Larger-subject arms (was: Study 2 validation layer, non-gating) |
| **Big-model split serving** | MiniMax-M2-class subject on the Studio (MLX / llama.cpp) while judges, orchestration, and analysis run elsewhere — no single machine can hold subject + judges. | Not started | MiniMax studies (wk 7–9) |
| **Rented reference precision** | Short 8×H100-class rental for MiniMax BF16 reference activations; local Q8 as working reference, rental only to validate Q8 ≈ BF16 on our measures. | Deferred by design | MiniMax Tier-2 week (wk 8), budget-permitting; divergence is itself a result |

## Explicitly not pursued for their own sake

`torch.distributed` / RPC-style tensor parallelism is out of scope: no subject
in the program needs it (the 4B fits everywhere; the MoE big model is served
by a single Studio), and adding it would be technology exhibition rather than
experiment support. The honest multi-machine story here is pipeline
parallelism across heterogeneous hosts plus concurrent condition collection —
which the experiments genuinely require.
