#!/usr/bin/env bash
#
# Drift guard: the NEXT_PUBLIC_* values passed as docker --build-arg in
# .github/workflows/{production,staging}.yml must match the Helm values
# they mirror (helm/torale/values-{production,staging}.yaml). Drift here
# means the deployed client bundle and the deployed runtime env disagree,
# which manifests as subtle SSR-vs-hydration mismatches OR auth flowing
# to the wrong Clerk tenant.
#
# We grep for the literal value strings in both files rather than parsing
# YAML — keeps the dep surface to just bash + grep + sed and survives
# either side adding/removing comments without false alarms.
#
# Exit 0 = matched. Exit 1 = drift; print which key disagreed.
#
# Per review notif-d7f9dcd9 / M8.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

extract_workflow() {
  # Args: <workflow_file> <key>
  # Returns the value following "<key>=" in the build-args block.
  local file="$1" key="$2"
  grep -E "^[[:space:]]+${key}=" "$file" \
    | head -1 \
    | sed -E "s|^[[:space:]]+${key}=||" \
    | sed -E 's|[[:space:]]+$||'
}

extract_helm_clerk() {
  local file="$1"
  grep -E '^  publishableKey:' "$file" | head -1 | sed -E 's/^  publishableKey:[[:space:]]+//' | tr -d '"'
}

extract_helm_posthog_key() {
  local file="$1"
  grep -E '^[[:space:]]+apiKey:' "$file" | head -1 | sed -E 's/^[[:space:]]+apiKey:[[:space:]]+//' | tr -d '"'
}

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

# --- production --------------------------------------------------------
WF_PROD="$ROOT/.github/workflows/production.yml"
HV_PROD="$ROOT/helm/torale/values-production.yaml"
report production NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY \
  "$(extract_workflow "$WF_PROD" NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY)" \
  "$(extract_helm_clerk "$HV_PROD")"
report production NEXT_PUBLIC_POSTHOG_API_KEY \
  "$(extract_workflow "$WF_PROD" NEXT_PUBLIC_POSTHOG_API_KEY)" \
  "$(extract_helm_posthog_key "$HV_PROD")"

# --- staging -----------------------------------------------------------
WF_STAGING="$ROOT/.github/workflows/staging.yml"
HV_STAGING="$ROOT/helm/torale/values-staging.yaml"
report staging NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY \
  "$(extract_workflow "$WF_STAGING" NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY)" \
  "$(extract_helm_clerk "$HV_STAGING")"
report staging NEXT_PUBLIC_POSTHOG_API_KEY \
  "$(extract_workflow "$WF_STAGING" NEXT_PUBLIC_POSTHOG_API_KEY)" \
  "$(extract_helm_posthog_key "$HV_STAGING")"

if [ "$failed" -eq 0 ]; then
  echo "OK: workflow build-args match Helm values for production + staging."
else
  exit 1
fi
