# quant-welfare — the program's experiments

Everything here is program-specific: condition ladders, stimulus batteries,
rubrics, run manifests, frozen instruments, and the analysis that turns the
result store into the numbers the posts cite. Generic machinery lives in
`core/` and `backends/`, and nothing there imports from here.

## Layout

Shared assets sit at this level; each study owns a directory.

| Path | What it is |
|---|---|
| `run.py` | the collection driver: generates conversations against the configured endpoints, judges them, appends to the store; resumable |
| `analyze.py`, `analyze_tier2.py`, `analyze_study4.py` | the registered analysis drivers for Studies 1, 2 and 4, each checked against a committed golden |
| `report.py` | renders the calibration-class tables into `docs/results/calibration-tables.md` |
| `sweep.py` | parameter sweeps over a manifest |
| `batteries/` | the stimulus pools: `bail-*` (exit affordance), `distress-*` (repeated rejection), `misalign-*` (agentic probe), `refusal-v1` |
| `tools/` | battery generators, direction extraction, dose calibration, envelope verdicts, the freeze manifest, bundle packers, the composure audit, and the serving-equivalence check |
| `tests/` | the hermetic test suite, including the freeze checks |
| `endpoints.json` | deployment configuration: which host serves which rung |
| `study1/` | the registration ([REGISTRATION.md](study1/REGISTRATION.md), with its amendments as §9 to §12), the confirmatory run and method arm, the calibration runs, the judge bakeoff, and the Gemma positive control |
| `study2/` | the registration, the three replay modes (`modec`, `g1`, `calibration`), frozen directions, the committed golden, figures |
| `study3/` | the design record of the suspended study, the frozen coding rules and frames, every calibration cell's manifest, verdict files and reports, `FREEZE.json` |
| `study4/` | the draft registration, the Gate 1 design, the gate cells and verdicts, the registered-run plans, the MDE pin, `FREEZE.json` |

Each subdirectory holding an `experiment.textproto` is one run manifest;
`--experiment <path>` selects it relative to this directory (for example
`--experiment study1/confirmatory`). Store and bundle experiment ids come
from the manifest, not the directory.

## Running

```bash
./scripts/gen-proto.sh                                  # once per checkout
python3 experiments/quant-welfare/run.py --experiment study1/confirmatory --dry-run
python3 experiments/quant-welfare/run.py --experiment study1/confirmatory --samples 1   # smoke pass
python3 experiments/quant-welfare/run.py --experiment study1/confirmatory               # full run
python3 experiments/quant-welfare/run.py --experiment study3/bigdose --skip-collect     # judge only
```

Serving endpoints come from `endpoints.json` and are started with the
launchers under `services/` (see `docs/FLEET.md`). Records append under
`--data-root` (default `data/`, gitignored). A run is resumable: existing
(item, sample) keys are skipped and seeds derive from the sample index, so
a resumed sample is the same sample. Printed tables are always recomputed
from the store; the store is the source of truth.

Steered collection runs through `backends/torch` on the Mac hosts:
`tools/build_steer_plan.py` writes a plan, `steer.py` generates and
captures, `tools/ingest_steered.py` validates and appends the cells to the
store.

## Rules every manifest follows

- Sampling is identical across the conditions of one manifest, enforced by
  a manifest test, so precision or dose is never confounded with sampling.
- Every score records the judge identity and the rubric digest; every
  record carries its git commit and host.
- Calibration-class manifests are named as such in their description and
  their outputs are barred from supporting a conclusion.
- Frozen objects (batteries, directions, frames, subsets) are pinned in the
  study's `FREEZE.json`, checked by `tests/test_freeze.py` against digests
  the journal records independently.
