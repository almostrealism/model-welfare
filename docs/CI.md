# Continuous integration — what is re-proved, and where

CI exists to keep "the instrument is stable" a continuously re-proven
claim rather than a one-time journal entry. Jobs split along one rule:
**does the job execute a model?** If not, it runs on GitHub-hosted runners
on every push. If so, it runs on the lab's own machines on a schedule or by
hand.

## The aggregator

Branch protection requires exactly one status check, `All Checks` in
`ci.yml`. It `needs:` every other job in that workflow, runs `if:
always()`, and fails only when a needed job ended in a state other than
`success` or `skipped`. Skipped is acceptable on purpose: path filters and
missing prerequisites can skip a job without wedging merges. Every job added
to `ci.yml` must be added to the aggregator's `needs:` list, or branch
protection cannot see it.

## Tier 1 — hermetic, every push (`ci.yml`)

| Job | What it re-proves |
|---|---|
| `test` (Python 3.11, 3.12, 3.13) | the full hermetic suite, including `test_freeze.py`, which checks every study's `FREEZE.json` against the repository and pins the journal's digests as independent constants so a manifest cannot be silently regenerated |
| `study1-reproduce` | `analyze.py` over the sha-pinned Study 1 release bundle still yields the committed `expected-results.json` |
| `tokenizer-spans` | the span algorithm against the real Qwen chat template and BPE, from a revision-pinned download, matches the committed expectations |

Same data and same code are deterministic, so these assert near-equality,
not tolerances. Any drift is a real change in code behavior.

## Tier 2 — released data, weekly (`calibration-data-stability.yml`)

`directions-stable`, `mde-stable` and `pilot-targets-stable` re-derive the
frozen directions, the pinned MDEs and the pilot target verdicts from the
released calibration assets. They still pin loose safetensors from the
`data-20260818` release, which remain downloadable; repointing them at
bundle-form assets is an open item in `PLANNING.md`.

## Tier 3 — model execution, schedule or dispatch (`workbench-stability.yml`)

`judge-stable` on the studio and `substrate-g1` and `capture-stable` on the
workbench re-run the serving-parity, capture-path and judge-ordering checks
with thresholds set inside the measured headroom, so drift trips before a
registered gate would. The workflow carries a collision guard that refuses
to start while an experiment is running on the host. It merges inert until
self-hosted runners with the matching labels are registered, and it is
deliberately not in the `All Checks` list.

## Policies

- Fork pull requests do not run workflows until a maintainer approves the
  run, which is what makes PR-triggered validation on self-hosted runners
  acceptable; the heavy model jobs stay on schedule or dispatch for
  operational reasons regardless.
- Releases are frozen snapshots. Notes, tag and assets stay mutually
  consistent with the repository at the tag, forever; current documents
  carry current commands.
- Generation is not re-run in CI. Re-generating pilots is
  sampling-stochastic, and the dynamic-range targets would fail on ordinary
  variance; generation stability is what the registered mechanical
  endpoint family measures.
