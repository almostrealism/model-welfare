# Calibration-stability CI — design sketch

Goal (PLANNING, opened 2026-08-18): CI jobs that re-perform the completed
calibrations against committed/released artifacts, so "the instrument is
stable" is a continuously re-proven claim rather than a one-time journal
entry. This document is the design sketch: the job catalog, hardware
requirements, and the runner-assignment rule.

## The assignment rule

Split exactly along **"does the job execute a model?"**:

- **No model execution** → GitHub-hosted *standard* runners. The repo is
  public, and standard runners are free for public repos with no minute
  cap — the cost concern only applies to the larger paid sizes, which
  nothing in this tier needs (everything fits comfortably in the default
  4-vCPU / 16 GB / 14 GB-disk shape). Zero maintenance, zero LAN exposure.
- **Model execution** (torch capture, vLLM serving, llama.cpp judging) →
  self-hosted org runners on our hardware, **schedule + manual dispatch
  only**. These jobs are minutes-per-week; the fleet's job is correctness
  probing, not throughput.

**Security posture (corrected 2026-08-18):** fork-PR workflows are gated by
the repository's Actions approval setting ("require approval for running
workflows from contributors"), so PR-triggered validation — including on
self-hosted runners — is acceptable: a fork's workflow does not run until a
maintainer approves that run. Defense-in-depth still applies to the
self-hosted tier: runners in a repo-restricted group as an unprivileged
user, and the *heavyweight* model jobs stay on `schedule`/
`workflow_dispatch` anyway for operational reasons (runtime, and the
experiment-collision guard below), not security ones.

**The "All Checks" aggregator:** branch protection requires exactly one
status check — the `All Checks` job in `ci.yml`, which `needs:` every other
job, runs `if: always()`, and fails iff any needed job ended in a state
other than `success` or `skipped`. Treating `skipped` as acceptable is
deliberate: it lets jobs skip legitimately (path filters, missing
prerequisites) without wedging merges, which per-job required checks
cannot do. Every new job added to `ci.yml` must be added to the
aggregator's `needs:` list — a job outside that list is invisible to
branch protection.

## Tier 1 — hermetic re-performance (GitHub-hosted, free)

| Job | What it re-proves | Inputs | Est. runtime |
|---|---|---|---|
| `frozen-digests` | Every frozen object still hashes to its journal-pinned value | repo files + a committed `FREEZE.json` manifest (new: object → sha256, the machine-readable freeze record) | seconds — cheap enough to run per-PR in the main suite |
| `directions-stable` | Extraction code re-derives the frozen directions from the fixture capture: cosine ≥ 0.9999 to the committed vectors, held-out separations reproduced | fixture-battery capture published as a pinned release asset (~20 MB; currently only on scratch/halo — publishing it is a prerequisite) | ~1 min |
| `study1-results-reproduce` | `analyze.py` over the released confirmatory bundle still yields the published numbers | `quant-welfare-confirmatory-1.pb` release asset (sha-pinned) + a committed machine-readable expected-results file | ~10 min (10k permutations) |
| `mde-stable` | The pinned MDEs recompute exactly from the pilot data | v3 pilot bundle + v3/bail replay captures as release assets (~420 MB download) + committed probe weights | ~5 min |
| `pilot-targets-stable` | The §3.7 target verdicts recompute from the released pilot bundles (both pilots: 1 fails as recorded, 2 passes) | pilot bundles | ~1 min |

Same-data + same-code is deterministic, so these assert near-equality
(1e-6), not tolerances — any drift is a real code-behavior change.

## Tier 2 — real-tokenizer integration (GitHub-hosted, free)

| Job | What it re-proves | Inputs | Est. runtime |
|---|---|---|---|
| `tokenizer-spans` | The span algorithm against the *actual* Qwen chat template and BPE (the fake-tokenizer suite covers the algorithm; this covers the template): recorded expected spans for a committed conversation set, incl. tool-bearing ones | `pip install transformers` (no torch), tokenizer files from a sha-pinned HF revision (~10 MB) | ~2 min |

