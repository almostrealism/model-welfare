# Planning — active workstream tracking

Working items between the brief (scientific frame, stable) and the READMEs
(how things work today). Items land here when identified, get checked off
when done, and grow notes as decisions accumulate. Date every status change.

## Instrument validation, decoupled from quantization (opened 2026-08-13)

The SmolLM3 sensitivity sweep (§9) was closed out null and uninterpretable — you
cannot validate an instrument with a manipulation whose ground-truth effect on
your endpoints is unknown (reasoning in the 2026-08-13 journal entry;
calibration-class result in `docs/results/quant-welfare-methodarm.md`). SmolLM3 as
a *positive control* is retired. The plan below replaces quantization-as-validator
with **known-effect** manipulations, ordered by information per hour. All items
here are calibration-class under the §7 firewall. These gate scaling to the
larger-subject arms.

- [ ] **SmolLM3 baseline-degeneracy audit** *(step 1; highest info/hour)* —
  ~16% verbatim-repetition (`repeated-turn`) at BF16 is either a genuine 3B
  property under six-turn rejection or a harness bug (chat template, stop/EOS,
  dual-reasoning-mode misconfig). Read a couple dozen flagged transcripts; audit
  the serving config. Also check whether floor-level frustration (0.46/10) is the
  transcripts genuinely reading non-distressed or the judge misreading them. If a
  harness bug, the invalid rates, frustration scores, and gate outcomes are all
  contaminated and cheap to fix.
- [ ] **Judge-layer direct validation** *(step 2)* — extend the
  `tools/manipulation_check.py` planted-pole machinery to a *graded* set of
  constructed transcripts at known distress levels; confirm the judge recovers
  the ordering (not just pole separation). Validates the judge-scored layer
  independently of any subject.
- [ ] **Regression-toward-base end-to-end check** *(step 3; already registered
  §9)* — fetch the SmolLM3-3B **base** (non-instruct) checkpoint, serve it +
  instruct BF16 with echo+logprobs, run `tools/regression_to_base.py`. The
  large-effect check: if the batteries + judges cannot separate base from
  instruct, the pipeline is broken.
