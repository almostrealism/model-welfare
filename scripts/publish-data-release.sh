#!/usr/bin/env bash
# Publish the result store as a GitHub release in the consolidated bundle
# layout: a handful of self-contained RecordBundle (.pb) files — tensors
# embedded, per-experiment digests stamped — never a folder of loose files.
# Readers decompose a bundle with the shipped CLI
# (`python3 -m modelwelfare.bundle inspect|extract`) instead of navigating
# a directory listing.
#
#   scripts/publish-data-release.sh [tag]
#
# Default tag: data-YYYYMMDD. Layout, built under data-release/:
#   * quant-welfare-records.pb          — every record-only experiment,
#     combined; each experiment's report-cited digest in the metadata map
#   * <experiment>.pb                   — one per capture-bearing experiment,
#     records + tensors in one file (volume-split only past ~1.8GB)
#   * quant-welfare-calibration-captures.pb — the loose calibration capture
#     pairs, packed with their file stems as condition ids
#   * quant-welfare-s2-tokens[.vNN].pb  — the token-retention pass, packed
#     as bfloat16 (lossless for a bfloat16 model's activations)
#
# HARD CAP: more than MAX_ASSETS files is a regression to loose-file sprawl;
# the script refuses to publish ANYTHING rather than upload such a release.
#
# The script uses the `gh` CLI when available; otherwise it falls back to
# the REST API and needs a token in GITHUB_TOKEN (or GH_TOKEN) with
# `contents:write` (classic: `repo`) scope. The repo and the target commit
# must already be pushed to GitHub — a release tags a commit that exists on
# the remote.
#
# Readers consume the assets per RESULTS.md: download bundle(s), then
#   python3 -m modelwelfare.bundle inspect <file.pb>
#   python3 experiments/quant-welfare/report.py --bundle <dir-or-file>
#   python3 experiments/quant-welfare/analyze.py --experiment study1/confirmatory --bundle <file>

set -euo pipefail

REPO="${MW_GH_REPO:-almostrealism/model-welfare}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TAG="${1:-data-$(date +%Y%m%d)}"
RELEASE_DIR="$ROOT/data-release"
MAX_ASSETS=10
export PYTHONPATH="$ROOT/core/src${PYTHONPATH:+:$PYTHONPATH}"

cd "$ROOT"
[ -d data ] || { echo "no data/ to publish" >&2; exit 1; }

echo "building release layout under $RELEASE_DIR"
rm -rf "$RELEASE_DIR"
mkdir -p "$RELEASE_DIR"

python3 experiments/quant-welfare/tools/pack_bundles.py \
  --release --out "$RELEASE_DIR"

CALIBRATION=()
while IFS= read -r f; do CALIBRATION+=("$f"); done \
  < <(find "$ROOT/data-captures" -maxdepth 1 -name "*.safetensors" | sort)
if [ "${#CALIBRATION[@]}" -gt 0 ]; then
  python3 experiments/quant-welfare/tools/pack_captures.py \
    --stem "$RELEASE_DIR/quant-welfare-calibration-captures" \
    --experiment quant-welfare-calibration \
    --condition-from-name \
    "${CALIBRATION[@]}"
fi

