---
description: Watches API reference. Create, list, update, and delete watches via REST API with JSON request/response examples.
---

# Watches API

Create and manage watches via REST API.

::: tip Naming during the transition
URLs still address watches as `tasks` (`/api/v1/tasks`) and the JSON payloads still use the `Task` shape. The rename to `webwhen` is a later phase — this page reflects the current shipping API.
:::

## Overview

Base URL: `https://api.webwhen.ai/api/v1/tasks`

Every endpoint requires authentication via API key or Clerk JWT unless noted otherwise.

## Endpoints

### Create a watch

Create a new watch. The schedule is determined automatically by the agent — it isn't user-settable.

**Endpoint:** `POST /api/v1/tasks`

**Headers:**
```
Authorization: Bearer {api_key}
Content-Type: application/json
```

**Request body:**
```json
{
  "name": "iPhone Release Watch",
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
| `name` | string | No | Watch name (default: `"New Monitor"`) |
| `search_query` | string | Yes | Search query for grounded search |
| `condition_description` | string | No | Condition to evaluate (defaults to `search_query` if omitted) |
| `state` | string | No | Initial state: `active` (default) or `paused` |
| `run_immediately` | boolean | No | Execute the watch immediately after creation (default: `false`) |
| `notifications` | array | No | Notification channel configs (email, webhook) |

**Response:** `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "660e8400-e29b-41d4-a716-446655440000",
  "name": "iPhone Release Watch",
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
curl -X POST https://api.webwhen.ai/api/v1/tasks \
  -H "Authorization: Bearer sk_..." \
  -H "Content-Type: application/json" \
  -d '{
    "search_query": "When is the next iPhone release?",
    "condition_description": "A specific date has been announced"
  }'
```

### List watches

Get every watch for the authenticated user. Returns a bare JSON array (no pagination wrapper).

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
    "name": "iPhone Release Watch",
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
# Get all watches
curl -X GET https://api.webwhen.ai/api/v1/tasks \
  -H "Authorization: Bearer sk_..."

# Get only active watches
curl -X GET "https://api.webwhen.ai/api/v1/tasks?state=active" \
  -H "Authorization: Bearer sk_..."
```

### Get a watch

Get details for a specific watch. This endpoint requires authentication.

- Owner: full watch details
- Public watch, authenticated non-owner: read-only, sensitive fields scrubbed
- Private watch, non-owner: 404

**Endpoint:** `GET /api/v1/tasks/{id}`

**Response:** `200 OK`

Returns a Task object (same schema as the create response). Includes embedded `last_execution` when available.

For anonymous access, use `GET /api/v1/public/tasks/id/{id}`. That endpoint
only returns public watches and always strips owner identity and notification
configuration, even when the request includes credentials.

### Update a watch

Update an existing watch. Only the fields provided are updated. State transitions are validated (for example, `paused` → `completed` is invalid).

**Endpoint:** `PUT /api/v1/tasks/{id}`

**Headers:**
```
Authorization: Bearer {api_key}
Content-Type: application/json
```

**Request body** (all fields optional):
```json
{
  "name": "Updated Watch Name",
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
| `name` | string | Watch name |
| `search_query` | string | Search query |
| `condition_description` | string | Condition to evaluate |
| `state` | string | `active`, `paused`, or `completed` |
| `notifications` | array | Notification channel configs |

**Response:** `200 OK` with the updated Task object.

**State transition errors** return `400`:
```json
{
  "detail": "Invalid state transition: paused -> completed"
}
```

If a state transition fails (for example, a scheduler error), every change in the request is rolled back.

### Delete a watch

Delete a watch and its scheduler job.

**Endpoint:** `DELETE /api/v1/tasks/{id}`

**Response:** `204 No Content`

### Execute a watch manually

Trigger immediate execution of a watch ("Run now"). Overrides any stuck execution.

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

Returns `409 Conflict` if the watch is already running (unless force override).

### Update watch visibility

Toggle a watch between public and private.

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

### Fork a watch

Fork a public watch. Creates a copy for the current user in the `paused` state.

**Endpoint:** `POST /api/v1/tasks/{id}/fork`

**Request body** (optional):
```json
{
  "name": "My Copy of the Watch"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | No | Custom name for the fork (default: `"{original name} (Copy)"`) |

**Response:** `200 OK` with the new Task object.

**Behavior:**
- The forked watch starts in `paused` state with `is_public: false`
- Copies `search_query` and `condition_description`
- When forking another user's watch, notification config is not copied (scrubbed)
- When forking your own watch, notification config is preserved
- Forking another user's watch increments `subscriber_count` on the original
- Sets `forked_from_task_id` on the new watch

**Errors:**
- `404` if the watch isn't found or isn't public (and isn't owned by you)
- `409` if there's a name collision after retries

## Task object schema

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique watch identifier |
| `user_id` | UUID | Owner user ID |
| `name` | string | Watch name |
| `search_query` | string | Search query for grounded search |
| `condition_description` | string | Condition to evaluate |
| `state` | string | `active`, `paused`, or `completed` |
| `next_run` | timestamp/null | Next scheduled execution time (set by the agent) |
| `is_public` | boolean | Whether the watch is publicly visible |
| `view_count` | integer | Number of public views |
| `subscriber_count` | integer | Number of forks by other users |
| `forked_from_task_id` | UUID/null | Source watch if this is a fork |
| `last_known_state` | object/null | Agent's state-tracking data |
| `last_execution_id` | UUID/null | ID of the most recent execution |
| `last_execution` | object/null | Embedded last execution (when available) |
| `notifications` | array | Notification channel configurations |
| `notification_email` | string/null | Email for notifications |
| `webhook_url` | string/null | Webhook URL for notifications |
| `state_changed_at` | timestamp | When state last changed |
| `immediate_execution_error` | string/null | Error from `run_immediately` (create only) |
| `created_at` | timestamp | Creation time |
| `updated_at` | timestamp/null | Last update time |

### Notification config object

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

At most one of each type is supported per watch.

## Error responses

### Validation error

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

### Not found

**Status:** `404 Not Found`
```json
{
  "detail": "Task not found"
}
```

### Invalid state transition

**Status:** `400 Bad Request`
```json
{
  "detail": "Invalid state transition: paused -> completed"
}
```

### Invalid notification

**Status:** `400 Bad Request`
```json
{
  "detail": "Invalid notification: ..."
}
```

## Next steps

- See the [Executions API](/api/executions) for watch-execution history
- Check the [Notifications API](/api/notifications) for delivery history
- Read the [Error Handling](/api/errors) guide
