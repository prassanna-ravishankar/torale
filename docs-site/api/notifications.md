---
description: Notifications API reference. View notification send history and task-scoped notification filtering.
---

# Notifications API

View notification send history and per-task notification filtering.

## Overview

Torale has two notification-related endpoints:

1. **`GET /api/v1/notifications/sends`** - Global notification send history (email/webhook delivery records)
2. **`GET /api/v1/tasks/{task_id}/notifications`** - Task-scoped: executions where condition was met

## Endpoints

### Notification Send History

View the delivery history of email and webhook notifications across all your tasks. This tracks actual send attempts, not just condition matches.

**Endpoint:** `GET /api/v1/notifications/sends`

**Headers:**
```
Authorization: Bearer {api_key}
```

**Query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `notification_type` | string | Filter by `email` or `webhook` |
| `task_id` | string | Filter by specific task UUID |
| `limit` | integer | Max results (default: 50) |
| `offset` | integer | Pagination offset (default: 0) |

**Response:** `200 OK`

```json
{
  "sends": [
    {
      "id": "880e8400-e29b-41d4-a716-446655440000",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "task_id": "660e8400-e29b-41d4-a716-446655440000",
      "execution_id": "770e8400-e29b-41d4-a716-446655440000",
      "recipient": "user@example.com",
      "notification_type": "email",
      "status": "sent",
      "error_message": null,
      "created_at": "2025-01-15T09:00:10Z"
    }
  ],
  "total": 42
}
```

**Examples:**
```bash
# Get all notification sends
curl -X GET https://api.torale.ai/api/v1/notifications/sends \
  -H "Authorization: Bearer sk_..."

# Filter by type
curl -X GET "https://api.torale.ai/api/v1/notifications/sends?notification_type=webhook" \
  -H "Authorization: Bearer sk_..."

# Filter by task
curl -X GET "https://api.torale.ai/api/v1/notifications/sends?task_id=660e8400..." \
  -H "Authorization: Bearer sk_..."

# Paginate
curl -X GET "https://api.torale.ai/api/v1/notifications/sends?limit=10&offset=20" \
  -H "Authorization: Bearer sk_..."
```

### Notification Send Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Send record ID |
| `user_id` | UUID | Task owner |
| `task_id` | UUID | Associated task |
| `execution_id` | UUID | Execution that triggered the send |
| `recipient` | string | Email address (for email type) |
| `notification_type` | string | `email` or `webhook` |
| `status` | string | Delivery status |
| `error_message` | string/null | Error if delivery failed |
| `created_at` | timestamp | When the send was attempted |

### Task-Scoped Notifications

Get executions where the condition was met for a specific task. This is a filtered view of the [Executions API](/api/executions).

**Endpoint:** `GET /api/v1/tasks/{task_id}/notifications`

See [Executions API - Task-Scoped Notifications](/api/executions#task-scoped-notifications) for details.

## Difference Between Endpoints

| Feature | `/notifications/sends` | `/tasks/{id}/notifications` |
|---------|----------------------|---------------------------|
| Scope | All tasks | Single task |
| What it tracks | Email/webhook delivery attempts | Executions where condition was met |
| Response type | Send records with delivery status | Execution objects with results |
| Use case | Audit notification delivery | View what triggered alerts |

## Next Steps

- View [Executions API](/api/executions) for full execution history
- Check [Tasks API](/api/tasks) for task management
- Read [Error Handling](/api/errors) guide
