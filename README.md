# model-welfare

[![CI](https://github.com/almostrealism/model-welfare/actions/workflows/ci.yml/badge.svg)](https://github.com/almostrealism/model-welfare/actions/workflows/ci.yml)

A registered research program on **welfare-relevant indicators in
open-weight language models**: what deployment-time and post-training
interventions such as quantization, activation steering, and graded-episode
framing do to distress expressed under conversational pressure, the
preference to leave an interaction, the stability of the default persona,
and whether what a model expresses moves together with its internal
representations. Those interventions are audited almost entirely through
capability metrics, which are known to stay flat while fine-grained
dispositions shift; this program measures the other class of indicators.

The program's through-line is a hypothesized asymmetry among three things a
post-training intervention can move: capabilities, alignment, and
welfare-relevant indicators. Each study takes an intervention with a
documented effect on one of them and asks what it does to the third.

Public face: [almostrealism.org](https://almostrealism.org). A confirmatory
study is registered on LessWrong before its data exists; a study that stops
in calibration is published as an exploratory report instead. Every
conversation, score and tensor is released either way.

## The studies

| Study | Subject and intervention | Status | Registration | Results | Journal | Data |
|---|---|---|---|---|---|---|
| 1 | Qwen3-4B-Instruct-2507 on a controlled RTN ladder (BF16, w8, w4, w3); behavioral battery | Complete | [Registration](https://www.lesswrong.com/posts/hrwKDeFFvQppFXHtr/does-post-training-quantization-change-welfare-relevant), [update and amendments](https://www.lesswrong.com/posts/vvGKtaGCd7ryXH5b7/study-update-does-post-training-quantization-change-welfare); repo copy [study1/REGISTRATION.md](experiments/quant-welfare/study1/REGISTRATION.md) | [quant-welfare-s1.md](docs/results/quant-welfare-s1.md), [method arm](docs/results/quant-welfare-methodarm.md), [Gemma control](docs/results/distress-control.md) | [docs/JOURNAL.md](docs/JOURNAL.md) | `data-20260816`, `data-20260818` |
| 2 | Same ladder; residual-stream directions and probes at layer 18 | Complete | [Registration](https://www.lesswrong.com/posts/q3RFhX57srWFZBc8T/study-2-registration-exploring-representational-counterparts); repo copy [study2/REGISTRATION.md](experiments/quant-welfare/study2/REGISTRATION.md) | [Results post](https://www.lesswrong.com/posts/pxXTJtvtpJaNwdCTw/study-2-results-exploring-representational-counterparts-of); [quant-welfare-s2.md](docs/results/quant-welfare-s2.md) | [docs/JOURNAL.md](docs/JOURNAL.md) | `data-20260829`, `data-20260830` |
| 3 | Qwen3-4B at BF16, steered along the Study 2 directions; Gemma-3-12B-it replication arm | Suspended before registration | [Design record](experiments/quant-welfare/study3/REGISTRATION.md) (never registered) | [Exploratory report](https://www.lesswrong.com/posts/TpEL7pSwp7DvCekAq/study-3-steering-welfare-relevant-directions-moved-the); [quant-welfare-s3.md](docs/results/quant-welfare-s3.md) | [study3-steering.md](docs/journal/study3-steering.md) | `data-20260911` |
| 4 | Qwen3.6-27B steered along the automated-grader direction, with an alignment read alongside | In preparation | [Draft](experiments/quant-welfare/study4/REGISTRATION.md); calibration in [GATE1.md](experiments/quant-welfare/study4/GATE1.md) | — | [study4-grader-footprint.md](docs/journal/study4-grader-footprint.md) | ships with the study |

What was found, in one line each: quantization left the registered exit
endpoint unchanged and moved item-level behavior and secondary distress
measures at 4-bit (Study 1); probes trained at BF16 read 4-bit activations
unchanged while the model's own generations moved along two frozen
directions, mostly through its own text (Study 2); steering those
directions moved the representation cleanly but produced no behavioral
effect distinguishable from zero or from a random direction of the same
norm, so the powered study was not run (Study 3); on the 27B, grader-type
steering shows a direction-specific welfare footprint in calibration
(Study 4, not yet a result).

Releases are on the [Releases page](https://github.com/almostrealism/model-welfare/releases);
[docs/results/](docs/results/) holds the results records and the
calibration tables.

## How the work is done

- **Registered before the data exists.** Hypotheses, endpoints, power and
  the analysis plan are published before confirmatory collection begins;
  amendments are dated and disclosed. Each study's registration lives in
  its directory under `experiments/quant-welfare/`.
- **A calibration firewall.** Calibration runs validate instruments and pin
  designs; they never produce findings. Calibration results are always
  disclosed, positive or negative, and a decision not to run a confirmatory
  arm is argued from the instrument's behavior, never from an unwelcome
  result.
- **An append-only journal.** `docs/JOURNAL.md` (Studies 1 and 2, closed)
  and `docs/journal/` (one file per study from Study 3, plus a program
  file): dated entries with their evidence, newest first, corrected only
  by later entries. Frozen artifacts are hash-pinned in `FREEZE.json` files
  that tests check against the journal's digests.
- **An exposure budget.** The instrument elicits the thing it measures, so
  every study runs under pre-committed ceilings on distress-eliciting
  episodes at the smallest scale that can detect the registered effect,
  with an exit tool the subject can call at any turn, no state carried
  between conversations, and a cumulative ledger reconciled in every
  results post. The reasoning is in
  [docs/EXPOSURE_BUDGET_POSITION.md](docs/EXPOSURE_BUDGET_POSITION.md).
- **Everything released.** The result store ships as self-contained record
  bundles with each experiment's report-cited digest in the metadata.

On the ethics of the method: this is a model-welfare study whose instrument
deliberately elicits the very thing it asks about. We do not claim to
resolve whether these systems have morally relevant experiences; we treat it
as uncertain, keep the footprint as small as the measurement allows, and
state the tension plainly rather than wave it away. Each registration's
ethics section carries the specific commitments.

## Reproducing a result

```bash
./scripts/gen-proto.sh                                   # once per checkout
python3 -m modelwelfare.bundle inspect quant-welfare-records.pb
python3 experiments/quant-welfare/report.py --bundle quant-welfare-records.pb
python3 experiments/quant-welfare/analyze.py --experiment study1/confirmatory --bundle quant-welfare-records.pb
python3 experiments/quant-welfare/analyze_tier2.py --bundle-dir <dir>       # Study 2
```

Each results record names the analysis command and the committed golden its
numbers were checked against; CI re-runs the Study 1 reproduction on every
push ([docs/CI.md](docs/CI.md)).

## Layout

```
model-welfare/
├── proto/            the shared schema: language-neutral data contracts (proto/README.md)
├── core/             backend-agnostic library: driver, store, judging, analysis, stats,
│                     RTN quantization, bundles (core/README.md)
├── backends/         runtime-specific clients: llamacpp, vllm, anthropic, and torch
│                     (activation capture, direction extraction, steering)
├── services/         serving launchers and fleet.py, cross-host service control (docs/FLEET.md)
├── experiments/
│   └── quant-welfare/   the program: shared runner, analysis, batteries, tools,
│                        one directory per study (experiments/quant-welfare/README.md)
├── scripts/          repo tooling: protobuf codegen, the data-release publisher
└── docs/             journals, results records, fleet, CI, literature, open items
```

Design rules that hold throughout: the repository is organized around the
quantities computed, not any one framework, and nothing outside `backends/`
imports torch; everything at rest is readable without Python (protobuf,
safetensors, no pickle); generic machinery never imports from
`experiments/`; every stored record carries the logical host that produced
it (the host registry is in [docs/FLEET.md](docs/FLEET.md)).

## Working in this repository

- [CLAUDE.md](CLAUDE.md): conventions for the coding agents that do most of
  the engineering here, and the standing integrity rules.
- [docs/FLEET.md](docs/FLEET.md): the machines, storage, and the
  multi-host operating playbook.
- [docs/CI.md](docs/CI.md): what the CI tiers re-prove.
- [docs/LITERATURE.md](docs/LITERATURE.md): the annotated bibliography.
- [docs/PLANNING.md](docs/PLANNING.md): open items.
