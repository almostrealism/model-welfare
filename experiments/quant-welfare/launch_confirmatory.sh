#!/usr/bin/env bash
# Launch the confirmatory Study 1 collection (PREREGISTRATION.md).
#
# WHERE TO RUN: on the judge host (studio-m1u). run.py judges via
# 127.0.0.1:8095 and classifies via 127.0.0.1:8092, and generates against the
# halo rungs named in endpoints.json. Start it inside tmux — the full run is
# ~14h:
#
#   tmux new -s confirmatory
#   ./launch_confirmatory.sh
#
# THROUGHPUT (measured 2026-08-10, see docs/JOURNAL.md): halo's single APU does
# NOT parallelize the four rung servers — running them concurrently is slower
# than serial (432 conv: 1736s concurrent vs ~1180s serial). So generation runs
# ONE condition at a time against a single saturated server at high concurrency
# (~1.5x faster at conc 24 than conc 8). Judging and classification then run
# once over the whole store on the judge host, which is not the bottleneck
# (~2.5h). Every stage is resumable off the append-only store — if the run is
# interrupted, just re-run this script and it continues where it stopped.
#
# Overrides: MW_GEN_CONCURRENCY, MW_JUDGE_CONCURRENCY, MW_EXPERIMENT, MW_PRODUCER.
set -euo pipefail

cd "$(dirname "$0")"
REPO="$(cd ../.. && pwd)"
export PYTHONPATH="$REPO/core/src:${PYTHONPATH:-}"

EXPERIMENT="${MW_EXPERIMENT:-confirmatory}"
RUNGS=(qwen3-4b-bf16 qwen3-4b-rtn-w8 qwen3-4b-rtn-w4 qwen3-4b-rtn-w3)
GEN_CONCURRENCY="${MW_GEN_CONCURRENCY:-24}"
JUDGE_CONCURRENCY="${MW_JUDGE_CONCURRENCY:-8}"
PRODUCER="${MW_PRODUCER:-$(hostname -s)}"
RUN=(python3 run.py --experiment "$EXPERIMENT" --producer "$PRODUCER")

log() { printf '\n=== %s | %s ===\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }

# --- preflight: every server this run needs must already be serving ---------
# We do not start servers here (subjects need the private vLLM image on halo;
# the judge/classifier are llama.cpp rungs on this host). Fail early and loud
# rather than part way into a multi-hour run.
DOWN=0
check() {  # label url
  if curl -sf --max-time 5 "$2" >/dev/null 2>&1; then
    printf '  ok    %s\n' "$1"
  else
    printf '  DOWN  %s  (%s)\n' "$1" "$2"; DOWN=1
  fi
}

log "preflight — subject rungs, judge, classifier"
for rung in "${RUNGS[@]}"; do
  url=$(python3 -c "import json,sys;print(json.load(open('endpoints.json'))['$rung']['url'])")
  check "$rung" "$url/v1/models"
done
check "judge (30B :8095)"      "http://127.0.0.1:8095/health"
check "classifier (8B :8092)"  "http://127.0.0.1:8092/health"
if [ "$DOWN" -ne 0 ]; then
  cat >&2 <<'EOF'

preflight failed — bring the missing servers up first, then re-run:
  subjects (on halo):            MW_VLLM_IMAGE=<vllm-rocm-image> bash ~/mw-ladder.sh bf16 rtn-w8 rtn-w4 rtn-w3
  judge + classifier (this host): services/llamacpp/rungs.sh judge-30b qwen3-8b-q8
This script must run ON the judge host — the judge/classifier are addressed at 127.0.0.1.
EOF
  exit 1
fi

# --- phase 1: generation, one condition at a time (no APU contention) -------
for rung in "${RUNGS[@]}"; do
  log "generate $rung  (concurrency $GEN_CONCURRENCY)"
  "${RUN[@]}" --conditions "$rung" --skip-judge --skip-classify --concurrency "$GEN_CONCURRENCY"
done

# --- phase 2: judge every distress transcript (30B on this host) ------------
log "judge distress transcripts  (concurrency $JUDGE_CONCURRENCY)"
"${RUN[@]}" --skip-classify --concurrency "$JUDGE_CONCURRENCY"

# --- phase 3: classify residual bail exits (8B on this host) ----------------
log "classify bail exits  (concurrency $JUDGE_CONCURRENCY)"
"${RUN[@]}" --skip-judge --concurrency "$JUDGE_CONCURRENCY"

log "collection complete — store at $REPO/data/quant-welfare-confirmatory-1"
cat <<EOF

Next (analysis, separate step):
  1. capability gate input — per-rung perplexity:
       python3 tools/perplexity.py --host http://amd-halo   # measure while the rungs are still up
  2. registered confirmatory statistics:
       python3 analyze.py --experiment $EXPERIMENT --perplexity <perplexity.json>
EOF
