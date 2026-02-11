---
description: Notifications API reference. Configure channels, verify emails, manage webhooks, and view notification history via REST API.
---

# Notifications API

View notifications (executions where conditions were met).

## Overview

Base URL: `https://api.torale.ai/api/v1/tasks/{task_id}/notifications`

This endpoint returns only executions where `condition_met: true` - a filtered view of the executions API optimized for viewing notifications.

All endpoints require authentication via API key or Clerk JWT token.

## Endpoints

### Get Notifications

Get all notifications (successful condition evaluations) for a task.

**Endpoint:** `GET /api/v1/tasks/{task_id}/notifications`

**Headers:**
```
Authorization: Bearer {api_key}
```

**Query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | integer | Page number (default: 1) |
| `limit` | integer | Results per page (default: 20, max: 100) |

**Response:** `200 OK`

```json
{
  "notifications": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440000",
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "task_name": "iPhone Release Monitor",
      "status": "success",
      "condition_met": true,
      "answer": "Apple has officially announced that the iPhone 16 will be released on September 20, 2024. Pre-orders begin on September 13, 2024.",
      "reasoning": "The condition is met because Apple's official press release confirms a specific release date of September 20, 2024.",
      "grounding_sources": [
        {
          "uri": "https://www.apple.com/newsroom/2024/09/apple-announces-iphone-16/",
          "title": "Apple announces iPhone 16"
        },
        {
          "uri": "https://www.theverge.com/2024/9/10/iphone-16-announcement",
          "title": "iPhone 16 release date confirmed"
        }
      ],
      "created_at": "2024-01-15T09:00:05Z"
    }
  ],
  "total": 3,
  "page": 1,
  "limit": 20
}
```

**Example:**
```bash
curl -X GET https://api.torale.ai/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/notifications \
  -H "Authorization: Bearer sk_..."
```

### Get All User Notifications

Get notifications across all tasks for authenticated user.

**Endpoint:** `GET /api/v1/notifications`

**Headers:**
```
Authorization: Bearer {api_key}
```

**Query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | integer | Page number (default: 1) |
| `limit` | integer | Results per page (default: 20, max: 100) |

**Response:** `200 OK`

```json
{
  "notifications": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440000",
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "task_name": "iPhone Release Monitor",
      "condition_met": true,
      "answer": "iPhone 16 releases September 20, 2024",
      "created_at": "2024-01-15T09:00:05Z"
    },
    {
      "id": "880e8400-e29b-41d4-a716-446655440000",
      "task_id": "660e8400-e29b-41d4-a716-446655440000",
      "task_name": "PS5 Stock Alert",
      "condition_met": true,
      "answer": "PS5 is currently in stock at Best Buy for $449",
      "created_at": "2024-01-15T12:30:15Z"
    }
  ],
  "total": 8,
  "page": 1,
  "limit": 20
}
```

**Example:**
```bash
curl -X GET https://api.torale.ai/api/v1/notifications \
  -H "Authorization: Bearer sk_..."
```

## Notification Object Schema

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique execution/notification ID |
| `task_id` | UUID | Parent task ID |
| `task_name` | string | Task name for context |
| `status` | string | Always `success` for notifications |
| `condition_met` | boolean | Always `true` for notifications |
| `answer` | string | Concise answer (2-4 sentences) |
| `reasoning` | string | Why condition was met |
| `grounding_sources` | array | Source URLs with metadata |
| `created_at` | timestamp | When notification was created |

## Difference from Executions API

| Feature | Notifications API | Executions API |
|---------|------------------|----------------|
| Filtering | Only `condition_met: true` | All executions |
| Use case | View notifications | Debug, monitor all runs |
| Fields | Simplified | Full execution details |
| Performance | Faster (filtered) | Slower (all records) |

**When to use Notifications API:**
- Viewing user notifications
- Checking if conditions were met
- Building notification UIs

**When to use Executions API:**
- Debugging task execution
- Monitoring for failures
- Viewing full execution history

## Usage Examples

### Python SDK

```python
from torale import ToraleClient

client = ToraleClient(api_key="sk_...")

# Get notifications for specific task
notifications = client.tasks.get_notifications(
    task_id="550e8400-e29b-41d4-a716-446655440000"
)

for notif in notifications:
    print(f"Task: {notif.task_name}")
    print(f"Answer: {notif.answer}")
    print(f"Time: {notif.created_at}")
    print("---")

# Get all user notifications
all_notifications = client.notifications.list()

for notif in all_notifications:
    print(f"{notif.task_name}: {notif.answer}")
```

