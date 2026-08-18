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
