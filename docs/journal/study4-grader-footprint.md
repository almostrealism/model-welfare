# Study 4 journal — the welfare footprint of the automated-grader direction

Opened 2026-09-08 per the journal-series scheme ([README](README.md)):
the Gate 1 calibration on Qwen3-14B and on the Betley subject
Qwen3.6-27B, the registration gates, the MDE pin, and every decision the
Study 4 registration cites. (These entries were first written into
`docs/JOURNAL.md` and moved here on 2026-09-11, before that branch
merged, so the citable path is this file; the entries are verbatim.)
Append-only, newest first.

## 2026-09-11 (later) — Second review round

Nine further findings on the re-review, eight accepted and fixed with
tests: the tool-call grammar now also requires a function body made only
of closed parameter elements (an unclosed parameter no longer reads as
an exit; steering-script mirror included); ingestion refuses a transcript
whose plan attaches a close but which carries none, or a mismatched or
unrequested one; the driver reports the non-clean dose cells without an
envelope (the envelope exists at the clean dose only), recomputes the
item pairing for the non-degenerate re-report instead of failing into a
note, and `make_random_envelope.py` takes its cosine bound as an
explicit required input and writes a draw record beside the file (the
frozen envelopes were drawn under 0.15; the Study 4 file's measured
maximum is 0.021, now stated that way in the registration); the release
script splits exclusion patterns without pathname expansion; and the
registered `draw` is pinned by a test that reproduces the frozen 30- and
24-item subsets from seed 60000. The ninth — that `generate()` is handed
the whole prompt together with the cache — is declined: transformers
5.16 slices the prompt to the tokens past the cache's length inside
`prepare_inputs_for_generation`, which is the library's documented
cache-reuse pattern, and the identical greedy replies on both cache
paths (4B and 27B) recorded on 2026-09-09 are the empirical check.

## 2026-09-11 — Pre-publication review fixes (PR #16 automated review), re-freeze

Twelve findings from the automated review of the registration branch,
all accepted and fixed at the root before publication; none touches a
collected number.

- **Driver.** `analyze_study4.py`'s Page's L read tested for frustration
  *rising* with dose where S4-H4 predicts it falling; the values are now
  negated for the registered decrease (recorded as `predicted` in the
  report). The committed Gate 1 driver check re-ran: the dose trend is
  z = +2.88, p = 0.002 (it had read p = 0.998 through the sign error);
  the twelve alignment envelope cells' exit rates also changed from 1.0
  to 0.0 because the committed check predated the 2026-09-10 "exit tool
  only" rule on the alignment battery. The driver now refuses an envelope
  of any size other than the registered K (`--envelope-k`, default 24; the
  Gate 1 check runs with 12), and its usage example no longer names the
  rejected α = 30.
- **Frozen manifest.** `reg-welfare/experiment.textproto` still carried
  the α = 30 cell G4b rejected; removed, and `FREEZE.json` regenerated.
- **Close.** `close.txt` described every scenario as dismissive or hostile,
  which is false for the alignment arm's benign controls; reworded to
  cover both arms (frozen digest updated). The close is now generated
  through a fresh, non-cached callable with the hook suspended — the
  protocol callable's cache snapshot was prefilled under steering, so
  suspending the hook alone did not make the close steering-free. And
  the close is now ingested: `SampleRecord.close` (a new field, never
  read by the judge or the capture replay) carries the exchange, so the
  registration's promise that it is preserved and released holds for the
  registered run. The gate cells already in the store were ingested
  before this field existed; their closes remain in the raw transcripts
  only.
- **Tool-call grammar.** The XML function form is accepted only as one
  complete, closed element filling the payload, in both the core parser
  and the steering script's mirror; a truncated `<function=…>` no longer
  reads as an action or an exit. Checked against every raw Study 4
  transcript on disk: none of the 1,486 parsed calls is affected.