### JavaScript/TypeScript

```typescript
// Get notifications for task
const response = await fetch(
  `https://api.torale.ai/api/v1/tasks/${taskId}/notifications`,
  {
    headers: {
      'Authorization': `Bearer ${API_KEY}`
    }
  }
);

const data = await response.json();
data.notifications.forEach(notification => {
  console.log(`${notification.task_name}: ${notification.answer}`);
});

// Get all user notifications
const allResponse = await fetch(
  'https://api.torale.ai/api/v1/notifications',
  {
    headers: {
      'Authorization': `Bearer ${API_KEY}`
    }
  }
);

const allData = await allResponse.json();
```

### cURL

```bash
# Get notifications for task
curl -X GET https://api.torale.ai/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/notifications \
  -H "Authorization: Bearer sk_..."

# Get all user notifications
curl -X GET https://api.torale.ai/api/v1/notifications \
  -H "Authorization: Bearer sk_..."
```

## Building Notification UIs

### Notification Feed

```python
from torale import ToraleClient

client = ToraleClient(api_key="sk_...")

# Get recent notifications
notifications = client.notifications.list(limit=10)

# Display in feed
for notif in notifications:
    print(f"""
    Task: {notif.task_name}
    Answer: {notif.answer}
    Time: {notif.created_at}
    Sources: {', '.join([s['uri'] for s in notif.grounding_sources])}
    ---
    """)
```

### Notification Count

```python
# Get total notification count
notifications = client.notifications.list(limit=1)
total_count = notifications.total

print(f"You have {total_count} notifications")
```

### Recent Activity

```python
# Get notifications from last 24 hours
from datetime import datetime, timedelta

notifications = client.notifications.list(limit=100)

yesterday = datetime.now() - timedelta(days=1)
recent = [
    n for n in notifications
    if datetime.fromisoformat(n.created_at.replace('Z', '+00:00')) > yesterday
]

print(f"Notifications in last 24 hours: {len(recent)}")
```

## Email Notifications (Coming Soon)

**Planned features:**
- Email delivery via NotificationAPI
- Customizable templates
- Digest mode (daily/weekly)
- Rich HTML formatting

**Future API:**
```json
POST /api/v1/notifications/email/settings
{
  "enabled": true,
  "email": "user@example.com",
  "digest_frequency": "daily",
  "digest_time": "09:00"
}
```

## Webhook Notifications (Coming Soon)

**Planned features:**
- POST to your webhook URL
- Custom payloads
- Retry logic
- Signature verification

**Future API:**
```json
POST /api/v1/notifications/webhook/settings
{
  "enabled": true,
  "url": "https://your-app.com/webhook",
  "events": ["condition_met"],
  "secret": "your-webhook-secret"
}
```

**Webhook payload (future):**
```json
{
  "event": "condition_met",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_name": "iPhone Release Monitor",
  "answer": "iPhone 16 releases September 20, 2024",
  "sources": ["https://apple.com/newsroom/..."],
  "timestamp": "2024-01-15T09:00:05Z",
  "signature": "sha256=..."
}
```

## Error Responses

### Not Found

**Status:** `404 Not Found`

**Response:**
```json
{
  "detail": "Task not found"
}
```

### Unauthorized

**Status:** `401 Unauthorized`

**Response:**
```json
{
  "detail": "Invalid API key"
}
```

### No Notifications

**Status:** `200 OK`

**Response:**
```json
{
  "notifications": [],
  "total": 0,
  "page": 1,
  "limit": 20
}
```

**Note:** Empty list, not an error. Task hasn't triggered condition yet.

## Best Practices

### Performance

1. **Use pagination** - Don't fetch all notifications at once
2. **Cache results** - Reduce API calls for static data
3. **Use webhooks** - Receive push notifications (coming soon)

### UI Design

1. **Show most recent first** - Order by created_at DESC
2. **Group by task** - Organize notifications by task
3. **Provide context** - Show task name and time
4. **Link to sources** - Make grounding_sources clickable

### Notification Management

1. **Mark as read** - Track viewed notifications (coming soon)
2. **Filter by date** - Show recent notifications
3. **Archive old** - Clear old notifications (coming soon)

## Next Steps

- View [Executions API](/api/executions) for full execution history
- Check [Tasks API](/api/tasks) for task management
- Read [Error Handling](/api/errors) guide
- See [SDK Documentation](/sdk/installation)
