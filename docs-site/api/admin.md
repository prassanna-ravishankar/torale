---
description: Admin API reference for platform management. User administration, system stats, task controls, and operational endpoints.
---

# Admin Endpoints

Platform monitoring and management endpoints for administrators.

## Overview

Base URL: `https://api.torale.ai/admin`

**Access:** Requires admin role in Clerk `publicMetadata`.

**Note:** All admin endpoints are hidden from the OpenAPI schema (`include_in_schema=False`). They do not appear in `/docs` or `/redoc`.

## Authentication

### Setting Admin Role

Set `{"role": "admin"}` in user's `publicMetadata` via Clerk Dashboard:

1. Go to Clerk Dashboard -> Users
2. Select user
3. Navigate to Metadata -> Public Metadata
4. Add:
   ```json
   {
     "role": "admin"
   }
   ```
5. Save

**Authorization header:**
```
Authorization: Bearer {clerk_jwt}
```

## Platform Monitoring

### Platform Statistics

**Endpoint:** `GET /admin/stats`

**Response:** `200 OK`

```json
{
  "users": {
    "total": 45,
    "capacity": 100,
    "available": 55
  },
  "tasks": {
    "total": 120,
    "triggered": 34,
    "trigger_rate": "28.3%"
  },
  "executions_24h": {
    "total": 580,
    "failed": 12,
    "success_rate": "97.9%"
  },
  "popular_queries": [
    {
      "search_query": "iPhone release date",
      "count": 15,
      "triggered_count": 3
    }
  ]
}
```

### All User Queries

**Endpoint:** `GET /admin/queries`

**Query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | integer | Max results (default: 100, max: 500) |
| `active_only` | boolean | Only show active tasks (default: false) |

**Response:** `200 OK`

```json
{
  "queries": [
    {
      "id": "550e8400...",
      "name": "iPhone Monitor",
      "search_query": "When is the next iPhone being released?",
      "condition_description": "A specific date has been announced",
      "next_run": "2025-01-16T09:00:00Z",
      "state": "active",
      "has_notification": false,
      "created_at": "2025-01-15T10:30:00Z",
      "user_email": "user@example.com",
      "execution_count": 15,
      "trigger_count": 0,
      "last_known_state": null,
      "state_changed_at": null
    }
  ],
  "total": 120
}
```

### All Executions

**Endpoint:** `GET /admin/executions`

**Query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | integer | Max results (default: 50, max: 200) |
| `status` | string | Filter by: `success`, `failed`, `running`, `pending` |
| `task_id` | UUID | Filter by specific task |

**Response:** `200 OK`

```json
{
  "executions": [
    {
      "id": "770e8400...",
      "task_id": "550e8400...",
      "status": "success",
      "started_at": "2025-01-15T09:00:00Z",
      "completed_at": "2025-01-15T09:00:04Z",
      "result": { "evidence": "...", "confidence": 90 },
      "error_message": null,
      "notification": null,
      "grounding_sources": [...],
      "search_query": "When is the next iPhone release?",
      "user_email": "user@example.com"
    }
  ],
  "total": 50
}
```

### Error Monitoring

**Endpoint:** `GET /admin/errors`

**Query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | integer | Max results (default: 50, max: 200) |

**Response:** `200 OK`

```json
{
  "errors": [
    {
      "id": "880e8400...",
      "task_id": "550e8400...",
      "started_at": "2025-01-15T10:23:15Z",
      "completed_at": "2025-01-15T10:23:20Z",
      "error_message": "Agent timeout after 60s",
      "search_query": "When is the next iPhone release?",
      "task_name": "iPhone Monitor",
      "user_email": "user@example.com"
    }
  ],
  "total": 12
}
```

### Scheduler Jobs

**Endpoint:** `GET /admin/scheduler/jobs`

**Response:** `200 OK`

```json
{
  "jobs": [
    {
      "id": "task-550e8400...",
      "name": "iPhone Monitor",
      "next_run_time": "2025-01-16T09:00:00Z",
      "paused": false,
      "trigger": "date[2025-01-16T09:00:00Z]"
    }
  ],
  "total": 85
}
```

## User Management

### List Users

**Endpoint:** `GET /admin/users`

**Response:** `200 OK`

