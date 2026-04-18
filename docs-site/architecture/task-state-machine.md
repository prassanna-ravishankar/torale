---
title: Task State Machine
description: Torale task lifecycle — active, paused, completed states. How transitions coordinate APScheduler jobs, how conditions terminate tasks, and the invariants enforced by the state machine.
---

# Task State Machine

A Torale monitoring task has a small, explicit state machine. This replaces the ad-hoc "is it running?" boolean that would otherwise creep into several places.

## States

A task is always in exactly one of three states (see `TaskState` in `backend/src/torale/tasks/tasks.py`):

| State | Meaning |
| --- | --- |
| `active` | The task is being checked on schedule. APScheduler has a live job for it. |
| `paused` | The task exists and is preserved, but no executions are running. The APScheduler job is removed. |
| `completed` | A terminal state for `notify_behavior="once"` tasks — the condition fired and the task has stopped. The user can re-activate. |

## Valid transitions

```
active    ──pause──→    paused
paused    ──resume──→   active
active    ──complete──→ completed   (agent returns next_run=null, or user action)
paused    ──complete──→ completed   (user action)
completed ──restart──→  active      (user action)
```

Anything else is rejected. In particular, `completed → paused` is disallowed: a completed task has no schedule, so "pause" has no meaning until it's activated again.

## Where the transitions live

The state machine is enforced at the service layer (`backend/src/torale/tasks/service.py`). Handlers:

- Accept the current state and the requested target
- Validate the transition is in the allowed set
- Update the database row
- Coordinate with APScheduler: add, pause, or remove the cron job in lockstep
- Roll back the DB write if the scheduler side fails (so DB and scheduler can't drift)

API routers call these service methods rather than writing to the tasks table directly. That keeps the state machine as a bottleneck.

## How tasks complete automatically

Most completions aren't user-initiated. The flow for `notify_behavior="once"` tasks is:

1. The scheduler tick fires a task execution
2. The agent runs (see [Grounded Search](/architecture/grounded-search))
3. The agent returns a `MonitoringResponse` where `condition_met=true` and `next_run=null`
4. The backend fires a notification
5. The backend transitions the task `active → completed`, which removes the APScheduler job

For `notify_behavior="always"`, the agent keeps returning a `next_run` timestamp even after matches, and the task stays `active` indefinitely until the user pauses it.

## Database shape

The state is a constrained text column on the `tasks` table:

```sql
state TEXT NOT NULL DEFAULT 'active'
CHECK (state IN ('active', 'paused', 'completed'))
```

No ordering is implied by the column — it's an enum, not a progress bar.

## Invariants

The state machine guarantees:

- **A task's scheduler presence matches its state.** `active` ↔ job exists; `paused` / `completed` ↔ job absent or paused.
- **No zombie jobs.** If the DB transition commits, the scheduler has been updated. If the scheduler update fails, the DB rolls back.
- **Terminal-but-reversible.** `completed` is "done for now", not "deleted". Users can restart a completed task and the full history is preserved.

## Related

- [Grounded Search](/architecture/grounded-search) — what runs during an execution, and how it decides `condition_met`/`next_run`
- [Self-Scheduling Agents](/architecture/self-scheduling-agents) — the broader loop the state machine sits inside
