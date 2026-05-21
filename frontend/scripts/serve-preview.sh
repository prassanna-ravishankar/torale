#!/usr/bin/env bash
#
# Start the Next.js standalone preview server — same entrypoint the prod
# image runs (`node .next/standalone/server.js`). Use this rather than
# `npm run start` / `next start`, which warn under output: 'standalone' and
# may diverge in middleware/headers behaviour.
#
# Prereq: `npm run build` must have produced .next/standalone.
#
# Usage:
#   ./scripts/serve-preview.sh          # foreground
#   ./scripts/serve-preview.sh &        # background (pid in $!)
#
# Env:
#   PORT       (default 3000)
#   HOSTNAME   (default 0.0.0.0)
# Plus all NEXT_PUBLIC_* needed at runtime — these supplement (don't
# replace) the values baked into the client bundle at build time.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SERVER="$ROOT/.next/standalone/server.js"

if [ ! -f "$SERVER" ]; then
  echo "ERROR: $SERVER missing. Run 'npm run build' first." >&2
  exit 1
fi

# The standalone bundle expects .next/static and public/ alongside its own
# server.js. The CI Dockerfile copies these explicitly; for local preview
# we mirror the layout here.
if [ ! -d "$ROOT/.next/standalone/.next/static" ]; then
  cp -R "$ROOT/.next/static" "$ROOT/.next/standalone/.next/static" 2>/dev/null || true
fi
if [ ! -d "$ROOT/.next/standalone/public" ] && [ -d "$ROOT/public" ]; then
  cp -R "$ROOT/public" "$ROOT/.next/standalone/public" 2>/dev/null || true
fi

cd "$ROOT/.next/standalone"
exec env HOSTNAME="${HOSTNAME:-0.0.0.0}" PORT="${PORT:-3000}" \
  NODE_ENV=production \
  NEXT_TELEMETRY_DISABLED=1 \
  node server.js