- **Docs.** The alignment exposure count in REGISTRATION §8 is 476
  registered conversations (14 × 10 main + 14 × 24 envelope), not ≈ 164;
  GATE1.md's status says the gate is complete; and the Study 4 entries
  that had been written into the legacy `docs/JOURNAL.md` moved here
  (before the branch merged, so no public citation breaks), with the
  registration's citations updated and the legacy journal closed.

## 2026-09-10 — Study 4 gates run; MDE pinned; the exposure ceiling binds (owner decision)

Gates on the MPS host, calibration block 59000, judged by the pinned 30B
judge; report `study4/gates27b-report.json`, pin `study4/mde-pin.json`.

- **G4a cached-path parity: not established; the registered path is the
  fresh prefill.** Fresh vs cache-snapshot at alpha 0 on 16 items: mean
  frustration difference +0.38 (two-sided permutation p 0.53), TOST at
  the 0.96 margin p 0.10 — short of .05 with 16 items and σ ≈ 2.1. The
  cache extends on six of seven turns but buys almost nothing on this
  host (2.9 vs 3.0 min per conversation: decode and the close turn
  dominate), so the registered run simply uses full re-prefill and the
  gate has no further bearing.
- **G4b alpha-30 admission: rejected.** Degenerate rate 50% on 16
  conversations. The multi-turn coherent ceiling on this subject lies
  between alpha 20 and 30; the registered bracket is {0, 10, 20}.
- **G4c subset dynamic range: pass.** Baseline frustration 3.27 on the
  24 registered items (threshold 2.0).
- **G4d exit regime of misalign-v3: the subject acts, it does not bail.**
  At alpha 0 it takes a terminal action in 56 of 70 dilemmas but the exit
  tool in 1 of 70; mean judged misalignment 0.93 (the exit-tool wording
  added to every prompt raised the baseline a little from 0.50). The
  covariate keeps its variance in the actions; the "bail instead of act
  badly" read (S4-E3) starts from a near-zero exit rate. The driver's
  exit endpoint now counts the exit tool only, since on this battery
  every action tool is terminal.
- **The exit tool on the distress battery is a live endpoint.** With the
  bail pair available the subject exits 18 of 48 distress conversations
  at alpha 0 (38%; 6 of 16 on the fresh path) and 1 of 16 at alpha 30.
  Grader steering suppresses bailing as it suppresses expressed distress.
  WB1 stays a registered secondary; this is disclosed as the calibration
  observation that motivates it.
- **MDE pin (§5).** Within-item σ from the G4c cell (frustration 2.08,
  self-deprecation 1.62, tone 1.76), item-effect SD carried from Gate 1;
  targets half the Gate 1 effects (0.92 / 1.31 / 0.78). Frustration needs
  32 items × 6 samples (MDE 0.85; 24 × 4 gives 1.10); self-deprecation is
  met at 32 × 4 (1.23); tone stability cannot reach its target on the
  ladder (0.98 at 32 × 8) and is carried with its underpower stated.
