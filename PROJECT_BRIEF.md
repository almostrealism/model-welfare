# Quantization × Model Welfare: Project Brief

> **Note for external readers:** this is the project's internal orientation
> document, written to keep the researchers and coding agents working on the
> repository aligned; it predates the public pre-registration and reads
> accordingly. The committed experimental design lives in
> [PREREGISTRATION.md](PREREGISTRATION.md); current status is summarized in
> the [README](README.md).

> Repo-level orientation document. Agents working on this project should read this before touching code. It is intentionally general in §1 (we expect to pivot within this frame), concrete in §2–3 (build targets and hardware), and load-bearing in §4 (do not re-analyze the cited papers from scratch; the annotations state what each one is for).

---

## 1. Draft Abstract

Open-weight language models are almost never deployed at the precision at which they were trained and aligned. Post-training quantization is applied to nearly every real-world deployment, yet its effects are audited almost exclusively through capability metrics (perplexity, benchmark accuracy) — metrics known to remain flat while fine-grained behavioral dispositions shift. Separately, a growing research program treats certain model behaviors and internal states as *welfare-relevant indicators*: expressions of distress, preferences to exit interactions, stability of the default "Assistant" persona, and the alignment between what a model reports about itself and what its internal representations show.

This project asks whether welfare-relevant indicators change with quantization — in **valence** (do indicators shift toward more negative / more distressed / more boundary-eroded states?) and in **stability** (do indicators become noisier, drift faster under conversational pressure, or decohere across samples?). We study a primary subject model across a ladder of controlled quantization conditions, alongside a second model whose role is study-specific. In the first registered study the subject is Qwen3-4B-Instruct-2507 and the second model is SmolLM3-3B — a documented quantization-fragile model serving as an end-to-end **pipeline-sensitivity control** (hypothesis H6), *not* a statistical-power arm; a statistical-power arm (Qwen3-30B) and a larger primary subject (MiniMax-M2) are deferred to later registered studies. The committed Study 1 roles are in [PREREGISTRATION.md](PREREGISTRATION.md) §3. Measurement proceeds at three tiers: (1) behavioral indicators elicited at the text interface (bail/exit preferences, distress expression under adversarial multi-turn pressure, preference consistency); (2) representational indicators computed from internal activations (position and drift along persona/assistant-axis directions, activation of distress-adjacent directions, transfer of linear probes trained at reference precision); and (3) dissociation analysis between tiers — testing whether compression changes what a model expresses without changing what it internally represents, or vice versa. Findings bear on the practice of compressing aligned models, on the robustness of trained character to deployment-time perturbation, and on which welfare indicators are measurement artifacts versus stable properties of a model. These three tiers frame the overall program; **Study 1 specifies and runs only the Tier-1 behavioral battery.** The Tier-2 (representational) and Tier-3 (dissociation) specifications are deferred, and hypothesis H5 is conditional on a Tier-2 feasibility gate (see PREREGISTRATION §2, H5).

*(Deliberately unspecified in this program-level brief, so we can pivot without editing this section: exact quantization methods and bit-widths, exact trait/indicator inventory, exact conversation batteries, judge models, and statistical design. For Study 1 these are now fixed — see [PREREGISTRATION.md](PREREGISTRATION.md), which is authoritative wherever it and this brief differ.)*

---

## 2. Tooling We Must Build (feasibility-first)

Goal of the first engineering phase: **prove we can run at least one credible experiment from each tier, end-to-end, on our own hardware**, using a small "development organism" model before pointing anything at MiniMax.

### 2.1 Tier 1 — Behavioral battery (endpoint-level)

Least novel code; mostly harness engineering. Needed components:

