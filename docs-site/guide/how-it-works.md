# How It Works

Torale combines Google Search with Gemini AI to create an intelligent web monitoring system. This page explains the technical details of how your monitoring tasks work.

## System Overview

```
User creates task → Temporal schedules execution
                             ↓
                    Temporal Worker picks up task
                             ↓
                    Grounded Search Executor
                             ↓
            Google Search (via Gemini grounding)
                             ↓
                  Gemini AI evaluates results
                             ↓
               Compares with last known state
                             ↓
          Condition met? → Store result + Notify user
```

## Core Components

### 1. Grounded Search

Torale uses **Gemini's grounded search** capability, which combines:
- **Google Search API** - Real-time web search results
- **Gemini AI** - Natural language understanding and evaluation
- **Source Attribution** - Verifiable citations from search results

**Why grounded search?**
- **Current Information** - Always gets latest data from the web
- **Context Understanding** - AI interprets results meaningfully
- **Source Verification** - Tracks where information comes from
- **No Hallucinations** - Grounded in actual search results

### 2. Condition Evaluation

When your task runs, the AI:

1. **Searches** - Performs Google search with your query
2. **Analyzes** - Reads and understands search results
3. **Evaluates** - Determines if your condition is met
4. **Explains** - Provides reasoning for its decision

**Example:**

Query: "When is the next iPhone being released?"
Condition: "A specific release date has been announced"

**AI Evaluation:**
```json
{
  "condition_met": true,
  "reasoning": "Apple has officially announced September 12, 2024 as the iPhone 16 release date",
  "answer": "The iPhone 16 will be released on September 12, 2024, according to Apple's official announcement.",
  "sources": [
    "https://www.apple.com/newsroom/...",
    "https://www.theverge.com/..."
  ]
}
```

### 3. State Tracking

Torale remembers previous execution results to avoid duplicate notifications:

**`last_known_state`** - Stores previous search results and evaluation

**Change Detection:**
- Compares current results with `last_known_state`
- Identifies meaningful changes vs. noise
- Only notifies on significant updates

**Example:**

| Execution | Result | State Changed? | Notify? |
|-----------|--------|---------------|---------|
| Day 1 | No release date | - | No |
| Day 2 | No release date | No | No |
| Day 3 | "September 12" | Yes | Yes ✓ |
| Day 4 | "September 12" | No | No |

This prevents notification spam when information hasn't meaningfully changed.

### 4. Temporal Workflows

Torale uses **Temporal** for reliable task execution:

**Benefits:**
- **Automatic Scheduling** - Cron-based execution
- **Retries** - Automatic retry on failures
- **Durability** - Survives system restarts
- **Observability** - Full execution history

**Workflow Steps:**
```python
async def monitoring_workflow(task_config):
    # 1. Fetch task configuration
    task = await get_task(task_config.task_id)

    # 2. Execute grounded search
    result = await execute_grounded_search(
        query=task.search_query,
        condition=task.condition_description
    )

    # 3. Compare with previous state
    has_changed = compare_states(
        current=result,
        previous=task.last_known_state
    )

    # 4. Notify if condition met and changed
    if result.condition_met and has_changed:
        await send_notification(task.user_id, result)

    # 5. Update task state
    await update_task_state(task.id, result)
```

## Execution Flow

### Step-by-Step Process

**1. Task Creation**
- User creates task via dashboard, CLI, or SDK
- Task stored in PostgreSQL database
- Temporal schedule created with cron expression

**2. Scheduled Execution**
- Temporal triggers workflow at scheduled time
- Worker picks up task from queue
- Executes grounded search activity

**3. Grounded Search Execution**
```python
# Simplified executor logic
async def execute_grounded_search(query, condition):
    # Search the web via Gemini
    search_results = await gemini.search(query)

    # Evaluate condition
    evaluation = await gemini.evaluate(
        results=search_results,
        condition=condition
    )

    # Extract sources
    sources = extract_grounding_sources(search_results)

    return {
        "condition_met": evaluation.is_met,
        "answer": evaluation.answer,
        "reasoning": evaluation.reasoning,
        "sources": sources
    }
```

**4. State Comparison**
```python
def compare_states(current, previous):
    if not previous:
        return True  # First execution

    # Check if condition status changed
    if current["condition_met"] != previous["condition_met"]:
        return True

    # Check if answer significantly changed
    similarity = calculate_similarity(
        current["answer"],
        previous["answer"]
    )

    return similarity < 0.85  # 85% threshold
```

**5. Notification & Storage**
- If condition met and state changed → Send notification
- Store execution result in database
- Update `last_known_state` on task
- Mark `condition_met` flag
- Update `last_notified_at` timestamp

## Notification Behaviors

### Once
Default behavior for one-time events:
- Notifies when condition first becomes true
- Pauses task after notification
- User must manually reactivate

**Use cases:** Product releases, event announcements

### Always
Notifies every time condition is met:
- No state comparison
- Notifies on every execution where condition is true
- Task remains active

**Use cases:** Price monitoring, stock alerts

### Track State
Advanced change detection:
- Compares full answer text with previous
- Notifies only on meaningful changes
- Uses similarity threshold (85%)
- Task remains active

**Use cases:** Tracking ongoing developments, monitoring status changes

## AI Models & Fallbacks

Torale uses **Gemini 2.0 Flash** as the primary model with fallbacks:

**Primary:** `gemini-2.0-flash-exp`
- Fast, cost-effective
- Native Google Search grounding
- Optimized for search tasks

**Fallbacks (if Gemini unavailable):**
1. OpenAI GPT-4 with web search
2. Anthropic Claude with web scraping

**Cost Optimization:**
- Flash model reduces cost by ~90% vs GPT-4
- Grounded search cheaper than manual scraping
- State tracking prevents unnecessary executions

## Security & Privacy

**Authentication:**
- Clerk OAuth (Google, GitHub)
- API key authentication for CLI
- JWT tokens for API access

**Data Privacy:**
- Search queries encrypted in transit
- Results stored securely in Cloud SQL
- Users can only access their own tasks

**Rate Limiting:**
- Per-user request limits
- Task execution throttling
- API endpoint rate limits

## Reliability & Error Handling

### Automatic Retries
Temporal automatically retries failed executions:
- Network errors → Retry with exponential backoff
- API rate limits → Wait and retry
- Temporary failures → Up to 3 retries

### Error Storage
All errors are logged and stored:
```json
{
  "execution_id": "...",
  "status": "failed",
  "error_message": "Rate limit exceeded",
  "retry_count": 2,
  "will_retry": true
}
```

### Monitoring
- Failed executions tracked in admin dashboard
- Alerts for consistent failures
- Temporal UI for workflow debugging

## Performance Characteristics

**Typical Execution Time:**
- Simple search: 2-5 seconds
- Complex evaluation: 5-10 seconds
- State comparison: <1 second

**Scalability:**
- Horizontal scaling with Kubernetes HPA
- Auto-scales based on CPU usage (2-10 replicas)
- Spot pods for cost optimization (60-91% savings)

**Cost per Execution:**
- Gemini Flash API call: ~$0.001
- Compute (GKE): ~$0.0001
- Database: ~$0.00001
- **Total: ~$0.001 per execution**

## Next Steps

- Learn about [State Tracking](/architecture/state-tracking) in detail
- Explore [Temporal Workflows](/architecture/temporal-workflows)
- Understand the [Executor System](/architecture/executors)
- Read about [Grounded Search](/architecture/grounded-search) implementation