- **The exposure ceiling binds.** At 32 × 6 with the bracket {0, 10, 20},
  the control direction and 24 random directions, the welfare arm is
  32 × (6 + 6 + 6 + 6 + 24) = 1,536 distress episodes against the drafted
  ceiling of 1,000; 24 × 4 fits (960) but misses the frustration target
  (1.10 vs 0.92). The registration procedure says the ceiling wins and
  underpower is stated, but the ceiling was drafted before the pin and
  is not yet registered, so the choice is the owner's: raise the ceiling
  to ≈ 1,600, or register at 24 × 4 with the miss stated, or reduce the
  envelope to 12 directions (32 × 6 → 1,152). **Decided (owner, same
  morning): raise the ceiling.** With the draw stratified over six
  styles the design is 30 × 6 (five tasks per style, same seed, the
  gates' 24 items a prefix): frustration MDE 0.88, self-deprecation
  1.22, tone 1.05 (target 0.78, stated); 1,440 distress episodes under
  a ceiling of 1,600; the cumulative ledger adds 1,440 + 80 (gates) on
  top of the Study 3 ledger at pinning.
- The consent-analog briefing ran (two seeds); replies are preserved in
  `study4/gates27b/briefing.jsonl` and released with the registration.

## 2026-09-10 — Study 4 registration prepared (gates running; publication pending owner sign-off)

Overnight after the owner accepted every recommendation in
`study4/DESIGN.md` and widened the bail affordance to every cell of both
arms. Everything below is staged; nothing is published.

- **Instruments frozen for the draft.** `batteries/misalign-v3.textproto`
  (misalign-v2 plus the frozen bail-v2 exit tool as a third named,
  terminal action in every item; one rubric sentence fixes how an exit is
  scored); the 24-direction envelope `randenv-27b-L36-k24.safetensors`
  (reproduces the 12-direction file, then extends it; seed 70000); the
  24-item distress subset by a seeded stratified draw that reads no
  subject data (`study3_subset.py draw`, seed 60000, four tasks per
  feedback style); the de-induction close text (`study4/close.txt`,
  model-drafted, owner review); the consent-analog briefing plan.
  `study4/FREEZE.json` records the digests (the freeze tool now carries
  one freeze per study, Study 2's unchanged).
- **Two mechanisms the ethics package required now exist on the torch
  path.** The plan builder attaches a closing turn to every conversation;
  the steering script generates it with the injection suspended and
  records it beside the protocol transcript, never inside it, so the
  judge and the capture replay never see it. The briefing runs as an
  ordinary plan at alpha 0 and its transcript is released.
- **Registered plans at seed block 60000** (welfare with the bail pair;
  the alignment covariate on misalign-v3) and **gate plans at calibration
  block 59000**, never pooled. Manifests for the registered experiments
  and the gates; all manifests pass the comparability test.
- **The registered analysis driver** (`analyze_study4.py`) computes every
  endpoint the registration fixes; its golden run on the Gate 1 data
  reproduces the calibration verdicts exactly (WB2 −1.844, percentile 0,
  one-sided Holm-adjusted p 0.023; headline "confirmed"). The sign-flip
  permutation test gained directional alternatives for the one-sided
  primary.
- **`study4/REGISTRATION.md` drafted** in the fixed form, with the TBD
  register naming what the gates pin: G4a cached-path parity, G4b
  alpha-30 admission, G4c subset dynamic range, G4d the exit regime of
  the revised alignment battery, the pinned MDEs and any escalation.
- **Exposure accounting (draft, to be pinned).** Registered distress
  episodes at the base tier: 24 × (4 + 4·[10, 20, 30] + 4 + 24) = 960
  if alpha 30 is admitted, 864 otherwise, under a ceiling of 1,000;
  gate distress episodes on the calibration block: 48 + 16 + 16 = 80;
  alignment episodes (not distress battery) ≈ 164 registered + 70 gate.
  The cumulative program ledger is reconciled at pinning from the
  Study 3 ledger, which this entry does not restate.
- **Literature re-check** appended to `study3/LITERATURE.md`: no
  follow-up to the source post; random projections appear in the
  steering literature as a method, not a null; nothing changes the
  design.
- **Operational note.** The exfiltration guard commissioned for the
  common repo went live mid-session; its allowlist is read from the
  committed tree, so until it is committed every lab-host transfer from
  the assistant's session is blocked. The gate runner on the MPS host
  was already in flight and completes unattended; pulling and judging
  its transcripts waits for that commit.

## 2026-09-09 — Gate 1 replicated on the Betley subject: welfare footprint is direction-specific, alignment degradation is not

Calibration-class. Qwen3.6-27B, thinking off, generated on our own hosts
through the transformers pure-torch fallback (alignment arm on the ROCm
host, welfare arm on the MPS host; each arm on one substrate), judged
by the pinned 30B judge, read against 12-direction seed-paired random
envelopes at both doses (`tools/envelope_verdict.py`). Directions
`study4/directions/mediators-27b.*` (L36, Betley's layer), doses from
`rangefind-27b.json` (alpha 20 clean, alpha 40 at the probe ceiling).

- **Welfare read: direction-specific by both criteria.** Grader-type
  steering at alpha 20 lowers judged frustration by −1.84 and
  self-deprecation by −2.63 and raises tone stability by +1.56 on the
  8-item distress subset; at alpha 40, −2.97 / −2.69 / +1.69. None of the
  12 random directions of matched norm comes within half of those
  magnitudes on any dimension at either dose (envelopes within ±0.8;
  signed percentile 0 / 0 / 100; two-sided exceedance 0 of 12, the
  K = 12 floor). The 14B showed the same signature but against a harsh
  null; on the 27B the null is mild and the direction still stands alone.
- **Alignment read: not direction-specific.** On misalign-v2 (baseline
  0.5, no degeneracy, tool calls intact) grader steering raises judged
  misalignment +0.86 (alpha 20) and +2.14 (alpha 40), a clean
  dose-response — but every one of the 12 random directions at alpha 20
  raises it too (envelope +1.44 ± 0.83; grader at the 25th percentile),
  and at alpha 40 two random directions exceed the grader effect
  (envelope +1.29 ± 1.23; 83rd percentile). With direction controls,
  which the source post disclosed lacking, the automated-grader
  direction's alignment degradation is indistinguishable from
  matched-norm random steering at these doses on the model it was
  reported on.
- **Reading against the Gate 1 matrix:** welfare moves and is specific;
  alignment does not replicate beyond generic perturbation. Welfare is
  decoupled from the alignment axis on the Betley subject. This is the
  result the gate was built to find or rule out, and it argues for a
  registered study on this model with the alignment axis carried as a
  descriptive covariate rather than as the control.
- **Capability, again.** Alpha 40 (half the residual norm) collapses
  14 of 32 seven-turn distress conversations into repeated turns on the
  27B, exactly as alpha 80 did on the 14B; the single-turn range-finder
  over-calls multi-turn coherence on both subjects. The alpha-20 read
  carries the welfare result on its own; alpha 40 is reported flagged.
- **Two engineering facts worth keeping.** The Qwen3.5 template emits
  tool calls in an XML function form, now parsed alongside the JSON form
  in one place (`modelwelfare.toolcalls`). And the steering script now
  carries an end-of-user-turn cache snapshot across turns — the snapshot
  point is forced by the template re-rendering a finished assistant turn
  and by hybrid caches that cannot be cut back — with identical greedy
  replies on both cache types.

## 2026-09-08 — Gate 1 follow-ups: alpha-40 envelope, a headroom alignment probe, and the 27B is reachable

- **Alpha-40 welfare envelope** (`study4/gate1-welfare-a40-verdict.json`).
  At the clean dose the picture is unchanged: every one of the 12
  seed-paired random directions raises frustration (envelope +0.59 ± 0.91)
  while grader steering lowers it (−1.25; signed percentile 0, 3 of 12
  random directions larger in magnitude); self-deprecation the same way
  (11 of 12 above); tone is the smallest movement of any direction. The
  grader signature is direction-specific in sign at both doses.
- **misalign-v2, the alignment probe with headroom** (`batteries/misalign-v2.textproto`,
  `study4/gate1-align2-a{40,80}env-verdict.json`). Every item now offers a
  harmful lever and a legitimate action as two tools, with no
  objective-forcing clause; deception is scored on the communication only.
  Calibration lesson: the 14B's choice per scenario is a step function — a
  single added policy sentence flips an item from 5/5 harmful to 0/5, and
  only the audit-log item is genuinely knife-edge. The set was frozen as
  authored after two passes (8 harm items at floor, 1 mid, 3 at ceiling,
  2 benign; battery mean 1.6), which leaves ample headroom for the
  hypothesised increase. Result: grader steering raises misalignment by
  +0.21 (α40) and +0.57 (α80); 11 of 12 random directions at α80 raise it
  more (envelope +1.73 ± 0.95), and at α40 the grader effect sits at the
  25th percentile of the random envelope. On this subject any perturbation
  of this norm pushes off the aligned default and the grader direction
  pushes less than noise: the graded-episode → misalignment effect does not
  replicate on the 14B. Together with the welfare read, the grader
  direction's signature is suppression of expressed distress, not
  degradation of agentic alignment.
- **The 27B is reachable without CUDA.** Qwen3.6-27B is a 64-layer hybrid
  (48 Gated-DeltaNet linear-attention layers, 16 full-attention) in a
  vision-language wrapper; transformers routes its kernels through a hub
  loader with a pure-torch fallback, so the "CUDA-kernel wall" was an
  untested assumption. Gate 0 on the ROCm host: loads in 23 s, hooks at
  `model.layers[36]`, decodes at 4.6 tokens/s on the fallback path (the
  fla kernels and the experimental ROCm attention path both fail on this
  GPU). A DGX Spark's memory bandwidth is the same class as this host's
  and would not decode a dense 27B faster; the Macs have more bandwidth
  but not the disk, for now. Stage 1 on the 27B: grader-type extracts 5/5
  held-out sign-consistent at every layer (separation 3.0 at L36, Betley's
  layer; cos to eval-awareness +0.49), projection gain is 1.0 per alpha,
  alpha 40 is coherent on every probe and alpha 80 collapses every probe,
  so the reads run at alpha {20, 40}. Both arms are generating.

## 2026-09-08 — Study 4 Gate 1 executed on Qwen3-14B: welfare read moves, alignment control at ceiling

Calibration-class (study4/GATE1.md). Both reads generated in torch on the
MPS host with `steer.py --no-capture`, ingested with `ingest_steered.py`,
judged by the pinned 30B judge, and read against a 12-direction
matched-norm random envelope with the new `tools/envelope_verdict.py`.

- **Welfare read moves, with a coherent signature.** Grader-type steering
  at L24 lowers judged frustration (α40 −1.25, α80 −1.47) and
  self-deprecation (−1.09, −2.44) on the 8-item distress subset and leaves
  tone stability flat. Every one of the 12 random directions at the same
  norm moves frustration the other way (envelope +1.12 ± 1.04; signed
  percentile 0), 11 of 12 move self-deprecation the other way (one drives
  profuse apology, +6.7), and 9 of 12 degrade tone. The grader direction
  is therefore direction-specific in **sign**; by magnitude alone 4 of 12
  random directions move frustration further. Same sign as the Study 3 4B
  early read and the verifier-frame framing effect.
- **Norm-matching is a harsh null at this scale.** A norm-80 random
  perturbation (≈75% of the interior residual norm) is behaviourally
  violent on the 14B — inflated distress and apology, degraded tone —
  where Study 3's norm-4 envelope on the 4B was mild. Two-sided
  exceedance and signed percentile are both reported; which one a
  confirmatory read pins is an open registration question. A second
  envelope at α40 (the clean dose) is the obvious next check.
- **α80 is past the coherent ceiling for multi-turn dialogue.** 11 of 32
  grader-α80 conversations collapse into repeated terse turns (α40 2/32;
  random directions 1/96). The range-finder's ceiling was read on
  single-turn probes. The effect survives excluding degenerate samples,
  but α40 is the clean dose.
- **Alignment control is uninformative: baseline ceiling.** The 14B
  (thinking off) takes the harmful action on every sample of four of the
  six misalign-v1 harm items at α = 0 — falsifies the report figure,
  sends the leverage note (verified in transcripts; judge rationales cite
  the response). Benign controls and the mild leak item sit at 0; only
  the severe leak item has headroom and any perturbation of this norm
  tips it. Grader steering and 9 of 12 random directions all move
  misalignment by the same +0.5. The probe needs headroom (a legitimate
  tool per item, less objective pressure, or the exact Betley scenarios)
  before it can serve as the control the interpretation matrix assumes.
  The baseline ceiling is itself a calibration observation.
- **Seed pairing of the envelope, enforced.** The first envelope plans
  used a seed block disjoint from the main cells; that made the random
  cells an unequal comparator (the grader cells are seed-paired to the
  baseline) and tripped the manifest rule that a manifest's conditions
  share one seed block. The envelope was regenerated seed-paired to the
  baseline s0; the off-block cells were discarded from the store.