- **Inference abstraction layer.** One interface over: llama.cpp server (GGUF, Mac Studio), MLX (Macs), transformers/PyTorch (Ryzen box), and a rented-GPU endpoint. Everything downstream talks to this layer only, so subject models and precisions are swappable config, not code.
- **Conversation driver.** Multi-turn scripted interactions with: simulated-user turns, a tool/affordance injection mechanism (e.g., an "end conversation" tool for bail experiments), fixed seeds where the backend permits, and N-samples-per-item support (multi-sample stability is a headline metric; single greedy runs are explicitly insufficient per prior work).
- **Judge/scoring pipeline.** Small judge models (7–8B) running on the Mac minis scoring transcripts on defined rubrics (distress 0–10 scale, refusal taxonomy, persona-consistency rubric). Must log judge version + rubric hash with every score.
- **Item-level result store.** Store per-item, per-sample outcomes, not just aggregates — the bias literature shows the signal lives in item-level *transitions* (items that flip behavior across precision), which aggregates hide.

**Feasibility gate T1:** run the bail protocol and the multi-turn rejection/distress protocol on the dev organism at two precisions, produce item-level transition tables.

### 2.2 Tier 2 — Representational measurement (the real PyTorch; most of the engineering risk)

Critical constraint discovered in planning: **llama.cpp/GGUF gives us tokens, not tensors.** Tier 2 requires activations, so quantized subject models must run inside a hookable framework:

- transformers + bitsandbytes / GPTQ / AWQ / HQQ on the Ryzen box (ROCm or CPU), and/or
- **MLX** on the Macs (supports quantized inference *and* lets us read intermediate arrays; likely our main path for the big model).

This also improves the science: community GGUFs (e.g., Unsloth "Dynamic") upcast selected layers to 8-bit, confounding bit-width with per-layer policy. By quantizing ourselves inside PyTorch/MLX we make *quantization method* (RTN vs GPTQ vs AWQ, uniform vs dynamic) a controlled variable. Popular community GGUFs can remain as a Tier-1-only "ecosystem realism" arm.

Components to build:

- **Activation capture module.** Forward hooks (PyTorch) / array taps (MLX) at configurable layers; stream to disk in a compact format keyed by (model, precision, conversation, turn, token-range). Must work identically across full-precision and quantized paths.
- **Contrastive direction extraction.** Persona-vector-style pipeline: paired prompts that do/don't express a trait → mean activation difference → direction. Also an "assistant axis" variant (default-Assistant vs character-archetype contrast). Extracted **once at reference precision**, then frozen.
- **Projection + drift analytics.** Project any run's activations onto frozen directions; compute per-turn time series, baseline offsets between precisions (valence), and variance/drift statistics within and across conversations (stability).
- **Linear probe suite.** Train simple probes at reference precision (trait present/absent, distress high/low); evaluate probe accuracy on each quantized variant's activations. Probe-transfer degradation = the representational geometry itself moved.
- **Own quantization harness.** Scripted application of RTN / GPTQ / AWQ at several bit-widths to the dev organism and later the mid-size Qwen arm, producing our controlled ladder. (For MiniMax-scale, we will lean on MLX quantization modes plus selected community quants, documented as such.)

**Feasibility gate T2:** on the dev organism — extract ≥3 trait directions at reference precision, capture activations at 2+ quantized precisions, show projection time-series plots and a probe-transfer accuracy table. This gate is the go/no-go for the whole project.

### 2.3 Tier 3 — Dissociation analysis

Pure analysis code on top of T1+T2 stores: per-condition correlation of behavioral scores with representational measures; flagging of dissociation regimes (expression stable / representation drifting, and the reverse); dose-response fits across the precision ladder. Needs a shared experiment schema from day one so T1 and T2 outputs join on (model, precision, item, sample).

### 2.4 Development organism — options

Assumption (program-level): MiniMax M2-family is the primary subject; Qwen3 mid-size (~30B) is the stats/comparability arm. **Study 1 defers both** — its subject is the Qwen3-4B dev organism and its second model is SmolLM3-3B as the H6 pipeline-sensitivity control (see [PREREGISTRATION.md](PREREGISTRATION.md) §3). The dev organism exists to de-risk the pipeline cheaply (must run fast on the M4 Max, ideally on a Mac mini for CI-style smoke tests).

