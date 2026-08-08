# Watch lifecycle safety

- Watches are ongoing by default. Only an explicit user/admin state transition may pause or complete one.
- Agent output `next_run=null` is not trusted as a task-state command. The backend records `agent_requested_completion` / `completion_suppressed` in the execution result and schedules a 24-hour fallback.
- `_schedule_next_run()` claims the schedule only while `tasks.state = 'active'` and re-checks after adding the APScheduler job. This prevents an in-flight run from resurrecting a concurrently paused/completed watch.
- Production audit on 2026-08-08 found 11 incorrectly auto-completed recurring watches and 13 stale nonterminal execution rows from early 2026.
