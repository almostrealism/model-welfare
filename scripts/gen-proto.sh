#!/usr/bin/env bash
# Generates Python protobuf bindings into core/src/modelwelfare/v1.
# Generated code is never committed; every checkout runs this before tests.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/core/src"

python3 -m grpc_tools.protoc \
  --proto_path="$ROOT/proto" \
  --python_out="$OUT" \
  --pyi_out="$OUT" \
  "$ROOT"/proto/modelwelfare/v1/*.proto

touch "$OUT/modelwelfare/v1/__init__.py"
echo "generated bindings in $OUT/modelwelfare/v1"