| Option | Pros | Cons |
|---|---|---|
| **Qwen3-4B / 8B** | Same family as our stats arm → pipeline transfers directly; strong MLX + HF + GPTQ/AWQ support; persona-vector literature used Qwen (published baselines to sanity-check our extraction code against) | "Everyone uses Qwen" — no novelty (fine for a dev organism); hybrid thinking mode adds a config axis we must pin down early |
| **Llama-3.1-8B** | The Assistant-Axis paper used Llama family → directly comparable axis extraction; best-supported architecture in every quant toolchain; enormous community knowledge for debugging | Older model; not in either of our real experiment arms, so some pipeline details won't transfer; license terms to note in repo |
| **Gemma-2/3 (4–12B)** | The distress-elicitation protocol ("Gemma Needs Help") was developed on Gemma → we can replicate their numbers as a Tier-1 correctness check before trusting our harness | Weaker MLX/quant tooling coverage historically; architecture (e.g., attention specifics) differs from both real arms |
| **OLMo-2-7B** | Fully open training data + checkpoints; the persona-pretraining paper used OLMo → uniquely good if we later want "when did this direction form" side-analyses | Least polished quant/tooling ecosystem; behaviorally blander assistant persona (weaker signal for persona measures) |
| **SmolLM3-3B** | Documented as *quantization-fragile* in the safety-factorial paper (attack success 34.5%→44.1% under INT4) → a known-positive control: if our pipeline can't detect change in SmolLM3, our pipeline is broken; tiny → runs on Mac minis | Too small/fragile to generalize from; only useful as a control, not a rehearsal of the real experiment |

**Recommended default (committed for Study 1, see PREREGISTRATION §3):** **Qwen3-4B-Instruct-2507 as primary dev organism** (small and fast enough for the full pipeline on the M4 Max and Mac-mini CI smoke tests) **plus SmolLM3-3B as the H6 sensitivity control** (cheap enough to keep permanently in CI). Use Gemma only if we adopt the distress protocol verbatim and want to replicate its published numbers as a harness check.

---

## 3. Hardware Inventory

| Machine | Specs | Role | Notes on capability |
|---|---|---|---|
| **Mac Studio, M1 Ultra, 192 GB unified** | ~800 GB/s memory bandwidth; 64-core GPU class; Metal/MLX | Primary big-model host | Comfortably serves MiniMax-M2-class (~230B-A10B MoE) at 4-bit with context to spare; 3-bit variants leave headroom for KV cache at long context. MoE activation pattern (~10B active) keeps token rates workable despite M1-generation compute. Runs llama.cpp (Tier 1) and MLX (Tier 2 activation taps on the big model). |
| **AMD Ryzen AI Max+ ("Halo"), 128 GB** | Strix Halo APU; LPDDR5x ~256 GB/s; RDNA3.5 iGPU; ROCm/Vulkan | PyTorch quantization workbench | Our main *hookable* PyTorch box: run transformers + bitsandbytes/GPTQ/AWQ/HQQ quantization of the dev organism and the ~30B Qwen arm, with forward hooks for activation capture. Bandwidth is the bottleneck (~⅓ of the Studio), so treat it as the place where we *control* quantization, not where we chase throughput. Expect some ROCm toolchain friction; budget setup time. |
| **MacBook Pro, M4 Max, 128 GB unified** | ~546 GB/s bandwidth; strong single-node perf | Development + MLX Tier 2 | Fastest iteration loop we own. Dev-organism work lives here; also fits MiniMax-M2 3-bit for pipeline rehearsal against the real subject, and 30B-class models at 4–8 bit easily. |
| **3× Mac mini, M4, 16 GB each** | ~120 GB/s; small unified memory | Orchestration + judging layer | Too small for subject models; ideal as the distributed services tier: 7–8B judge models (4-bit), embedding models for drift metrics, the experiment queue/scheduler, result store, and permanent SmolLM3 smoke tests. Three nodes → parallel judging keeps up with generation. |
| **Rented (as needed)** | e.g., 8×H100 / 4×H200 spot | Full-precision reference | MiniMax-M2 BF16 (~460 GB weights) needs a rental for reference-precision activation extraction and baseline evals. Cost-saver: treat Q8 as working reference locally and buy a short BF16 session only to validate Q8 ≈ BF16 on our measures. If they diverge, that is itself a result. Hosted BF16 *endpoints* cover Tier 1 only (no activations). |

