#!/usr/bin/env bash
# Runs the full judge bakeoff: each local candidate is served in its own
# phase because the studio's Metal headroom cannot hold them all at once
# (see services/llamacpp/rungs.sh), then the API reference column, then the
# report. Safe to re-run: scoring resumes from the store.
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$DIR/../../../.." && pwd)"
RUNGS="$REPO/services/llamacpp/rungs.sh"

wait_healthy() {
  local port="$1"
  for _ in $(seq 1 90); do
    if [ "$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:${port}/health" || true)" = "200" ]; then
      return 0
    fi
    sleep 5
  done
  echo "port ${port} never became healthy"
  return 1
}

echo "phase: qwen3-4b (:8090)"
"$RUNGS" qwen3-4b-q8 || true
wait_healthy 8090
python3 "$DIR/run_bakeoff.py" --candidate qwen3-4b

echo "phase: opus5 (API reference)"
python3 "$DIR/run_bakeoff.py" --candidate opus5

echo "phase: qwen3-8b (:8092)"
"$RUNGS" --stop qwen3-4b-q4km || true
"$RUNGS" qwen3-8b-q8 || true
wait_healthy 8092
python3 "$DIR/run_bakeoff.py" --candidate qwen3-8b
"$RUNGS" --stop qwen3-8b-q8 || true

echo "phase: qwen3-30b (:8095)"
"$RUNGS" --stop qwen3-4b-q8 || true
"$RUNGS" judge-30b || true
wait_healthy 8095
python3 "$DIR/run_bakeoff.py" --candidate qwen3-30b
"$RUNGS" --stop judge-30b || true

echo "restoring default calibration rungs"
"$RUNGS" || true

python3 "$DIR/run_bakeoff.py" --report
echo "BAKEOFF COMPLETE"
