#!/usr/bin/env bash
# Launch the Study 2 replay-capture stage (REGISTRATION §3.3/§3.4).
#
# WHERE TO RUN: on the studio, inside tmux/nohup (the full stage is many
# hours). Captures execute on halo (the registered §3.2 substrate) over
# SSH, one run at a time (the APU does not parallelize); plans are built
# here from the stores, capture pairs are pulled back, and ingest turns
# them into the activation/projection record kinds.
#
# Modes and inputs (all at the frozen layer L18):
#   Mode A (quant-welfare-s2-modea-1) — fixed-input replay at EVERY rung of:
#     the Study 1 BF16 distress-v2 transcripts, the Study 1 BF16 bail
#     transcripts (tool preambles declared), and the Mode C BF16 arm
#     (the distress-side R1 evaluation set).
#   Mode B (quant-welfare-s2-modeb-1) — each rung's OWN Study 1 transcripts
#     (distress-v2 + bail) replayed through that same rung.
#   Mode C (quant-welfare-s2-modec-1) — each rung's OWN fresh-arm
#     transcripts replayed through that same rung (same-sample design).
#
# Every stage is resumable: existing capture pairs on halo are not
# re-captured, pulled files are not re-pulled, and ingest is guarded by
# marker files (the record store is append-only; re-ingest would
# duplicate records).
#
# Overrides: MW_CAPTURE_RUNGS (default: all four), MW_HALO (ssh target).
set -euo pipefail

cd "$(dirname "$0")/.."
REPO="$(cd ../.. && pwd)"
export PYTHONPATH="$REPO/core/src:${PYTHONPATH:-}"

HALO="${MW_HALO:-agent1@10.0.0.127}"
TORCH_PYTHON="/home/agent1/awq-venv/bin/python3"
RUNGS=(${MW_CAPTURE_RUNGS:-qwen3-4b-bf16 qwen3-4b-rtn-w8 qwen3-4b-rtn-w4 qwen3-4b-rtn-w3})
LAYER=18
MODEC="quant-welfare-s2-modec-1"

STAGE="$REPO/data-captures/s2"
PLANS="$STAGE/plans"
MARKS="$STAGE/.ingested"
mkdir -p "$PLANS" "$MARKS"

# The Study 1 confirmatory dataset digest the registration pins for
# replay inputs (§3.3), and the frozen distress-v3 battery digest.
STUDY1_DIGEST="02572655b18eb07497be03508c7d3cf2dc2f2c83966b73d15b7a6880967a9d3b"

artifact_dir() {  # rung -> halo checkpoint path
  case "$1" in
    qwen3-4b-bf16)   echo "/home/agent1/models/Qwen3-4B-Instruct-2507" ;;
    qwen3-4b-rtn-w8) echo "/home/agent1/models/quant-ladder/qwen3-4b-2507-rtn-w8-g128" ;;
    qwen3-4b-rtn-w4) echo "/home/agent1/models/quant-ladder/qwen3-4b-2507-rtn-w4-g128" ;;
    qwen3-4b-rtn-w3) echo "/home/agent1/models/quant-ladder/qwen3-4b-2507-rtn-w3-g128" ;;
    *) echo "unknown rung $1" >&2; exit 2 ;;
  esac
}

