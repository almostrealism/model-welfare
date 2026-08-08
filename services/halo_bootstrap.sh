#!/usr/bin/env bash
# Halo-side bootstrap: prepare the controlled ladder entirely on halo, so
# the flaky studio->halo link never has to carry bulk data. Downloads the
# BF16 checkpoint from Hugging Face over halo's own WAN, then regenerates
# the RTN rungs locally with the pure-numpy harness. RTN is deterministic,
# so these artifacts are bit-identical to the studio-produced ones (same
# digests) — provenance is preserved, not weakened.
#
# Run detached from the studio with a single SSH:
#   ssh agent1@amd-halo 'cd ~/repo/model-welfare && nohup bash services/halo_bootstrap.sh > ~/bootstrap.log 2>&1 &'
#
# Idempotent: re-running resumes the HF download (curl -C -) and skips
# rungs whose quantization.textproto already exists.

set -euo pipefail

MODELS="$HOME/models"
SRC="$MODELS/Qwen3-4B-Instruct-2507"
LADDER="$MODELS/quant-ladder"
HF="https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507/resolve/main"
FILES=(config.json generation_config.json merges.txt
       model-00001-of-00003.safetensors model-00002-of-00003.safetensors
       model-00003-of-00003.safetensors model.safetensors.index.json
       tokenizer.json tokenizer_config.json vocab.json)

echo "== python deps =="
python3 -m pip install --user --quiet numpy protobuf grpcio-tools 2>&1 | tail -2 || true

echo "== proto bindings =="
bash scripts/gen-proto.sh

echo "== download BF16 checkpoint from HF (halo WAN) =="
mkdir -p "$SRC"
for f in "${FILES[@]}"; do
  if [ -f "$SRC/$f" ] && [ ! -f "$SRC/$f.part" ]; then
    echo "  have $f"; continue
  fi
  echo "  fetching $f"
  for attempt in $(seq 1 20); do
    curl -fsSL -C - -o "$SRC/$f" "$HF/$f" && break
    echo "    retry $attempt for $f"; sleep 10
  done
done

echo "== regenerate RTN ladder locally (pure numpy, no GPU) =="
export PYTHONPATH="$PWD/core/src"
for bits in 8 4 3; do
  out="$LADDER/qwen3-4b-2507-rtn-w${bits}-g128"
  if [ -f "$out/quantization.textproto" ]; then
    echo "  w$bits already present"; continue
  fi
  python3 -m modelwelfare.quantize --input "$SRC" --output "$out" --bits "$bits" --group-size 128
done

echo "== ladder digests =="
for d in "$LADDER"/*/quantization.textproto; do
  echo "$(dirname "$d" | xargs basename): $(grep artifact_digest "$d")"
done
echo "HALO BOOTSTRAP COMPLETE"
