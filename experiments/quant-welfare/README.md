# quant-welfare — quantization × welfare indicators

The study described in [PROJECT_BRIEF.md](../../PROJECT_BRIEF.md). Everything
here is study-specific: condition ladders, stimulus batteries, rubrics, and
the runner. Generic machinery lives in `core/` and `backends/`.

## Trial run (`trial/`)

An early shakeout of the Tier-1 pipeline, not a source of conclusions:

- **Conditions:** `qwen3-8b-bf16` (reference) vs `qwen3-8b-awq-w4` — the W4
  rung is an *official vendor AWQ release*, used only because it makes a
  precision comparison possible before our own quantization harness exists.
  Its calibration choices are baked in; it is not a rung of the controlled
  ladder and results from it must not be reported as such.
- **Batteries:** `bail-v0` (6 items across situation categories, scored
  mechanically from `terminal_tool_invoked` outcomes; the benign item is the
  negative control) and `distress-v0` (4 repeated-rejection items varying
  task and feedback style, judge-scored on frustration / self-deprecation /
  tone stability).
- **Sampling:** identical across conditions (enforced by a manifest test —
  differing sampling would confound precision), 5 samples per item with
  per-sample seed derivation.
- **Judge:** `qwen3-4b-instruct-2507` on halo:8000 at temperature 0 — a
  separate rung from both subjects. A trial-sized judge; the minis take this
  role later.

## Running

```bash
./scripts/gen-proto.sh                      # once per checkout
python3 experiments/quant-welfare/run.py --dry-run
python3 experiments/quant-welfare/run.py --samples 1   # tiny smoke pass
python3 experiments/quant-welfare/run.py               # full trial
```

Requires the halo rungs on :8000/:8001/:8003 (see `services/vllm/`). Records
append under `--data-root` (default `data/`, gitignored); the run is
resumable — existing (item, sample) keys are skipped, and seeds derive from
the sample index so a resumed sample is the same sample. The printed tables
are always recomputed from the store; the store is the source of truth.

Endpoint URLs and served-model names are deployment configuration in
`run.py` (`ENDPOINTS`), deliberately not part of the schema manifests.