```json
{
  "users": [
    {
      "id": "660e8400...",
      "email": "user@example.com",
      "clerk_user_id": "user_2abc...",
      "is_active": true,
      "created_at": "2025-01-10T08:30:00Z",
      "task_count": 8,
      "total_executions": 145,
      "notifications_count": 12,
      "role": "developer"
    }
  ],
  "capacity": {
    "used": 45,
    "total": 100,
    "available": 55
  }
}
```

### Deactivate User

Sets `is_active = false` and pauses all active tasks via state machine.

**Endpoint:** `PATCH /admin/users/{user_id}/deactivate`

**Response:** `200 OK`

```json
{
  "status": "deactivated",
  "user_id": "660e8400...",
  "tasks_paused": 5,
  "tasks_failed": null
}
```

### Update User Role

Update a user's role in Clerk `publicMetadata`. Admins cannot change their own role.

**Endpoint:** `PATCH /admin/users/{user_id}/role`

**Request body:**
```json
{
  "role": "developer"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `role` | string/null | `"admin"`, `"developer"`, or `null` (remove role) |

**Response:** `200 OK`

```json
{
  "status": "updated",
  "user_id": "660e8400...",
  "role": "developer"
}
```

### Bulk Update Roles

**Endpoint:** `PATCH /admin/users/roles`

**Request body:**
```json
{
  "user_ids": ["uuid-1", "uuid-2"],
  "role": "developer"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `user_ids` | array | 1-100 user UUIDs |
| `role` | string/null | `"admin"`, `"developer"`, or `null` |

**Response:** `200 OK`

```json
{
  "updated": 2,
  "failed": 0,
  "errors": []
}
```

## Task Administration

### Execute Any Task

Manually trigger execution of any user's task.

**Endpoint:** `POST /admin/tasks/{task_id}/execute`

**Query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `suppress_notifications` | boolean | Suppress notifications (default: false) |

**Response:** `200 OK`

```json
{
  "id": "770e8400...",
  "task_id": "550e8400...",
  "status": "pending",
  "message": "Execution started (notifications enabled)"
}
```

### Update Task State

Transition any task through valid state changes. Invalid transitions are rejected.

**Endpoint:** `PATCH /admin/tasks/{task_id}/state`

**Request body:**
```json
{
  "state": "paused"
}
```

Valid transitions:
- `active` <-> `paused`
- `active` -> `completed`
- `completed` -> `active`

**Response:** `200 OK`

```json
{
  "id": "550e8400...",
  "state": "paused",
  "previous_state": "active",
  "message": "Task state updated to paused"
}
```

### Reset Task History

Delete recent executions and reset task state so the agent re-evaluates fresh.

**Endpoint:** `DELETE /admin/tasks/{task_id}/reset`

**Query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `days` | integer | Delete executions from last N days (default: 1, max: 30) |

**Response:** `200 OK`

```json
{
  "status": "reset",
  "task_id": "550e8400...",
  "executions_deleted": 15,
  "days": 1
}
```

## Waitlist Management

### List Waitlist

**Endpoint:** `GET /admin/waitlist`

**Query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status_filter` | string | Filter by: `pending`, `invited`, `converted` |

**Response:** `200 OK`

```json
[
  {
    "id": "990e8400...",
    "email": "waiting@example.com",
    "created_at": "2025-01-10T08:00:00Z",
    "status": "pending",
    "invited_at": null,
    "notes": null
  }
]
```

### Waitlist Statistics

**Endpoint:** `GET /admin/waitlist/stats`

**Response:** `200 OK`

```json
{
  "pending": 23,
  "invited": 10,
  "converted": 45,
  "total": 78
}
```

### Update Waitlist Entry

**Endpoint:** `PATCH /admin/waitlist/{entry_id}`

**Request body:**
```json
{
  "status": "invited",
  "notes": "Sent invite email"
}
```

**Response:** `200 OK` with updated entry.

### Delete Waitlist Entry

**Endpoint:** `DELETE /admin/waitlist/{entry_id}`

**Response:** `200 OK`

```json
{
  "status": "deleted"
}
```

## Error Responses

### Forbidden

**Status:** `403 Forbidden`

```json
{
  "detail": "Admin access required"
}
```

User doesn't have admin role in Clerk metadata.

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

## Next Steps

- Check [Tasks API](/api/tasks) for task management
- View [Executions API](/api/executions) for execution details
- Read [Error Handling](/api/errors) guide
