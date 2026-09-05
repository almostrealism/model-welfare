# Program journal — cross-study entries

Opened 2026-09-05 per the journal-series scheme ([README](README.md)):
infrastructure, instrument findings that outlive a study, and
program-level policy. Append-only, newest first.

## 2026-09-05 — Fleet findings from the Study 3 workbench days

Recorded here because they concern the fleet, not one study's
registration (Study 3's journal carries a one-line pointer where its
gates depend on these).

**Halo environment drift since the Study 2 era** (all worked around,
none data-affecting; consistent with the CI-runner setup period):

- the `vllm-rocm:latest` image tag is gone; the containers' actual
  image survives as read-only `oci-registry.ryai.dev/ryai-vllm:latest`
  — launch with `MW_VLLM_IMAGE=` until retagged;
- the GPU pool reports **94.19 GiB**, and the ladder's per-rung
  default `MW_GPU_FRAC=0.18` no longer boots a single rung (negative
  KV headroom); single-rung use wants ~0.35, and concurrent
  vLLM + torch loads must be budgeted against the 94 GiB explicitly
  (a 12B torch load needs ~23 GiB free);
- rootless-podman port forwarding answers only on the LAN interface —
  `localhost` connections to published ports reset while the LAN
  address serves; halo's LAN address is currently 192.168.8.226 (the
  fleet config's 10.0.0.127 LAN-first entry is stale; the `amd-halo`
  hostname still resolves);
- the GitHub Actions runner idles harmlessly (no observed memory or
  performance interference across two heavy workbench days).

**The fused-attention capability map** (the finding behind Study 3's
arm-D trajectory): PyTorch's fast SDPA backends on ROCm come from
aotriton, which does not function on the workbench's RDNA-class iGPU
(gated off; force-enable crashes) — torch there falls back to unfused
math attention, ~14× slow at 12B. The gap is specific to the hookable
torch path: vLLM's own ROCm kernels are fine on the same silicon.
Apple silicon carries fused attention in both its stacks (torch-MPS
fused Metal path; MLX first-class): measured with the identical
steering code, Gemma-3-12B-it runs ~583 s/conversation on the
workbench vs **~197 s/conversation on the Studio (torch-MPS)**. Fleet
consequence: hookable big-model work routes to the Macs; the workbench
remains the quantization/vLLM host; cross-host substrate changes are
gated (Study 3's G4), with the 2026-08-22 cross-machine
outlier-channel finding as the known risk each such gate must measure.

**Operational conventions hardened this week:** long-running local
jobs go in detached tmux sessions (the harness reaps its own
background tasks; the August `v3pilot` session was the precedent);
remote jobs are `nohup`-detached and survive channel loss; `fleet exec`
passes a single argv (no shell interpretation) — use plain ssh for
compound remote commands.
