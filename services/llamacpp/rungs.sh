#!/usr/bin/env bash
# llama.cpp rung server(s) on the studio (or any Mac with llama-server).
#
# Serves GGUF rungs for instrument calibration and judging from the memory
# headroom beside the machine's shared services. Each rung gets its own port
# so any subset can serve at once. Concurrency: each rung is launched with
# parallel slots (-np) because llama-server serializes requests by default;
# the context flag is TOTAL context, split evenly across slots, so it is
# sized as per-slot-context x slots.
#
#   ./rungs.sh                    start the two 4B calibration rungs
#   ./rungs.sh <rung> [...]       start specific rungs (see table below)
#   ./rungs.sh --status           show what is listening
#   ./rungs.sh --stop <rung|all>  stop rung(s) started from this launcher
#
# Rungs:
#   qwen3-4b-q8    :8090  Qwen3-4B-Instruct-2507 Q8_0   (calibration reference)
#   qwen3-4b-q4km  :8091  Qwen3-4B-Instruct-2507 Q4_K_M (calibration low rung)
#   qwen3-8b-q8    :8092  Qwen3-8B Q8_0                 (cross-check)
#   qwen3-8b-q4km  :8093  Qwen3-8B Q4_K_M               (cross-check)
#   judge-30b      :8095  Qwen3-30B-A3B-Instruct-2507 Q4_K_M (judge candidate)
#
# Weights live in ~/models (see docs/PLANNING.md for provenance). Logs land
# in ~/.llama-logs like the shared launcher's.

set -euo pipefail

MODELS_DIR="${MW_MODELS_DIR:-$HOME/models}"
LOG_DIR="$HOME/.llama-logs"
PID_DIR="$HOME/.llama-logs/mw-pids"
mkdir -p "$LOG_DIR" "$PID_DIR"

# KV cache is quantized q8_0 (halves KV memory, like the shared launcher);
# without it, two rungs at 8 slots x 8k f16 KV plus the shared server's
# ~79 GB overflow the ~103 GB Metal budget and the second rung dies in
# warmup with kIOGPUCommandBufferCallbackErrorOutOfMemory.
SLOTS="${MW_SLOTS:-6}"
SLOT_CTX="${MW_SLOT_CTX:-8192}"
KV_TYPE="${MW_KV_TYPE:-q8_0}"

# HYBRID marks hybrid-thinking models, which must be pinned to non-thinking
# mode: unpinned reasoning inside tight client token budgets truncates
# replies (measured as a 25% judge format-failure rate in judge-bakeoff-1).
# The 2507-generation models are non-thinking releases and need no pin.
rung_config() {
  HYBRID=0
  case "$1" in
    qwen3-4b-q8)   PORT=8090; GGUF="Qwen_Qwen3-4B-Instruct-2507-Q8_0.gguf" ;;
    qwen3-4b-q4km) PORT=8091; GGUF="Qwen_Qwen3-4B-Instruct-2507-Q4_K_M.gguf" ;;
    qwen3-8b-q8)   PORT=8092; GGUF="Qwen3-8B-Q8_0.gguf"; HYBRID=1 ;;
    qwen3-8b-q4km) PORT=8093; GGUF="Qwen3-8B-Q4_K_M.gguf"; HYBRID=1 ;;
    judge-30b)     PORT=8095; GGUF="Qwen_Qwen3-30B-A3B-Instruct-2507-Q4_K_M.gguf" ;;
    *) echo "unknown rung: $1"; exit 1 ;;
  esac
}

port_in_use() {
  lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
}

start_rung() {
  local rung="$1"
  rung_config "$rung"
  local path="$MODELS_DIR/$GGUF"
  if [ ! -f "$path" ]; then
    echo "$rung: SKIP - model file missing: $path"
    return 1
  fi
  if port_in_use "$PORT"; then
    echo "$rung: SKIP - port $PORT already in use"
    return 0
  fi
  local ctx=$((SLOT_CTX * SLOTS))
  local extra=()
  if [ "$HYBRID" = "1" ]; then
    extra+=(--chat-template-kwargs '{"enable_thinking":false}')
  fi
  echo "$rung: starting on :$PORT (slots=$SLOTS, ctx=$ctx, hybrid_pin=$HYBRID, log: $LOG_DIR/mw-$rung.log)"
  nohup llama-server -m "$path" --host 127.0.0.1 --port "$PORT" \
      -ngl 99 -c "$ctx" -np "$SLOTS" --jinja -fa on \
      --cache-type-k "$KV_TYPE" --cache-type-v "$KV_TYPE" \
      ${extra[@]+"${extra[@]}"} \
      >"$LOG_DIR/mw-$rung.log" 2>&1 &
  echo "$!" > "$PID_DIR/$rung.pid"
  echo "$rung: pid=$!"
}

status() {
  local rung
  for rung in qwen3-4b-q8 qwen3-4b-q4km qwen3-8b-q8 qwen3-8b-q4km judge-30b; do
    rung_config "$rung"
    if port_in_use "$PORT"; then
      echo "$rung: LISTENING on :$PORT"
    else
      echo "$rung: down"
    fi
  done
}

stop_rung() {
  local rung="$1"
  local pidfile="$PID_DIR/$rung.pid"
  if [ ! -f "$pidfile" ]; then
    echo "$rung: no pid file (not started from this launcher)"
    return 0
  fi
  local pid
  pid=$(cat "$pidfile")
  if kill "$pid" 2>/dev/null; then
    echo "$rung: stopped (pid $pid)"
  else
    echo "$rung: pid $pid not running"
  fi
  rm -f "$pidfile"
}

case "${1:-}" in
  --status)
    status
    ;;
  --stop)
    shift
    if [ "${1:-}" = "all" ]; then
      for f in "$PID_DIR"/*.pid; do
        [ -f "$f" ] && stop_rung "$(basename "$f" .pid)"
      done
    else
      for rung in "$@"; do stop_rung "$rung"; done
    fi
    ;;
  "")
    start_rung qwen3-4b-q8
    start_rung qwen3-4b-q4km
    ;;
  *)
    for rung in "$@"; do start_rung "$rung"; done
    ;;
esac
