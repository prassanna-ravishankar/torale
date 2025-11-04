# Torale Frontend

Web interface for the Torale grounded search monitoring platform.

## Problem Statement

Users need to monitor the web for specific conditions ("Tell me when the next iPhone is announced", "Alert me when pool memberships open") without manually checking multiple sources or understanding complex automation tools.

**Core Challenge**: Make AI-powered web monitoring accessible to non-technical users while maintaining transparency about how monitoring works and why conditions trigger.

## What the Frontend Must Solve

### 1. Task Creation & Management
**Problem**: Users need to express monitoring intent in natural language and understand how it will be executed.

**Required Capabilities**:
- Create tasks by describing **what to search** and **when to notify**
- Translate user intent into search queries and trigger conditions
- Configure monitoring schedules (frequency of checks)
- Choose notification behavior (once, always, on state change)
- Enable/disable active monitoring
- Delete unwanted tasks

**Key Challenges**:
- Making cron schedules human-readable ("every day at 9am" vs "0 9 * * *")
- Helping users write effective search queries
- Setting appropriate check frequencies (avoid over-checking)
- Explaining what "condition met" means for their specific task

### 2. Notifications & Alerts
**Problem**: Users need to know immediately when their monitored condition is met, with evidence.

**Required Capabilities**:
- Display notifications where condition was met
- Show **what changed** from last check (state comparison)
- Provide **grounding sources** (URLs) as evidence
- Explain **why** the condition triggered
- Filter full execution history vs. notifications only

**Key Challenges**:
- Distinguishing "condition met" from regular executions
- Presenting grounding sources credibly (are these URLs trustworthy?)
- Showing state changes clearly ("release date changed from unknown to Sept 12")
- Managing notification fatigue (too many alerts)

### 3. Execution Transparency
**Problem**: Users need to trust the system is working and understand what it's finding.

**Required Capabilities**:
- View execution history per task
- See what the LLM found during each search
- Display grounding sources (search result URLs)
- Show execution status (pending, running, success, failed)
- Explain failures clearly
- Track last execution time and next scheduled run

**Key Challenges**:
- Making LLM responses understandable (technical jargon vs. plain language)
- Displaying source attribution without overwhelming users
- Explaining temporal workflows to non-technical users
- Showing why something *didn't* trigger

### 4. State & History Visualization
**Problem**: Users need to see how monitored information changes over time.

**Required Capabilities**:
- Show current state vs. historical state
- Display "last known state" for each task
- Track when condition was last met
- Visualize execution timeline
- Compare states across executions

**Key Challenges**:
- Representing unstructured state data (JSON) visually
- Showing what changed between states
- Making historical data useful (not just logs)
- Balancing detail vs. simplicity

### 5. Authentication & Onboarding
**Problem**: New users need to understand what Torale does and create their first monitoring task.

**Required Capabilities**:
- User registration and login (JWT-based)
- First-time user guidance
- Example monitoring use cases
- Quick task templates ("Monitor product availability", "Track release dates")

**Key Challenges**:
- Explaining grounded search in simple terms
- Setting realistic expectations (LLM accuracy, search limitations)
- Avoiding analysis paralysis (too many options)
- Getting users to their first successful notification quickly

## Backend API Reference

The backend provides these endpoints (see `backend/src/torale/api/routers/tasks.py`):

```
POST   /auth/register                      # Create account
POST   /auth/jwt/login                     # Get JWT token

POST   /api/v1/tasks                       # Create monitoring task
GET    /api/v1/tasks                       # List tasks
GET    /api/v1/tasks/{id}                  # Get task details
PUT    /api/v1/tasks/{id}                  # Update task
DELETE /api/v1/tasks/{id}                  # Delete task
POST   /api/v1/tasks/{id}/execute          # Manual execution (testing)
GET    /api/v1/tasks/{id}/executions       # Full execution history
GET    /api/v1/tasks/{id}/notifications    # Filtered: condition_met = true
```

## Data Models

### Task
```typescript
{
  id: UUID
  name: string
  schedule: string  // cron expression
  executor_type: "llm_grounded_search"
  search_query: string  // "When is next iPhone release?"
  condition_description: string  // "A specific date is announced"
  notify_behavior: "once" | "always" | "track_state"
  is_active: boolean

  // State tracking
  condition_met: boolean
  last_known_state: object  // Extracted structured data
  last_notified_at: datetime | null

  // Metadata
  created_at: datetime
  updated_at: datetime | null
}
```

### Task Execution
```typescript
{
  id: UUID
  task_id: UUID
  status: "pending" | "running" | "success" | "failed"
  started_at: datetime
  completed_at: datetime | null

  // Grounded search results
  result: {
    answer: string  // LLM's synthesis of search results
    current_state: object  // Extracted structured data
  }
  condition_met: boolean  // Did trigger condition fire?
  change_summary: string | null  // What changed from last run
  grounding_sources: Array<{
    url: string
    title: string
  }>

  // Error handling
  error_message: string | null
}
```

## User Flows to Support

### Primary Flow: Create First Monitoring Task
1. User describes what they want to monitor
2. System helps form search query + condition
3. User sets check frequency
4. System confirms task created and when first check runs
5. User sees task appear in dashboard with "pending" status

### Secondary Flow: Get Notified When Condition Triggers
1. Temporal runs scheduled search
2. LLM evaluates condition
3. Condition met → creates notification
4. User sees notification in UI
5. User views evidence (grounding sources, state change)

### Tertiary Flow: Review Execution History
1. User selects a task
2. Views timeline of executions
3. Sees what was found each time
4. Understands why condition did/didn't trigger
5. Adjusts search query or condition if needed

## Design Considerations (Decisions Needed)

- **Framework choice**: React, Next.js, Vue, Svelte?
- **State management**: Context, Redux, Zustand, TanStack Query?
- **Styling approach**: Tailwind, CSS-in-JS, component library?
- **Real-time updates**: Polling, WebSockets, SSE?
- **Notification UX**: In-app only, or integrate browser notifications?
- **Mobile responsiveness**: Mobile-first, desktop-first, or progressive?
- **Accessibility**: WCAG compliance level?

## Quick Start

```bash
# Start backend services
just dev

# Frontend development (to be added)
cd frontend
# Install dependencies
# Start dev server
# Run tests
```

## Structure

TBD - Will be organized based on chosen framework and architecture decisions.
