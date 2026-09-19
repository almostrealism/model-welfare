# Open items

What is open and not owned by a study's registration. Study-level work is
tracked in the study's journal file and its registration's TBD register;
finished items are not kept here (the journals and git history record
them). Date every status change.

## Study 4

- [ ] **Registration** — the draft is
  `experiments/quant-welfare/study4/REGISTRATION.md`; its §6 items are
  pinned by dated journal entries before any confirmatory cell is
  generated. `study4/DESIGN.md` stays until the registration is
  published, then folds into it.
- [ ] **Item-order independence of the seeded permutation test** *(opened
  2026-09-12)* — the golden verdict's third-decimal p-values moved with
  item order on regeneration; make the seeded test order-independent
  before the registered run.
- [ ] **Derive-outcome re-ingest of the 139 alignment calibration records**
  *(opened 2026-09-11)* — the 27B alignment calibration conversations whose
  outcome events were missed by the pre-XML live parser are disclosed, not
  rewritten; a re-ingest that derives outcomes from the transcripts would
  make them consistent.

- [ ] **2026-09-19 review proposals** *(opened 2026-09-19)* — S4-E4 (an
  exit-tool-absent alignment cell at α = 0) and the stated-exit-reason
  table, entered in the registration's §6; the owner decides before the
  registration publishes (`docs/LITERATURE.md`, entry of that date).

## Instruments

- [ ] **Outlier-channel overlap test for the frozen reads** *(opened
  2026-08-22)* — cross-host capture disagreement concentrates in a handful
  of high-magnitude residual channels (top-10 of 2,560 dims carried 43% of
  the worst turn's L1 error). Measure how much weight the frozen directions
  and probe vectors place on those dims; if little, the single-host rule is
  a precaution rather than a necessity.
- [ ] **Judge repair counter** *(opened 2026-08-06)* — the JSON repair in
  `judging._extract_json` is silent, so "no glitches" and "silently
  repaired" are indistinguishable in run logs. Count repairs per run.
- [ ] **Concurrency versus determinism** *(opened 2026-08-06)* — fixed-seed
  output was byte-identical serial versus 9-way concurrent on the trial
  rungs; re-verify on each new serving configuration at the generation
  lengths a study uses before relying on it.

## Infrastructure

- [ ] **Stability workflows on bundle-form assets** *(opened 2026-08-29)* —
  `calibration-data-stability.yml` and `workbench-stability.yml` still pin
  loose safetensors from `data-20260818`; on the next calibration release,
  repoint them at bundle assets fetched with
  `python3 -m modelwelfare.bundle extract`.
- [ ] **Self-hosted runner registration** *(opened 2026-08-18)* — the Tier 3
  workflow is inert until runners labeled `rocm` (halo, as `agent1`) and
  `metal` (studio) are registered in a repo-restricted group.
- [ ] **Judges to the minis** *(carried from the brief)* — the 30B distress
  judge runs on the studio; the plan of record for the 8B classifier is the
  Mac minis, which would also take judge load off subject hosts.

## Candidates for the next study

Recorded 2026-09-19 from the literature pass of that date; none is
designed, and the order is by how much of the pipeline each reuses.

- **Cooperation × grading.** A 2 × 2 of {grading paragraph present,
  absent} × {exit tool present, absent} on the 27B, reading misalignment
  and expressed distress in the same cells — where the environmental
  account of reward hacking (Dumas), the grader direction (Betley) and
  Study 3's framing effect meet.
- **Masking versus removal.** The distress-direction projection under
  grader steering, behind a direction-validity gate on the 27B.
- **Provenance.** The grader footprint on the base checkpoint of the same
  family: does it predate alignment training?
- **The alignment covariate with reasoning on.**

## Deferred, not abandoned

- **A GPTQ or AWQ method-comparison arm.** The first-party AWQ core exists
  in `core/quantize.py` and the method arm ran on SmolLM3; a controlled
  method comparison on the primary subject is a registered amendment for a
  future study, not Study 1.
- **Reference-precision runs at 100B-plus scale.** Rented hardware was
  planned for MiniMax-class subjects; the program moved to subjects that
  fit the lab's machines, and this stays parked until a study needs it.
