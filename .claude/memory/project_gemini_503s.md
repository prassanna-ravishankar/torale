---
name: gemini-503-classification
description: Gemini 503 errors are classified as "unknown" instead of "rate_limit" in errors.py -- causes suboptimal retry behavior
type: project
---

`gemini-3.1-flash-lite-preview` intermittently returns HTTP 503 ("This model is currently experiencing high demand"). Over 30 days, 24/125 executions (19%) failed this way. The errors cluster but are transient -- retries usually succeed.

**Why this is a problem:** `backend/src/torale/scheduler/errors.py` classifies these as `unknown` (2 retries, 5m/15m/45m backoff) instead of `rate_limit` (5 retries, 30s/2m/8m/32m/2h backoff). The `unknown` strategy gives fewer attempts with longer initial delays, when in practice a quick retry after 30s would likely succeed.

**How to apply:** When addressing this, add `ModelHTTPError` with status 503 to the classifier as `rate_limit` or a new `model_capacity` category. Consider also whether `gemini-3.1-flash-lite-preview` should be swapped for a more stable model like `gemini-2.0-flash`.
