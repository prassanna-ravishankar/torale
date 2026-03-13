---
description: Tasks API reference. Create, list, update, and delete monitoring tasks via REST API with JSON request/response examples.
---

# Tasks API

Create and manage monitoring tasks via REST API.

## Overview

Base URL: `https://api.torale.ai/api/v1/tasks`

All endpoints require authentication via API key or Clerk JWT token unless noted otherwise.

## Endpoints

### Create Task

Create a new monitoring task. The schedule is determined automatically by the agent -- it is not user-settable.

**Endpoint:** `POST /api/v1/tasks`

**Headers:**
```
Authorization: Bearer {api_key}
Content-Type: application/json
```

**Request body:**
```json
{
  "name": "iPhone Release Monitor",
  "search_query": "When is the next iPhone being released?",
  "condition_description": "Apple has officially announced a specific release date",
  "run_immediately": false,
  "notifications": [
    { "type": "email", "address": "me@example.com" }
  ]
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | No | Task name (default: `"New Monitor"`) |
| `search_query` | string | Yes | Search query for grounded search |
| `condition_description` | string | No | Condition to evaluate (defaults to `search_query` if omitted) |
| `state` | string | No | Initial state: `active` (default) or `paused` |
| `run_immediately` | boolean | No | Execute task immediately after creation (default: `false`) |
| `notifications` | array | No | Notification channel configs (email, webhook) |

**Response:** `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "660e8400-e29b-41d4-a716-446655440000",
  "name": "iPhone Release Monitor",
  "search_query": "When is the next iPhone being released?",
  "condition_description": "Apple has officially announced a specific release date",
  "state": "active",
  "next_run": "2025-01-15T10:31:00Z",
  "is_public": false,
  "view_count": 0,
  "subscriber_count": 0,
  "forked_from_task_id": null,
  "last_known_state": null,
  "last_execution_id": null,
  "last_execution": null,
  "notifications": [
    { "type": "email", "address": "me@example.com" }
  ],
  "state_changed_at": "2025-01-15T10:30:00Z",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": null,
  "immediate_execution_error": null
}
```

**Example:**
```bash
curl -X POST https://api.torale.ai/api/v1/tasks \
  -H "Authorization: Bearer sk_..." \
  -H "Content-Type: application/json" \
  -d '{
    "search_query": "When is the next iPhone release?",
    "condition_description": "A specific date has been announced"
  }'
```

### List Tasks

Get all tasks for authenticated user. Returns a bare JSON array (no pagination wrapper).

**Endpoint:** `GET /api/v1/tasks`

**Headers:**
```
Authorization: Bearer {api_key}
```

**Query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `state` | string | Filter by state: `active`, `paused`, or `completed` |

**Response:** `200 OK`

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "iPhone Release Monitor",
    "search_query": "When is the next iPhone being released?",
    "condition_description": "A specific date has been announced",
    "state": "active",
    "next_run": "2025-01-16T09:00:00Z",
    "is_public": false,
    "view_count": 0,
    "subscriber_count": 0,
    "forked_from_task_id": null,
    "last_known_state": null,
    "last_execution_id": null,
    "last_execution": null,
    "notifications": [],
    "state_changed_at": "2025-01-15T10:30:00Z",
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": null
  }
]
```

**Examples:**
```bash
# Get all tasks
curl -X GET https://api.torale.ai/api/v1/tasks \
  -H "Authorization: Bearer sk_..."

# Get only active tasks
curl -X GET "https://api.torale.ai/api/v1/tasks?state=active" \
  -H "Authorization: Bearer sk_..."
```

### Get Task

Get details for a specific task. Supports authenticated and unauthenticated access.

- Owner: full task details
- Public task, non-owner: read-only, sensitive fields (email, webhook, notifications) scrubbed
- Private task, non-owner: 404

**Endpoint:** `GET /api/v1/tasks/{id}`

**Response:** `200 OK`

Returns a Task object (same schema as create response). Includes embedded `last_execution` if available.

### Update Task

Update an existing task. Only provided fields are updated. State transitions are validated (e.g., `paused` -> `completed` is invalid).

**Endpoint:** `PUT /api/v1/tasks/{id}`

**Headers:**
```
Authorization: Bearer {api_key}
Content-Type: application/json
```

**Request body** (all fields optional):
```json
{
  "name": "Updated Task Name",
  "search_query": "New search query",
  "condition_description": "New condition",
  "state": "paused",
  "notifications": [
    { "type": "email", "address": "new@example.com" }
  ]
}
```

