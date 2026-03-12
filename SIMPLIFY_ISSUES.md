# Codebase Simplify Issues

Full-codebase review. Issues grouped by size. Check off as fixed.

## Small Fixes

- [x] **S1: Extract DeleteMonitorDialog** — 3 identical delete confirmation dialogs in TaskCard, TaskListRow, TaskDetail. Extract to shared `torale/DeleteMonitorDialog.tsx`.
- [x] **S2: Stringly-typed status values** — Raw strings where `TaskStatus` enum exists in job.py, repository.py, tasks.py router, activities.py. All parameterized with enum values.
- [x] **S3: Extract `formatShortDateTime`** — 8 occurrences across TaskCard, TaskListRow, TaskDetail, ExecutionTimeline, admin tables. Extracted to `lib/utils.ts`, replaced all usages.
- [x] **S4: Extract `getErrorMessage` utility** — 16 occurrences of `err instanceof Error ? err.message : '...'`. Extracted to `lib/utils.ts`, replaced all usages.
- [x] **S5: Extract `buildVanityUrl` utility** — 6 occurrences in TaskEditDialog, Explore, VanityTaskRedirect. Extracted to `lib/utils.ts`, replaced all usages.
- [x] **S6: Consolidate `GroundingSource` type** — Removed duplicate from `admin/types.ts`, re-exports from `types/index.ts`. Fixed wrong field name (`uri` → `url`).
- [x] **S7: Remove duplicate `_is_safe_url` call** — Removed redundant pre-check in `agent.py:_fetch_and_extract`; `_validate_request` event hook already covers it.
- [x] **S8: Consolidate `getCurrentUser`/`getUserWithNotifications`** — `getCurrentUser` now delegates to `getUserWithNotifications` (same endpoint, superset type).
- [ ] **S9: Extract `FieldError` component** — 4 occurrences of validation error display pattern in TaskCreationDialog and TaskEditDialog.
- [x] **S10: Push `configExpanded` state into TaskConfiguration** — Removed from TaskDetail, now internal to TaskConfiguration.
- [ ] **S11: Duplicate ReactMarkdown components config** — TaskDetail and ExecutionTimeline define near-identical `components` prop objects.

## Medium Fixes

- [x] **M1: Admin stats sequential queries → `asyncio.gather`** — 4 independent DB queries now run concurrently.
- [ ] **M2: Duplicate execution/notification endpoint handlers** — `tasks.py` `get_task_executions` and `get_task_notifications` are near-identical. Extract shared helper.
- [ ] **M3: `_check_task_access` fetches `SELECT *`** — Only needs `user_id` and `is_public`. Narrow the query.
- [ ] **M4: `delete_task` double-queries** — First verifies existence, then deletes. Delete directly and check result.
- [ ] **M5: `list_public_tasks` two queries → window function** — `SELECT COUNT(*)` then paginated query. Use `count(*) OVER()`.
- [ ] **M6: `start_task_execution` two queries → one** — Checks for running execution and gets retry count separately. Combine.
- [ ] **M7: API client `buildUrl` helper** — 6 occurrences of URLSearchParams building pattern in `lib/api.ts`.

## Large Fixes (architectural)

- [ ] **L1: Router bypasses repository** — `api/routers/tasks.py` has 480+ lines of raw SQL duplicating `TaskRepository` methods.
- [ ] **L2: Repository parameter sprawl** — `TaskRepository.create_task` and `update_task` each take 11 params. Should accept Pydantic models.
- [ ] **L3: MonitoringResponse cross-repo duplication** — Duplicated between `torale-agent/models.py` and `backend/src/torale/scheduler/models.py`. Style drifting.
- [ ] **L4: WebhookDeliveryService per-call httpx client** — Creates/destroys httpx client per webhook send.
- [ ] **L5: Agent `_fetch_and_extract` per-call httpx client** — Creates fresh client per URL fetch.
- [ ] **L6: InMemoryTaskStore grows unbounded** — Stores all task results with no eviction. Slow memory leak.
- [ ] **L7: `_TASK_WITH_EXECUTION_QUERY` raw SQL vs repository** — Router duplicates PyPika join logic from repository.

## Skipping (behavior change risk / not worth it)

- **NotificationChannelSelector useEffect sync** — Refactoring to direct onChange would change timing semantics.
- **TaskDetail activeTab URL sync** — Would need careful URL-as-source-of-truth refactor.
- **TaskDetail eager notification loading** — Behavior change (lazy load on tab click).
- **Dashboard optimistic updates on toggle/delete** — Behavior change, risk of stale UI.
- **`update_task` unconditional re-fetch** — Would need conditional logic based on state transition.
