# Agent Architecture

Torale uses a Claude-powered monitoring agent instead of the previous multi-provider pipeline.

## Architecture Overview

```
APScheduler (cron trigger)
    ↓
Backend (job.py orchestrator)
    ↓
Agent (Claude + MCP tools)
    ↓
Structured Response → Persist + Notify + Reschedule
```

## Agent Workflow

The agent receives a prompt with the task's search query, condition, and previous evidence, then:

1. **Gets current datetime** via MCP tool
2. **Retrieves memories** from Mem0 (scoped to task)
3. **Searches** via Perplexity MCP tool
4. **Evaluates** condition against search results
5. **Stores** new meta-knowledge in Mem0
6. **Returns** structured response

## Response Format

```json
{
  "evidence": "Internal reasoning and findings (audit trail)",
  "sources": ["url1", "url2"],
  "confidence": 0-100,
  "next_run": "ISO timestamp or null",
  "notification": "User-facing message or null"
}
```

## Backend Orchestration

`job.py` handles the execution lifecycle:

1. Creates execution record in database
2. Calls agent via A2A JSON-RPC
3. Maps response to `task_executions` row
4. Sends notifications if condition met
5. Auto-completes task if `notify_behavior="once"`
6. Dynamically reschedules via agent's `next_run`

## Benefits

1. **Single call** — No multi-step pipeline coordination
2. **Agent memory** — Mem0 provides cross-run context without explicit state management
3. **Dynamic scheduling** — Agent adjusts check frequency based on context
4. **Simpler error handling** — Retry the whole call, not individual activities
