# Study 3 — machine plan for confirmatory collection, and schedule status

Simplified operational report. Two questions: **(1) what each machine
does during the main (confirmatory) data collection**, and **(2) how the
current situation compares with the planned schedule** (the registration
sprint in [docs/CALENDAR.md](../../../docs/CALENDAR.md), Fri Sep 4 → Tue
Sep 9). Written 2026-09-06 (Sat).

---

## 1. Machine plan for confirmatory collection

The fleet's binding constraint is unchanged: **halo's APU torch path is
the irreducible serial resource** — steered generation cannot be
parallelized off it for the Qwen arms, so keeping the halo queue fed sets
the wall clock. Everything else parallelizes around it.

| Machine | Chip / mem | Confirmatory role | Notes |
|---|---|---|---|
| **halo** | Ryzen AI Max+, 128 GB | **Qwen arms A (steering) + B (cancellation)** on the APU torch path, serial (~45 h); **arm C** framing cells beside it on the GPU via vLLM (~1 day, overlapped, cheap) | The serial bottleneck. vLLM arms run on the GPU concurrently with torch on the APU. |
| **studio** | M1 Ultra, 128 GB | **Gemma arm D** (torch-MPS, ~197 s/conv) **and** the pinned **Qwen3-30B judge** (:8095) + Qwen3-8B exit classifier (:8092) | Dual duty: it is the primary arm-D host and the judge host. Judge load is interleaved with generation. |
| **m4max** | M4 Max, 128 GB | **Gemma arm D**, second host — but only under the host-constant rule below | Faster silicon, but NOT interchangeable with studio (see §1.1). Also a spare judge instance if judging backs up. |
| **mini-1..3** | M4, 16 GB | judges / queue / result-store / smoke tests | 16 GB caps them to the smaller judge/classifier GGUFs; useful to offload judging from studio during the confirmatory wave. |

### 1.1 The arm-D host rule (this is the load-bearing decision)