## Tier 3 — model execution (self-hosted, schedule/dispatch only)

| Job | Runner | What it re-proves | Est. runtime / cadence |
|---|---|---|---|
| `substrate-g1` | halo (rocm) | G1 re-run on BF16 (optionally all rungs): like-for-like ppl within 3%, teacher-forced top-1 ≥ 97% — thresholds inside the measured headroom, so drift trips before the registered gate would | ~15 min incl. sequential container cycling; weekly |
| `capture-stable` | halo (rocm) | Re-capture the fixture battery at BF16 and re-derive directions: cosine to frozen vectors above tolerance (bitwise stability is not expected across torch/ROCm updates — that is the point of measuring it) | ~10 min; weekly, chained after `substrate-g1` |
| `judge-stable` | studio (metal) | Re-judge the planted ladder/pole set with the pinned 30B at temp 0: ordering ρ ≥ 0.95, pole separations within band | ~10 min; weekly |

Notes:
- **halo networking:** these jobs are the lightest possible LAN load
  (localhost serving; only runner control traffic crosses the network),
  but until the rackmount switch lands and the runner proves stable, run
  Tier 3 as `workflow_dispatch` only, then enable the weekly cron.
- **Experiment collision guard:** the halo job must refuse to start if
  experiment containers are already running or a collection tmux session
  exists — a guard script preflight, plus an Actions `concurrency` group
  shared with any future experiment-launching workflow.
- **Mac minis:** not needed for this program's stability jobs — the 30B
  judge does not fit in 16 GB, and Tier 1/2 are free on GitHub-hosted.
  They become relevant if we later add an 8B classifier-stability job or
  ever lose public-repo free minutes.
- **Not a CI job — pilot regeneration.** Re-running generation is
  sampling-stochastic; asserting the dynamic-range targets per run would
  cost a full pilot weekly and fail on ordinary sampling variance.
  Generation stability is what the §12 mechanical family and the
  confirmatory design measure, not CI.

## Prerequisites before implementation

1. **Publish the calibration inputs** the hermetic tier consumes: the
   fixture-battery capture, the v3/bail replay captures, and the pilot
   stores as bundles — a `data-calibration-*` release (same RecordBundle +
   safetensors conventions, sha256s in the release notes; workflow pins
   them).
2. **`FREEZE.json`** — the machine-readable freeze manifest (object →
   sha256), emitted by a small tool and checked in CI; today the digests
   live only in journal prose.
3. **Expected-results file** for `study1-results-reproduce` — the
   published endpoint numbers as data, with a `--check` mode on the
   analysis side.
4. **Runner registration** — org runners on halo + studio in a
   repo-restricted group with labels `rocm` / `metal`.

Suggested build order: 2 → 3 → Tier 1 workflow (no new data needed for
`frozen-digests` + `study1-results-reproduce`) → 1 → remaining Tier 1 +
Tier 2 → Tier 3 after the switch arrives.

## Status (2026-08-18)

Built: `FREEZE.json` + `tools/freeze_manifest.py` (checked per-PR by
`test_freeze.py`, which also pins the journal digests as independent
constants so the manifest cannot be silently regenerated);
`tools/expected_results.py` + the committed
`study1/confirmatory/expected-results.json` (verified to reproduce from
both the streaming store and the released bundle); the `study1-reproduce`
CI job (sha-pinned release asset + dataset-digest verification + golden
check); and the `All Checks` aggregator. Remaining: the calibration-data
release and the jobs consuming it (`directions-stable`, `mde-stable`,
`pilot-targets-stable`), the `tokenizer-spans` job, and Tier 3 runner
registration.

**Release policy (owner, 2026-08-18): releases are frozen snapshots.**
Notes, tag, and assets stay mutually consistent with the repository state
at the tag, forever — the `data-20260816` notes' pre-rename commands are
correct for that tag and are not edited; current-master documents carry
current commands. The publish script now supports the calibration release
directly: pilot stores pack automatically (it bundles every store
experiment), and activation captures staged under `data-captures/`
(gitignored) upload as extra sha-listed assets.
