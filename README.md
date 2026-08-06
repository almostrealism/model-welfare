# model-welfare

Research infrastructure for systematic behavioral and representational studies of
language models. The first study hosted here examines whether post-training
quantization shifts welfare-relevant indicators — see [PROJECT_BRIEF.md](PROJECT_BRIEF.md).

## Design principles

1. **Math first, tools second.** The repository is organized around the
   quantities being computed (directions, projections, drift statistics, probe
   transfer, item-level transitions), not around the API of any one framework.
   PyTorch is the current implementation vehicle for representational work, but
   nothing outside `backends/` may depend on it. Someone with the relevant ML
   background should be able to retarget the repo to a different stack by
   replacing `backends/` subtrees only.

2. **No language-specific persistence.** Everything at rest is readable without
   a Python interpreter. Records and configuration use protobuf (schemas in
   `proto/`); tensors use safetensors; derived analysis tables may use Parquet.
   Pickle (and any format whose spec is "whatever this library version wrote")
   is prohibited.

3. **Multiple experiments, one infrastructure.** Generic machinery — the data
   contracts, inference backends, measurement code, services — lives at top
   level. Anything specific to a single study (its conditions, stimulus items,
   rubrics, analysis) lives under `experiments/<study>/`. Nothing generic may
   import from `experiments/`.

4. **Hardware placement is explicit.** Work runs across several machines with
   different runtimes. Code that only functions on a particular runtime is
   segregated by directory, and every stored record carries the logical host
   name that produced it (see host registry below).

## Layout

```
model-welfare/
├── PROJECT_BRIEF.md         # scientific orientation for the current study
├── proto/                   # THE SHARED SCHEMA — language-neutral data contracts
│   └── modelwelfare/v1/     # (see proto/README.md for storage conventions)
├── core/                    # backend-agnostic library: measures, drivers, analysis
│                            # (may import: proto-generated code, numpy-level math)
├── backends/                # runtime-specific implementations of core interfaces
│   ├── torch/               #   transformers + GPTQ/AWQ/HQQ/bitsandbytes; forward
│   │                        #   hooks for activation capture (Ryzen "halo", ROCm/CPU)
│   ├── mlx/                 #   Apple-silicon inference, quantization, array taps
│   │                        #   (Mac Studio, MacBook Pro)
│   └── llamacpp/            #   client for llama.cpp GGUF servers — Tier 1 only,
│                            #   tokens not tensors; no activation capture possible
├── services/                # long-running roles pinned to machines: judge workers,
│                            # experiment queue, result store (Mac minis)
├── experiments/             # one subtree per study
│   └── quant-welfare/       #   the quantization × welfare study: condition ladder,
│                            #   item batteries, rubrics, analysis
├── scripts/                 # repo tooling, e.g. gen-proto.sh (protobuf codegen;
│                            # generated bindings are never committed)
└── docs/
```

Directories are created as their first real content lands; this tree is the
committed plan.

## Host registry

Logical names used in `RuntimeSpec.host` and in service placement. Keep this
table in sync with reality — records are joined and audited by these names.

| Logical name | Machine | Runtimes | Role |
|---|---|---|---|
| `studio-m1u` | Mac Studio, M1 Ultra, 192 GB | llama.cpp, MLX | primary big-model host |
| `halo` | Ryzen AI Max+, 128 GB | PyTorch (ROCm/CPU) | quantization workbench, hookable inference |
| `mbp-m4max` | MacBook Pro M4 Max, 128 GB | MLX, llama.cpp | development, dev-organism work |
| `mini-1`..`mini-3` | Mac mini M4, 16 GB | llama.cpp, MLX | judges, queue, result store, smoke tests |
| `rented-*` | cloud GPU (as needed) | PyTorch (CUDA) | full-precision reference runs |