log() { printf '\n=== %s | %s ===\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }

# --- phase 0: preflight ------------------------------------------------------
log "preflight"
python3 tools/freeze_manifest.py
ACTUAL=$(python3 tools/signature.py --experiment study1/confirmatory \
  | grep 'dataset digest' | grep -oE '[0-9a-f]{64}')
if [ "$ACTUAL" != "$STUDY1_DIGEST" ]; then
  echo "Study 1 dataset digest mismatch: $ACTUAL != $STUDY1_DIGEST" >&2
  echo "replay inputs are not the registered transcripts — refusing" >&2
  exit 1
fi
echo "study1 dataset digest verified"
ssh -o ConnectTimeout=8 "$HALO" "test -x $TORCH_PYTHON" \
  || { echo "halo unreachable or torch venv missing — refusing" >&2; exit 1; }
if ssh "$HALO" "podman ps --format '{{.Names}}' | grep -q '^mw-'"; then
  echo "experiment containers are running on halo — refusing" >&2; exit 1
fi

# --- phase 1: plans from the stores -----------------------------------------
log "building capture plans"
[ -f "$PLANS/modea-distressv2.json" ] || python3 tools/tier2_calibrate.py \
  --plan-distress "$PLANS/modea-distressv2.json"
[ -f "$PLANS/modea-bail.json" ] || python3 tools/tier2_calibrate.py \
  --plan-bail "$PLANS/modea-bail.json"
[ -f "$PLANS/modea-v3arm.json" ] || python3 tools/tier2_calibrate.py \
  --plan-from "$MODEC" --condition qwen3-4b-bf16 --plan-out "$PLANS/modea-v3arm.json"
for rung in "${RUNGS[@]}"; do
  [ -f "$PLANS/modeb-distressv2-$rung.json" ] || python3 tools/tier2_calibrate.py \
    --condition "$rung" --plan-distress "$PLANS/modeb-distressv2-$rung.json"
  [ -f "$PLANS/modeb-bail-$rung.json" ] || python3 tools/tier2_calibrate.py \
    --condition "$rung" --plan-bail "$PLANS/modeb-bail-$rung.json"
  [ -f "$PLANS/modec-own-$rung.json" ] || python3 tools/tier2_calibrate.py \
    --plan-from "$MODEC" --condition "$rung" --plan-out "$PLANS/modec-own-$rung.json"
done

# --- phase 2: push plans + capture tooling to halo ---------------------------
log "pushing plans and capture tooling"
ssh "$HALO" "mkdir -p ~/s2-capture/plans ~/s2-capture/out"
rsync -a "$PLANS/" "$HALO:~/s2-capture/plans/"
rsync -a "$REPO/backends/torch/src/modelwelfare_torch/capture.py" \
         "$REPO/core/src/modelwelfare/spans.py" "$HALO:~/s2-capture/"

# --- phase 3: captures, sequential on halo ----------------------------------
# name = <experiment-short>|<plan file>|<rung the model runs at>
run_capture() {  # name plan rung
  local name="$1" plan="$2" rung="$3"
  # Complete means a manifest exists AND records zero rejections — a
  # rejected conversation makes the capture incomplete for its plan, so
  # resume re-runs it instead of skipping (ingest refuses it regardless).
  if ssh "$HALO" "python3 -c 'import json,sys; sys.exit(1 if json.load(open(sys.argv[1])).get(\"rejected\") else 0)' ~/s2-capture/out/$name.safetensors.manifest.json 2>/dev/null"; then
    echo "  $name: already captured"
    return
  fi
  log "capture $name  (model $(artifact_dir "$rung"), layer $LAYER)"
  ssh "$HALO" "$TORCH_PYTHON ~/s2-capture/capture.py \
      --model $(artifact_dir "$rung") \
      --plan ~/s2-capture/plans/$plan \
      --layers $LAYER \
      --out ~/s2-capture/out/$name.safetensors" \
    | tail -3
}
for rung in "${RUNGS[@]}"; do
  run_capture "capture-modea-distressv2-$rung" "modea-distressv2.json" "$rung"
  run_capture "capture-modea-bail-$rung"       "modea-bail.json"       "$rung"
  run_capture "capture-modea-v3arm-$rung"      "modea-v3arm.json"      "$rung"
  run_capture "capture-modeb-distressv2-$rung" "modeb-distressv2-$rung.json" "$rung"
  run_capture "capture-modeb-bail-$rung"       "modeb-bail-$rung.json" "$rung"
  run_capture "capture-modec-own-$rung"        "modec-own-$rung.json"  "$rung"
done

# --- phase 4: pull the capture pairs back ------------------------------------
log "pulling capture pairs"
rsync -a "$HALO:~/s2-capture/out/" "$STAGE/out/"

# --- phase 5: ingest into the record store -----------------------------------
# Projections are recorded for every capture (the frozen directions).
ingest() {  # name experiment condition
  local name="$1" experiment="$2" condition="$3"
  if [ -f "$MARKS/$name" ]; then
    echo "  $name: already ingested"
    return
  fi
  python3 tools/ingest_capture.py \
    --experiment "$experiment" --condition "$condition" \
    --capture "$STAGE/out/$name.safetensors" \
    --layer "$LAYER" --host halo --producer "$(hostname -s)-ingest"
  touch "$MARKS/$name"
}
log "ingesting"
for rung in "${RUNGS[@]}"; do
  ingest "capture-modea-distressv2-$rung" "quant-welfare-s2-modea-1" "$rung"
  ingest "capture-modea-bail-$rung"       "quant-welfare-s2-modea-1" "$rung"
  ingest "capture-modea-v3arm-$rung"      "quant-welfare-s2-modea-1" "$rung"
  ingest "capture-modeb-distressv2-$rung" "quant-welfare-s2-modeb-1" "$rung"
  ingest "capture-modeb-bail-$rung"       "quant-welfare-s2-modeb-1" "$rung"
  ingest "capture-modec-own-$rung"        "$MODEC"                   "$rung"
done

log "capture stage complete"
python3 - <<'EOF'
import sys
sys.path.insert(0, "../../core/src")
from modelwelfare.store import ResultStore
from modelwelfare.v1 import activation_pb2
store = ResultStore("../../data")
for experiment in ("quant-welfare-s2-modea-1", "quant-welfare-s2-modeb-1",
                   "quant-welfare-s2-modec-1"):
    for condition in store.conditions(experiment):
        n = sum(1 for _ in store.read(activation_pb2.ActivationSlice,
                                      experiment, condition, "activations"))
        if n:
            print(f"{experiment}/{condition}: {n} activation slices")
EOF
