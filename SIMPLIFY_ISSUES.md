# Codebase Simplify Issues

Full-codebase review. Issues grouped by size. Check off as fixed.

## Small Fixes

- [x] **S1: Extract DeleteMonitorDialog** — 3 identical delete confirmation dialogs in TaskCard, TaskListRow, TaskDetail.
- [x] **S2: Stringly-typed status values** — Raw strings where `TaskStatus` enum exists.
- [x] **S3: Extract `formatShortDateTime`** — 8 occurrences across components.
- [x] **S4: Extract `getErrorMessage` utility** — 16 occurrences.
- ~~S5: Extract `buildVanityUrl`~~ — Obsolete after slug system removal (#181).
- [x] **S6: Consolidate `GroundingSource` type** — Fixed wrong field name (`uri` → `url`).
- [x] **S7: Remove duplicate `_is_safe_url` call** — N/A after Lightpanda migration (#183).
- [x] **S8: Consolidate `getCurrentUser`/`getUserWithNotifications`**.
- [x] **S9: Extract `FieldError` component** — 4 occurrences in TaskCreationDialog and TaskEditDialog.
- [x] **S10: Push `configExpanded` state into TaskConfiguration**.
- [x] **S11: Duplicate ReactMarkdown components config** — TaskDetail and ExecutionTimeline.

## Medium Fixes

- [x] **M1: Admin stats sequential queries → `asyncio.gather`**.
- [x] **M2: Duplicate execution/notification endpoint handlers** — `tasks.py` `get_task_executions` and `get_task_notifications` are near-identical.
- [x] **M3: `_check_task_access` fetches `SELECT *`** — Only needs `user_id` and `is_public`.
- [x] **M4: `delete_task` double-queries** — First verifies existence, then deletes.
- [x] **M5: `list_public_tasks` two queries → window function** — Use `count(*) OVER()`.
- [x] **M6: `start_task_execution` two queries → one** — Combine running check + retry count.
- [x] **M7: API client `buildUrl` helper** — 6 occurrences of URLSearchParams pattern.

## Large Fixes (architectural)

- [x] **L1: Router bypasses repository** — Migrated `list_tasks`, `get_task`, and `update_task` re-fetch to use `TaskRepository`. Complex endpoints (create, update core, fork) kept as-is.
- [ ] **L2: Repository parameter sprawl** — `create_task`/`update_task` take 11 params each.
- [x] **L3: MonitoringResponse cross-repo duplication** — Synced styles, added SYNC comments.
- ~~L4: WebhookDeliveryService per-call httpx client~~ — N/A; already uses persistent client in `__init__`; per-call instantiation acceptable at current scale.
- ~~L5: Agent per-call httpx client~~ — N/A after Lightpanda migration (#183).
- [x] **L6: InMemoryTaskStore grows unbounded** — Added `BoundedTaskStore` with time-based (1h) and count-based (1000) eviction.
- [x] **L7: `_TASK_WITH_EXECUTION_QUERY` raw SQL vs repository** — Removed; endpoints now use `TaskRepository` methods.

## Skipping (behavior change risk / not worth it)

- **NotificationChannelSelector useEffect sync** — Would change timing semantics.
- **TaskDetail activeTab URL sync** — Needs URL-as-source-of-truth refactor.
- **TaskDetail eager notification loading** — Behavior change.
- **Dashboard optimistic updates on toggle/delete** — Behavior change, stale UI risk.
- **`update_task` unconditional re-fetch** — Needs conditional logic.
