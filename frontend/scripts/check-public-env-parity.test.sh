#!/usr/bin/env bash
#
# Regression tests for scripts/check-public-env-parity.sh.
#
# The parity script extracts values from YAML with anchored regex / awk —
# brittle by construction. These tests guard against silent regressions
# in that extractor by running the script end-to-end against fixture
# YAML under scripts/fixtures/parity/ exercising the formatting variants
# the parser is expected to tolerate (and a few it is NOT expected to
# tolerate, pinning current behaviour).
#
# Test rig: for each scenario, build a sandbox tree under a temp dir
# containing .github/workflows/{production,staging}.yml and
# helm/torale/values-{production,staging}.yaml, point ROOT_OVERRIDE at
# it, and run the script. Assert exit code + DRIFT output as expected.
#
# Style: hand-rolled assertions, no test framework. Mirrors
# lib/seo/jsonLd.test.ts.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PARITY_SCRIPT="$SCRIPT_DIR/check-public-env-parity.sh"
FIX="$SCRIPT_DIR/fixtures/parity"

GREEN=$'\033[92m'
RED=$'\033[91m'
DIM=$'\033[2m'
RESET=$'\033[0m'

failed=0

pass() { printf '%sOK%s   %s\n' "$GREEN" "$RESET" "$1"; }
fail() { printf '%sFAIL%s %s\n' "$RED"   "$RESET" "$1"; failed=$((failed + 1)); }

# make_bundle <dir> <prod_workflow> <stg_workflow> <prod_values> <stg_values>
make_bundle() {
  local dir="$1" wf_prod="$2" wf_stg="$3" vals_prod="$4" vals_stg="$5"
  mkdir -p "$dir/.github/workflows" "$dir/helm/torale"
  cp "$wf_prod"   "$dir/.github/workflows/production.yml"
  cp "$wf_stg"    "$dir/.github/workflows/staging.yml"
  cp "$vals_prod" "$dir/helm/torale/values-production.yaml"
  cp "$vals_stg"  "$dir/helm/torale/values-staging.yaml"
}

# run_scenario <label> <expected_exit> <expect_drift_key_or_empty> <prod_vals> <stg_vals> <prod_wf> <stg_wf>
run_scenario() {
  local label="$1" expected_exit="$2" expect_drift_key="$3"
  local vals_prod="$4" vals_stg="$5" wf_prod="$6" wf_stg="$7"

  local tmp
  tmp="$(mktemp -d -t parity-test.XXXXXX)"
  make_bundle "$tmp" "$wf_prod" "$wf_stg" "$vals_prod" "$vals_stg"

  local out actual_exit
  out="$(ROOT_OVERRIDE="$tmp" bash "$PARITY_SCRIPT" 2>&1)" && actual_exit=0 || actual_exit=$?

  if [ "$actual_exit" -eq "$expected_exit" ]; then
    pass "$label: exit $actual_exit (expected $expected_exit)"
  else
    fail "$label: exit $actual_exit, expected $expected_exit"
    printf '%s%s%s\n' "$DIM" "$out" "$RESET"
  fi

  if [ -n "$expect_drift_key" ]; then
    if printf '%s\n' "$out" | grep -q "DRIFT .* $expect_drift_key"; then
      pass "$label: DRIFT mentions $expect_drift_key"
    else
      fail "$label: expected DRIFT for $expect_drift_key in output"
      printf '%s%s%s\n' "$DIM" "$out" "$RESET"
    fi
  elif [ "$expected_exit" -eq 0 ]; then
    if printf '%s\n' "$out" | grep -q "^DRIFT"; then
      fail "$label: unexpected DRIFT line in passing scenario"
      printf '%s%s%s\n' "$DIM" "$out" "$RESET"
    else
      pass "$label: no DRIFT lines"
    fi
  fi

  rm -rf "$tmp"
}

# ---- scenarios ---------------------------------------------------------

# 1. Canonical: workflow build-args == helm values. MUST pass.
run_scenario "canonical-match" 0 "" \
  "$FIX/values-canonical.yaml" \
  "$FIX/values-canonical.yaml" \
  "$FIX/workflow-canonical.yml" \
  "$FIX/workflow-canonical.yml"

# 2. Extra whitespace (blank lines between siblings). MUST pass.
run_scenario "extra-whitespace" 0 "" \
  "$FIX/values-extra-whitespace.yaml" \
  "$FIX/values-extra-whitespace.yaml" \
  "$FIX/workflow-canonical.yml" \
  "$FIX/workflow-canonical.yml"

# 3. Trailing spaces after every scalar. MUST pass — script strips them.
run_scenario "trailing-spaces" 0 "" \
  "$FIX/values-trailing-spaces.yaml" \
  "$FIX/values-trailing-spaces.yaml" \
  "$FIX/workflow-canonical.yml" \
  "$FIX/workflow-canonical.yml"

# 4. Unquoted PostHog scalars (YAML allows either form). MUST pass.
run_scenario "unquoted-scalars" 0 "" \
  "$FIX/values-unquoted.yaml" \
  "$FIX/values-unquoted.yaml" \
  "$FIX/workflow-canonical.yml" \
  "$FIX/workflow-canonical.yml"

# 5. Drift: values diverge from workflow. MUST fail with PostHog drift.
run_scenario "drift-posthog-apikey" 1 "NEXT_PUBLIC_POSTHOG_API_KEY" \
  "$FIX/values-drifted.yaml" \
  "$FIX/values-canonical.yaml" \
  "$FIX/workflow-canonical.yml" \
  "$FIX/workflow-canonical.yml"

# 6. Drift: workflow has wrong PostHog key. MUST fail.
run_scenario "drift-workflow-side" 1 "NEXT_PUBLIC_POSTHOG_API_KEY" \
  "$FIX/values-canonical.yaml" \
  "$FIX/values-canonical.yaml" \
  "$FIX/workflow-drifted.yml" \
  "$FIX/workflow-canonical.yml"

# 7. Pin behaviour: trailing spaces AFTER a closing `"` on quoted scalars
#    leave a stray quote in the extracted value, so parity reports drift
#    on the PostHog keys. If the parser is hardened to strip
#    whitespace-before-quotes, update this scenario deliberately.
run_scenario "quoted-trailing-spaces-pin" 1 "NEXT_PUBLIC_POSTHOG_API_KEY" \
  "$FIX/values-quoted-trailing-spaces.yaml" \
  "$FIX/values-canonical.yaml" \
  "$FIX/workflow-canonical.yml" \
  "$FIX/workflow-canonical.yml"

# 8. Pin behaviour: inline-comment values currently DO NOT parse cleanly
#    (the parser leaves the comment in the value), so parity must report
#    drift. If a future PR adds proper YAML parsing, update this case
#    deliberately.
run_scenario "inline-comments-pin" 1 "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY" \
  "$FIX/values-inline-comments.yaml" \
  "$FIX/values-canonical.yaml" \
  "$FIX/workflow-canonical.yml" \
  "$FIX/workflow-canonical.yml"

# ---- summary -----------------------------------------------------------

if [ "$failed" -gt 0 ]; then
  printf '\n%s%d test(s) failed%s\n' "$RED" "$failed" "$RESET"
  exit 1
fi
printf '\n%sAll parity tests passed%s\n' "$GREEN" "$RESET"
