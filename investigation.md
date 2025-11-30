# Torale Issue Investigation

## Investigation Date: 2025-11-30

## Issues Identified

### 1. Missing Grounding Source Links

**Symptoms:**
- Execution results show structured state data (e.g., "Initial Launch", "Version 0.3 Release") but no clickable URLs
- Users can't navigate to the actual sources that informed the search results
- See screenshot: Image #2 shows detailed state breakdown but zero visible links

**Questions to Answer:**
- [x] Are links missing from the API response (`grounding_sources` field)? **YES**
- [x] Are links present in API but not rendered in frontend? **NO - API has empty array**
- [x] Is this related to the Vertex AI URL filtering that was added previously? **YES**
- [x] Which component is responsible for rendering grounding sources? **GroundingSourceList component**

**ROOT CAUSE IDENTIFIED:**
- Gemini API changed behavior: **ALL grounding sources now come as Vertex AI redirect URLs**
- Previous code (line 207-210 in `grounded_search.py`) filters out Vertex AI redirects
- This was meant to filter infrastructure URLs, but now filters out ALL sources
- Result: `grounding_sources` array is always empty

**Evidence:**
- Test query "What is the capital of France?" returns 5 grounding chunks
- All chunks have `web.uri` like: `https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF...`
- All chunks have `web.title` with clean domain names: "britannica.com", "coe.int", "wikipedia.org"
- Current filter: `if "vertexaisearch.cloud.google.com" in uri: continue` removes them all

**Investigation Steps:**
1. ✅ Check API response for a recent execution with `grounding_sources`
2. ✅ Verify grounding source filtering logic in backend
3. ✅ Test with isolated script to confirm behavior
4. ✅ Identify exact line causing issue

**FIX IMPLEMENTED (Awaiting User Testing):**

**Approach: Remove Filter + Hide URL Display**
- Backend: Removed Vertex AI redirect filter (lines 207-210 in `grounded_search.py`)
- Frontend: Hide URL display in `GroundingSourceList.tsx` (show only clean domain as link)
- Tests: Added assertions to verify sources are populated + regression test

**Files Changed:**
- `backend/src/torale/executors/grounded_search.py` (filter removed)
- `frontend/src/components/ui/GroundingSourceList.tsx` (URL hidden)
- `backend/tests/test_gemini_integration.py` (assertions added)
- `backend/tests/test_executors.py` (source count check added)
- `backend/tests/test_grounding_sources_regression.py` (new regression test)

**What Users See Now:**
- UI: Clean "britannica.com" as clickable link (redirect URL hidden)
- Webhooks: Full JSON with redirect URLs (unchanged)
- Emails: Novu template renders `<a href=redirect-url>domain</a>` (unchanged)

**Testing Status:**
- ✅ **Backend fix verified**: WORKING - `test_grounding_sources.py` confirms sources now populated
  - France query: 4 sources (was 0 before fix)
  - A2A protocol query: 6 sources (was 0 before fix)
  - Vertex AI redirect URLs preserved with clean titles
