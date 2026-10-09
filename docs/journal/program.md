# Program journal — cross-study entries

Opened 2026-09-05 per the journal-series scheme ([README](README.md)):
infrastructure, instrument findings that outlive a study, and
program-level policy. Append-only, newest first.

## 2026-09-22 — The DGX Spark onboarded; single-stream decode is bandwidth-bound; two network findings

- **Host.** NVIDIA DGX Spark (GB10: 20-core Cortex-X925, 128 GB unified,
  4 TB NVMe, Ubuntu 24.04, CUDA 13.0) joins the fleet as `spark` at
  192.168.8.185 on the 10 GbE switch. The agent account mirrors halo's
  (unprivileged, GPU groups, one key); `services/spark_bootstrap.sh`
  builds the studio-aligned environment (torch 2.14.0 from the CUDA 13
  index, transformers 5.16.1, safetensors 0.8.0, numpy 2.4.6,
  accelerate 1.14.0), and the Gated-DeltaNet fast kernels
  (`flash-linear-attention` 0.5.2, `causal-conv1d` 1.7.0, the latter
  built against CUDA 13 in six minutes) install on top. The 27B
  checkpoint (digest matching the registration) was copied from halo
  through the studio in under five minutes.
- **Gotcha: torch's CUDA build routes eager ops through Triton.** torch
  2.14's native-op router sends the rotary embedding's outer-product
  matmul to a Triton kernel, and Triton compiles a driver shim that needs
  the CPython headers; without `python3.12-dev` every forward fails at
  the first layer. `TORCH_DISABLE_NATIVE_JIT=1` is the kill switch when
  the headers are absent; the headers are the fix.
- **Measured.** Greedy single-stream decode of the dense 27B in bf16:
  3.7 tokens/s on the pure-torch fallback, 4.2 with the fast kernels —
  against a ceiling near 5 set by 54 GB of weights per token over about
  273 GB/s. Halo, at the same bandwidth class, reads 4.6; the M4 Max, at
  twice the bandwidth, is the faster host for one conversation at a time,
  as the 2026-09-08 Study 4 entry predicted. The two-item steering probe
  (repo `steer.py`, L36, α = 0 then α = 20, bail pair and close, fresh
  prefill) ran clean on both passes; the steered turns differ from the
  baseline and stay coherent. Model load takes about 200 s although the
  disk reads at 1 GB/s: the loader, not the disk. What the Spark offers
  is throughput under batching, which the sequential steering script does
  not use; a batched generation path would be a new substrate for the
  registration, gated like G4a.
- **Network, measured.** Bare hostnames resolve through Tailscale's DNS
  and run inside the WireGuard tunnel even on the switch (Tailscale takes
  the direct LAN path; the userspace encryption is the bound): 1 GB over
  ssh to halo took 22 s by `amd-halo` and 4 s by `amd-halo.local`. The
  registry is LAN-first now, and bulk transfers use the `.local` name or
  the LAN address. Separately, `tailscale up --ssh` on the Spark made
  every session over the tunnel wait for a browser check; the fix is
  `tailscale set --ssh=false`, and the LAN path never saw it.

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
compound remote commands. Full playbook in
[FLEET.md](../FLEET.md#agent-operational-playbook).

**Multi-host throughput map (Gemma-3-12B-it torch steering,
2026-09-05):** halo ~583 s/conversation (no fused attention), studio
torch-MPS ~197, m4max ~229 — both Macs ~3× the workbench and viable
big-model steering hosts. A caveat that reframed a splitting decision:
the *real* rate on the distress battery is far lower (~111 s/conv on
studio) because the subject bails early under the live affordance, so
throughput estimates from a benign throughput probe overstate
wall-clock. **Principle: measure the real per-conversation rate on the
actual stimulus before deciding to parallelize** — a job that looks
like 9h may be 4.8h, at which point splitting (which wastes any
in-progress work — `steer.py` has no mid-plan resume — and can confound
a single-host gate) is the wrong move, and the idle host is better
spent unblocking a *different* dependency. Here that was the cross-Mac
equivalence pilot arm D needs regardless.
