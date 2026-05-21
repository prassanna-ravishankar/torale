#!/usr/bin/env bash
#
# Diff response headers between current prod (nginx-served) and a preview
# Next.js build, for every public route. Catches CSP / cache / HSTS drift.
#
# Usage:
#   PROD_URL=https://webwhen.ai PREVIEW_URL=http://localhost:3000 \
#     ./scripts/headers-diff.sh
#
# Intended for run-before-cutover; not a CI gate. Some drift is expected
# (e.g. nginx Server header vs Next.js, X-Powered-By, ETag shapes). Eyeball
# the report and confirm only intentional deltas.

set -euo pipefail

PROD_URL="${PROD_URL:-https://webwhen.ai}"
PREVIEW_URL="${PREVIEW_URL:-http://localhost:3000}"

ROUTES=(
  /
  /changelog
  /terms
  /privacy
  /explore
  /compare/visualping-alternative
  /use-cases/steam-game-price-alerts
  /concepts/self-scheduling-agents
)

normalize() {
  # Strip ephemeral headers that always differ and aren't semantic.
  grep -vE '^(date|etag|x-request-id|cf-ray|server|age|x-powered-by|x-vercel|set-cookie):' \
    | sed -E 's/[[:space:]]+$//' \
    | sort
}

for route in "${ROUTES[@]}"; do
  echo "=== $route ==="
  prod=$(mktemp); preview=$(mktemp)
  curl -sSI -L --max-time 10 "$PROD_URL$route"    | tr -d '\r' | normalize > "$prod"    || true
  curl -sSI -L --max-time 10 "$PREVIEW_URL$route" | tr -d '\r' | normalize > "$preview" || true
  diff -u "$prod" "$preview" || true
  rm -f "$prod" "$preview"
  echo
done
