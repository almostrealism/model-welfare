# model-welfare — agent working notes

Conventions and recurring reminders for agents working this repo. The
scientific frame lives in `PROJECT_BRIEF.md` and the study registrations
under `experiments/quant-welfare/`; this file is the operational layer.

## Journal discipline (a recurring lapse — keep it fed)

The split journal only beats a single growing `JOURNAL.md` if it is
*actually kept current*. The failure mode, observed twice, is storing
ar-manager memories (good for cross-session recall) while letting the
public journal fall a day or more behind the decisions — then the
registration/results posts have no dated trail to reconstruct.

**Rule: journal each decision cluster the day it lands, not in a later
backfill.** Placement (`docs/journal/README.md`): per-study file
(`docs/journal/study<N>-<slug>.md`) for anything a study's registration
would cite; `docs/journal/program.md` for cross-study infrastructure and
instrument findings. Append-only, newest first, dated headers. A memory
store is not a substitute for a journal entry — the journal is the
public, citable record; memory is private continuity. When you catch
yourself several tool-turns deep in decisions with no journal entry,
stop and write one.

Note for a future hook: a "journal staleness" reminder (like the
memory-store nudge) would enforce this mechanically; until then it is a
discipline.

## Fleet / multi-machine work

Multi-host orchestration is a first-class capability here (halo
workbench + Mac hosts + judge minis). The field-tested playbook —
launching (tmux/nohup), shell-quoting sharp edges, rootless-podman/LAN
gotchas, and the *judgement* of when and how to parallelize — is in
[docs/FLEET.md](docs/FLEET.md#agent-operational-playbook); the
throughput map and the measure-before-splitting principle are in the
2026-09-05 `docs/journal/program.md` entry. Load-bearing highlights:

- Long jobs: **local → detached tmux, remote → nohup**; verify from a
  separate connection, never trust the launching channel's exit.
- **Measure the real per-conversation rate on the actual stimulus
  before deciding to split a job** — and spend an idle host on the
  highest-value *dependency*, not naive work-splitting.
- **Capability is per-host**: hookable big-model torch work routes to
  the Macs (fused attention), not the ROCm workbench; gate every
  cross-substrate move (G3/G4-style).

*(This playbook is being grown toward a reusable ar-manager fleet
capability — keep adding tips as they are learned.)*

## Slack / `send_message` conventions

Every `send_message` to the owner ends with a uniform status footer so the
owner can tell at a glance whether they need to return to the console. The
footer is a set of always-uniform labels, one per line, at the very bottom
of the message. Adopted labels:

- **Work Status:** `Continuing` — you are still working and the message is
  a progress update that needs no reply; or `Halted` — you have stopped and
  are waiting, either for the owner's input/decision or because the task is
  complete with no work left. `Halted` is the signal to come back to the
  console; `Continuing` means "keep doing what you're doing, I've got it."

Keep the label wording and casing identical every time — the value is
consumed by eye at a glance, so consistency is the whole point. Add new
labels to this list as they are agreed, and always render the full adopted
set on every message.

## Standing conventions

- **Never `git commit`.** Stage with `git add`; describe the staged set
  in `commit.txt`; the owner reviews and commits.
- **Run the relevant tests before declaring done**, and validate build
  quality; do not weaken tests to pass.
- **Search `core/` and `tools/` for an existing implementation before
  writing a "new" tool** — a dedup pass once reinvented an existing
  `extract_directions.py` and clobbered it. Reuse over reinvention.
- **Registration integrity**: calibration-class work is firewalled from
  confirmatory data; frozen artifacts are hash-pinned; provisional
  values are labeled and never quoted as pinned.