Arm D (Gemma-3-12B replication) is the one arm that can span two hosts
(studio + m4max), and the design already registered the safeguard:
**every within-endpoint contrast runs host-constant** — both cells of any
comparison (e.g. steered vs unsteered for one endpoint) are generated on
the *same* Mac; the two Macs parallelize by taking **different whole
contrasts**, never by splitting one (DESIGN §2.4, "conditions split
host-constant-within-condition per the Study 2 rule").

Gate **G4d** turned that prudent rule into an empirically required one:
on identical seeds/prompts/weights the two Macs' Gemma outputs diverge
**−0.72 on frustration (p 0.025)**, coherently across the welfare family
(m4max reads more distressed), with the mechanical family identical and
apparatus parity confirmed. So a contrast split across the two Macs would
confound host with condition by ~0.7 of a frustration point — exactly the
artifact the rule exists to prevent.

**What the aligned-stack probe adds (verdict in §3):** the G4d divergence
was measured across machines that had drifted apart on the whole ML stack
(torch 2.8 vs 2.14, transformers 4.57 vs 5.16, different `steer.py`, plus
macOS 15 vs 26 and M1 vs M4). The probe re-runs the highest-divergence
items on m4max with a stack aligned to studio (torch 2.14.0 / transformers
5.16.1 / repo `steer.py`), leaving only OS + silicon different. The result
decides which operating posture we adopt:

- **If alignment collapses the divergence** → the Macs are interchangeable
  once their stacks are pinned identical; arm D may use both hosts freely,
  and the fleet standing rule becomes "pin the ML stack, then hosts are
  fungible." Roughly halves arm-D wall clock (both Macs, any split).
- **If divergence persists** → it is OS/silicon and irreducible; the
  host-constant-within-contrast rule stands as the operating constraint.
  Arm D still uses both Macs (parallelizing by whole contrasts), just never
  splits a single contrast.

Either way arm D proceeds; the probe only sets how freely the two Macs may
be mixed.

---

## 2. Schedule status vs plan

Registration sprint target: **calibration closed Mon Sep 8, registration
of record Tue Sep 9.** Status as of Sat Sep 6 midday:

**Done / ahead:**

- Gates: G1 (Study 2 substrate), **G3a** and **G3b** (both PASS, thresholds
  pinned), **G4a** (teacher-forced, PASS), **G4b** (MPS↔vLLM behavioral
  parity, PASS), **G4d** measured (cross-Mac; fails as an *interchangeability*
  certificate but usable under the host rule).
- Gemma instrument gate run: directions PASS at L30/L36 (L30 frozen); the
  band probe fails informatively (high-elicitation degeneracy), disclosed.
- Arm C framing pilot complete + judged (manipulation check passes).
- Qwen dose sweep complete; eval-awareness and grader-type direction sets
  built; item-random-effect MDE tool built; stratified subset frozen.

**Remaining before registration (Sun–Mon work):**

- MDE pinning + power-floor pass (calibration variances now in hand).
- Freeze artifacts (Gemma directions at L30, seed blocks, digests, coding
  rules) + journal pre-commitments.
- Study 2 addendum draft (disclosure obligation, publishes with registration).
- Registration final pass (fold in the Gemma gate, arm C validation, the
  exit endpoint, the 4th frame, the G4 legs; close the TBD register).
- **Ratify the arm-D host rule** in light of the §3 probe verdict.

**Assessment: on track, trending slightly ahead on gates.** The gate
program (G3*/G4*) that the sprint was most exposed to is essentially
closed a day early; what remains is pinning/freezing/writing, which is
desk work with no hardware dependency and fits the Sun–Mon buffer. The
one schedule risk the calendar flagged — Gemma instrument-gate failure —
did not materialize as a blocker (directions pass; the probe fail is
disclosed, not disqualifying). No slip is projected against the Tue Sep 9
registration date.

**Post-registration collection envelope (unchanged):** ~5.5–6 days
serialized on the halo APU (Qwen A+B ≈ 45 h) + Gemma arm D on the Macs
(concurrent with halo, wall clock set by the host rule + §3 verdict) +
arm C on vLLM (~1 day, overlapped) + judging in parallel on studio/minis.

---

## 3. Aligned-stack probe — verdict

**Most of the divergence was software-stack drift, not hardware — but a
residual remains, and the probe is underpowered to call it zero.**

The two machines had drifted apart on the entire ML stack. What actually
generated each side:

| | studio subset | m4max (original) | m4max (aligned probe) |
|---|---|---|---|
| torch | 2.14.0 | **2.8.0** | 2.14.0 |
| transformers | 5.16.1 | **4.57.6** | 5.16.1 |
| `steer.py` | repo (442 ln) | **~/steer (447 ln)** | repo (442 ln) |
| macOS | 15.7.1 | 26.3.1 | 26.3.1 |
| silicon | M1 Ultra | M4 Max | M4 Max |

So the original G4d compared machines differing on **five** axes, not one.
The probe regenerated the 8 highest-divergence items on m4max with torch,
transformers, and `steer.py` pinned to studio's — leaving only **macOS +
silicon** different — and re-judged on the same 30B. Result on those 8
items (frustration, the primary endpoint):

- **Original divergence** (studio − old m4max): mean **−1.71**, paired
  permutation **p 0.033** (significant).
- **After aligning the stack** (studio − aligned m4max): mean **−0.67**,
  paired permutation **p 0.44** (not significant).

Aligning the software stack **more than halved the signed frustration
divergence and removed its significance** (~40 % of the magnitude
remains). tone_stability moved the same way, less far (+1.92 → +1.33, p
0.033 → 0.16). So a large share of the cross-Mac difference was
torch/transformers/`steer.py` drift — a fixable configuration problem, not
the hardware.

**Two honest caveats.** (1) A residual remains (~40 % on frustration, more
on tone_stability); it is consistent with the irreducible macOS/silicon
difference we cannot align in-box. (2) At **n = 8 items × 3 samples** the
equivalence test is underpowered — "no longer significant" is *not* proof
of equivalence, only that the large, significant gap has collapsed toward
noise. Per-item deltas at 3 samples are themselves noisy (one item's gap
widened after alignment); only the aggregate is interpretable.

### Recommendation

1. **Pin the ML stack across all arm-D hosts** (the `mw-venv-t214` stack:
   torch 2.14.0 / transformers 5.16.1 / accelerate 1.14.0 / repo
   `steer.py`), regardless of anything else. This is now built on m4max and
   should be the standard; it removed most of the measured divergence and
   costs nothing to keep.
2. **Keep the host-constant-within-contrast rule as the operating
   default.** It fully eliminates cross-host risk whether or not the
   residual is real, it is already in the registration (DESIGN §2.4), and
   it costs no statistical power — arm D still uses both Macs, parallelizing
   by whole contrasts. We do **not** need to relax it, so we accept it, now
   understanding it guards a small residual rather than the large gap G4d
   first showed.
3. **If we later want to split a single contrast across the two Macs** (to
   halve one contrast's wall clock), it would require a larger equivalence
   pilot on the aligned stacks (e.g. the full 20 items × ≥10 samples) to
   positively certify equivalence. Not needed for the current envelope; the
   whole-contrast split already parallelizes arm D across both hosts.

**Net:** we got the "why" — the machines had silently drifted apart on
software, that explains the bulk of the divergence, and the small residual
plus the free safety rule mean arm D proceeds on both Macs with confidence,
no schedule cost.
