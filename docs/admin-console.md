# Admin Console

## Overview

The Torale admin console provides full platform visibility for the 100-user limited beta. It allows admins to monitor all user queries, track Temporal workflows, debug execution failures, and manage platform capacity.

## Purpose

For a 100-user beta platform, the admin console serves critical needs:
- **Usage Analysis**: See what users are actually monitoring
- **Debugging**: Quickly identify and fix execution failures
- **Capacity Management**: Track seats and manually manage user access
- **Platform Health**: Monitor Temporal workflows and schedules
- **Support**: View user queries and execution results for troubleshooting

## Authentication & Authorization

### Setting Up Admin Access

Torale uses Clerk's `publicMetadata` for role management. To make a user an admin:

**Option 1: Clerk Dashboard (Recommended)**
1. Navigate to [Clerk Dashboard](https://dashboard.clerk.com) → Users
2. Find your user account
3. Click "Edit User" → "Public metadata"
4. Add the following JSON:
   ```json
   {
     "role": "admin"
   }
   ```
5. Save changes

**Option 2: Clerk API**
```bash
curl -X PATCH "https://api.clerk.com/v1/users/{user_id}/metadata" \
  -H "Authorization: Bearer ${CLERK_SECRET_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "public_metadata": {
      "role": "admin"
    }
  }'
```

### Access Control

All admin endpoints require:
1. Valid Clerk authentication (JWT token)
2. `publicMetadata.role === "admin"` in Clerk user object

The backend verifies this via the `require_admin` dependency:

```python
def require_admin(current_user = Depends(get_current_user)):
    if current_user.get("public_metadata", {}).get("role") != "admin":
        raise HTTPException(403, "Admin access required")
    return current_user
```

Frontend routes check the role via Clerk's `useUser()` hook:

```typescript
const { user } = useUser();
if (user?.publicMetadata?.role !== 'admin') {
  return <Navigate to="/dashboard" />;
}
```

## Admin Console Features

### 1. Overview Dashboard

**Endpoint**: `GET /admin/stats`

**What You See**:
- **User capacity**: X/100 seats used, Y available
- **Task statistics**: Total active tasks, how many have triggered conditions
- **24-hour metrics**: Executions count, failure rate, success percentage
- **Popular queries**: Top 10 most common search queries with trigger counts

**Use Cases**:
- Quick health check of the platform
- Identify trending use cases
- Monitor daily activity levels
- Spot anomalies (high failure rates, low usage)

### 2. All Queries View

**Endpoint**: `GET /admin/queries?limit=100&active_only=false`

**What You See**:
- Every user's search query and condition description
- Task schedules (cron expressions)
- Execution counts per task
- Which queries have met their trigger conditions
- User email for each task
- Active/inactive status

**Use Cases**:
- **Usage research**: What are people actually monitoring?
- **Pattern discovery**: Common query types (product releases, price drops, event tickets)
- **Support**: Debug why a user's task isn't working
- **Feature ideas**: Identify gaps (e.g., many stock monitoring queries → build dedicated stock tracker)

**Example Data**:
```json
{
  "user_email": "user@example.com",
  "name": "iPhone Release Monitor",
  "search_query": "When is the next iPhone being released?",
  "condition_description": "A specific release date has been announced",
  "schedule": "0 9 * * *",
  "execution_count": 15,
  "trigger_count": 1,
  "condition_met": true,
  "is_active": true
}
```

### 3. Execution History

**Endpoint**: `GET /admin/executions?limit=50&status=<filter>&task_id=<filter>`

**What You See**:
- Full execution results with Gemini's answers
- Grounding sources (URLs that were used)
- Condition evaluation (met/not met)
- Change summaries (what changed from last check)
- Error messages for failed executions
- Execution duration and timestamps

**Query Parameters**:
- `limit`: Number of results (default: 50, max: 200)
- `status`: Filter by `success`, `failed`, or `running`
- `task_id`: Filter by specific task

**Use Cases**:
- **Debugging**: See exactly what Gemini returned and why a condition wasn't met
- **Verification**: Check grounding sources for accuracy
- **Performance**: Identify slow queries
- **Support**: Show users what their task is actually finding

**Example Execution Result**:
```json
{
  "id": "uuid",
  "task_id": "uuid",
  "user_email": "user@example.com",
  "search_query": "When is the next iPhone release?",
  "started_at": "2025-01-15T09:00:00Z",
  "completed_at": "2025-01-15T09:00:03Z",
  "status": "success",
  "condition_met": true,
  "result": {
    "answer": "Apple has announced the iPhone 16 will be released on September 20, 2025.",
    "evaluation": "The condition is met because a specific release date has been officially announced."
  },
  "grounding_sources": [
    {
      "uri": "https://www.apple.com/newsroom/2025/09/iphone-16-announcement/",
      "title": "Apple announces iPhone 16"
    }
  ],
  "change_summary": "New official release date announced (previously unconfirmed)"
}
```

### 4. Temporal Workflows

**Endpoints**:
- `GET /admin/temporal/workflows` - Recent workflow executions
- `GET /admin/temporal/schedules` - All active schedules

**What You See**:

**Schedules**:
- Schedule ID (matches task ID)
- Cron spec
- Next scheduled run time
- Paused/running status
- Recent action count

**Workflows**:
- Workflow ID and run ID
- Workflow type (e.g., `TaskExecutionWorkflow`)
- Status (RUNNING, COMPLETED, FAILED, TIMED_OUT)
- Start/close timestamps
- Execution duration

**Use Cases**:
- **Health monitoring**: Are schedules running as expected?
- **Debugging**: Identify stuck workflows
- **Capacity planning**: How many workflows are running concurrently?
- **Incident response**: Quickly spot temporal failures

**Example Schedule**:
```json
{
  "schedule_id": "task-abc123",
  "spec": "0 9 * * * (daily at 9am)",
  "paused": false,
  "next_run": "2025-01-16T09:00:00Z",
  "recent_actions": 15,
  "created_at": "2025-01-01T00:00:00Z"
}
```

### 5. Error Tracking

**Endpoint**: `GET /admin/errors?limit=50`

**What You See**:
- Failed execution details
- Full error messages and stack traces
- Associated user and task info
- Timestamp of failure

**Use Cases**:
- **Proactive monitoring**: Catch issues before users report them
- **Pattern identification**: Common failure types (API rate limits, malformed queries)
- **Quality improvement**: Fix problematic query patterns
- **User support**: Reach out to users with broken tasks

**Common Error Patterns**:
```
"Gemini API rate limit exceeded"
"Search query too vague, no relevant results"
"Temporal workflow timeout after 10 minutes"
"Database connection pool exhausted"
```

### 6. User Management

**Endpoint**: `GET /admin/users`

**What You See**:
- All user accounts with email and Clerk ID
- Signup date
- Task count per user
- Total execution count
- Number of triggered conditions
- Active/inactive status

**Actions**:
- `PATCH /admin/users/{user_id}/deactivate` - Manually deactivate a user (frees a seat)

**Use Cases**:
- **Capacity management**: See who's using seats
- **Power user identification**: Find most active users for feedback
- **Cleanup**: Deactivate dormant accounts
- **Support**: Quickly find user by email to debug their issues

### 7. Capacity Monitoring

**Endpoint**: `GET /auth/capacity` (Public - no auth required)

**What You See**:
```json
{
  "total": 100,
  "used": 87,
  "available": 13,
  "is_full": false
}
```

**Used By**:
- Landing page ("13 seats available")
- Admin dashboard
- Signup flow (block new signups when full)

## Backend Implementation

### Admin Routes Structure

All admin endpoints are in `backend/src/torale/api/routes/admin.py`:

```python
router = APIRouter(prefix="/admin", tags=["admin"])

# All routes use require_admin dependency
@router.get("/stats")
async def get_platform_stats(
    db = Depends(get_db),
    admin = Depends(require_admin)
): ...

@router.get("/queries")
async def list_all_queries(...): ...

@router.get("/executions")
async def list_recent_executions(...): ...

@router.get("/temporal/workflows")
async def list_temporal_workflows(...): ...

@router.get("/temporal/schedules")
async def list_temporal_schedules(...): ...

@router.get("/errors")
async def list_recent_errors(...): ...

@router.get("/users")
async def list_users(...): ...

@router.patch("/users/{user_id}/deactivate")
async def deactivate_user(...): ...
```

### Database Queries

Admin queries use aggregations and joins to provide comprehensive views:

```sql
-- Example: Get all queries with stats
SELECT
    t.id,
    t.search_query,
    t.condition_description,
    u.email as user_email,
    COUNT(te.id) as execution_count,
    SUM(CASE WHEN te.condition_met THEN 1 ELSE 0 END) as trigger_count
FROM tasks t
JOIN users u ON u.id = t.user_id
LEFT JOIN task_executions te ON te.task_id = t.id
GROUP BY t.id, u.email
ORDER BY t.created_at DESC;
```

### Temporal Client Integration

Admin endpoints create Temporal clients to query workflow/schedule state:

```python
# Connect to Temporal (Cloud or self-hosted)
if settings.temporal_api_key:
    client = await Client.connect(
        settings.temporal_host,
        namespace=settings.temporal_namespace,
        tls=True,
        api_key=settings.temporal_api_key,
    )
else:
    client = await Client.connect(
        settings.temporal_host,
        namespace=settings.temporal_namespace,
    )

# List schedules
async for schedule in client.list_schedules():
    handle = client.get_schedule_handle(schedule.id)
    desc = await handle.describe()
    # Process schedule info...
```

## Frontend Implementation

### Route Setup

Add admin route in `frontend/src/App.tsx`:

```typescript
import { AdminConsole } from './pages/Admin';

function App() {
  return (
    <Routes>
      {/* ... other routes */}
      <Route path="/admin" element={<AdminConsole />} />
    </Routes>
  );
}
```

### Navigation

Show admin link only to admin users:

```typescript
// In Navbar component
import { useUser } from '@clerk/clerk-react';

function Navbar() {
  const { user } = useUser();

  return (
    <nav>
      <Link to="/dashboard">Dashboard</Link>
      {user?.publicMetadata?.role === 'admin' && (
        <Link to="/admin">Admin Console</Link>
      )}
    </nav>
  );
}
```

### Component Structure

```typescript
export function AdminConsole() {
  const { user } = useUser();
  const [activeTab, setActiveTab] = useState('overview');

  // Role check
  if (user?.publicMetadata?.role !== 'admin') {
    return <Navigate to="/dashboard" />;
  }

  // Tab-based navigation
  return (
    <div className="admin-console">
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="queries">Queries</TabsTrigger>
          <TabsTrigger value="executions">Executions</TabsTrigger>
          <TabsTrigger value="temporal">Temporal</TabsTrigger>
          <TabsTrigger value="errors">Errors</TabsTrigger>
          <TabsTrigger value="users">Users</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <OverviewStats />
        </TabsContent>

        {/* Other tabs... */}
      </Tabs>
    </div>
  );
}
```

## Security Considerations

### Role-Based Access Control
- Admin role stored in Clerk's `publicMetadata` (visible to client)
- Backend **always** verifies role from Clerk JWT (can't be spoofed)
- Frontend role check is UX only - not security boundary

### Data Privacy
- Admins can see all user queries and results
- This is acceptable for 100-user beta with ToS agreement
- For production scale, consider:
  - Audit logging (who viewed what user's data)
  - User consent for data access
  - Anonymized analytics

### API Rate Limiting
- Admin endpoints should have rate limits (future)
- Prevent abuse: `GET /admin/executions` with large limits
- Consider pagination for large datasets

## Monitoring Best Practices

### Daily Admin Routine (5 minutes)

1. **Check Overview**: Any red flags? (high failure rate, low usage)
2. **Scan Errors**: Common patterns? Need fixes?
3. **Review Temporal**: Any stuck workflows?
4. **Capacity Check**: Approaching 100 users?

### Weekly Analysis (30 minutes)

1. **Popular Queries**: Identify feature opportunities
2. **User Engagement**: Who's active? Who churned?
3. **Performance**: Slow queries? Optimize them
4. **Support**: Reach out to users with failed tasks

### Alerts to Set Up (Future)

- Email when capacity > 95%
- Slack alert when failure rate > 10%
- Daily summary of new signups
- Weekly report of triggered conditions

## Common Debugging Scenarios

### Scenario 1: User reports "task not triggering"

**Steps**:
1. Go to "All Queries" tab
2. Find user by email
3. Click execution count → view recent executions
4. Check `condition_met` field and `result.evaluation`
5. Review grounding sources - are they relevant?
6. Common issue: Condition too vague or query not specific enough

### Scenario 2: High failure rate in stats

**Steps**:
1. Go to "Errors" tab
2. Look for common error patterns
3. Check if Gemini API rate limit hit
4. Check if Temporal workflows timing out
5. Fix root cause (add backoff, increase timeout, etc.)

### Scenario 3: Temporal schedule not running

**Steps**:
1. Go to "Temporal" tab → Schedules
2. Find schedule by task ID
3. Check if paused (shouldn't be unless user deactivated task)
4. Check "next_run" time - is it in the future?
5. Go to Workflows tab - see if executions are failing
6. Check Temporal UI for detailed workflow history

### Scenario 4: User hitting capacity limit

**Steps**:
1. Go to "Users" tab
2. Sort by "Tasks" column descending
3. Find inactive users (0 tasks, old signup date)
4. Click "Deactivate" to free seats
5. Or: Increase `MAX_USERS` if appropriate

## Future Enhancements

### Phase 2: Enhanced Analytics
- User retention metrics (DAU/MAU)
- Query category classification (price tracking, event monitoring, etc.)
- Temporal performance charts (execution time distribution)
- Cost tracking (Gemini API usage per user)

### Phase 3: Support Tools
- User impersonation ("View as user")
- Manual task execution from admin console
- Bulk task management (pause all failing tasks)
- Export functionality (CSV download of queries/executions)

### Phase 4: Automation
- Auto-pause tasks with 10+ consecutive failures
- Email notifications for critical errors
- Capacity alerts (90% full)
- Weekly admin digest emails

## Configuration

### Environment Variables

```bash
# Clerk (for role verification)
CLERK_SECRET_KEY=sk_test_...
CLERK_PUBLISHABLE_KEY=pk_test_...

# Temporal (for workflow querying)
TEMPORAL_HOST=us-central1.gcp.api.temporal.io:7233
TEMPORAL_NAMESPACE=quickstart-baldmaninc.g5zzo
TEMPORAL_API_KEY=eyJ...

# Platform limits
MAX_USERS=100  # Configurable capacity
```

### Feature Flags (Future)

```python
# backend/src/torale/core/config.py
class Settings(BaseSettings):
    admin_console_enabled: bool = True
    max_users: int = 100
    admin_query_limit: int = 500  # Max records per query
```

## API Reference

### GET /admin/stats
Returns platform-wide statistics.

**Response**:
```json
{
  "users": {
    "total": 87,
    "capacity": 100,
    "available": 13
  },
  "tasks": {
    "total": 234,
    "triggered": 45,
    "trigger_rate": "19.2%"
  },
  "executions_24h": {
    "total": 567,
    "failed": 12,
    "success_rate": "97.9%"
  },
  "popular_queries": [
    {
      "search_query": "When is the next iPhone release?",
      "count": 15,
      "triggered_count": 3
    }
  ]
}
```

### GET /admin/queries
List all user queries.

**Query Parameters**:
- `limit` (int, default: 100, max: 500)
- `active_only` (bool, default: false)

**Response**: Array of task objects with user info and stats.

### GET /admin/executions
List task execution history.

**Query Parameters**:
- `limit` (int, default: 50, max: 200)
- `status` (string): `success`, `failed`, `running`
- `task_id` (uuid): Filter by specific task

**Response**: Array of execution objects with full results.

### GET /admin/temporal/workflows
List recent Temporal workflow executions.

**Response**: Array of workflow objects from Temporal API.

### GET /admin/temporal/schedules
List all active Temporal schedules.

**Response**: Array of schedule objects with next run times.

### GET /admin/errors
List recent failed executions.

**Query Parameters**:
- `limit` (int, default: 50, max: 200)

**Response**: Array of failed executions with error messages.

### GET /admin/users
List all platform users.

**Response**:
```json
{
  "users": [
    {
      "id": "uuid",
      "email": "user@example.com",
      "clerk_user_id": "user_xyz",
      "is_active": true,
      "created_at": "2025-01-01T00:00:00Z",
      "task_count": 5,
      "total_executions": 123,
      "conditions_met_count": 8
    }
  ],
  "capacity": {
    "used": 87,
    "total": 100,
    "available": 13
  }
}
```

### PATCH /admin/users/{user_id}/deactivate
Manually deactivate a user account.

**Response**:
```json
{
  "status": "deactivated"
}
```

## Implementation Checklist

- [ ] Backend: Create `admin.py` routes file
- [ ] Backend: Implement `require_admin` dependency
- [ ] Backend: Add all admin endpoints
- [ ] Backend: Test Temporal client integration
- [ ] Frontend: Create `Admin.tsx` component
- [ ] Frontend: Add tab-based navigation
- [ ] Frontend: Implement data fetching for each tab
- [ ] Frontend: Add admin route and navbar link
- [ ] Security: Set first admin via Clerk dashboard
- [ ] Testing: Verify non-admins cannot access endpoints
- [ ] Documentation: Update API docs

**Estimated Effort**: 1 day (6-8 hours)
