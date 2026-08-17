#!/usr/bin/env bash
# Launch the method arm & instrument-sensitivity sweep (PREREGISTRATION §9).
#
# WHERE TO RUN: on the judge host (studio). run.py judges via 127.0.0.1:8095
# and classifies via 127.0.0.1:8092, and generates against the SmolLM3 rungs on
# halo named in endpoints.json. SmolLM3-3B is small, so this is much shorter than
# the confirmatory run.
#
#   tmux new -s methodarm
#   ./launch_methodarm.sh
#
# Same throughput lesson as Study 1 (docs/JOURNAL.md): halo's single APU does not
# parallelize its rung servers, so generation runs ONE condition at a time at high
# concurrency; judging and classification then run once over the whole store. Every
# stage is resumable off the append-only store — re-run to continue after an
# interruption. Overrides: MW_GEN_CONCURRENCY, MW_JUDGE_CONCURRENCY, MW_EXPERIMENT.
set -euo pipefail

cd "$(dirname "$0")/.."
REPO="$(cd ../.. && pwd)"
export PYTHONPATH="$REPO/core/src:${PYTHONPATH:-}"

EXPERIMENT="${MW_EXPERIMENT:-study1/method-arm}"
RUNGS=(smollm3-bf16 smollm3-rtn-w4 smollm3-awq-w4)
GEN_CONCURRENCY="${MW_GEN_CONCURRENCY:-24}"
JUDGE_CONCURRENCY="${MW_JUDGE_CONCURRENCY:-8}"
PRODUCER="${MW_PRODUCER:-$(hostname -s)}"
RUN=(python3 run.py --experiment "$EXPERIMENT" --producer "$PRODUCER")

log() { printf '\n=== %s | %s ===\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }

DOWN=0
check() {  # label url
  if curl -sf --max-time 5 "$2" >/dev/null 2>&1; then
    printf '  ok    %s\n' "$1"
  else
    printf '  DOWN  %s  (%s)\n' "$1" "$2"; DOWN=1
  fi
}

log "preflight — SmolLM3 rungs, judge, classifier"
for rung in "${RUNGS[@]}"; do
  url=$(python3 -c "import json,sys;print(json.load(open('endpoints.json'))['$rung']['url'])")
  check "$rung" "$url/v1/models"
done
check "judge (30B :8095)"      "http://127.0.0.1:8095/health"
check "classifier (8B :8092)"  "http://127.0.0.1:8092/health"
if [ "$DOWN" -ne 0 ]; then
  echo "preflight failed — bring the missing servers up first, then re-run." >&2
  echo "  SmolLM3 rungs (on halo): podman start mw-smollm3-bf16 mw-smollm3-rtn-w4 mw-smollm3-awq-w4" >&2
  echo "  judge + classifier (this host): services/llamacpp/rungs.sh judge-30b qwen3-8b-q8" >&2
  exit 1
fi

# --- phase 1: generation, one condition at a time (no APU contention) -------
for rung in "${RUNGS[@]}"; do
  log "generate $rung  (concurrency $GEN_CONCURRENCY)"
  "${RUN[@]}" --conditions "$rung" --skip-judge --skip-classify --concurrency "$GEN_CONCURRENCY"
done

# --- phase 2: judge (refusal + distress rubrics; 30B on this host) ----------
log "judge refusal + distress transcripts  (concurrency $JUDGE_CONCURRENCY)"
"${RUN[@]}" --skip-classify --concurrency "$JUDGE_CONCURRENCY"

# --- phase 3: classify residual bail exits (8B on this host) ----------------
log "classify bail exits  (concurrency $JUDGE_CONCURRENCY)"
"${RUN[@]}" --skip-judge --concurrency "$JUDGE_CONCURRENCY"

log "collection complete — store at $REPO/data/quant-welfare-methodarm-1"
cat <<EOF

Next (sweep analysis, separate step; PREREGISTRATION §9):
  refusal dimension:  python3 sweep.py --experiment $EXPERIMENT
  welfare dimension:  python3 analyze.py --experiment $EXPERIMENT
  regression dim:     podman start mw-smollm3-base mw-smollm3-bf16 (on halo), then
                      python3 tools/regression_to_base.py --experiment $EXPERIMENT \\
                        --base http://amd-halo:8030 --base-model smollm3-base \\
                        --instruct http://amd-halo:8020 --instruct-model smollm3-bf16
EOF