**Updatable fields:**

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Task name |
| `search_query` | string | Search query |
| `condition_description` | string | Condition to evaluate |
| `state` | string | `active`, `paused`, or `completed` |
| `notifications` | array | Notification channel configs |

**Response:** `200 OK` with updated Task object.

**State transition errors** return `400`:
```json
{
  "detail": "Invalid state transition: paused -> completed"
}
```

If a state transition fails (e.g., scheduler error), all changes in the request are rolled back.

### Delete Task

Delete a task and its scheduler job.

**Endpoint:** `DELETE /api/v1/tasks/{id}`

**Response:** `204 No Content`

### Execute Task Manually

Trigger immediate execution of a task ("Run Now"). Overrides any stuck execution.

**Endpoint:** `POST /api/v1/tasks/{id}/execute`

**Response:** `200 OK`

```json
{
  "id": "770e8400-e29b-41d4-a716-446655440000",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "started_at": "2025-01-15T10:30:00Z",
  "completed_at": null,
  "result": null,
  "error_message": null,
  "notification": null,
  "grounding_sources": null,
  "created_at": "2025-01-15T10:30:00Z"
}
```

Execution happens asynchronously. Poll the executions endpoint to check progress.

Returns `409 Conflict` if task is already running (unless force override).

### Update Task Visibility

Toggle a task between public and private.

**Endpoint:** `PATCH /api/v1/tasks/{id}/visibility`

**Request body:**
```json
{
  "is_public": true
}
```

**Response:** `200 OK`
```json
{
  "is_public": true
}
```

### Fork Task

Fork a public task. Creates a copy for the current user in `paused` state.

**Endpoint:** `POST /api/v1/tasks/{id}/fork`

**Request body** (optional):
```json
{
  "name": "My Copy of Task"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | No | Custom name for fork (default: `"{original name} (Copy)"`) |

**Response:** `200 OK` with the new Task object.

**Behavior:**
- Forked task starts in `paused` state, `is_public: false`
- Copies `search_query`, `condition_description`
- If forking another user's task, notification config is not copied (scrubbed)
- If forking your own task, notification config is preserved
- Forking another user's task increments `subscriber_count` on the original
- Sets `forked_from_task_id` on the new task

**Errors:**
- `404` if task not found or not public (and not owned)
- `409` if name collision after retries

## Task Object Schema

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique task identifier |
| `user_id` | UUID | Owner user ID |
| `name` | string | Task name |
| `search_query` | string | Search query for grounded search |
| `condition_description` | string | Condition to evaluate |
| `state` | string | `active`, `paused`, or `completed` |
| `next_run` | timestamp/null | Next scheduled execution time (set by agent) |
| `is_public` | boolean | Whether task is publicly visible |
| `view_count` | integer | Number of public views |
| `subscriber_count` | integer | Number of forks by other users |
| `forked_from_task_id` | UUID/null | Source task if this is a fork |
| `last_known_state` | object/null | Agent's state tracking data |
| `last_execution_id` | UUID/null | ID of the most recent execution |
| `last_execution` | object/null | Embedded last execution (when available) |
| `notifications` | array | Notification channel configurations |
| `notification_email` | string/null | Email for notifications |
| `webhook_url` | string/null | Webhook URL for notifications |
| `state_changed_at` | timestamp | When task state last changed |
| `immediate_execution_error` | string/null | Error from `run_immediately` (create only) |
| `created_at` | timestamp | Task creation time |
| `updated_at` | timestamp/null | Last update time |

### Notification Config Object

```json
{
  "type": "email",
  "address": "user@example.com"
}
```

or

```json
{
  "type": "webhook",
  "url": "https://your-app.com/webhook",
  "method": "POST",
  "headers": { "X-Custom": "value" }
}
```

At most one of each type is supported per task.

## Error Responses

### Validation Error

**Status:** `422 Unprocessable Entity`
```json
{
  "detail": [
    {
      "loc": ["body", "search_query"],
      "msg": "Field required",
      "type": "missing"
    }
  ]
}
```

### Not Found

**Status:** `404 Not Found`
```json
{
  "detail": "Task not found"
}
```

### Invalid State Transition

**Status:** `400 Bad Request`
```json
{
  "detail": "Invalid state transition: paused -> completed"
}
```

### Invalid Notification

**Status:** `400 Bad Request`
```json
{
  "detail": "Invalid notification: ..."
}
```

## Next Steps

- View [Executions API](/api/executions) to check task execution history
- Check [Notifications API](/api/notifications) for notification send history
- Read [Error Handling](/api/errors) guide
