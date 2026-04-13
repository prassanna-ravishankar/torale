---
name: execution-id-reuse-legacy-data
description: Historical task_executions rows have inflated durations and stale error fields from pre-fix execution_id reuse bug
type: project
---

Before PR #207 (merged 2026-04-10), the success path in `job.py` forwarded `execution_id` to `_schedule_next_run`, causing every scheduled run to reuse the same `task_executions` row. This produced rows with `started_at` from the first-ever run and `completed_at` from the latest run (durations of days/weeks), and stale error fields from intermediate failures.

**Why this matters for future work:**
- Historical rows with multi-day durations are not bugs -- they're pre-fix artifacts that will age out as new rows are created per-run.
- Some tasks had only 1 execution row despite running for months. This caused the welcome email (`is_first_execution` check) to re-fire on first post-fix run for long-lived tasks. One-time issue, now resolved.
- 5 tasks were incorrectly marked `completed` with non-null `next_run` in their last result. These were manually reactivated on 2026-04-12.

**How to apply:** Don't backfill or "fix" old rows. If a user reports weird durations on old executions, this is why. New executions create fresh rows with correct durations.