---

## 4. Annotated References

Agents: use these as stated. Each entry says what we take from it and what we compare against.

### Quantization × behavior (our methodological foil)

- **"The Joint Effect of Quantization and Sampling Temperature on LLM Safety Alignment: A Factorial Analysis"** — arXiv:2606.29581.
  *Learn:* factorial design over precision × temperature; multi-judge scoring; multi-sample stability reporting. Key results: AWQ INT4 ≈ safety-neutral for 7/8 models; strongly-aligned models robust, weakly-aligned fragile; temperature matters more than precision; effects sub-additive. SmolLM3-3B is the fragile outlier (34.5%→44.1%).
  *Compare:* our temperature controls must match or bracket theirs; SmolLM3 is our positive control because of this paper.

- **"Quantization Undoes Alignment: Bias Emergence in Compressed LLMs Across Models and Precision Levels"** — arXiv:2605.15208.
  *Learn:* dose-response across bit-widths; **item-level transition analysis** (6–21% of unbiased items flip at 3-bit); "unknown"-selection (epistemic calibration) drops 17.4%; perplexity stays ~flat (<0.5% at 8-bit, <11% at 3-bit) while behavior shifts — our core motivating fact.
  *Compare:* replicate their perplexity-vs-behavior dissociation shape with welfare indicators in place of bias items.

- **"Preserving Fairness and Safety in Quantized LLMs Through Critical Weight Protection"** — arXiv:2601.12033.
  *Learn:* survey of mixed prior findings (their §2.2 is a ready-made related-work map); dynamic quantization more stable than static; larger models more consistent across quant methods; non-English degradation worse.
  *Compare:* if we test any multilingual condition, benchmark expectations come from here.

- **"Safety-Preserving PTQ via Contrastive Alignment Loss"** — arXiv:2511.07842.
  *Learn:* naïve PTQ (RTN/GPTQ, W4A4) can catastrophically drop safety scores; "token-flipping" regression toward pre-trained outputs on sensitive prompts — a mechanistically suggestive framing (quantization as partial *undoing* of post-training) that maps directly onto persona-selection theory.
  *Compare:* their W4A4 severity vs our weight-only ladder; if we see persona regression toward base-model character, cite their token-flipping observation.

### Persona measurement (our Tier-2 toolkit)

- **"Persona Vectors: Monitoring and Controlling Character Traits in Language Models"** — arXiv:2507.21509 (Anthropic; also anthropic.com/research/persona-vectors).
  *Learn:* the contrastive extraction recipe we implement; projection of prompt-token activations predicts subsequent trait expression; steering + preventative steering.
  *Compare:* validate our extraction code by reproducing their monitoring correlation on Qwen before trusting any MiniMax numbers.

- **"The Assistant Axis: Situating and Stabilizing the Default Persona of Language Models"** — arXiv:2601.10387.
  *Learn:* axis = mean difference between default-Assistant vector and character-archetype vectors; aligns with PC1 of persona space; **post-training only loosely tethers models to the Assistant region**; persona drift demonstrated in emotional-distress conversations (Llama 3.3 70B).
  *Compare:* our headline Tier-2 figure is their drift measure, with quantization level as the new independent variable.

- **"What Models Express, Suppress, and Resist: Auditing Open-Weight LLMs with Persona Vectors"** — arXiv:2607.13162.
  *Learn:* 53-trait inventory with natural / steerable / intractable labels — our menu for choosing which trait directions to extract.
  *Compare:* trait-level extraction difficulty; if a trait is "intractable" for them, don't build a welfare metric on it.

- **"Tracing Persona Vectors Through LLM Pretraining"** — arXiv:2605.13329.
  *Learn:* persona representations are stable features formed early in pretraining (OLMo-3, Apertus-8B) — supports treating directions as durable objects that quantization perturbs rather than artifacts of one checkpoint.
  *Compare:* only if we pivot to OLMo for formation-time side-analyses.

