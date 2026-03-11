---
description: Executions API reference. View task execution history, check status, retrieve results, and query execution details via REST API.
---

# Executions API

View task execution history and results.

## Overview

Base URL: `https://api.torale.ai/api/v1/tasks/{task_id}/executions`

Supports both authenticated and unauthenticated access (for public tasks).

## Endpoints

### Get Execution History

Get all executions for a specific task. Returns a bare JSON array (no pagination wrapper).

**Endpoint:** `GET /api/v1/tasks/{task_id}/executions`

**Query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | integer | Max results to return (default: 100) |

**Response:** `200 OK`

```json
[
  {
    "id": "770e8400-e29b-41d4-a716-446655440000",
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "success",
    "started_at": "2025-01-15T09:00:00Z",
    "completed_at": "2025-01-15T09:00:05Z",
    "result": {
      "evidence": "Search results confirm Apple announced iPhone 16 release...",
      "confidence": 95,
      "sources": ["https://apple.com/newsroom/..."]
    },
    "notification": "Apple has officially announced that the iPhone 16 will be released on September 20, 2025.",
    "grounding_sources": [
      {
        "uri": "https://www.apple.com/newsroom/2025/09/apple-announces-iphone-16/",
        "title": "Apple announces iPhone 16"
      }
    ],
    "error_message": null,
    "created_at": "2025-01-15T09:00:00Z"
  }
]
```

**Examples:**
```bash
# Get all executions (up to 100)
curl -X GET https://api.torale.ai/api/v1/tasks/550e8400.../executions \
  -H "Authorization: Bearer sk_..."

# Limit results
curl -X GET "https://api.torale.ai/api/v1/tasks/550e8400.../executions?limit=10" \
  -H "Authorization: Bearer sk_..."
```

**Access control:**
- Task owner: full access
- Public task: anyone can view executions (no auth required)
- Private task, non-owner: 404

## Execution Object Schema

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique execution identifier |
| `task_id` | UUID | Parent task ID |
| `status` | enum | `pending`, `running`, `success`, `retrying`, `failed`, `cancelled` |
| `started_at` | timestamp | When execution started |
| `completed_at` | timestamp/null | When execution completed (null if still running) |
| `result` | object/null | Agent result with evidence, confidence, sources |
| `notification` | string/null | User-facing notification message (null if condition not met) |
| `grounding_sources` | array/null | Source URLs backing the evidence |
| `error_message` | string/null | Error details if status is `failed` |
| `created_at` | timestamp | Execution creation time |

### Key difference: `notification` vs `result`

- `notification`: User-facing markdown message, only present when the condition was met. This is what gets sent to the user via email/webhook.
- `result`: Internal agent result with evidence and confidence. Present on all completed executions regardless of whether the condition was met.

## Execution Statuses

### pending
Initial state before execution starts.

### running
Execution in progress (searching, evaluating condition).

### success
Execution completed successfully. Check `notification` field to see if condition was met.

### retrying
Transient failure, will be retried automatically.

### failed
Persistent or user-actionable failure. Check `error_message` for details.

### cancelled
Execution was cancelled (e.g., by a manual "Run Now" that overrode a stuck execution).

## Task-Scoped Notifications

Filter executions to only those where the condition was met.

**Endpoint:** `GET /api/v1/tasks/{task_id}/notifications`

**Query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | integer | Max results to return (default: 100) |

**Response:** `200 OK`

Returns the same execution object array, but filtered to only executions where `notification IS NOT NULL`.

```json
[
  {
    "id": "770e8400-e29b-41d4-a716-446655440000",
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "success",
    "notification": "Apple has officially announced the iPhone 16 release date...",
    "grounding_sources": [...],
    "started_at": "2025-01-15T09:00:00Z",
    "completed_at": "2025-01-15T09:00:05Z",
    "result": {...},
    "error_message": null,
    "created_at": "2025-01-15T09:00:00Z"
  }
]
```

Same access control rules as the executions endpoint.

## Error Responses

### Not Found

**Status:** `404 Not Found`
```json
{
  "detail": "Task not found"
}
```

Returned when the task doesn't exist, or is private and the requester is not the owner.

## Next Steps

- View [Notifications API](/api/notifications) for notification send history
- Check [Tasks API](/api/tasks) for task management
- Read [Error Handling](/api/errors) guide