- ✅ Integration tests: Updated with grounding source assertions
- ⏳ Regression tests: Written but have mocking issues (doesn't affect fix verification)
- ⏳ User verification: **Ready for testing** - Run a task execution and check sources appear in UI
- ⏳ Email rendering: Awaiting Novu test (if configured)

**User Verification Steps:**
1. Run existing task or create new one
2. Check execution history - verify grounding sources appear
3. Click on source links - verify they open correct pages
4. Check email notifications (if configured) - verify sources render

**Rollback Plan:**
If issues arise, revert by:
1. Re-add filter in `grounded_search.py` (lines 207-210)
2. Re-show URL in `GroundingSourceList.tsx` (lines 37-39)

---

### 1b. Email Notifications Not Sending

**Symptoms:**
- After fixing grounding sources, email notifications still not received
- Notification UI says "notification sent" but no email arrives
- Worker logs show ERROR: "Notification activity error" at line 276 in activities.py

**ROOT CAUSE IDENTIFIED:**
- Migration `f3004543fd24` renamed `notification_sends.sent_at` to `created_at` for consistency (line 45)
- Code in `email_verification.py` still queries for `sent_at` column (lines 206, 220)
- Column doesn't exist → query fails → spam limit check fails → notification never sends

**Evidence:**
- Worker error at `EmailVerificationService.check_spam_limits()` line 203
- Query: `SELECT COUNT(*) FROM notification_sends WHERE user_id = $1 AND sent_at > $2`
- Migration shows: `op.alter_column("notification_sends", "sent_at", new_column_name="created_at")`

**FIX IMPLEMENTED:**
- **File**: `backend/src/torale/core/email_verification.py`
- **Lines 206, 220**: Changed `sent_at > $2` to `created_at > $2` in both spam limit queries
- **Services restarted**: `docker compose restart workers`

**Testing Status:**
- ⏳ User verification: **Ready for testing** - Trigger a notification and check if email arrives
- ⏳ Check worker logs for errors: `docker compose logs workers -f`

**User Verification Steps:**
1. Trigger a task execution that meets condition (or manually execute existing task)
2. Check email inbox for notification
3. Verify no errors in worker logs

---

### 2. Pause Behavior Confusion & Contradictory Status Badges

**Symptoms:**
- Task shows both "Triggered" AND "Paused" badges simultaneously (Image #1)
- Confusing UX: Is the task running or not? What does "Triggered" even mean?
- "Triggered" badge persists forever after first condition met
- No distinction between user-paused vs auto-completed tasks

**Current State Questions:**
- [x] Where is the "Paused" state stored? **`is_active` field (false = paused)**
- [x] What triggers the pause state? **User action OR auto-pause when `notify_behavior="once"` + condition met**
- [x] Does paused task still create Temporal schedules? **No, schedules pause when `is_active=false`**
- [x] Does pause stop executions or just notifications? **Stops executions (Temporal schedule pauses)**
- [x] Is there a pause/unpause API endpoint? **Yes, `PUT /tasks/{id}` with `is_active` toggle**

**ROOT CAUSE IDENTIFIED:**

**Problem 1: Sticky `condition_met` State**
- `tasks.condition_met` column is set to `true` when condition first met (line 146 in activities.py)
- **Never cleared back to false** when subsequent executions don't meet condition
- Result: "Triggered" badge shows forever, even if no longer true

**Problem 2: Auto-Pause Misunderstood as User Pause**
- System auto-sets `is_active=false` when `notify_behavior="once"` + condition met (lines 168-176 in activities.py)
- UI shows generic "Paused" badge with no indication it was auto-stopped
- User thinks they paused it, or something broke
- No way to distinguish: "I paused this" vs "System completed and stopped this"

**Problem 3: No Semantic Status**
- Status derived from multiple boolean fields (`is_active`, `condition_met`) in each component
- Inconsistent logic across TaskCard, TaskDetail, Dashboard
- No single source of truth for "what is this task doing?"

**FIX IMPLEMENTED:**

**Approach: Centralized Status Logic with Three States**
- **Active**: `is_active=true` → Task monitoring on schedule (🟢 Monitoring)
- **Completed**: `is_active=false` + `last_execution.condition_met=true` → Auto-stopped after notify_behavior="once" (✅ Completed)
- **Paused**: `is_active=false` + `last_execution.condition_met=false/null` → User manually paused (⏸️ Paused)

**Architecture Changes:**

1. **Database Migration** (`c36fe95dcb98_add_last_execution_id_to_tasks.py`)
   - Added `tasks.last_execution_id` column to track latest execution
   - Backfilled from most recent execution per task
   - Kept old `condition_met` and `last_notified_at` columns (marked DEPRECATED for gradual migration)

2. **Backend Changes**
   - Created `backend/src/torale/core/task_status.py` - centralized status logic
   - Updated `workers/activities.py` line 148 to set `last_execution_id` after execution
   - Updated API `tasks.py` endpoints (list_tasks, get_task) to LEFT JOIN and embed latest execution
   - Updated `core/models.py` Task model with new fields (marked old fields DEPRECATED)

3. **Frontend Changes**
   - Created `frontend/src/lib/taskStatus.ts` - mirrors backend logic
   - Updated `types/index.ts` with `TaskExecutionSummary` interface and new Task fields
   - Updated `TaskCard.tsx` to use centralized status (single badge, no duplicates)
   - Updated `TaskDetail.tsx` to use centralized status
   - Updated `Dashboard.tsx` tabs: "All | 🟢 Monitoring | ✅ Completed | ⏸️ Paused"

**Files Changed:**
- `backend/alembic/versions/c36fe95dcb98_add_last_execution_id_to_tasks.py` (NEW)
- `backend/src/torale/core/task_status.py` (NEW)
- `backend/src/torale/core/models.py` (updated Task model)
- `backend/src/torale/workers/activities.py` (line 148: set last_execution_id)
- `backend/src/torale/api/routers/tasks.py` (list_tasks, get_task: embed execution)
- `frontend/src/lib/taskStatus.ts` (NEW)
- `frontend/src/types/index.ts` (TaskExecutionSummary interface, updated Task)
- `frontend/src/components/TaskCard.tsx` (use status module)
- `frontend/src/components/TaskDetail.tsx` (use status module)
- `frontend/src/components/Dashboard.tsx` (new tab structure)
- `backend/tests/test_task_status.py` (NEW - comprehensive tests)
- `frontend/src/lib/taskStatus.test.ts` (NEW - comprehensive tests)

**What Users See Now:**
- **Single status badge** per task (no contradictions)
- **Active tasks**: "🟢 Monitoring" - running on schedule
- **Completed tasks**: "✅ Completed" - notified once and auto-stopped
- **Paused tasks**: "⏸️ Paused" - manually stopped by user
- **Dashboard tabs**: Filter by activity state instead of sticky "Triggered" state
- **Clear semantics**: User immediately understands what each task is doing

**Testing Status:**
- ✅ **Backend tests**: All pass (`uv run python tests/test_task_status.py`)
  - Enum values correct
  - Active status logic correct
  - Completed status logic correct
  - Paused status logic correct
  - Status info structure correct
- ✅ **Frontend tests**: All pass (`npx tsx src/lib/taskStatus.test.ts`)
  - Same test coverage as backend
  - Ensures consistency between frontend/backend
- ✅ **Migration applied**: Successfully backfilled `last_execution_id`
- ⏳ **User verification**: Ready for testing in live environment

**User Verification Steps:**
1. Check Dashboard - verify tabs show "🟢 Monitoring / ✅ Completed / ⏸️ Paused"
2. Check task cards - verify single status badge (no "Triggered + Paused" contradictions)
3. Create task with `notify_behavior="once"` → trigger condition → verify shows "✅ Completed"
4. Manually pause active task → verify shows "⏸️ Paused"
5. Resume paused task → verify shows "🟢 Monitoring"

**Rollback Plan:**
If issues arise:
1. Database: Revert migration `c36fe95dcb98` (drops `last_execution_id` column)
2. Backend: Remove `task_status.py`, revert model/API/worker changes
3. Frontend: Revert to old badge logic (show `condition_met` + `is_active` separately)

**Manual Testing Flows:**

*Critical flows to verify the fix and prevent regressions.*

**Test 1: Three States Work Correctly**
1. Create task with `notify_behavior="once"` and simple condition (e.g., "capital of France")
2. ✅ Initially shows "🟢 Monitoring" in dashboard
3. Run task → condition met → ✅ Shows "✅ Completed" (blue badge)
4. Manually resume task → ✅ Shows "🟢 Monitoring" again
5. Manually pause task → ✅ Shows "⏸️ Paused" (yellow badge)
6. ✅ Each state shows ONLY ONE badge (no contradictions)

**Test 2: Dashboard Tabs Filter Correctly**
1. Create mix: 1 active, 1 completed (auto-stopped), 1 paused task
2. ✅ "All Tasks" shows all 3
3. ✅ "🟢 Monitoring" shows only active task
4. ✅ "✅ Completed" shows only auto-stopped task
5. ✅ "⏸️ Paused" shows only manually paused task

**Test 3: Active Tasks Don't Change on Execution**
1. Create active task, run it multiple times with varying results
2. ✅ Task stays "🟢 Monitoring" as long as `is_active=true`
3. ✅ Status only changes when paused OR auto-stopped (notify_behavior="once" + condition met)

**Test 4: No Contradictory Badges (Regression Test)**
1. Test ANY task in ANY state
2. ✅ NEVER see "Triggered" + "Paused" together
3. ✅ ALWAYS see exactly ONE status badge

**Quick Checks:**
- ✅ Dashboard loads fast (no N+1 queries)
- ✅ Badge on card matches badge on detail page
- ✅ Status persists on page reload

**Automated Tests:**
```bash
# Backend (11 assertions)
cd backend && uv run python tests/test_task_status.py

# Frontend (12 assertions)
cd frontend && npx tsx src/lib/taskStatus.test.ts
```

---

### 3. Post-Task Creation UX - "Emptiness"

**Symptoms:**
- After creating a task, users feel lost about what happens next
- "No channels configured" (Image #3) feels broken rather than informative
- No confirmation email explaining the monitoring setup
- Unclear when first check will run
- Unclear how users will be notified

**Current Gaps:**
- ❌ No welcome/confirmation email after task creation
- ❌ No clear indication of when first execution will run
- ❌ "No channels configured" feels like an error state (but in-app notifications work)
- ❌ No post-creation success message or guidance

**Proposed Solutions:**
1. **Welcome Email** (send immediately after task creation):
   - Confirmation of what's being monitored (query + condition)
   - Next scheduled check time (e.g., "First check: Tomorrow at 12:00 AM")
   - How to view results (link to task detail page)
   - How you'll be notified (in-app for now, mention future email/SMS)
   - How to pause/edit/delete task
   - Should this be sent even if task is created in paused state?

2. **Improved In-App UX**:
   - Post-creation success message with next steps
   - Replace "No channels configured" with "In-app notifications enabled"
   - Show next execution time prominently on task detail page
   - Consider onboarding flow for first-time users

**Questions to Answer:**
- [ ] Should email be sent for paused tasks?
- [ ] Should email be sent when editing a task?
- [ ] What email service to use? (NotificationAPI? Direct SMTP? SendGrid?)
- [ ] Should we batch emails or send individually?
- [ ] What's the email template format?

**Investigation Steps:**
1. Decide on email service provider
2. Design email template (HTML + plain text)
3. Identify trigger points for sending email (post-creation only? edits too?)
4. Update frontend to show better post-creation feedback
5. Fix "No channels configured" messaging

---

### 4. Timezone Mismatch - Schedules Run in UTC, Display in Local Time

**Symptoms:**
- Users set schedule thinking "9am" = their local time
- Task actually runs at 9am UTC (could be 1am PST, 5pm JST, etc.)
- No indication in UI that schedules are UTC-based

**ROOT CAUSE IDENTIFIED:**
- **Temporal schedules default to UTC** when no timezone specified
- **Frontend displays times in user's browser timezone** via `Intl.DateTimeFormat`
- User creates task "0 9 * * *" thinking = 9am their time
- Temporal runs it at 9am UTC (hours off from user's expectation)

**Evidence:**
1. **Backend**: `ScheduleSpec(cron_expressions=[task.schedule])` - no timezone param
   - File: `backend/src/torale/api/routers/tasks.py:214, 740`
   - Temporal default: UTC timezone for cron expressions

2. **Frontend**: `new Intl.DateTimeFormat("en-US", {...}).format(date)` - no timezone param
   - File: `frontend/src/components/ExecutionTimeline.tsx:48-53`
   - Browser default: User's local timezone

3. **Schedule Display**: Uses `cronstrue` to convert cron to human readable
   - File: `frontend/src/components/ui/CronDisplay.tsx:17-21`
   - Shows "At 09:00 AM" but doesn't clarify UTC vs local

**Impact:**
- User in PST sets "0 9 * * *" expecting 9am PST
- Task runs at 9am UTC = 1am PST (8 hours early!)
- Confusing: execution history shows "1:00 AM" in timeline but user set "9:00 AM"

**Potential Solutions:**

**Option 1: Store User Timezone + Convert to UTC**
- Store user's timezone in user profile (detect from browser)
- Convert user's local cron to UTC cron before creating Temporal schedule
- Display times in user's timezone consistently
- Backend handles all conversion

**Option 2: Add Timezone to Schedule UI**
- Let user pick timezone when creating task (dropdown)
- Pass timezone to Temporal: `ScheduleSpec(cron_expressions=[...], timezone="America/Los_Angeles")`
- Display times in selected timezone
- More explicit but adds complexity

**Option 3: Force Everything to UTC**
- Show UTC times in UI with clear "UTC" label
- Schedule builder shows UTC times
- User converts manually (simplest backend, hardest UX)

**Recommended: Option 1**
- Best UX: "just works" for users
- Transparent: shows their local time everywhere
- Backend responsibility: handle timezone math

**Investigation Status:**
- ✅ Root cause confirmed
- ⏳ Solution design needed
- ⏳ User feedback: Which option feels best?

---

## Investigation Plan

### Phase 1: Diagnosis (understand current state)
- [ ] Issue #1: Check API responses for grounding sources
- [ ] Issue #1: Review grounding source rendering logic
- [ ] Issue #2: Find pause implementation in codebase
- [ ] Issue #2: Test pause behavior with Temporal
- [ ] Issue #3: Review post-creation flow in frontend

### Phase 2: Root Cause Analysis
- [ ] Document findings for each issue
- [ ] Identify exact components/files that need changes
- [ ] Confirm expected behavior with user

### Phase 3: Solution Implementation
- [ ] Fix grounding source links
- [ ] Fix/clarify pause behavior
- [ ] Implement welcome email system
- [ ] Improve post-creation UX

---

### 5. AI Task Suggestion - notify_behavior Not Intelligently Chosen

**Symptoms:**
- When using "Magic Input" / AI-powered task creation, the suggested `notify_behavior` doesn't match user intent
- AI defaults to same behavior regardless of task type
- Users must manually change notification mode after AI suggestion

**ROOT CAUSE IDENTIFIED:**
- Backend prompt in `/api/v1/tasks/suggest` endpoint doesn't provide guidance on when to use each `notify_behavior`
- Current prompt just says: `- notify_behavior: One of "once", "always", "track_state"`
- No examples or rules for AI to understand which mode fits which use case

**Expected Behavior:**
The AI should intelligently choose `notify_behavior` based on task type:
- **"once"**: One-time announcements (product releases, date announcements, event confirmations)
  - Example: "When is next iPhone release?" → notify once when date announced
- **"always"**: Recurring opportunities (price drops, stock availability, new job postings)
  - Example: "PS5 in stock at Best Buy" → notify every time it comes back in stock
- **"track_state"**: Monitoring changes (when information changes or updates)
  - Example: "Capital of France" → notify when answer changes (rare, but comprehensive)

**Impact:**
- Users creating tasks via AI suggestion get suboptimal notification modes
- Extra manual work to correct after suggestion
- Reduced "magic" feeling of AI-powered task creation

**Potential Fix:**
Update the system instruction in `backend/src/torale/api/routers/tasks.py` (lines ~368-378) to include guidance:

```python
- notify_behavior: Choose intelligently based on the task type:
  * "once" - For one-time announcements (product releases, date announcements, event confirmations)
  * "always" - For recurring opportunities (price drops, stock availability, new job postings)
  * "track_state" - For monitoring changes (when information changes or updates)
```

**Files Involved:**
- `backend/src/torale/api/routers/tasks.py` (suggest_task endpoint, lines ~368-378)

**Investigation Status:**
- ✅ Root cause identified
- ⏳ User decision: Fix now or document for later?
- ⏳ Priority: Medium (UX polish, not critical)

---

## Notes

- All issues seem related to the user-facing experience after task creation/execution
- Focus area: Post-MVP polish and UX refinement
- No critical failures, but "emptiness" reduces user confidence in the platform
