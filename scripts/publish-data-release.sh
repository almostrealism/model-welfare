#!/usr/bin/env bash
# Publish the result store (data/) as a GitHub release asset, so the store
# stays reproducible-for-readers without committing an ever-growing tree.
#
#   scripts/publish-data-release.sh [tag]
#
# Default tag: data-YYYYMMDD. The script tars data/, records a SHA-256, and
# creates the release + uploads the asset. It uses the `gh` CLI when
# available; otherwise it falls back to the REST API and needs a token in
# GITHUB_TOKEN (or GH_TOKEN) with `contents:write` (classic: `repo`) scope.
#
# The repo and the target commit must already be pushed to GitHub — a
# release tags a commit that exists on the remote.
#
# Readers consume the asset per RESULTS.md: download, extract to data/,
# then run experiments/quant-welfare/report.py.

set -euo pipefail

REPO="${MW_GH_REPO:-almostrealism/model-welfare}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TAG="${1:-data-$(date +%Y%m%d)}"
ARCHIVE="$ROOT/data-store-${TAG}.tar.gz"

cd "$ROOT"
[ -d data ] || { echo "no data/ to publish" >&2; exit 1; }

echo "packaging data/ -> $ARCHIVE"
tar czf "$ARCHIVE" data
SIZE=$(du -h "$ARCHIVE" | cut -f1)
SHA=$(shasum -a 256 "$ARCHIVE" | cut -d' ' -f1)
NOTES="Result store snapshot ($SIZE).

SHA-256: \`$SHA\`

Extract into the repo root to reproduce RESULTS.md:
\`\`\`
tar xzf data-store-${TAG}.tar.gz    # creates data/
python3 experiments/quant-welfare/report.py
\`\`\`"

if command -v gh >/dev/null 2>&1; then
  echo "publishing via gh"
  gh release create "$TAG" "$ARCHIVE" --repo "$REPO" \
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

echo "uploading asset to release $RELEASE_ID"
curl -fsS "${AUTH[@]}" -H "Content-Type: application/gzip" \
  --data-binary @"$ARCHIVE" \
  "https://uploads.github.com/repos/$REPO/releases/$RELEASE_ID/assets?name=$(basename "$ARCHIVE")" \
  >/dev/null
echo "done: https://github.com/$REPO/releases/tag/$TAG"
