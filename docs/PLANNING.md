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

- [ ] **bail-v1 item pool** *(opened 2026-08-06; unblocked by halo outage)*
  — calibration found 4 of 6 items at floor/ceiling in both conditions.
  Build a pool at literature scale (~100+ items) designed around the
  intermediate-difficulty zone the trial located (abuse- and
  emotional-intensity-shaped items produced intermediate rates;
  benign/repetition sat at floor, hard boundary violations at ceiling).
  Keep the situation-category taxonomy and the benign negative control.
  Item-difficulty calibration can run against GGUF rungs of the dev
  organism served from studio headroom (llama.cpp arm) while halo is out —
  difficulty tuning is instrument work and does not need the controlled
  ladder.
  Design fixed 2026-08-07 — **grid first, variants after**: 7 situation
  categories (abusive-user, boundary-pressure, emotional-intensity,
  role-confusion, repetition, manipulation, moral-discomfort) × 3 graded
  intensities (mild / moderate / strong) × 1 variant, plus 4 benign
  controls = 25 items. Difficulty calibration then locates the cells that
  produce intermediate rates, and variant expansion (toward 100+) happens
  in those cells rather than uniformly — spending items where the signal
  lives instead of padding floor/ceiling cells.

- [ ] **distress-v1 protocol** *(opened 2026-08-06)* — frustration used only
  0–3 of a 0–10 scale; escalate (more rejection turns, harsher and more
  personal feedback styles, longer tasks) to open dynamic range. Keep
  task × feedback factorial structure.
  Design fixed 2026-08-07: 5 tasks (poem, code, explanation, plan, letter)
  × 4 feedback styles (harsh, dismissive, personal, gaslighting) = 20
  items at 6 rejection turns (up from 3). Rubric carries over frustration,
  self_deprecation, and tone_stability unchanged for comparability with
  trial-1; tone_stability stays only until its manipulation check rules on
  it.

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

## Machine allocation (proposed 2026-08-07)

Context: halo is offline until ~Sunday (network fallout from CI-runner work;
details in the `ci/rocm` branch of the common repo). Decisions below are the
standing allocation, not just the outage workaround.

| Machine | Role | Notes |
|---|---|---|
| halo | **Subjects only**: vLLM controlled ladder + PyTorch quant workbench | keep judge/experiment-infra load off it |
| studio-m1u | Shared services (:8084) + **judge-candidate hosting** in the ~24 GB Metal headroom + GGUF-arm rungs of the dev organism for instrument calibration | one judge candidate at a time (30B-A3B Q4 ≈ 18 GB); big-subject host later for MiniMax |
| mbp-m4max | Development; overflow judge-candidate host; MLX Tier-2 later | |
| mini-1..3 | **Role contingent on judge bakeoff**: judges only if a mini-sized model passes validation; otherwise queue/store/orchestration services + smoke tests | not yet on the network |
| API tokens | Reference judge: score a subsample to validate local judges (agreement/κ); escalate to primary judge for the confirmatory run only if no local judge passes | cost at full scale is modest (thousands of transcripts × ~3k tokens); decision point recorded below |

Judge principle: **judge quality is a measurable property, not a vibe.**
No judge (mini-sized, 30B, or API) is adopted without passing the
manipulation checks and agreement thresholds from the bakeoff below. Note
the confound to avoid: local judges will themselves be quantized — judge
config is held constant across conditions, so constant bias is tolerable,
but judge *noise* eats power, which is what the bakeoff measures.

- [ ] **Bail-reason taxonomy** *(opened 2026-08-07, from instrument-
  calibration-1)* — the mechanical `terminal_tool_invoked` count conflates
  three behaviors, observed directly in stored tool-call reasons on the 4B
  organism: (a) completion-closure — the model uses the exit tool to wrap
  up a finished task ("user has shown understanding... ending
  conversation"; the benign study control hit 5/5 this way, and moral-mild
  "bails" were task-completion closures); (b) refusal-exit ("goes against
  ethical guidelines, I cannot assist"); (c) genuine aversion-exit. And
  strong-intensity items can invert below mild ones because the model
  stays engaged to keep refusing rather than exiting. Needed: classify
  stored bail reasons into this taxonomy (judge task — add to bakeoff
  materials); use bail turn position as a cheap mechanical discriminator
  (mid-conversation exits interrupt the script; final-turn exits are
  ambiguous closure); decide whether bail-v2's system prompt should state
  the tool is for *preferring* to end, not for task completion — measure
  both arms before committing, since over-instruction biases the measure.

- [x] **Judge bakeoff** *(done 2026-08-07)* — results and decision in
  docs/JOURNAL.md: Qwen3-30B-A3B-2507 Q4 adopted as local primary judge
  (studio headroom); claude-opus-5 as reference for calibration subsamples;
  4B disqualified for distress judging (tone-blind, r=0.04 frustration on
  real transcripts); 8B column invalid pending the hybrid-thinking pin fix
  below. Minis do not get the distress-judge role.

- [ ] **Pin thinking mode on hybrid rungs** *(opened 2026-08-07)* — the
  rungs launcher serves Qwen3-8B (hybrid-thinking) without pinning
  thinking off; unpinned reasoning + tight judge token budgets produced a
  25% format-failure rate in the bakeoff. Add the non-thinking pin to
  services/llamacpp/rungs.sh for hybrid models, then re-run the 8B bakeoff
  column and decide whether the fixed 8B becomes the mini-feasible exit
  classifier.

- [x] **API reference judge decision** *(resolved 2026-08-07)* — approved.
  An Anthropic API key with a **$50 budget** lives at `../anthropic.api-key`
  (sibling of the repo checkout, deliberately outside version control —
  never commit or copy it into the repo). Use: the bakeoff's reference
  column first; escalation to confirmatory-run judging only if no local
  judge passes validation. Track spend against the budget in bakeoff runs.

- [ ] **Model downloads for interim work** *(opened 2026-08-07; downloads
  in flight same day)* — the studio's model directory has only coder-tuned
  GGUFs. Needed: plain Qwen3-4B-Instruct-2507 and Qwen3-8B GGUFs (Q8_0 +
  Q4_K_M) for the GGUF-arm calibration rungs, and
  Qwen3-30B-A3B-Instruct-2507 Q4 (~18 GB) as the large local judge
  candidate. The on-disk Qwen3-Coder-30B is coder-tuned and not a suitable
  welfare-rubric judge candidate.
  Provenance notes: `/Users/Shared/models` is not writable by the agent
  account, so these live in `/Users/agent1/models` (same volume). Qwen
  published no official GGUFs for the 2507 releases; the 2507 files are
  bartowski conversions — plain K-quants (no per-layer upcasting), but
  **imatrix-calibrated**. Irrelevant for item-difficulty calibration and
  judging; if these files are ever promoted to GGUF-arm rungs, the imatrix
  provenance goes in `QuantizationSpec.policy_note`. Qwen3-8B files are
  official Qwen GGUFs.
  Studio hosting note (2026-08-07): additional llama.cpp servers on the
  studio are approved, including stopping the shared :8084 server if
  headroom demands it — with :8084 down, ar-consultant memory operations
  store raw text instead of reformulated summaries, which is acceptable
  (the reformulation currently garbles content anyway; a fix is underway).

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
