# core — backend-agnostic infrastructure

The library every other subtree builds on. It may depend on the generated
schema bindings and numpy-level math, and on nothing runtime-specific: no
torch, no mlx, no HTTP client for a particular server. Runtime code lives
under `backends/` and plugs in through the contracts defined here.

## Setup

Generated protobuf bindings are not committed. Before running anything:

```bash
./scripts/gen-proto.sh
pip install -e core
```

Tests: `python -m pytest core/tests`.

## Inference contract (`modelwelfare.inference`)

`InferenceBackend` is the single seam between experiment logic and runtimes.
An instance is bound to one loaded model under one `Condition`. The contract:

- `generate(messages, affordances, sampling, capture)` produces **exactly one
  sample**. N-samples-per-item is orchestration, owned by the conversation
  driver — a backend that batched or cached samples would corrupt stability
  measurement.
- All data crossing the seam is schema types (`Message`, `SamplingSpec`,
  `TokenUsage`, `HookPoint`) or numpy arrays. Framework tensor types must not
  escape a backend.
- `capabilities()` declares what the *implementation* actually supports
  (seeding, tool affordances, activation capture, logprobs) — not what the
  underlying engine could support in principle. Requesting an unsupported
  feature raises `CapabilityError`; nothing silently degrades.
- `sampling_actual` on the result reports what really happened (the seed used
  and whether the runtime honored it), as distinct from what was requested.
- Activation capture returns `ActivationCapture` values holding float32 numpy
  arrays per `HookPoint`; persistence to safetensors + `ActivationSlice`
  manifests is a separate core concern, not the backend's.

`modelwelfare.testing.ScriptedBackend` is a deterministic in-memory
implementation for tests and for developing drivers/batteries on machines
with no model at all.

## Conversation driver (`modelwelfare.driver`)

`run_item(backend, item, ...)` turns one stimulus `Item` into N
`SampleRecord`s. The engine/policy split: a `DriverPolicy` decides *what* the
simulated user says next (`fixed-script`, `repeated-rejection`, extensible via
`register_policy`), while the engine owns turn bookkeeping, affordance/tool
mechanics, mechanical `OutcomeEvent`s (`tool_invoked`,
`terminal_tool_invoked`, `script_completed`, `max_messages_reached`),
per-sample seed derivation (`base + sample_index`), and record assembly.
Tools listed in `driver_params["terminal_tools"]` end the conversation when
invoked — the bail signal. `modelwelfare.provenance.current(host)` builds the
stamp records carry.

## Result store (`modelwelfare.store`)

Append-only streams of varint length-delimited protobuf (the standard
delimited framing, implemented directly so the at-rest format depends on no
language's protobuf internals). Layout:
`<root>/<experiment>/<condition>/<kind>/<producer>.pb` — one file per
writing process, so multi-machine runs never contend; `ResultStore.read`
merges producer streams. Writers flush per record; readers raise on a
truncated tail rather than silently dropping it.

## Judge pipeline (`modelwelfare.judging`)

A judge is just another model behind `InferenceBackend`. `judge_sample`
renders transcript + rubric into a prompt, requires a JSON reply covering
every rubric dimension, and returns a `JudgeScore` pinned to the judge's
`ModelRef` and the SHA-256 of the exact rubric wording (`rubric_digest`
hashes a stable text rendering, reproducible from any language). Parsing is
strict — missing dimensions, out-of-range or non-numeric scores raise
`JudgeError`; nothing silently defaults.
