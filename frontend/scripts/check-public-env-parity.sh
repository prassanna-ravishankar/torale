#!/usr/bin/env bash
#
# Drift guard: every NEXT_PUBLIC_* value passed as docker --build-arg in
# .github/workflows/{production,staging}.yml must match the Helm values
# the runtime pod will read at request time. Drift means the deployed
# client bundle and the deployed runtime env disagree — manifests as
# subtle SSR-vs-hydration mismatches OR auth flowing to the wrong Clerk
# tenant.
#
# Per review notif-d7f9dcd9 (M8) and the round-2 notif-20f6866d (H2):
# now compares ALL five NEXT_PUBLIC_* keys, not just Clerk PK + PostHog
# key. Add new keys here as they're added to the workflows + values.
#
# Exit 0 = matched. Exit 1 = drift; prints which key disagreed.

set -euo pipefail

# ROOT_OVERRIDE allows tests (scripts/check-public-env-parity.test.sh) to
# point this script at a fixture tree containing .github/workflows/*.yml
# and helm/torale/values-*.yaml. Defaults to the repo root.
ROOT="${ROOT_OVERRIDE:-$(cd "$(dirname "$0")/../.." && pwd)}"

# ---- extractors --------------------------------------------------------
#
# We grep nested YAML without pulling in yq — the values structure is
# stable and shallow enough that anchored regex is reliable.

extract_workflow() {
  # Args: <workflow_file> <key>
  # Returns the value following "<key>=" in the build-args block.
  local file="$1" key="$2"
  grep -E "^[[:space:]]+${key}=" "$file" \
    | head -1 \
    | sed -E "s|^[[:space:]]+${key}=||" \
    | sed -E 's|[[:space:]]+$||'
}

# helm/torale/values-*.yaml format:
#   clerk:
#     publishableKey: pk_live_...
#   posthog:
#     apiKey: "phc_..."
#     apiHost: "https://eu.posthog.com"
#   domains:
#     live:
#       frontend: webwhen.ai
#       api: api.webwhen.ai

# Extracts a top-level key.subkey value (`clerk.publishableKey`,
# `posthog.apiKey`, `posthog.apiHost`).
extract_helm_kv() {
  # Args: <file> <top_key> <child_key>
  local file="$1" top="$2" child="$3"
  awk -v top="$top" -v child="$child" '
    $0 ~ "^"top":" { in_top = 1; next }
    in_top && /^[^[:space:]]/ { in_top = 0 }
    in_top && $0 ~ "^[[:space:]]+"child":" {
      sub("^[[:space:]]+"child":[[:space:]]+", "")
      gsub(/^"|"$/, "")
      sub(/[[:space:]]+$/, "")
      print
      exit
    }
  ' "$file"
}

# Extracts domains.live.<child>. The two-level nesting needs its own awk
# pass (yq would be cleaner but we keep the dep surface tiny).
extract_helm_domain_live() {
  # Args: <file> <child>
  local file="$1" child="$2"
  awk -v child="$child" '
    /^domains:/         { in_domains = 1; next }
    in_domains && /^[^[:space:]]/ { in_domains = 0 }
    in_domains && /^  live:/      { in_live = 1; next }
    in_live && /^  [^[:space:]]/  { in_live = 0 }
    in_live && $0 ~ "^    "child":" {
      sub("^    "child":[[:space:]]+", "")
      gsub(/^"|"$/, "")
      sub(/[[:space:]]+$/, "")
      print
      exit
    }
  ' "$file"
}

# ---- comparisons -------------------------------------------------------

failed=0
report() {
  local env="$1" key="$2" wf="$3" helm="$4"
  if [ "$wf" != "$helm" ]; then
    echo "DRIFT [$env] $key:"
    echo "  workflow: $wf"
    echo "  helm:     $helm"
    failed=1
  fi
}

check_env() {
  # Args: <env-label> <workflow_yml> <helm_values_yml>
  local env="$1" wf="$2" hv="$3"
  local api_host site_host clerk_pk ph_key ph_host

  api_host=$(extract_helm_domain_live "$hv" api)
  site_host=$(extract_helm_domain_live "$hv" frontend)
  clerk_pk=$(extract_helm_kv "$hv" clerk publishableKey)
  ph_key=$(extract_helm_kv "$hv" posthog apiKey)
  ph_host=$(extract_helm_kv "$hv" posthog apiHost)

  report "$env" NEXT_PUBLIC_API_BASE_URL \
    "$(extract_workflow "$wf" NEXT_PUBLIC_API_BASE_URL)" \
    "https://${api_host}"
  report "$env" NEXT_PUBLIC_SITE_ORIGIN \
    "$(extract_workflow "$wf" NEXT_PUBLIC_SITE_ORIGIN)" \
    "https://${site_host}"
  report "$env" NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY \
    "$(extract_workflow "$wf" NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY)" \
    "$clerk_pk"
  report "$env" NEXT_PUBLIC_POSTHOG_API_KEY \
    "$(extract_workflow "$wf" NEXT_PUBLIC_POSTHOG_API_KEY)" \
    "$ph_key"
  report "$env" NEXT_PUBLIC_POSTHOG_HOST \
    "$(extract_workflow "$wf" NEXT_PUBLIC_POSTHOG_HOST)" \
    "$ph_host"
}

check_env production \
  "$ROOT/.github/workflows/production.yml" \
  "$ROOT/helm/torale/values-production.yaml"

check_env staging \
  "$ROOT/.github/workflows/staging.yml" \
  "$ROOT/helm/torale/values-staging.yaml"

if [ "$failed" -eq 0 ]; then
  echo "OK: workflow build-args match Helm values for production + staging (5 keys each)."
else
  exit 1
fi
