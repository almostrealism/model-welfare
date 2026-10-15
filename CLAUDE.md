# model-welfare — agent working notes

Conventions and recurring reminders for agents working this repo. The
scientific frame lives in `README.md` and the study registrations under
`experiments/quant-welfare/`; this file is the operational layer.

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
- **Calibration is not a registration loophole** (guardrail, 2026-09-07,
  Study 3 §7). Calibration validates instruments and pins design; it never
  produces findings that dodge public registration. (1) Calibration results
  are always disclosed, positive or negative. (2) A calibration probe that
  measures a registered confirmatory endpoint at meaningful scale cannot
  substitute for, or excuse skipping, the registered finding — report it as
  calibration with its limits stated. (3) A decision NOT to run a
  confirmatory arm is argued from the instrument's behavior (e.g. "the
  instrument produces no signal"), never from an unwelcome result, and the
  calibration data behind it is published. A program that runs many small
  probes will feel the pull to relabel an effectively-confirmatory probe as
  "calibration" to keep a null out of the record; that is the thing this
  guards against.

## Before linking a file from a public post, read its header

A post links a file at a pinned commit, and the first thing a reader sees
is the file's header comment. On 2026-10-15 the Study 4 registration post
was about to link `study3/directions/grader-type-contrast.textproto`,
whose first line still read "DRAFT — owner review required before the
calibration freeze" six weeks after the freeze; five more linked files
carried the same kind of stale line. The pre-publication review had
checked that every linked path existed and that the registration's own
status header was flipped, and had not opened the files. The rule: for
every file a post will link, read its header (and for a document, its
status line) and remove every "draft", "pending", "review required",
"proposed" or "TBD" that no longer holds. Grep is the first pass
(`grep -n -i -E 'draft|pending|review required|proposed|TBD'` over the
link list); reading the header is the second. A frozen file whose header
changes is re-frozen (`tools/freeze_manifest.py --study N --write`);
rubric digests hash the rubric message, not the file, so a comment edit
does not disturb recorded scores.

## Write for readers outside the program (a recurring risk)

Every public text this repo produces — registration posts, results
posts, the README, the registrations they link — is read by people who
have not been working on the project. The writer is the person least
able to see where the text assumes they have. The only comment on the
Study 3 post (Clément Dumas, 2026-09-16) is the concrete case:

> FWIW the TLDR seems to be written for someone that already know about
> the project. I don't know what the frozen direction are, what are the
> judged behavioral effect measured, "direction-specific welfare
> footprint" reads like a claudism that sounds impressive but is
> meaningless. That will probably make a lot of people just skip your
> post

Each phrase he named has a precise meaning inside the program and none
outside it. The same failure turned up in the Study 4 registration as
"frames never shown" — a judge-hygiene sentence inherited from Study 3,
where frames (context wrappers) were the manipulation; Study 4 has no
frames, so the sentence was referent-less and the owner could not tell
what it meant. Two kinds of error, both invisible to whoever has been
inside the work:

1. **Program vocabulary used as if it were English.** frozen, pinned,
   calibration-class, judged, footprint, direction-specific, envelope,
   matched-norm, battery, bail affordance, de-induction close,
   talker-side, substrate, golden run, firewall, admission read. Each
   needs a plain definition at first use or a plain replacement
   (`experiments/quant-welfare/study4/POST_OUTLINE.md` §0 has the table).
2. **Sentences carried over from an earlier study** whose referent no
   longer exists, or whose fact has changed (Study 4's "certified by G4a"
   survived after G4a failed).

**Rule: before any public text is called ready, run an outsider read,
and warn the owner about the owner's own sentences, not just the agent's.**
The owner has asked for this explicitly: when their draft presents
something in a way a reader outside the project will not follow, say so,
with the sentence quoted and a plain alternative — this is not nit-picking
of voice, which is unwelcome; it is the one review the writer cannot do
alone. The mechanical form of the check: hand the text, and nothing else,
to a fresh subagent with no project context and ask it to list every
term it cannot define from the text itself and every sentence it cannot
parse; a fresh agent lacks the context in the same way the reader does.
Then grep the text for every phrase that also appears in the previous
study's registration and confirm each still names something in this one.
The result is reported to the owner as a list of quoted sentences with
replacements; it is a blocking item on the publication checklist of each
post outline.
