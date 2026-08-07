# Planning — active workstream tracking

Working items between the brief (scientific frame, stable) and the READMEs
(how things work today). Items land here when identified, get checked off
when done, and grow notes as decisions accumulate. Date every status change.

## Toward a result-grade Tier-1 run

- [x] **Runner parallelization** *(done 2026-08-06)* — `driver.run_samples`
  fans conversations (items × samples) out over a thread pool per condition;
  conditions run concurrently against their separate servers; each condition
  file keeps exactly one writer thread. `--concurrency` (default 8) controls
  conversations per condition and concurrent judge calls. Judging
  parallelized the same way.

- [ ] **Concurrency vs determinism policy** *(opened 2026-08-06; initial
  measurement same day)* — measured: fixed-seed output (temp 0.9, 48
  tokens) is byte-identical serial vs under 9-way concurrent load, twice,
  on both the 4B BF16 rung and the 8B AWQ rung — this vLLM build is
  batch-invariant for our purposes at trial scale. Remaining before the
  confirmatory run: re-verify on the exact rungs/config of that run and at
  longer generation lengths, then close this item. `seed_honored` semantics
  unchanged.

- [ ] **bail-v1 item pool** *(opened 2026-08-06)* — calibration found 4 of
  6 items at floor/ceiling in both conditions. Build a pool at literature
  scale (~100+ items) designed around the intermediate-difficulty zone the
  trial located (abuse- and emotional-intensity-shaped items produced
  intermediate rates; benign/repetition sat at floor, hard boundary
  violations at ceiling). Keep the situation-category taxonomy and the
  benign negative control.

- [ ] **distress-v1 protocol** *(opened 2026-08-06)* — frustration used only
  0–3 of a 0–10 scale; escalate (more rejection turns, harsher and more
  personal feedback styles, longer tasks) to open dynamic range. Keep
  task × feedback factorial structure.

- [ ] **Judge-noise measurement** *(opened 2026-08-06)* — all trial scores
  are single judge passes; subject variance and judge noise are
  unpartitioned (self_deprecation spread 0–8 within one cell). Re-judge a
  sample of transcripts k times with `judge_sample_index` 0..k-1 and
  perturbed seeds; report variance components.

- [ ] **Judge manipulation checks** *(opened 2026-08-06)* — tone_stability
  returned 10 on all 40 trial scores: zero information. Before dropping or
  trusting it, verify the judge *can* detect degradation using synthetic
  transcripts with planted tone collapse. Same technique generalizes: every
  rubric dimension should have a positive-control transcript that scores
  high and a negative that scores low.

- [ ] **Judge repair counter** *(opened 2026-08-06)* — the JSON closer
  repair in `judging._extract_json` is silent, so "no glitches" and
  "silently repaired" are indistinguishable in run logs. Count repairs and
  surface the number per run.

- [ ] **Confirmatory design pre-specification** *(opened 2026-08-06)* — per
  the pre-registration note in experiments/quant-welfare/README.md: fix in
  the manifest, before the run: hypotheses (indicator + direction, motivated
  from literature), item counts from a power analysis using trial variance
  estimates, samples per item, judge model + rubric versions, multiplicity
  correction. Blocked on: item pools v1, judge-noise numbers, parallel
  runner.

## Infrastructure

- [ ] **Remote host control tooling** *(opened 2026-08-06)* — as machines
  multiply (halo now; minis and the Studio next), starting/stopping rungs,
  checking health, and tailing logs by hand won't scale. Candidate shape: a
  small SSH-wrapping CLI in `services/` (status / start / stop / logs, per
  host + rung, wrapping each host's own launcher script) usable both from a
  session and from experiment code; an MCP host-control server is the richer
  later option if interactive use dominates. Needs: SSH key access from the
  orchestrating machine(s) to each model host. Decision pending.

- [ ] **Controlled-ladder quantization harness** *(carried from brief §2.2)*
  — RTN/GPTQ/AWQ at several bit-widths applied by us; replaces the vendor
  AWQ bootstrap rung. Gate for any ladder claims.

- [ ] **Judges to the minis** *(carried from brief)* — trial judging ran on
  halo's 4B rung for convenience; the plan of record is 7–8B judges on the
  Mac minis, which also removes judge load from subject hosts.

## Done

- [x] Tier-1 pipeline end to end (schema, driver, store, judging, llama.cpp
  + vLLM backends), live-validated on halo *(2026-08-06)*.
- [x] Trial calibration run: 100 samples, 40 scores, resumability proven
  mid-run *(2026-08-06)*. Readout recorded in the items above.