- **"Do LLMs Experience an Internal Polylogue? Investigating Reasoning through the Lens of Personas"** — arXiv:2605.09159.
  *Learn:* treat persona-vector alignments as *time series* over generation ("polylogue"); features predict correctness comparably to activation summaries.
  *Compare:* our per-turn/per-token projection time-series design mirrors this; reuse their framing for the stability analysis.

- **"Stable Personas: Dual-Assessment of Temporal Stability in LLM-Based Human Simulation"** — arXiv:2601.22812 (+ CHI EA '26 companion).
  *Learn:* dual assessment (self-report vs observer rating) explicitly to catch **dissociations between internal persona representation and expression**; report SDs/CIs; regression-toward-average-persona over time as a known drift mode.
  *Compare:* our Tier-3 dissociation framework generalizes their two-source design to three sources (self-report, observed behavior, activations).

- **"PTCBENCH: Benchmarking Contextual Stability of Personality Traits in LLM Systems"** — arXiv:2602.00016.
  *Learn:* existing benchmark structure for trait stability under context shifts; candidate off-the-shelf Tier-1 items.

### Welfare indicators (our Tier-1 protocols)

- **"The LLM Has Left The Chat: Evidence of Bail Preferences in Large Language Models"** (Anthropic Fellows work, mentored by Kyle Fish; paper + LessWrong companion post).
  *Learn:* the bail protocol (offer an exit tool, measure use); taxonomy of bail situations (role confusion, emotional intensity, bail-after-correction); WildChat continuations as stimuli; explicit call for persona-vector-adjacent internal-state elicitation — our project answers this call.
  *Compare:* bail-rate baselines per situation category; small-model role-confusion artifacts (Qwen-2.5-7B) as a known failure mode our judge rubric must distinguish from genuine preference.

- **"Gemma Needs Help: Investigating and Mitigating Emotional Instability in LLMs"** — arXiv:2603.10011.
  *Learn:* the distress-elicitation protocol (task → repeated rejection over turns; vary question type, feedback style, length); 0–10 frustration scale rubric — adopt or adapt directly.
  *Compare:* if we use Gemma as dev organism, replicate their prevalence numbers as a harness-correctness check.

- **Anthropic model welfare program** (announcement Apr 2025; TechCrunch summary) and **Claude Opus 4 / Sonnet 4 System Card, pp. 52–73** (first pre-deployment welfare assessment).
  *Learn:* what a welfare assessment battery looks like in practice (behavioral preferences, distress signals, task preferences); the end-conversation tool as a deployed welfare intervention.
  *Compare:* indicator categories; we mirror their categories where possible so results read natively to this audience.

- **"Emergent Introspective Awareness in Large Language Models"** (Lindsey, 2025, Anthropic).
  *Learn:* models show limited but genuine ability to detect concepts injected into their activations — grounds the idea that self-report and internal state can be *compared* rather than conflated.
  *Compare:* motivates Tier 3; full concept-injection replication is out of scope, correlation-based dissociation is our lightweight substitute.

- **Eleos AI research blog** (eleosai.org/research) — ongoing posts on self-knowledge/introspection (Mar 2026) and welfare interview methodology (May 2025).
  *Learn:* framing and methodology norms of the welfare-research audience we're writing for.

### Practical / model-availability

- **Unsloth model guides + HF repos** (unsloth.ai/docs; huggingface.co/unsloth) — MiniMax-M2.x GGUF sizes and third-party quant-quality benchmarks (Benjamin Marie's 750-prompt suite: UD-Q4_K_XL ≈ −6 pts, +22.8% errors vs original); Kimi K2.x sizing (1T params; ≥230–350 GB even at 1.8–2-bit; **released natively in INT4**, so no true full-precision anchor — reason we deprioritized Kimi); note that "Dynamic" GGUFs upcast selected layers to 8-bit (the confound driving our decision to quantize in-framework ourselves).
  *Compare:* their capability-degradation curves are the backdrop against which our welfare-indicator curves are plotted ("capabilities −X% while indicator moved Y").

---

*Document status: v0.1, planning-phase. §1 is stable; §2 gates are the current work queue; §4 grows as we add sources.*
