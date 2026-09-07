# Program calendar — Study 2 through the MiniMax test

Drafted 2026-08-16 at the Study 1 → Study 2 pivot. Pacing assumption:
roughly **one study per week**, calibrated to Study 1's actual clock
(registration Aug 10 → confirmatory + method arm + validation + amendments +
update post by Aug 16). Weeks are Monday-anchored; ~10 weeks total, ending
before Nov 1. Buffers are real — Study 1 consumed one full week of
unplanned audit/amendment work, and this plan assumes that happens again
twice. Tooling-surface targets referenced below are inventoried in
[TOOL_GOALS.md](TOOL_GOALS.md).

| Week | Dates | Focus | Tooling surfaces landed |
|---|---|---|---|
| **1** | Aug 17–23 | **Study 2 registration + instrument build.** Finalize `study2/REGISTRATION.md`, publish as post #3. Build the torch **activation capture module**; run gate G1 (substrate equivalence, discharging the serving-equivalence commitment). | Activation capture (PyTorch, hooks) |
| **2** | Aug 24–30 | **Study 2 calibration.** **Contrastive direction extraction** at BF16 (distress, assistant-axis, refusal); **linear probe** training; layer freeze; gate G2; MDE pinned. MLX tap prototype for the cross-framework check. | Direction extraction; probe training loops |
| **3** | Aug 31–Sep 6 | **Study 2 confirmatory.** Capture Modes A/B across the ladder with **concurrent per-condition collection across hosts** (halo + M4 Max, digest-verified merge); Mode C; analysis; results doc. | Concurrent multi-host collection; probe-transfer analysis |
| **4** | Sep 7–13 | **Study 3 — dissociation + causal validation.** Tier-3 dissociation analysis (S2-H5 resolution across the joined stores); **steering** validation of the frozen directions (write-path hooks). Study 2/3 results post (#4). | Steering (causal interventions) |
| **5** | Sep 14–20 | **Study 4 registration + start — Qwen3-30B stats arm.** Tier 1 battery + Tier-2 capture at 30B. Quantize the 30B ladder first-party; multi-host collection is mandatory at this scale. | 30B quantization harness; multi-host at scale |
| **6** | Sep 21–27 | **Study 4 completion + buffer.** Analysis, results doc, post (#5). Slack absorbs Study 4 overrun; if genuinely idle: first-party **GPTQ** to complete the method arm. | (buffer; optional GPTQ) |
| **7** | Sep 28–Oct 4 | **Study 5 registration + pilot — MiniMax-M2.** Artifact strategy (MLX quantization modes + documented community quants); Studio serving; Tier 1 battery pilot; capability gate. | Big-model split serving |
| **8** | Oct 5–11 | **Study 5 Tier-2 capture.** MLX array taps on the Studio; Q8-as-working-reference validation; optional short rented BF16 session to validate Q8 ≈ BF16 on our measures. | MLX capture path; (optional) rented reference |
| **9** | Oct 12–18 | **Study 5 analysis + program synthesis.** MiniMax dissociation read; cross-subject synthesis (4B → 30B → M2 dose/size structure); final post draft (#6). | — |
| **10** | Oct 19–25 | **Buffer + final publication.** Data releases for every study; synthesis post published; repo closed out (results docs, bundles, TOOL_GOALS review). | — |

**Dependencies and risk notes**

- Weeks 1–3 are strictly ordered by Study 2's gates (G1 → calibration/G2 →
  confirmatory); a G2 failure converts week 3 into instrument iteration and
  pushes everything right — the two buffer allocations (wk 6, wk 10) cover
  one such slip.
- The MiniMax weeks (7–9) are the original motivating test and are protected:
  if the 30B arm threatens them, Study 4's Tier-2 capture drops to a reduced
  layer/item set before MiniMax slips.
- The rented-GPU reference (wk 8) is optional and budget-gated; local Q8 as
  working reference is the plan of record, and Q8-vs-BF16 divergence, if a
  rental happens, is reported as a result in its own right.

## Study 3 registration sprint — Sep 4 (Fri) → Sep 9 (Tue)

Appended 2026-09-04. Study 3's scope grew beyond the week-4 line above
(graded-episode framing arm, Gemma full replication, the stratified
subset + gradient hypotheses from the 09-04 audit), and the holiday
weekend is the push to registration. Machine truth this plan is built
around: **halo's APU torch path is the irreducible serial resource**
(steered generation ~42 s/conversation at 4B; ~11 min/sweep run) —
everything else parallelizes around it (vLLM arms on halo's GPU beside
torch; the 30B judge on studio, already up; m4max available as a second
judge instance when the confirmatory judging wave needs it; minis
offline). Keeping the APU queue fed is the schedule.

| When | APU (halo torch) | Beside it | Gate/freeze output |
|---|---|---|---|
| **Fri eve** | range-finder dose sweep (21 runs, done ~17:00) → queued: G3b torch α=0 pilot (200 conv), eval-awareness capture | G3b vLLM arm collecting + judging (studio); G3a **done** (report committed) | range-finder analysis → refined grid chosen; refined sweep launched overnight |
| **Sat** | refined Qwen sweep (registered grade, 8–12 h) → Gemma bring-up: throughput check, then Gemma direction-extraction captures | G3b analysis (`g3_behavioral`), thresholds drafted; Gemma vLLM rung up, stratifier pilot (20×10) + judging; frames + eval-awareness set **owner review** | G3a/G3b thresholds pinned from measured margins; Qwen α* + onsets pinned |
| **Sun** | Gemma dose range-finder → refined sweep (12B ≈ 2–2.5× slower) | Gemma probe training + G2-style gate; eval-awareness extraction + sign-consistency; framing pilot (vLLM) + prompt-induction cell; item-random-effect MDE tool | Gemma instrument gate verdict; Gemma bail-format decision |
| **Mon** | buffer: re-runs, Gemma refined-sweep completion | MDE pinning + power-floor pass; TBD closure (seeds, digests, coding rules); FREEZE artifacts + journal pre-commitments; Study 2 addendum draft | **calibration close: all registration material ready** |
| **Tue** | idle (pre-confirmatory) | registration post authored + published; Study 2 addendum appended | **registration of record** |

Post-registration (unchanged from the DESIGN §4 envelope): confirmatory
collection ≈ 5.5–6 days serialized APU (Qwen A+B ≈ 45 h, Gemma D ≈
80–85 h) + C arms on vLLM (~1 day, overlapped) + judging in parallel
(studio + m4max); analysis driver written during collection; results
≈ 2–2.5 weeks after registration. Risks: Gemma instrument-gate failure
(registered cut line), halo availability, judge throughput (mitigated
by the m4max second instance).

## Study 3 registration — pivot and revised ETA (appended 2026-09-06, Sat eve)

The original Sep 9 (Tue) registration slipped when calibration, right before
freeze, revealed the **steering intervention is behaviorally weak**: at the
quantization-matched dose the distress direction moves the representation but
not the behavior, and its frustration effect is *below* the matched-norm
random-direction envelope (both Qwen-4B and Gemma-3-12B). The
steering-sufficiency thesis (Q1/Q2) is in doubt; the framing arm (Q3) is
unaffected and is the arm with real signal (verifier frame −1.13). The freeze
is otherwise complete (thresholds, α*, digests, MDE, gates all pinned).

**In flight (Sat eve):** three probes to decide the registration's spine —
(a) assistant-axis steering pilot + matched random envelope on halo (the axis
was Study 2's more robust direction and was never behaviorally tested);
(b) a larger-α distress dose arm + matched random envelope on m4max;
(c) framing promoted toward the study's spine (no new compute — pilot exists).

**Revised ETA (branches by what (a)/(b) show):**

| Outcome | Registration spine | Registration ETA |
|---|---|---|
| (a) axis steering shows a real, direction-specific effect | steering rescued via the robust direction; re-scope arms A/B around it | ~Sep 10–11 (Wed–Thu) |
| (a)/(b) both null → framing-centric | Q3/framing becomes the confirmatory spine; steering reported as an honest null (a real contribution); re-scope hypotheses + endpoints | ~Sep 11–12 (Thu–Fri) |
| 4B-too-small concern forces (d) subject-switch | full re-extraction/re-calibration/re-gating on a larger subject | ~Sep 16–19 (following week) |

(d) is now a **live, owner-flagged future pivot** — the 4B model may be too
small for the most interesting effects — held pending the (a)/(b) reads.
Post-registration confirmatory envelope is unchanged in shape but its
*content* shifts with the spine (a framing-centric study is lighter on the
APU-serial steering time and heavier on vLLM framing cells).
