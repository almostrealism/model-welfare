#!/usr/bin/env bash
# Publish the result store as a GitHub release, one RecordBundle per
# experiment — self-describing .pb files (condition and record kind carried by
# the data; report-cited data_digest stamped in metadata), so readers download
# only the experiments they want and the store stays reproducible-for-readers
# without committing an ever-growing tree.
#
#   scripts/publish-data-release.sh [tag]
#
# Default tag: data-YYYYMMDD. The script consolidates data/ into
# data-bundles/ via tools/pack_bundles.py (which refuses to drop any record
# stream), records per-file SHA-256s, and creates the release with every
# bundle as an asset. It uses the `gh` CLI when available; otherwise it falls
# back to the REST API and needs a token in GITHUB_TOKEN (or GH_TOKEN) with
# `contents:write` (classic: `repo`) scope.
#
# The repo and the target commit must already be pushed to GitHub — a
# release tags a commit that exists on the remote.
#
# Readers consume the assets per RESULTS.md: download bundle(s), then
#   python3 experiments/quant-welfare/report.py --bundle <dir-or-file>
#   python3 experiments/quant-welfare/analyze.py --experiment study1/confirmatory --bundle <file>
#   python3 experiments/quant-welfare/tools/signature.py --experiment study1/confirmatory --bundle <file>

set -euo pipefail

REPO="${MW_GH_REPO:-almostrealism/model-welfare}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TAG="${1:-data-$(date +%Y%m%d)}"
BUNDLES="$ROOT/data-bundles"

cd "$ROOT"
[ -d data ] || { echo "no data/ to publish" >&2; exit 1; }

echo "consolidating data/ -> $BUNDLES (one bundle per experiment)"
rm -rf "$BUNDLES"
python3 experiments/quant-welfare/tools/pack_bundles.py --out "$BUNDLES"

shopt -s nullglob
BUNDLE_FILES=("$BUNDLES"/*.pb)
[ "${#BUNDLE_FILES[@]}" -gt 0 ] || { echo "no bundles produced under $BUNDLES" >&2; exit 1; }

SHAS=""
for f in "${BUNDLE_FILES[@]}"; do
  SHAS="$SHAS$(shasum -a 256 "$f" | sed "s|$BUNDLES/||")"$'\n'
done
SIZE=$(du -sh "$BUNDLES" | cut -f1)
NOTES="Result store, one self-describing RecordBundle per experiment ($SIZE total).

Per-file SHA-256:
\`\`\`
$SHAS\`\`\`

Each bundle's metadata carries the content-based dataset digest the results
documents cite (layout- and order-independent; provenance excluded), so a
report's digest can be confirmed from the corresponding bundle alone.

Reproduce from a download directory:
\`\`\`
python3 experiments/quant-welfare/report.py --bundle <dir-or-file>
python3 experiments/quant-welfare/analyze.py --experiment study1/confirmatory --bundle quant-welfare-confirmatory-1.pb
python3 experiments/quant-welfare/tools/signature.py --experiment study1/confirmatory --bundle quant-welfare-confirmatory-1.pb
\`\`\`"

if command -v gh >/dev/null 2>&1; then
  echo "publishing via gh"
  gh release create "$TAG" "${BUNDLE_FILES[@]}" --repo "$REPO" \
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

for f in "${BUNDLE_FILES[@]}"; do
  echo "uploading $(basename "$f") to release $RELEASE_ID"
  curl -fsS "${AUTH[@]}" -H "Content-Type: application/octet-stream" \
    --data-binary @"$f" \
    "https://uploads.github.com/repos/$REPO/releases/$RELEASE_ID/assets?name=$(basename "$f")" \
    >/dev/null
done
echo "done: https://github.com/$REPO/releases/tag/$TAG"
