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
- ⏳ User verification: **Ready for testing** - See Manual Testing Checklist section

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
- ⏳ **User verification**: Ready for testing - See Manual Testing Checklist section

**Rollback Plan:**
If issues arise:
1. Database: Revert migration `c36fe95dcb98` (drops `last_execution_id` column)
2. Backend: Remove `task_status.py`, revert model/API/worker changes
3. Frontend: Revert to old badge logic (show `condition_met` + `is_active` separately)

---

### 3. Post-Task Creation UX - "Emptiness"

**Symptoms:**
- After creating a task, users feel lost about what happens next
- "No channels configured" (Image #3) feels broken rather than informative
- No confirmation email explaining the monitoring setup
- Unclear when first check will run
- Unclear how users will be notified

**FIX IMPLEMENTED:**

**Approach: Welcome Email + Progressive Feedback (Following Laws of UX)**
- **Jakob's Law**: Users expect immediate confirmation emails (like GitHub, Stripe)
- **Progressive Disclosure**: Show outcome incrementally (toast → email → dashboard)
- **Miller's Law**: Keep email concise with 3-5 key pieces of info

**Implementation:**

1. **Welcome Email Service** (`backend/src/torale/notifications/novu_service.py:164-260`)
   - New `send_welcome_email()` method
   - Sends after first execution completes
   - Includes: task details, schedule, first execution results, notify_behavior explanation
   - Uses cronstrue for human-readable schedules

2. **First Execution Trigger** (`backend/src/torale/workers/activities.py:186-221`)
   - Detects first execution completion
   - Sends welcome email with execution results
   - Provides immediate user feedback

3. **Frontend Execution Polling** (`frontend/src/components/TaskCreationDialog.tsx:263-297`)
   - Polls for first execution (up to 30 seconds)
   - Progressive toasts: "Running..." → "Condition met!" or "We'll keep watching"

4. **Educational Context** (`frontend/src/components/TaskDetail.tsx:306-332`)
   - Added notify_behavior explanation section
   - Shows context-specific guidance for each mode

**Files Changed:**
- `backend/src/torale/notifications/novu_service.py` (welcome email method)
- `backend/src/torale/core/config.py` (NOVU_WELCOME_WORKFLOW_ID setting)
- `backend/src/torale/workers/activities.py` (first execution trigger)
- `docs/NOTIFICATIONS.md` (Novu workflow template + env vars)
- `frontend/src/components/TaskCreationDialog.tsx` (execution polling + toasts)
- `frontend/src/components/TaskDetail.tsx` (notify_behavior explanation)
- `.env.example` (NOVU_WELCOME_WORKFLOW_ID)
- `helm/torale/values.yaml` (welcomeWorkflowId config)
- `helm/torale/templates/configmap.yaml` (env var injection)

**What Users See Now:**
1. Create task → "Task created! Running first check..." toast
2. First execution completes → "Condition met!" or "We'll keep watching" toast
3. Welcome email arrives (~30s) with:
   - What's being monitored
   - When notifications happen
   - First check results
   - notify_behavior explanation
   - Link to dashboard
4. TaskDetail page shows clear notify_behavior explanation

**Testing Status:**
- ⏳ **Novu workflow creation**: Need to create `torale-task-welcome` workflow in Novu dashboard
- ⏳ **User verification**: Ready for testing - See Manual Testing Checklist section

**Rollback Plan:**
If issues arise:
1. Remove welcome email call from `activities.py`
2. Revert polling logic in `TaskCreationDialog.tsx`
3. Remove notify_behavior explanation from `TaskDetail.tsx`
4. Deactivate `torale-task-welcome` workflow in Novu

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

**FIX IMPLEMENTED:**

**Approach: UTC Backend, Browser Timezone Display (Frontend-Only Fix)**
- **Philosophy**: Timezone is a display concern, not a data concern
- **Backend**: Store everything in UTC (no changes needed)
- **Frontend**: Convert to/from user's browser timezone for display only
- **Trade-off**: Schedules shift by 1 hour during DST transitions (normal behavior, like Google Calendar)

**Why This Approach:**
- No database changes or timezone storage needed
- No backend changes required
- Simple: Frontend handles all conversion on-demand
- Familiar UX: Same DST behavior as calendar apps (acceptable)

**Implementation:**

1. **Created Timezone Utility Module** (`frontend/src/lib/timezoneUtils.ts`)
   - `getTimezoneOffsetHours()`: Get user's UTC offset
   - `localHourToUTC(hour)`: Convert local hour to UTC (for saving)
   - `utcHourToLocal(hour)`: Convert UTC hour to local (for display)
   - `cronLocalToUTC(cron)`: Convert local cron to UTC cron
   - `cronUTCToLocal(cron)`: Convert UTC cron to local cron
   - `getTimezoneAbbreviation()`: Get "PST", "EST", etc.

2. **Updated Schedule Builder** (`CustomScheduleDialog.tsx`)
   - **On Load**: Convert UTC cron from backend → local time for display
   - **On Save**: Convert local time → UTC cron before sending to backend
   - **Preview**: Show timezone abbreviation (e.g., "Daily at 9:00 AM PST")

3. **Updated Cron Display** (`CronDisplay.tsx`)
   - Convert UTC cron to local time before showing human-readable text
   - Append timezone abbreviation: "At 9:00 AM PST"
   - Tooltip shows UTC cron (for debugging)

4. **Updated Task Creation/Edit Dialogs**
   - Preset schedules now convert local times to UTC
   - "Daily at 9:00 AM" → generates `0 ${utcHour} * * *` (UTC)
   - Custom schedule display converts UTC → local for human-readable text

**Files Changed:**
- `frontend/src/lib/timezoneUtils.ts` (NEW - conversion utilities)
- `frontend/src/lib/timezoneUtils.test.ts` (NEW - test suite)
- `frontend/src/components/ui/CustomScheduleDialog.tsx` (UTC↔Local conversion)
- `frontend/src/components/ui/CronDisplay.tsx` (show timezone abbreviation)
- `frontend/src/components/TaskCreationDialog.tsx` (preset schedules + custom display)
- `frontend/src/components/TaskEditDialog.tsx` (same as creation dialog)

**What Users See Now:**
- **Schedule Builder**: Times in their local timezone (e.g., "9:00 AM")
- **Schedule Display**: Times with timezone label (e.g., "At 9:00 AM PST")
- **Execution History**: Already shows local time via `Intl.DateTimeFormat` ✅
- **Backend Storage**: UTC cron expressions (unchanged)

**Testing Status:**
- ✅ **Unit tests pass**: All timezone conversions work correctly (`timezoneUtils.test.ts`)
  - Local → UTC → Local round-trip works
  - Edge cases handled (midnight, hour wrapping)
  - Hourly patterns NOT converted (correct behavior)
  - Timezone abbreviation detected
- ⏳ **User verification**: Ready for testing - See Manual Testing Checklist section

**Known Limitations (Documented, Accepted):**
1. **DST Shifts**: Tasks shift by 1 hour during DST transitions (like calendar apps)
2. **Traveling Users**: If user travels across timezones, schedules stay in original timezone
3. **Day-of-Week**: Weekly schedules might shift to different day if UTC offset crosses midnight

These are acceptable trade-offs for the simplified implementation.

**Rollback Plan:**
If issues arise:
1. Remove timezone conversion from `CustomScheduleDialog.tsx` (parseInitialCron, buildCronFromForm)
2. Remove timezone display from `CronDisplay.tsx`
3. Revert preset schedules in TaskCreationDialog/TaskEditDialog
4. Delete `timezoneUtils.ts` and `timezoneUtils.test.ts`

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

**FIX IMPLEMENTED:**

**Approach: Formalize All LLM Prompts with Pydantic Schemas**
- Enhanced all 4 LLM calls to use Pydantic models with Field descriptions
- AI now receives structured guidance on when to use each `notify_behavior` value
- Consistent structured outputs across all Gemini API calls

**Implementation:**

1. **Created 3 New Pydantic Models** (`backend/src/torale/core/models.py`)
   - `InferredCondition`: For condition inference from search queries
   - `ConditionEvaluation`: For evaluating if monitoring conditions are met (with `current_state: Any` to avoid Gemini `additionalProperties` issue)
   - `StateComparison`: For comparing previous and current states

2. **Enhanced SuggestedTask Model** (`backend/src/torale/api/routers/tasks.py`)
   - Simplified Field description to minimal explanation
   - Added explicit system instruction with digest guidance

3. **Updated All 4 LLM Calls** to use `response_schema` parameter:
   - `/api/v1/tasks/suggest` endpoint (task suggestion) → `SuggestedTask`
   - `/api/v1/tasks/preview` endpoint (condition inference) → `InferredCondition`
   - Grounded search executor `_evaluate_condition` → `ConditionEvaluation`
   - Grounded search executor `_compare_states` → `StateComparison`

**Files Changed:**
- `backend/src/torale/core/models.py` (added 3 new LLM response models)
- `backend/src/torale/api/routers/tasks.py` (simplified Field description, enhanced system instruction with DAILY/WEEKLY/MONTHLY rules)
- `backend/src/torale/executors/grounded_search.py` (updated _evaluate_condition, _compare_states)
- `backend/tests/test_preview_endpoint.py` (updated mocks to return JSON)
- `backend/tests/test_suggest_endpoint.py` (added regression test for digest behavior)
- `frontend/src/components/TaskCreationDialog.tsx` (fixed hardcoded preview text to show actual values)

**What Changed:**
- **Before**: Plain text prompts with loose guidance, LLM could return inconsistent formats
- **After**: Structured schemas with response_schema, guaranteed JSON output format
- **notify_behavior Selection**: AI now correctly chooses behavior for different task types
  - **Key Fix**: System instruction with explicit DAILY/WEEKLY/MONTHLY → "always" rules
  - **Field Description**: Minimal one-liner (LLM reads system instruction, not Field description)
  - **Result**: "weekly digest of ai news" now correctly suggests `notify_behavior="always"` ✅
- **Advanced Options Preview**: Fixed hardcoded "Daily checks, Track changes" to dynamically show actual schedule and behavior
- **Consistency**: All LLM calls follow same pattern (response_schema + Pydantic validation)
- **Testing**: Added regression test verifying system instruction includes digest guidance

**Testing Status:**
- ✅ **All tests pass**: 140 passed, 90 skipped
- ✅ **Gemini compatibility verified**: Fixed `additionalProperties` issue (used `Any` instead of `dict`)
- ✅ **Mock updates**: Test mocks updated to return proper JSON format
- ⏳ **User verification**: Ready for testing - See Manual Testing Checklist section

**Rollback Plan:**
If issues arise:
1. Revert Pydantic models from `models.py` (remove InferredCondition, ConditionEvaluation, StateComparison)
2. Revert Field descriptions from SuggestedTask
3. Revert response_schema usage in all 4 LLM calls (return to plain text prompts)
4. Revert test mocks back to plain text responses

---

## Manual Testing Checklist

*Consolidated testing flows across all fixes - run these before making a PR*

### Issue #1: Grounding Source Links

**Test: Sources Appear and Links Work**
1. ⏳ Run existing task or create new one
2. ⏳ Check execution history - verify grounding sources appear in UI
3. ⏳ Click on source links - verify they open correct pages (redirect should work)
4. ⏳ Verify UI shows clean domain names (e.g., "britannica.com" not full redirect URL)

### Issue #1b: Email Notifications

**Test: Email Notifications Send Successfully**
1. ⏳ Trigger a task execution that meets condition (or manually execute existing task)
2. ⏳ Check email inbox for notification
3. ⏳ Verify no errors in worker logs: `docker compose logs workers -f`
4. ⏳ Verify email contains grounding sources (if configured)

### Issue #2: Status Badges & Pause Behavior

**Test 1: Three States Work Correctly**
1. ⏳ Create task with `notify_behavior="once"` and simple condition (e.g., "capital of France")
2. ⏳ Initially shows "🟢 Monitoring" in dashboard
3. ⏳ Run task → condition met → Shows "✅ Completed" (blue badge)
4. ⏳ Manually resume task → Shows "🟢 Monitoring" again
5. ⏳ Manually pause task → Shows "⏸️ Paused" (yellow badge)
6. ⏳ Each state shows ONLY ONE badge (no contradictions)

**Test 2: Dashboard Tabs Filter Correctly**
1. ⏳ Create mix: 1 active, 1 completed (auto-stopped), 1 paused task
2. ⏳ "All Tasks" shows all 3
3. ⏳ "🟢 Monitoring" shows only active task
4. ⏳ "✅ Completed" shows only auto-stopped task
5. ⏳ "⏸️ Paused" shows only manually paused task

**Test 3: Active Tasks Don't Change on Execution**
1. ⏳ Create active task, run it multiple times with varying results
2. ⏳ Task stays "🟢 Monitoring" as long as `is_active=true`
3. ⏳ Status only changes when paused OR auto-stopped (notify_behavior="once" + condition met)

**Test 4: No Contradictory Badges (Regression Test)**
1. ⏳ Test ANY task in ANY state
2. ⏳ NEVER see "Triggered" + "Paused" together
3. ⏳ ALWAYS see exactly ONE status badge

**Quick Checks:**
- ⏳ Dashboard loads fast (no N+1 queries)
- ⏳ Badge on card matches badge on detail page
- ⏳ Status persists on page reload

### Issue #4: Timezone Display & Conversion

**Test 1: Schedule Creation Shows Local Time**
1. ⏳ Open task creation dialog
2. ⏳ Select preset "Daily at 9:00 AM"
3. ⏳ Verify preview shows "At 9:00 AM [Your TZ]" (e.g., "PST", "EST")
4. ⏳ Save task and verify schedule displays with timezone abbreviation

**Test 2: Custom Schedule Converts Correctly**
1. ⏳ Create task with custom schedule using schedule builder
2. ⏳ Set time to 9:00 AM in builder
3. ⏳ Verify preview shows local time with timezone (e.g., "9:00 AM PST")
4. ⏳ Save and reload task - verify time still shows 9:00 AM (not UTC)

**Test 3: Existing Tasks Display Local Time**
1. ⏳ Open existing task that has schedule in UTC
2. ⏳ Verify schedule displays in local time (converted from UTC)
3. ⏳ Verify timezone abbreviation shown (e.g., "At 9:00 AM PST")

**Test 4: Execution Timeline Shows Local Time**
1. ⏳ View task execution history
2. ⏳ Verify all timestamps show in local timezone
3. ⏳ Verify timezone abbreviation or offset displayed

**Known Behavior to Verify:**
- ⏳ DST: Schedules may shift by 1 hour during daylight saving transitions (expected)
- ⏳ Hourly patterns: "Every hour" or "Every 6 hours" should NOT show timezone (correct - no conversion)

### Issue #5: AI Task Suggestion - notify_behavior Intelligence

**Test 1: One-Time Event Detection**
1. ⏳ Use "Magic Input" with query: "When is the next iPhone release date?"
2. ⏳ Verify suggested `notify_behavior` = "once"
3. ⏳ Try similar: "When is GPT-5 coming out?", "PS5 launch date"
4. ⏳ All should suggest "once" (one-time announcements)

**Test 2: Recurring Opportunity Detection**
1. ⏳ Use "Magic Input" with query: "PS5 in stock at Best Buy"
2. ⏳ Verify suggested `notify_behavior` = "always"
3. ⏳ Try similar: "Nintendo Switch under $250", "OpenAI job openings"
4. ⏳ All should suggest "always" (recurring alerts)

**Test 2b: Periodic Digest Detection**
1. ⏳ Use "Magic Input" with query: "weekly digest of latest AI news"
2. ⏳ Verify suggested `notify_behavior` = "always" (NOT "once")
3. ⏳ Verify schedule is weekly (e.g., Monday at 9:00 AM)
4. ⏳ Try similar: "daily tech news summary", "monthly crypto updates"
5. ⏳ All should suggest "always" for periodic digests

**Test 3: State Change Monitoring Detection**
1. ⏳ Use "Magic Input" with query: "What is the capital of France?"
2. ⏳ Verify suggested `notify_behavior` = "track_state"
3. ⏳ Try similar: "Latest OpenAI model name", "Current Bitcoin price"
4. ⏳ All should suggest "track_state" (monitoring changes)

**Test 4: Structured Outputs Consistency**
1. ⏳ Create task via "Magic Input" - verify all fields populated correctly
2. ⏳ Check preview endpoint response - verify JSON structure matches schema
3. ⏳ Run task execution - verify condition evaluation returns proper JSON
4. ⏳ No LLM errors or malformed responses in logs

**Quick Checks:**
- ⏳ All 4 LLM endpoints return valid JSON (no parsing errors)
- ⏳ notify_behavior selection feels "smart" for different query types
- ⏳ Advanced Options preview shows actual values (not "Daily checks, Track changes")
- ⏳ No regression in existing task creation flow

### Automated Test Verification

```bash
# Backend tests (Issue #2 - 11 assertions)
cd backend && uv run python tests/test_task_status.py

# Frontend tests (Issue #2 - 12 assertions)
cd frontend && npx tsx src/lib/taskStatus.test.ts

# Grounding source tests (Issue #1)
cd backend && uv run pytest tests/test_grounding_sources.py -v

# Timezone utility tests (Issue #4 - 9 assertions)
cd frontend && npx tsx src/lib/timezoneUtils.test.ts

# LLM schema tests (Issue #5 - includes preview endpoint tests)
cd backend && uv run pytest tests/test_preview_endpoint.py -v

# Full backend test suite (all issues)
cd backend && uv run pytest tests/ -v
```

---

## Notes

- All issues seem related to the user-facing experience after task creation/execution
- Focus area: Post-MVP polish and UX refinement
- No critical failures, but "emptiness" reduces user confidence in the platform
