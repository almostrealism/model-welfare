# model-welfare

[![CI](https://github.com/almostrealism/model-welfare/actions/workflows/ci.yml/badge.svg)](https://github.com/almostrealism/model-welfare/actions/workflows/ci.yml)

**Does post-training quantization change welfare-relevant indicators in
open-weight language models?** Nearly every deployed open-weight model runs
at a precision it was never aligned at, and compression is audited almost
entirely through capability metrics — metrics known to stay flat while
fine-grained behavioral dispositions shift. This project measures what
compression does to a different class of indicators: distress expression
under conversational pressure, preferences to exit interactions, persona
stability, and the relationship between what a model expresses and what its
internal representations show.

Start here:

- **[PREREGISTRATION.md](PREREGISTRATION.md)** — the confirmatory study:
  hypotheses, design, analysis plan, and an explicit register of what is
  still open. Registered before confirmatory data collection.
- **[PROJECT_BRIEF.md](PROJECT_BRIEF.md)** — the internal orientation
  document: the full three-tier research frame, hardware, and annotated
  bibliography.
- **[docs/JOURNAL.md](docs/JOURNAL.md)** — the lab notebook: dated design
  decisions with their evidence, including instrument findings from the
  calibration phase.
- **[RESULTS.md](RESULTS.md)** — where results land. Currently holds
  calibration-class tables only (instrument validation, barred from
  supporting conclusions); confirmatory results will appear here.
- **[docs/PLANNING.md](docs/PLANNING.md)** — open workstream items.

## Status (2026-08-08)

| Piece | State |
|---|---|
| Tier 1 pipeline (schema, driver, store, judging, llama.cpp + vLLM + API backends) | **Built and live-validated**; multi-machine, resumable, parallel |
| Tier 1 instruments (bail two-tool protocol, distress battery, exit-reason taxonomy) | **Calibrated** through two instrument-design cycles (see journal) |
| Judges | **Selected empirically**: local 30B distress primary + 8B exit classifier + API reference, via manipulation-check bakeoff |
| Item pools at confirmatory scale | **Built and difficulty-calibrated**: 154 graded bail items (E1 MDE ≈ 0.13), 60 distress items; power recomputed (PREREGISTRATION §5) |
| Controlled quantization harness | **RTN built and tested** (`core/quantize.py`; grid-membership + cross-library checks); GPTQ/AWQ and the serving-equivalence check are not built — they gate the confirmatory run, not publication |
| Tier 2 (activation capture, directions, probes) | **Not started** — subject to the feasibility gate in the brief; hypothesis H5 is conditional on it |
| Tier 3 (dissociation analysis) | Depends on Tier 2 |

Research infrastructure is general: the schema, backends, driver, store,
and judging layers are experiment-agnostic, and the quantization study is
the first resident of `experiments/`.

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
├── core/                    # backend-agnostic library: measures, drivers, analysis,
│                            # RTN quantization (imports only proto code + numpy)
├── backends/                # runtime-specific implementations of core interfaces
│   ├── llamacpp/            #   client for llama.cpp GGUF servers (ecosystem arm)
│   ├── vllm/                #   client for vLLM servers (controlled-ladder arm)
│   ├── anthropic/           #   client for the Anthropic API (reference judge)
│   ├── torch/    (PLANNED)  #   transformers + forward-hook activation capture (Tier 2)
│   └── mlx/      (PLANNED)  #   Apple-silicon inference + array taps (Tier 2)
├── services/                # serving/orchestration scripts: vLLM + llama.cpp
│                            # launchers, cross-host control wrapper
├── experiments/             # one subtree per study
│   └── quant-welfare/       #   the quantization × welfare study: manifests, item
│                            #   batteries, rubrics, runner, analysis, bakeoff
├── scripts/                 # repo tooling, e.g. gen-proto.sh (protobuf codegen;
│                            # generated bindings are never committed)
└── docs/
```

Entries marked `(PLANNED)` do not exist yet — they name the Tier-2 work the
architecture is designed for. Everything else is present.

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
