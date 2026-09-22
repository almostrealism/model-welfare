#!/usr/bin/env bash
# Spark-side bootstrap: build the studio-aligned steering environment on the
# DGX Spark (aarch64, CUDA 13) so the torch backend runs there with the same
# software versions the registered Mac runs use (torch 2.14.0, transformers
# 5.16.1, safetensors 0.8.0, numpy 2.4.6, accelerate 1.14.0 — the set the
# m4max `mw-venv-t214` alignment fixed on 2026-09-05), generate the proto
# bindings, and prove CUDA works with a bf16 matmul. Weights are not
# downloaded here: they are copied from the studio over the LAN.
#
# Run detached from the studio with a single SSH:
#   ssh agent1@192.168.8.185 'cd ~/repo/model-welfare && nohup bash services/spark_bootstrap.sh > ~/bootstrap.log 2>&1 &'
#
# Idempotent: the venv is reused and pip skips satisfied pins.

set -euo pipefail

VENV="$HOME/mw-venv-t214"
TORCH_INDEX="https://download.pytorch.org/whl/cu130"
PINS=(transformers==5.16.1 safetensors==0.8.0 numpy==2.4.6 accelerate==1.14.0 protobuf grpcio-tools)

echo "== host =="
uname -m; head -1 /etc/os-release; nvidia-smi --query-gpu=name,driver_version --format=csv,noheader

echo "== python venv =="
[ -d "$VENV" ] || python3 -m venv "$VENV"
source "$VENV/bin/activate"
python3 -m pip install --quiet --upgrade pip 2>&1 | tail -1

echo "== torch (CUDA 13 wheel index; pinned to the studio's version, else the newest there) =="
if ! python3 -m pip install --quiet torch==2.14.0 --index-url "$TORCH_INDEX" 2>&1 | tail -3; then
  echo "torch==2.14.0 is not on the cu130 index for this platform; installing the newest cu130 torch instead"
  python3 -m pip install --quiet torch --index-url "$TORCH_INDEX" 2>&1 | tail -3
fi

echo "== pinned stack =="
python3 -m pip install --quiet "${PINS[@]}" 2>&1 | tail -3

echo "== proto bindings =="
bash scripts/gen-proto.sh

echo "== versions =="
python3 - <<'PY'
import sys, torch, transformers, safetensors, numpy, google.protobuf, accelerate
print("python", sys.version.split()[0])
for m in (torch, transformers, safetensors, numpy, google.protobuf, accelerate):
    print(m.__name__, m.__version__)
PY

echo "== cuda check =="
python3 - <<'PY'
import time, torch
assert torch.cuda.is_available(), "torch.cuda.is_available() is False"
d = torch.device("cuda")
print("device", torch.cuda.get_device_name(0), "| cuda", torch.version.cuda, "| capability", torch.cuda.get_device_capability(0))
free, total = torch.cuda.mem_get_info()
print(f"memory free/total GB {free/1e9:.1f}/{total/1e9:.1f}")
a = torch.randn(8192, 8192, device=d, dtype=torch.bfloat16); b = torch.randn(8192, 8192, device=d, dtype=torch.bfloat16)
torch.cuda.synchronize(); t = time.time()
for _ in range(10): c = a @ b
torch.cuda.synchronize(); dt = time.time() - t
print(f"bf16 matmul 8192^3 x10: {dt:.2f}s = {10*2*8192**3/dt/1e12:.1f} TFLOP/s; finite={torch.isfinite(c).all().item()}")
print("sdpa flash available:", torch.backends.cuda.flash_sdp_enabled())
PY

echo "== backend import =="
cd "$(dirname "$0")/.."
PYTHONPATH=core/src:backends/torch/src python3 -c "import modelwelfare_torch.steer as s; print('steer.py imports:', s.__file__)"
echo "SPARK BOOTSTRAP COMPLETE"