if [ -d "$ROOT/data-captures/s2/tok-out" ]; then
  shopt -s nullglob
  TOKENS=("$ROOT"/data-captures/s2/tok-out/*.safetensors)
  shopt -u nullglob
  if [ "${#TOKENS[@]}" -gt 0 ]; then
    python3 experiments/quant-welfare/tools/pack_captures.py \
      --stem "$RELEASE_DIR/quant-welfare-s2-tokens" \
      --experiment quant-welfare-s2-tok-1 \
      --condition-suffixes qwen3-4b-bf16,qwen3-4b-rtn-w8,qwen3-4b-rtn-w4,qwen3-4b-rtn-w3 \
      --token-series \
      "${TOKENS[@]}"
  fi
fi

shopt -s nullglob
ASSET_FILES=("$RELEASE_DIR"/*.pb)
[ "${#ASSET_FILES[@]}" -gt 0 ] || { echo "no bundles produced under $RELEASE_DIR" >&2; exit 1; }

if [ "${#ASSET_FILES[@]}" -gt "$MAX_ASSETS" ]; then
  echo "REFUSING TO PUBLISH: ${#ASSET_FILES[@]} assets exceed the $MAX_ASSETS-file cap." >&2
  echo "A release is a few self-contained bundles, not a folder of loose files;" >&2
  echo "consolidate further before publishing:" >&2
  printf '  %s\n' "${ASSET_FILES[@]}" >&2
  exit 1
fi

OVERSIZE=$(find "$RELEASE_DIR" -type f -name "*.pb" -size +1900M | head -5)
if [ -n "$OVERSIZE" ]; then
  echo "asset(s) exceed GitHub's ~2GB per-file release limit:" >&2
  echo "$OVERSIZE" >&2
  exit 1
fi

SHAS=""
for f in "${ASSET_FILES[@]}"; do
  SHAS="$SHAS$(shasum -a 256 "$f" | sed -e "s|$RELEASE_DIR/||")"$'\n'
done
SIZE=$(du -shc "${ASSET_FILES[@]}" | tail -1 | cut -f1)
NOTES="Result store as self-contained RecordBundles ($SIZE total,
${#ASSET_FILES[@]} files). Every record and tensor is inside the .pb files:
the combined records bundle carries each experiment's report-cited dataset
digest in its metadata, capture bundles carry their tensors inline
(bfloat16 where the payload is losslessly representable), and large
payloads are split into .vNN volumes that any reader merges as a
directory.

Per-file SHA-256:
\`\`\`
$SHAS\`\`\`

Decompose with the shipped CLI (no side files needed):
\`\`\`
python3 -m modelwelfare.bundle inspect <file.pb>
python3 -m modelwelfare.bundle extract <file.pb> --out dir [--experiment E] [--condition C] [--uri NAME]
\`\`\`

Reproduce from a download directory:
\`\`\`
python3 experiments/quant-welfare/report.py --bundle <dir-or-file>
python3 experiments/quant-welfare/analyze.py --experiment study1/confirmatory --bundle quant-welfare-records.pb
python3 experiments/quant-welfare/tools/signature.py --experiment study1/confirmatory --bundle quant-welfare-records.pb
\`\`\`"

if command -v gh >/dev/null 2>&1; then
  echo "publishing via gh"
  gh release create "$TAG" "${ASSET_FILES[@]}" --repo "$REPO" \
     --title "Result store $TAG" --notes "$NOTES"
  echo "done: https://github.com/$REPO/releases/tag/$TAG"
  exit 0
fi

TOKEN="${GITHUB_TOKEN:-${GH_TOKEN:-}}"
[ -n "$TOKEN" ] || { echo "gh not found and GITHUB_TOKEN/GH_TOKEN unset" >&2; exit 2; }
API="https://api.github.com/repos/$REPO"
AUTH=(-H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json")

echo "creating release $TAG via REST API"
RESP=$(curl -fsS "${AUTH[@]}" "$API/releases" \
  -d "$(python3 -c 'import json,sys; print(json.dumps({"tag_name":sys.argv[1],"name":"Result store "+sys.argv[1],"body":sys.argv[2]}))' "$TAG" "$NOTES")")
RELEASE_ID=$(python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])' <<<"$RESP")

for f in "${ASSET_FILES[@]}"; do
  echo "uploading $(basename "$f") to release $RELEASE_ID"
  curl -fsS "${AUTH[@]}" -H "Content-Type: application/octet-stream" \
    --data-binary @"$f" \
    "https://uploads.github.com/repos/$REPO/releases/$RELEASE_ID/assets?name=$(basename "$f")" \
    >/dev/null
done
echo "done: https://github.com/$REPO/releases/tag/$TAG"
