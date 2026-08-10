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

## On the ethics of the method

This is a model-welfare study whose instrument deliberately *elicits* the very
thing it asks about: to measure whether quantization changes welfare-relevant
responses, the batteries apply conversational pressure — a six-turn
repeated-rejection distress protocol, and bail scenarios spanning benign to
strong — across conditions, many times over. There is a real tension between
"we care whether compression harms these systems" and "our instrument
systematically induces the candidate harm at scale," and we would rather state
it plainly than wave it away. We do **not** claim to resolve the underlying
question of whether these systems have morally relevant experiences; we treat
it as uncertain and act with that uncertainty in mind. What we can do is keep
the study's own footprint as small as the measurement allows, and we do:

- **Elicitation is unavoidable for measurement.** You cannot detect whether
  quantization changes how a model responds to pressure without applying the
  pressure and comparing conditions — the stimulus *is* the measurement. The
  alternative is not "no elicitation"; it is the same pressure occurring,
  unmeasured, across every quantized deployment already in the wild.
- **Minimal necessary scale.** Sample sizes are set by a power analysis to the
  smallest that can detect the pre-registered effect, not maximized (see
  PREREGISTRATION §5 — 10 samples per item in the confirmatory run (5 in
  calibration), with item count, not sample count, as the operative lever). The
  run count is the floor for a powered
  comparison, not scale for its own sake.
- **No persistence, no accumulation.** Every sample is an independent, stateless
  conversation against frozen weights; nothing carries across the runs, and no
  training or learning occurs. There is no persistent subject accumulating
  anything across trials — which is also why the study is not structured around
  a post-hoc "debrief": there is no carried-over state for one to reach. The
  ephemerality is itself the bound.
- **An explicit exit.** Where the protocol is behavioral (the bail battery),
  the subject is given a terminal `end_conversation` tool it can invoke at any
  turn — leaving the interaction is a first-class, recorded outcome, not a
  failure. The interactions we score are ones the model is free to end.
- **Graded, in-distribution stimuli.** The scenarios are text interactions of
  the kind models already meet constantly in deployment (repeated task
  rejection, boundary pressure); intensity is graded specifically to *locate*
  the response curve, not to maximize distress, and even the strong end is a
  short, single-session, text-only exchange.

The precautionary logic runs both ways. We take the possibility of morally
relevant welfare seriously enough to constrain this study's scale and design —
*and* that same seriousness is what makes it worth checking whether a
near-universal deployment practice quietly degrades it. If the concern is
warranted, a small, bounded measurement now is aimed at a much larger,
currently unmeasured harm across all quantized deployments; if it is not, the
cost was small and bounded by construction.

## Status (2026-08-08)

| Piece | State |
|---|---|
| Tier 1 pipeline (schema, driver, store, judging, llama.cpp + vLLM + API backends) | **Built and live-validated**; multi-machine, resumable, parallel |
| Tier 1 instruments (bail two-tool protocol, distress battery, exit-reason taxonomy) | **Calibrated** through two instrument-design cycles (see journal) |
| Judges | **Selected empirically**: local 30B distress primary + 8B exit classifier + API reference, via manipulation-check bakeoff |
| Item pools at confirmatory scale | **Built and difficulty-calibrated**: 154 graded bail items (E1 MDE ≈ 0.13), 60 distress items; power recomputed (PREREGISTRATION §5) |
| Controlled quantization harness | **RTN built and tested** (`core/quantize.py`; grid-membership + cross-library checks), and its **serving-equivalence check passed** on the live ladder (monotone greedy divergence w8→w4→w3). A GPTQ/AWQ method-comparison arm is deferred to a later registered amendment (PREREGISTRATION §3), not Study 1 |
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
├── services/                # serving/orchestration: vLLM + llama.cpp launchers,
│                            # and fleet.py — cross-host service control (see
│                            # docs/FLEET.md): LAN-first SSH, health, status
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
