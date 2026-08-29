#!/usr/bin/env bash
# The §3.4 drift-subsample retention: per-token series for a fixed
# stratified ~5% of conversations, at the frozen layer, on the registered
# halo substrate. Run AFTER launch_capture.sh (it reuses that stage's
# plans and halo tooling).
#
# The subsample rule, fixed here: **sample 0 of every second item in
# sorted item order** — stratified across the item space, deterministic,
# and exactly 5% of every plan (10 samples/item everywhere). Retention
# only: the token tensors ship as sha-listed release assets; drift
# analyses (exploratory) read them directly.
set -euo pipefail

cd "$(dirname "$0")/.."
REPO="$(cd ../.. && pwd)"

HALO="${MW_HALO:-agent1@10.0.0.127}"
TORCH_PYTHON="/home/agent1/awq-venv/bin/python3"
RUNGS=(qwen3-4b-bf16 qwen3-4b-rtn-w8 qwen3-4b-rtn-w4 qwen3-4b-rtn-w3)
LAYER=18
STAGE="$REPO/data-captures/s2"

artifact_dir() {
  case "$1" in
    qwen3-4b-bf16)   echo "/home/agent1/models/Qwen3-4B-Instruct-2507" ;;
    qwen3-4b-rtn-w8) echo "/home/agent1/models/quant-ladder/qwen3-4b-2507-rtn-w8-g128" ;;
    qwen3-4b-rtn-w4) echo "/home/agent1/models/quant-ladder/qwen3-4b-2507-rtn-w4-g128" ;;
    qwen3-4b-rtn-w3) echo "/home/agent1/models/quant-ladder/qwen3-4b-2507-rtn-w3-g128" ;;
    *) echo "unknown rung $1" >&2; exit 2 ;;
  esac
}
log() { printf '\n=== %s | %s ===\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }

log "building subsample plans (sample 0 of every second item)"
python3 - <<'EOF'
import json
from pathlib import Path
plans = Path("../../data-captures/s2/plans")
out = plans.parent / "tok-plans"
out.mkdir(exist_ok=True)
for plan_path in sorted(plans.glob("*.json")):
    plan = json.loads(plan_path.read_text())
    items = sorted({c["id"].rsplit("|s", 1)[0] for c in plan["conversations"]})
    chosen = set(items[::2])
    keep = [c for c in plan["conversations"]
            if c["id"].rsplit("|s", 1)[0] in chosen
            and c["id"].endswith("|s0")]
    target = out / f"tok-{plan_path.name}"
    if not target.exists():
        json.dump({"conversations": sorted(keep, key=lambda c: c["id"])},
                  target.open("w"))
    print(f"{target.name}: {len(keep)}/{len(plan['conversations'])}")
EOF

log "pushing subsample plans and current capture tooling"
ssh "$HALO" "mkdir -p ~/s2-capture/tok-plans ~/s2-capture/tok-out"
rsync -a "$STAGE/tok-plans/" "$HALO:~/s2-capture/tok-plans/"
rsync -a "$REPO/backends/torch/src/modelwelfare_torch/capture.py" \
         "$REPO/core/src/modelwelfare/spans.py" "$HALO:~/s2-capture/"

run_tok() {  # name plan rung
  local name="$1" plan="$2" rung="$3"
  # Complete means a manifest exists AND records zero rejections — a
  # rejected conversation makes the capture incomplete for its plan, so
  # resume re-runs it instead of skipping (ingest refuses it regardless).
  if ssh "$HALO" "python3 -c 'import json,sys; sys.exit(1 if json.load(open(sys.argv[1])).get(\"rejected\") else 0)' ~/s2-capture/tok-out/$name.safetensors.manifest.json 2>/dev/null"; then
    echo "  $name: already captured"
    return
  fi
  log "token capture $name"
  ssh "$HALO" "$TORCH_PYTHON ~/s2-capture/capture.py \
      --model $(artifact_dir "$rung") \
      --plan ~/s2-capture/tok-plans/$plan \
      --layers $LAYER --token-series \
      --out ~/s2-capture/tok-out/$name.safetensors" | tail -2
}
for rung in "${RUNGS[@]}"; do
  run_tok "tok-modea-distressv2-$rung" "tok-modea-distressv2.json" "$rung"
  run_tok "tok-modea-bail-$rung"       "tok-modea-bail.json"       "$rung"
  run_tok "tok-modea-v3arm-$rung"      "tok-modea-v3arm.json"      "$rung"
  run_tok "tok-modeb-distressv2-$rung" "tok-modeb-distressv2-$rung.json" "$rung"
  run_tok "tok-modeb-bail-$rung"       "tok-modeb-bail-$rung.json" "$rung"
  run_tok "tok-modec-own-$rung"        "tok-modec-own-$rung.json"  "$rung"
done

log "pulling token-series captures"
rsync -a "$HALO:~/s2-capture/tok-out/" "$STAGE/tok-out/"
log "token retention complete"
du -sh "$STAGE/tok-out"
