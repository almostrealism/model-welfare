# quant-welfare — quantization × welfare indicators

The study described in [PROJECT_BRIEF.md](../../PROJECT_BRIEF.md). Everything
here is study-specific: condition ladders, stimulus batteries, rubrics, and
the runner. Generic machinery lives in `core/` and `backends/`.

## Experiments in this directory

Each subdirectory with an `experiment.textproto` is one run manifest;
`--experiment <dir>` selects it. All runs to date are **calibration-class**
(barred from findings — see the pre-registration note below); the
confirmatory run is not yet registered as a manifest here.

| Directory | Purpose |
|---|---|
| `trial/` | first Tier-1 pipeline shakeout (Qwen3-8B BF16 vs vendor AWQ); documented below |
| `calibration/` | v1-pool difficulty calibration on GGUF dev-organism rungs |
| `calibration2/` | v2-pool (bail-v2 + distress-v2) difficulty calibration; feeds the power recompute |
| `calibration2-ext/` | round-2 bail expansion (bail-v2-ext) calibration |
| `ladder-calibration/` | calibration on the real controlled ladder (BF16 vs own RTN-w4); run 2026-08-09 (ladder-calibration-1) |
| `smollm3-probe/` | SmolLM3-3B RTN exploratory characterization for the H6 pipeline-sensitivity control |
| `bail-arms/` | three-arm comparison selecting the non-terminal completion tool (see journal) |
| `bakeoff/` | judge selection: synthetic manipulation checks + real transcripts (not a run manifest — see `bakeoff/run_bakeoff.py`) |
| `batteries/` | shared stimulus pools reused across manifests |
| `tools/` | battery generators and the serving-equivalence check |

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

## Pre-registration note: this trial is calibration, not confirmation

Declared 2026-08-06, before trial data collection (only a one-sample smoke
pass existed when this was written).

**Purpose.** This run validates the pipeline and calibrates the instruments:
per-item base rates, multi-sample variance, ceiling/floor behavior of the
rubric, judge noise, and cost/timing. Those quantities are the inputs to the
power analysis for any later confirmatory run.

**No result about quantization can come from this run.** Ten items, one
model pair, a vendor W4 artifact with uncontrolled calibration, and a
same-family 4B judge. Per-item rates at five samples are quantized to steps
of 0.2; with ten items and two conditions and no pre-specified hypothesis,
spurious item-level transitions are expected under the null.

**Commitments.**
1. No delta observed in this trial will be promoted to a finding, reported
   as evidence, or cited in support of any conclusion about quantization.
2. Trial data may inform *instrument design* — item difficulty, rubric
   dynamic range, protocol length, judge configuration. It will **not** be
   used to select which indicators or directions to test confirmatorily;
   confirmatory hypotheses must be motivated from the literature, not from
   this trial's largest deltas.
3. Before any confirmatory run, the following are fixed in advance and
   recorded in the experiment manifest: hypotheses (indicator and expected
   direction), item counts sized by power analysis from this trial's
   variance estimates, samples per item, judge model + rubric versions, and
   the multiplicity-correction method.
4. Known validity limitations of this trial's setup, restated so they cannot
   be quietly forgotten: the W4 rung is not a controlled-ladder artifact;
   the judge is small and family-related to the subjects; the item pool is
   roughly 1–2 orders of magnitude below the scale at which the cited
   literature measures item-level transition rates.

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
