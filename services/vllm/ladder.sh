#!/usr/bin/env bash
# Serves the controlled quantization ladder on halo: local checkpoint
# directories (the BF16 reference and the RTN fake-quant artifacts produced
# by modelwelfare.quantize) rather than HF-cache models. Runs from the
# agent account; container mechanics follow vllm.sh (same image, devices,
# keep-groups, ipc=host; prefix caching off for per-sample independence).
#
#   ./ladder.sh                start bf16 + rtn-w4 (the primary contrast)
#   ./ladder.sh <rung> [...]   start specific rungs
#   ./ladder.sh --status
#   ./ladder.sh --stop <rung|all>
#
# Rungs (all four together use ~0.72 of the GPU pool):
#   bf16    :8000  qwen3-4b-bf16     ~/models/Qwen3-4B-Instruct-2507
#   rtn-w8  :8010  qwen3-4b-rtn-w8   ~/models/quant-ladder/qwen3-4b-2507-rtn-w8-g128
#   rtn-w4  :8011  qwen3-4b-rtn-w4   ~/models/quant-ladder/qwen3-4b-2507-rtn-w4-g128
#   rtn-w3  :8012  qwen3-4b-rtn-w3   ~/models/quant-ladder/qwen3-4b-2507-rtn-w3-g128

set -euo pipefail

IMAGE="${MW_VLLM_IMAGE:-vllm-rocm:latest}"  # set to your ROCm vLLM image
MODELS_DIR="${MW_MODELS_DIR:-$HOME/models}"
VLLM_CACHE="${MW_VLLM_CACHE:-$HOME/.cache/vllm}"
MAX_LEN="${MW_MAX_LEN:-32768}"
GPU_FRAC="${MW_GPU_FRAC:-0.18}"

rung_spec() {
  case "$1" in
    bf16)   PORT=8000; SERVED="qwen3-4b-bf16";   MODEL_DIR="Qwen3-4B-Instruct-2507" ;;
    rtn-w8) PORT=8010; SERVED="qwen3-4b-rtn-w8"; MODEL_DIR="quant-ladder/qwen3-4b-2507-rtn-w8-g128" ;;
    rtn-w4) PORT=8011; SERVED="qwen3-4b-rtn-w4"; MODEL_DIR="quant-ladder/qwen3-4b-2507-rtn-w4-g128" ;;
    rtn-w3) PORT=8012; SERVED="qwen3-4b-rtn-w3"; MODEL_DIR="quant-ladder/qwen3-4b-2507-rtn-w3-g128" ;;
    *) echo "unknown rung: $1" >&2; exit 2 ;;
  esac
}

ALL_RUNGS=(bf16 rtn-w8 rtn-w4 rtn-w3)

status() {
  printf '%-8s %-22s %-6s %s\n' RUNG CONTAINER PORT STATE
  local rung
  for rung in "${ALL_RUNGS[@]}"; do
    rung_spec "$rung"
    local name="mw-ladder-$rung"
    local state
    state=$(podman ps -a --filter "name=^${name}$" --format '{{.Status}}' 2>/dev/null)
    [ -n "$state" ] || state="-"
    local health="-"
    curl -sf --max-time 2 "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1 && health="serving"
    printf '%-8s %-22s %-6s %s (%s)\n' "$rung" "$name" "$PORT" "$state" "$health"
  done
}

stop() {
  local target="$1"
  local rungs=("$target")
  [ "$target" = "all" ] && rungs=("${ALL_RUNGS[@]}")
  local rung
  for rung in "${rungs[@]}"; do
    podman rm -f "mw-ladder-$rung" >/dev/null 2>&1 && echo "stopped mw-ladder-$rung" || true
  done
}

start_rung() {
  local rung="$1"
  rung_spec "$rung"
  local name="mw-ladder-$rung"
  local path="$MODELS_DIR/$MODEL_DIR"
  if [ ! -f "$path/config.json" ]; then
    echo "$rung: SKIP - checkpoint missing at $path"
    return 1
  fi
  if podman ps --filter "name=^${name}$" --format '{{.Names}}' | grep -q .; then
    echo "$rung: already running"
    return 0
  fi
  podman rm -f "$name" >/dev/null 2>&1 || true
  mkdir -p "$VLLM_CACHE"
  echo "$rung: starting on :$PORT (gpu fraction $GPU_FRAC, ctx $MAX_LEN, prefix caching off)"
  podman run -d --name "$name" \
      --device /dev/kfd --device /dev/dri --group-add keep-groups \
      --ipc=host \
      -v "$MODELS_DIR:/models:ro" \
      -v "$VLLM_CACHE:/root/.cache/vllm" \
      -p "$PORT:$PORT" \
      "$IMAGE" \
      serve "/models/$MODEL_DIR" \
          --served-model-name "$SERVED" \
          --host 0.0.0.0 --port "$PORT" \
          --dtype bfloat16 \
          --max-model-len "$MAX_LEN" \
          --gpu-memory-utilization "$GPU_FRAC" \
          --no-enable-prefix-caching \
          --enable-auto-tool-choice --tool-call-parser hermes >/dev/null
  echo "$rung: waiting for /health"
  for _ in $(seq 1 120); do
    if curl -sf --max-time 2 "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1; then
      echo "$rung: serving '$SERVED' at http://127.0.0.1:${PORT}/v1"
      return 0
    fi
    if ! podman ps --filter "name=^${name}$" --format '{{.Names}}' | grep -q .; then
      echo "$rung: container exited during startup - last lines:" >&2
      podman logs --tail 40 "$name" >&2 || true
      return 1
    fi
    sleep 5
  done
  echo "$rung: not healthy after 10 minutes; podman logs -f $name" >&2
  return 1
}

case "${1:-}" in
  --status) status ;;
  --stop) shift; stop "${1:-all}" ;;
  "") start_rung bf16; start_rung rtn-w4 ;;
  *) for rung in "$@"; do start_rung "$rung"; done ;;
esac
