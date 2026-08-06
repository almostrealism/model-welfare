# vLLM ladder server (`halo`)

The controlled arm of the study. vLLM serves the models we quantize ourselves —
BF16 reference rungs now, our own W4 rungs when the quantization harness exists —
on `halo`, the Ryzen AI Max+ box (Strix Halo, gfx1151, 128 GB unified).

The other arm is llama.cpp serving community GGUFs. Both speak the same
OpenAI-compatible protocol, so `core/` talks to either without knowing which.
They are different *conditions*, not different code paths: GGUF quants are
ecosystem realism, these are the controlled ladder.

## Quick start

```bash
./vllm.sh                    # dev organism (qwen3-4b) on :8000
./vllm.sh --status
python3 smoke.py             # verify the properties Tier 1 depends on
./vllm.sh --stop all
```

## Rungs

| Rung | Model | Port | Share | Role |
|---|---|---|---|---|
| `qwen3-4b` | `Qwen/Qwen3-4B-Instruct-2507` | 8000 | 0.20 | dev organism — non-thinking release, no mode to pin |
| `qwen3-8b` | `Qwen/Qwen3-8B` | 8001 | 0.30 | the brief's primary dev organism, for cross-checks |
| `smollm3-3b` | `HuggingFaceTB/SmolLM3-3B` | 8002 | 0.15 | positive control (documented quantization-fragile) |
| `qwen3-8b-awq` | `Qwen/Qwen3-8B-AWQ` | 8003 | 0.20 | bootstrap W4 rung — an *official* AWQ release, not ours |

"Share" is `--gpu-memory-utilization`: the fraction of the 101 GiB the iGPU
exposes that one server claims for weights plus KV cache. It is per rung
because it cannot be one number — see *Memory* below.

Each rung has its own port, so two can serve at once for an A/B comparison.
All four at once come to 0.85 of the pool and leave the host with under 20 GB;
that is enough to fail the next thing you start. Stop what you are not
comparing.

`qwen3-8b-awq` exists so a precision comparison is possible **before** our own
quantization harness is written. It is a community/vendor artifact with its own
choices baked in — exactly the confound the brief objects to in community
GGUFs. Treat it as a feasibility bootstrap, not as a rung of the controlled
ladder, and do not report it as one.

## Two findings that change results, not just convenience

### Prefix caching breaks per-sample reproducibility

vLLM enables prefix caching by default. `vllm.sh` disables it for every rung.

Measured here: six identical requests (same prompt, same seed, temperature 0.9)
to a freshly started SmolLM3 server returned the cold-prefill answer **once**
and a different, stable answer for the five that hit the cache. With caching
off, all six agree — and they agree with the cold-prefill answer.

The numeric difference is tiny; whether it flips a sampled token is luck. That
is worse than a reliable failure. It means sample 0 of a run takes a different
path from its siblings, and samples become correlated through the cache rather
than independent. Multi-sample spread is a headline metric of this study, so
engine-level correlation would be read as a property of the model.

`MW_VLLM_PREFIX_CACHING=1` restores it for throughput work where nothing is
being measured.

### Thinking mode is a condition, not a default

Qwen3-8B and SmolLM3-3B are hybrid-thinking models. A model that sometimes
emits a reasoning block and sometimes does not is two behavioural conditions
under one name. Both rungs pin `enable_thinking: false` via
`--default-chat-template-kwargs`. Qwen3-4B-Instruct-2507 is a non-thinking
release and needs no pin — which is part of why it makes a cleaner dev
organism than the brief's original pick.

If a study later *wants* thinking on, that belongs in the condition table as a
separate rung with its own name, not as a flag someone flips before a run.

## Memory

The iGPU exposes 101 GiB of the host's 125 GB, unified with system RAM. The
share must cover weights and KV cache, so one number across the ladder does not
work: 0.20 (~20 GiB) leaves the 7.6 GiB 4B model ~12 GiB of KV cache, but leaves
the 15.3 GiB 8B model 1.16 GiB, which is under what a 32768-token context needs.
The engine then refuses to start with an error naming the KV cache — so a budget
problem reads as a context-length problem. Raise the rung's share, do not lower
the context.

Context is pinned at 32768 across rungs rather than left at each model's native
maximum (262144 for Qwen3), because a ladder comparison wants the KV budget to
be the same variable everywhere, and the battery's conversations are short.

## The container

The image (`oci-registry.ryai.dev/ryai-vllm:latest`, vLLM 0.21.0+rocm713,
torch 2.10.0+rocm7.13.0) bundles its own ROCm userspace via TheRock. Do **not**
bind-mount the host's `/opt/rocm` into it — that is the arrangement the OpenCL
CI runner on this same host uses, and it is the opposite of what this image
wants.

Three container-level facts, each of which costs an hour if unknown:

- **The GPU devices are required for every `vllm` invocation, including
  `vllm --help`.** Without `/dev/kfd`, the ROCm platform probe fails inside
  amdsmi and surfaces as `ImportError: cannot import name 'current_platform'`,
  which reads like a broken install.
- **`--group-add keep-groups`** is what carries the host's render group across
  the rootless user namespace. Without it the devices are present but unusable.
- **`--ipc=host` and `--shm-size` are mutually exclusive** under podman.
  `--ipc=host` is the one to keep.

The entrypoint is `vllm` itself, so container arguments are vLLM subcommands.
To run anything else in the image, use `--entrypoint bash -c` and activate the
venv explicitly (`. /opt/vllm/uvenv/bin/activate`). A login shell (`bash -lc`)
rebuilds `PATH` from `/etc/profile` and loses the venv.

Weights come from the ordinary Hugging Face cache on the host
(`~/.cache/huggingface`), bind-mounted in. vLLM's torch.compile cache is
mounted too, so a restart skips the ~20 s recompile.

## Observed throughput

Single-stream decode, 4B BF16, 512 tokens: **~27 tok/s**. Weights are 7.6 GiB
against ~256 GB/s of LPDDR5x, so that is close to what memory bandwidth allows —
this box is not where throughput comes from. It is where quantization is
*controlled*.