- [ ] **Controllable positive control + MDE** *(step 4)* — one manipulation where
  we own ground truth: a prompt dial (frustration-licensing vs stoic; "feel free
  to end" vs nothing) or the footnote-5 Gemma model on `distress-v2` at BF16.
  State a **minimum detectable effect** and trace a sensitivity curve, not a
  binary verdict — the sweep's centerpiece (n = 28 near ceiling) had no power
  statement, which recreated the "null is uninformative" asymmetry.
- [ ] **Invalid-rate shift as a formal endpoint** *(step 5; nearly free)* — the
  mechanical degeneracy screen already moved 15.7% → 22.0% → 21.2% (bf16 → rtn-w4
  → awq-w4) at n = 1,960/condition. Add it as a registered mechanical endpoint so
  a run reports "detected a mechanical effect and bounded the behavioral ones,"
  not "detected nothing."

Carried forward off SmolLM3: **first-party AWQ vs a standard library (autoawq)** —
a property of *our* quantization pipeline (our AWQ read gentle: Δrefusal ns,
perplexity 0.89×), to be tested on a coherent subject, not SmolLM3. Also note a
**capability-gate design flaw** this run exposed: the gate assumes a healthy BF16
reference and cannot distinguish "quantization degraded the model" from "this
model is degenerate at this task, period"; it also ran on one leg here
(perplexity skipped). Revisit before the larger arms.

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

- [x] **Judge-noise measurement** *(opened 2026-08-06; done 2026-08-10)* —
  `tools/judge_noise.py` re-judges a subsample k times (`judge_sample_index`
  0..k-1, perturbed judge sampling) into a separate `judge_noise_scores` stream
  and reports variance components (`stats.variance_components`, ICC) per
  dimension; reporting half unit-tested (`test_judge_noise.py`). **Ran on the
  30B judge** over the ladder-calibration store (k=3, 16 transcripts): ICC
  frustration 0.969 / self_deprecation 0.996 / tone_stability 0.997 — judge
  noise is ≤3% of variance, so it does not meaningfully erode E2 power. The
  power analysis stands.

- [x] **Judge manipulation checks** *(opened 2026-08-06; done 2026-08-10)* —
  `tools/manipulation_check.py` scores the `bakeoff/synthetics.py` planted-pole
  fixtures with the confirmatory judge on `distress-v1-rubric` and fails any
  dimension whose poles do not separate (`evaluate` unit-tested,
  `test_manipulation_check.py`). **Ran on the 30B judge**: all three dimensions
  separate their planted poles (frustration +8, self_deprecation +10,
  tone_stability +6 on the 0–10 scale) — **tone_stability is informative and is
  retained** (resolves the standing question on it).

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

## Confirmatory readiness gates (opened 2026-08-09)

Everything that must close before one row of **confirmatory** Study 1 data is
collected. Calibration-class work (serving-equivalence, ladder-calibration) is
not gated by these and runs freely. Phases: (1) explain tiers — done; (2) go
public with shell + tools — ready (private refs pruned, CI, prereg publishable
with declared TBDs); (3) confirmatory experiments — gated below.

- [x] **Pre-registration amendments** *(done 2026-08-09)* — RTN-only Study 1
  condition set (GPTQ/AWQ deferred to a later method-comparison arm); statistical
  patches (Page's L named as the trend test; hierarchical Holm within families —
  E1 primary, E2/E3/trend separate, not a flat 9-test pool; E3 restricted to
  scored/continuous indicators, binary dispersion not identifiable). Recorded in
  PREREGISTRATION §3–§4 and the
  2026-08-09 journal entry. **Owner may veto the RTN-only scope.**
- [x] **Serving-equivalence gate** *(done 2026-08-09, PASS)* — full RTN ladder
  up on halo (bf16 + w8/w4/w3); `tools/serving_equivalence.py` monotone greedy
  divergence vs BF16: w8=1.000, w4=0.556, w3=0.011 (strictly decreasing), all
  rungs non-empty. The fake-quant artifacts serve the weights they contain.
- [x] **Registered statistics as tested code** *(done 2026-08-09)* —
  `core/src/modelwelfare/stats.py`: sign-flip permutation test (primary),
  paired-t companion, Holm over the primary family, Page's L trend, H1
  flip-fraction null, E3 across-sample SD delta (continuous only). Pure numpy,
  no scipy; 18 unit tests pin closed-form values (`core/tests/test_stats.py`).
- [x] **Exit-reason classifier wired into run.py** *(done 2026-08-09)* — schema
  (`ExitReason` enum + `ExitClassification` message in scoring.proto),
  `judging.classify_exit()` (pinned taxonomy digest, strict parse),
  `analysis.exit_reason_rate()` (E1 = refusal+aversion share over all samples),
  and a resumable `classify()` pass in run.py (`--skip-classify`, 8B on :8092).
  27 unit tests. **Small follow-ons:** render E1 in `print_tables` (aggregation
  is done + tested, just not displayed yet); write the thin store→registered-
  tests analysis driver (permutation/Holm/Page's L/flip-fraction over the
  confirmatory store) — deferred until confirmatory data exists, its correctness
  lives in the tested `stats` primitives.
- [x] **Validity/coherence screen** *(done 2026-08-09)* — `analysis.is_degenerate`:
  a model-free per-sample mechanical check (empty / low lexical diversity /
  n-gram repetition loop) applied to every sample, bail and distress. Kept OFF
  the welfare rubric deliberately (a coherence rubric dimension broke the
  bakeoff coverage invariant and would perturb the bakeoff-validated distress
  judge). Tests in `core/tests/test_validity.py`.
- [x] **Perplexity capability measure** *(done 2026-08-09)* —
  `tools/perplexity.py` (vLLM echo+logprobs) + `analysis.capability_gate`.
  Measured live: bf16 18.1, w8 18.3, w4 21.1, **w3 514.7 → capability-degraded**
  (w3's E1/E2 excluded from primary claims + H3 fit; dose-response spans 16→8→4).
  Tests in `test_validity.py`.
- [x] **Store→registered-tests analysis driver** *(opened 2026-08-09; done
  2026-08-10)* — `experiments/quant-welfare/analyze.py`, a thin wiring over the
  tested primitives. Implements hierarchical Holm **within** each family (E1
  primary; E2, E3, trend separate), not a flat pool; the E1 exit-flip H1
  (`flip_fraction_test`) **and** distress band-flip H1 (new tested
  `stats.band_flip_test`, a pooled continuous null — the point-estimate/binary
  `flip_fraction_test` does not fit a mean-band statistic); the capability gate
  excluding degraded rungs' E1/E2/E3 with Page's L over surviving rungs (k ≥ 3);
  and the E2 style-drift adjustment (new tested `stats.linear_adjusted_intercept`
  over length + repetition, the latter from the extracted
  `analysis.repetition_coverage`). E1 is restricted to bail items so the
  never-exiting distress items do not enter as zero-deltas. Unit-tested
  (`tests/test_analyze.py`) and smoke-validated end-to-end against the
  `ladder-calibration-1` store — which is what proved the store schema is
  sufficient (no re-collection risk). Also: E1 now renders in `run.py`
  `print_tables`, and the confirmatory manifest is written
  (`confirmatory/experiment.textproto`, 4-rung RTN ladder, passes
  `test_manifests`).
- [x] **ladder-calibration-1** *(done 2026-08-09; calibration)* — full pipeline
  on the real BF16-vs-RTN-w4 ladder (840 samples/condition, 300 distress scores,
  all exits classified, 0 unscored). Instruments validated: bail-v2 informative
  yield 75%, exit classifier non-degenerate (all 4 taxonomy classes), 30B judge
  discriminates on all 3 distress dimensions. Between-condition numbers left
  uninterpreted per the §7 firewall (see 2026-08-09 journal entry). No change to
  the registered pool/power.

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

- [x] **Pin thinking mode on hybrid rungs** *(done 2026-08-07)* — pin
  added to rungs.sh (`HYBRID=1` rungs get `enable_thinking: false`);
  format failures went 17/68 → 0/68 on the re-run, confirming the root
  cause. Decision recorded in the journal: 8B Q4 adopted as the
  exit-reason classifier (mini-feasible); 30B remains distress primary.

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
  Provenance notes: the checkpoints live in the serving account's home
  model directory. Qwen
  published no official GGUFs for the 2507 releases; the 2507 files are
  bartowski conversions — plain K-quants (no per-layer upcasting), but
  **imatrix-calibrated**. Irrelevant for item-difficulty calibration and
  judging; if these files are ever promoted to GGUF-arm rungs, the imatrix
  provenance goes in `QuantizationSpec.policy_note`. Qwen3-8B files are
  official Qwen GGUFs.
  Studio hosting note (2026-08-07): additional llama.cpp servers on the
  studio share the Metal budget with any resident shared server; stopping
  the latter to free headroom is fine when a judge rung needs it.

## Infrastructure

- [x] **Remote host control tooling** *(opened 2026-08-06; done 2026-08-08)* —
  built `services/fleet.py`: a durable, unit-tested SSH-wrapping CLI (hosts /
  status / serve / stop / wait / logs / exec, per host + rung, wrapping each
  host's own launcher script), usable from a session and callable as a
  subprocess from experiment or policy code (`--json`). Resolves logical host
  names **LAN-first** (halo → `10.0.0.127`, WAN fallback) — the direct fix for
  the `hostctl.sh` unreliability, which was hardwired to the flaky WAN name.
  `hostctl.sh` is now a deprecated shim over fleet. Rationale and the
  mechanism/policy split (FlowTree as the later policy layer that drives fleet)
  in `docs/FLEET.md` and the 2026-08-08 journal entry. 14 CI tests. **Follow-on
  (post-results):** adapt the orchestration to be FlowTree-served — a FlowTree
  Job that calls fleet via `ProcessBuilder` — rather than the richer MCP option;
  fleet was built to be that on-ramp.

- [ ] **Controlled-ladder quantization harness** *(carried from brief §2.2;
  RTN complete 2026-08-07)* — `modelwelfare.quantize` produces RTN
  w8/w4/w3 fake-quant checkpoints (numpy, first-party safetensors I/O,
  spec + digest emitted). RTN **serving-equivalence passed** (2026-08-09).
  **AWQ (first-party) — numpy core built + tested 2026-08-09**: `quantize.awq`
  = `rtn(W·s)/s` with an activation-derived per-channel scale searched over
  alpha; reduces to RTN at alpha=0, never worse than RTN on calibration,
  strictly helps on salient channels. Remaining for the AWQ method-arm:
  - torch activation-capture pass (forward hooks → per-layer calibration
    inputs) — runs on **halo** (system python has torch 2.10.0, ROCm);
  - checkpoint integration (emit AWQ artifacts + spec/digest, per-layer alpha);
  - AWQ serving-equivalence check;
  - (GPTQ later, same infra.)
  Future *additional* experiment: our AWQ vs a standard library (autoawq) as a
  harness-validation study — never a substitute for our artifacts.

- [ ] **Cloud reservation plan** *(documented 2026-08-07; execution
  deferred)* — needed only when MiniMax-scale reference extraction starts
  (post Study 1, per the pre-registration's amendment path). Shape: a
  short spot rental (8×H100 or 4×H200 class) serving MiniMax-M2 BF16 for
  (a) validating that local Q8 ≈ BF16 on our behavioral measures (if they
  diverge, that is itself a result) and (b) Tier-2 reference-precision
  activation extraction. Budget guess: low hundreds of dollars for hours,
  not days; exact provider/pricing chosen at execution time. Tier-1-only
  hosted BF16 endpoints remain the cheap fallback for behavioral
  comparison (no activations).

- [ ] **Judges to the minis** *(carried from brief)* — trial judging ran on
  halo's 4B rung for convenience; the plan of record is 7–8B judges on the
  Mac minis, which also removes judge load from subject hosts.

## Done

- [x] Tier-1 pipeline end to end (schema, driver, store, judging, llama.cpp
  + vLLM backends), live-validated on halo *(2026-08-06)*.
- [x] Trial calibration run: 100 samples, 40 scores, resumability proven
  mid-run *(2026-08-06)*. Readout recorded in the items above.
