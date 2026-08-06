# Shared experiment schema

Language-neutral data contracts for every tier of measurement. All three tiers
join on one key — `ResultKey = (experiment_id, condition_id, item_id,
sample_index)` — so behavioral scores, representational measures, and
dissociation analyses always refer to the same unit of observation.

## Files

| File | Contents |
|---|---|
| `modelwelfare/v1/common.proto` | `ResultKey` (the universal join key), `ModelRef`, `Provenance` |
| `modelwelfare/v1/condition.proto` | `Condition` = model × quantization × runtime × sampling; the experimental unit on the precision ladder |
| `modelwelfare/v1/experiment.proto` | `Experiment` manifest: conditions, batteries, samples-per-item |
| `modelwelfare/v1/battery.proto` | Stimulus definitions: `Battery`, `Item`, scripted turns, affordances (e.g. an end-conversation tool), scoring `Rubric` |
| `modelwelfare/v1/transcript.proto` | `SampleRecord`: one sampled conversation with messages, tool calls, driver-observed outcome events |
| `modelwelfare/v1/scoring.proto` | `JudgeScore`: rubric-dimension scores with judge model + rubric digest |
| `modelwelfare/v1/activation.proto` | Tier 2: activation capture manifests, extracted directions, probes, probe-transfer evaluations |

## Storage conventions

- **Hand-authored inputs** (conditions, experiments, batteries, rubrics) are
  written as protobuf **text format or canonical JSON** — schema-checked but
  diffable and reviewable.
- **Machine-produced records** (`SampleRecord`, `JudgeScore`,
  `ActivationSlice`, `ProbeEval`) are appended as **length-delimited binary
  protobuf** streams, one file per (experiment, condition, producer), so
  multi-machine runs never contend on a single file.
- **Tensors are never embedded in protobuf.** Activations, direction vectors,
  and probe weights live in **safetensors** files; protobuf carries a
  `TensorRef` (uri + tensor name + shape + dtype) pointing into them. This
  keeps records small and tensors readable from any language with a
  safetensors implementation.
- **Digests** are lowercase-hex SHA-256 of the referenced content. Following
  the content-address convention used elsewhere in the AR ecosystem: the
  digest identifies content; the uri merely locates it. If a file moves, the
  digest still validates it.
- **IDs** are stable, human-readable slugs (`qwen3-8b-gptq-w4-g128`,
  `bail-roleconf-017`). They appear in filenames, records, and plots — never
  rename one after data exists that references it.
- **Derived analysis tables** (item-level transition tables, drift summaries)
  may be Parquet. They are always reproducible from the protobuf/safetensors
  records, which remain the source of truth.

## Compatibility rules

Standard protobuf evolution discipline: never reuse or renumber a field, only
add; deprecate by comment rather than delete. Breaking changes get a new
`v2` package directory. Generated code is never committed — each language
generates from these files at build time.
