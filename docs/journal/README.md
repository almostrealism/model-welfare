# The journal series — organization from Study 3 onward

`docs/JOURNAL.md` is the program journal for the Study 1 and Study 2 era
and **closes to new entries at Study 2 close** (its final entry will say
so and point here). It is never edited, moved, or split: registrations
and posts cite its entries by date, the freeze tests pin digests it
records in prose, and the append-only rule is the integrity model — a
retroactive split would break every citation.

From Study 3 onward, entries land in this directory:

- **`study<N>-<slug>.md`** (e.g. `study3-steering.md`) — one file per
  study, opened at the study's first design entry and closed at its
  results entry. Everything a study's registration or results post would
  cite lives in that study's file: design decisions, pre-commitments,
  calibration freezes and amendments, collection milestones, the
  analysis-run record.
- **`program.md`** — cross-study entries: infrastructure (fleet, CI,
  runners, serving), instrument findings that outlive a study
  (cross-machine agreement, judge behavior), program-level policy and
  amendment decisions, and study-boundary handoffs.

Placement rule: *file under the study whose registration would cite it;
if no single study's registration would, it is program-level.* When an
entry genuinely concerns two homes, it lives in one and the other gets a
dated one-line pointer — never a copy.

Conventions carried over unchanged from `docs/JOURNAL.md`:

- **Append-only, newest first, dated headers.** Wrong entries are
  corrected by later entries, never edited.
- **Pre-commitments must predate the work they govern** in the public
  history — the property registrations lean on.
- Hash pins recorded in prose here are independently pinned by tests
  (the FREEZE pattern), so neither record can be silently regenerated.

Citation form from registrations and posts: name the file and the dated
header (e.g. "docs/journal/study3-steering.md, 2026-09-02 entry"), the
same way posts 1–4 cite `docs/JOURNAL.md` entries by date.
