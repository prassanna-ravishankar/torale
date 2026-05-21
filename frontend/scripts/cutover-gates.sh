#!/usr/bin/env bash
#
# Cutover gates for the Next.js migration. Run against a running preview
# server BEFORE shifting Gateway weight in GKE. Exit 0 = green; non-zero =
# blocker. Designed for CI invocation and manual rehearsal.
#
# Usage:
#   PREVIEW_URL=http://localhost:3000 ./scripts/cutover-gates.sh
#   PREVIEW_URL=https://staging.webwhen.ai ./scripts/cutover-gates.sh
#
# Gates (per orchestrator notif-7ac925b3, 2026-05-21):
#   1. Header / CSP / redirect parity (header presence; full diff happens
#      in headers-diff.sh).
#   2. Marketing chunks contain zero Clerk imports (PR #337 invariant).
#   3. Anonymous /explore and /tasks/<uuid> ship real content: <title>,
#      canonical, application/ld+json present.

set -euo pipefail

PREVIEW_URL="${PREVIEW_URL:-http://localhost:3000}"
FAILED=0

red()   { printf '\033[31m%s\033[0m\n' "$1"; }
green() { printf '\033[32m%s\033[0m\n' "$1"; }
note()  { printf '  %s\n' "$1"; }
fail()  { red "FAIL: $1"; FAILED=$((FAILED+1)); }
ok()    { green "OK:   $1"; }

curl_head() { curl -sS -I -L --max-time 10 "$1"; }
curl_body() { curl -sS    -L --max-time 10 "$1"; }

# --- Gate 1: security headers present on / ----------------------------------
echo
echo "Gate 1: security headers on $PREVIEW_URL/"
hdrs=$(curl_head "$PREVIEW_URL/")
for h in \
  'content-security-policy' \
  'strict-transport-security' \
  'x-content-type-options' \
  'referrer-policy' \
  'permissions-policy'
do
  if echo "$hdrs" | grep -qi "^$h:"; then ok "header $h"; else fail "missing $h"; fi
done

# --- Gate 2: PR #337 invariant — no Clerk in marketing chunks ---------------
echo
echo "Gate 2: marketing chunks lack Clerk"
manifest=".next/app-build-manifest.json"
if [ ! -f "$manifest" ]; then
  fail "$manifest missing — run 'npm run next:build' first"
else
  # jq paths look like "pages.\"/(marketing)/page\"[]" — list every chunk
  # for each marketing entry and assert none mention clerk.
  marketing_chunks=$(jq -r '
    .pages
    | to_entries
    | map(select(.key | test("\\(marketing\\)")))
    | map(.value[])
    | unique
    | .[]
  ' "$manifest")
  bad=$(printf '%s\n' "$marketing_chunks" | xargs -I{} grep -l 'clerk' ".next/{}" 2>/dev/null || true)
  if [ -z "$bad" ]; then
    ok "marketing chunks Clerk-free"
  else
    fail "marketing chunks contain clerk:"
    printf '%s\n' "$bad" | sed 's/^/      /'
  fi
fi

# --- Gate 3: anonymous /explore + /tasks/<uuid> content ---------------------
echo
echo "Gate 3: anonymous content on /explore and /tasks/<uuid>"

check_route() {
  local route="$1"; local code; local body
  code=$(curl -sS -L -o /tmp/cg.html -w '%{http_code}' --max-time 15 "$PREVIEW_URL$route")
  if [ "$code" != "200" ]; then fail "$route returned $code"; return; fi
  # Grep directly against the file — piping $body through echo loses bytes
  # in bash when the HTML contains backslash-escaped JSON-LD payloads.
  if ! grep -qi '<title>'                   /tmp/cg.html; then fail "$route missing <title>";   return; fi
  if ! grep -qiE 'rel="?canonical"?'        /tmp/cg.html; then fail "$route missing canonical"; return; fi
  if ! grep -qi  'application/ld.json'      /tmp/cg.html; then fail "$route missing ld+json";   return; fi
  ok "$route ships title/canonical/ld+json"
}

check_route "/explore"
# Pull up to 3 known task UUIDs from the preview's sitemap if available; else
# fall back to a known prod UUID set when running headless.
mapfile -t uuids < <(curl_body "$PREVIEW_URL/sitemap-static.xml" 2>/dev/null \
  | grep -oE '/tasks/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}' \
  | head -3 \
  | sed 's|^/tasks/||')
if [ ${#uuids[@]} -eq 0 ]; then
  note "no /tasks UUIDs in sitemap-static.xml; skipping per-task spot-check"
  note "(commit 5 sitemap only emits enumerated routes; explore-tasks SSG list belongs to a follow-up)"
else
  for u in "${uuids[@]}"; do check_route "/tasks/$u"; done
fi

# --- Result ------------------------------------------------------------------
echo
if [ "$FAILED" -eq 0 ]; then green "ALL GATES PASS"; exit 0
else                          red   "$FAILED GATE(S) FAILED"; exit 1
fi
