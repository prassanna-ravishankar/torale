---
description: Tasks API reference. Create, list, update, and delete monitoring tasks via REST API with JSON request/response examples.
---

# Tasks API

Create and manage monitoring tasks via REST API.

## Overview

Base URL: `https://api.torale.ai/api/v1/tasks`

All endpoints require authentication via API key or Clerk JWT token.

## Endpoints

### Suggest Task (AI-Powered)

Generate task configuration from natural language description.

**Endpoint:** `POST /api/v1/tasks/suggest`

**Headers:**
```
Authorization: Bearer {api_key}
Content-Type: application/json
```

**Request body:**
```json
{
  "prompt": "Notify me when the PS5 Pro is in stock at Best Buy",
  "current_task": {
    "name": "PS5 Monitor",
    "search_query": "PS5 availability Best Buy",
    "condition_description": "PS5 is in stock",
    "schedule": "0 * * * *",
    "notify_behavior": "once"
  }
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `prompt` | string | Yes | Natural language description of what to monitor |
| `current_task` | object | No | Current task configuration for context-aware updates |

**Response:** `200 OK`

```json
{
  "name": "PS5 Pro Stock Monitor",
  "search_query": "PS5 Pro in stock Best Buy",
  "condition_description": "PS5 Pro is available for purchase at Best Buy",
  "schedule": "*/30 * * * *",
  "notify_behavior": "once"
}
```

**Example:**
```bash
# Generate new task from scratch
curl -X POST https://api.torale.ai/api/v1/tasks/suggest \
  -H "Authorization: Bearer sk_..." \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Tell me when iPhone 17 release date is announced"}'

# Update existing task (context-aware)
curl -X POST https://api.torale.ai/api/v1/tasks/suggest \
  -H "Authorization: Bearer sk_..." \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "add river facing",
    "current_task": {
      "name": "London Apartment Monitor",
      "search_query": "apartments for sale london e2 0fq",
      "condition_description": "Price below 450000 GBP",
      "schedule": "0 9 * * *",
      "notify_behavior": "always"
    }
  }'
```

**Use Cases:**
- **Quick Task Creation**: Describe what you want in plain English
- **Context-Aware Refinement**: Update existing tasks while preserving details
- **Schedule Suggestions**: AI determines optimal check frequency
- **Smart Defaults**: Automatically sets appropriate notify behavior

### Create Task

Create a new monitoring task.

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
  "schedule": "0 9 * * *",
  "notify_behavior": "once",
  "run_immediately": false
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | No | Task name (auto-generated if omitted) |
| `search_query` | string | Yes | Search query for grounded search |
| `condition_description` | string | Yes | Condition to evaluate |
| `schedule` | string | Yes | Cron expression for execution schedule |
| `notify_behavior` | string | No | `once` or `always` (default: `once`) |
| `run_immediately` | boolean | No | Execute task immediately after creation (default: `false`) |

**Response:** `201 Created`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "660e8400-e29b-41d4-a716-446655440000",
  "name": "iPhone Release Monitor",
  "search_query": "When is the next iPhone being released?",
  "condition_description": "Apple has officially announced a specific release date",
  "schedule": "0 9 * * *",
  "notify_behavior": "once",
  "state": "active",
  "last_known_state": null,
  "last_execution_id": null,
  "last_execution": null,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Example:**
```bash
curl -X POST https://api.torale.ai/api/v1/tasks \
  -H "Authorization: Bearer sk_..." \
  -H "Content-Type: application/json" \
  -d '{
    "search_query": "When is the next iPhone release?",
    "condition_description": "A specific date has been announced",
    "schedule": "0 9 * * *"
  }'
```

### Preview Task

Test a search query without creating a task.

**Endpoint:** `POST /api/v1/tasks/preview`

**Headers:**
```
Authorization: Bearer {api_key}
Content-Type: application/json
```

**Request body:**
```json
{
  "search_query": "When is the next iPhone being released?",
  "condition_description": "Apple has officially announced a specific release date"
}
```

**Response:** `200 OK`

```json
{
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
  ]
}
```

**Example:**
```bash
curl -X POST https://api.torale.ai/api/v1/tasks/preview \
  -H "Authorization: Bearer sk_..." \
  -H "Content-Type: application/json" \
  -d '{
    "search_query": "When is the next iPhone release?",
    "condition_description": "A specific date has been announced"
  }'
```

### List Tasks

Get all tasks for authenticated user.

**Endpoint:** `GET /api/v1/tasks`

**Headers:**
```
Authorization: Bearer {api_key}
```

**Query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `active` | boolean | Filter by active status (`true` or `false`) |
| `page` | integer | Page number (default: 1) |
| `limit` | integer | Results per page (default: 20, max: 100) |

**Response:** `200 OK`

```json
{
  "tasks": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "iPhone Release Monitor",
      "search_query": "When is the next iPhone being released?",
      "condition_description": "A specific date has been announced",
      "schedule": "0 9 * * *",
      "notify_behavior": "once",
      "state": "active",
      "last_known_state": null,
      "last_execution_id": null,
      "last_execution": null,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T14:23:45Z"
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 20
}
```

**Examples:**
```bash
# Get all tasks
curl -X GET https://api.torale.ai/api/v1/tasks \
  -H "Authorization: Bearer sk_..."

# Get only active tasks
curl -X GET "https://api.torale.ai/api/v1/tasks?active=true" \
  -H "Authorization: Bearer sk_..."

# Pagination
curl -X GET "https://api.torale.ai/api/v1/tasks?page=2&limit=10" \
  -H "Authorization: Bearer sk_..."
```

### Get Task

Get details for a specific task.

**Endpoint:** `GET /api/v1/tasks/{id}`

**Headers:**
```
Authorization: Bearer {api_key}
```

**Response:** `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "660e8400-e29b-41d4-a716-446655440000",
  "name": "iPhone Release Monitor",
  "search_query": "When is the next iPhone being released?",
  "condition_description": "Apple has officially announced a specific release date",
  "schedule": "0 9 * * *",
  "notify_behavior": "once",
  "state": "active",
  "last_known_state": {
    "answer": "iPhone 16 releases September 20, 2024",
    "timestamp": "2024-01-15T14:23:45Z"
  },
  "last_execution_id": "880e8400-e29b-41d4-a716-446655440000",
  "last_execution": {
    "id": "880e8400-e29b-41d4-a716-446655440000",
    "condition_met": true,
    "status": "success",
    "started_at": "2024-01-15T14:23:00Z",
    "completed_at": "2024-01-15T14:23:45Z"
  },
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T14:23:45Z"
}
```

**Example:**
```bash
curl -X GET https://api.torale.ai/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer sk_..."
```

### Update Task

Update an existing task.

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
  "schedule": "0 */6 * * *",
  "notify_behavior": "always",
  "state": "active"
}
```

**Response:** `200 OK`

Returns updated task object (same format as Get Task).

**Example:**
```bash
# Update schedule
curl -X PUT https://api.torale.ai/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer sk_..." \
  -H "Content-Type: application/json" \
  -d '{"schedule": "0 */6 * * *"}'

# Pause task
curl -X PUT https://api.torale.ai/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer sk_..." \
  -H "Content-Type: application/json" \
  -d '{"state": "paused"}'
```

### Delete Task

Delete a task and its scheduled jobs.

**Endpoint:** `DELETE /api/v1/tasks/{id}`

**Headers:**
```
Authorization: Bearer {api_key}
```

**Response:** `204 No Content`

**Example:**
```bash
curl -X DELETE https://api.torale.ai/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer sk_..."
```

### Execute Task Manually

Trigger immediate execution of a task (testing purposes).

**Endpoint:** `POST /api/v1/tasks/{id}/execute`

**Headers:**
```
Authorization: Bearer {api_key}
```

**Response:** `202 Accepted`

```json
{
  "message": "Task execution initiated",
  "execution_id": "770e8400-e29b-41d4-a716-446655440000"
}
```

**Example:**
```bash
curl -X POST https://api.torale.ai/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/execute \
  -H "Authorization: Bearer sk_..."
```

**Note:** Execution happens asynchronously. Check execution status using Executions API.

## Task Object Schema

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique task identifier |
| `user_id` | UUID | Owner user ID |
| `name` | string | Task name |
| `search_query` | string | Search query for grounded search |
| `condition_description` | string | Condition to evaluate |
| `schedule` | string | Cron expression |
| `notify_behavior` | enum | `once` or `always` |
| `state` | string | Task state: `active`, `paused`, or `completed` |
| `last_known_state` | object | Previous execution state (for state tracking) |
| `last_execution_id` | UUID | ID of the most recent execution |
| `last_execution` | object | Embedded last execution summary (condition_met, status, etc.) |
| `created_at` | timestamp | Task creation time |
| `updated_at` | timestamp | Last update time |

## Validation Rules

### Search Query
- **Required:** Yes
- **Min length:** 10 characters
- **Max length:** 500 characters
- **Format:** Natural language question

### Condition Description
- **Required:** Yes
- **Min length:** 10 characters
- **Max length:** 500 characters
- **Format:** Clear, objective criteria

### Schedule
- **Required:** Yes
- **Format:** Valid cron expression (5 fields)
- **Example:** `0 9 * * *` (daily at 9 AM)

### Notify Behavior
- **Required:** No (default: `once`)
- **Valid values:** `once`, `always`

### Name
- **Required:** No (auto-generated if omitted)
- **Max length:** 200 characters

## Error Responses

### Validation Error

**Status:** `422 Unprocessable Entity`

**Response:**
```json
{
  "detail": [
    {
      "loc": ["body", "schedule"],
      "msg": "Invalid cron expression",
      "type": "value_error"
    }
  ]
}
```

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

### Forbidden

**Status:** `403 Forbidden`

**Response:**
```json
{
  "detail": "Not authorized to access this task"
}
```

**Cause:** Trying to access another user's task.

## Usage Examples

### Python

```python
from torale import ToraleClient

client = ToraleClient(api_key="sk_...")

# Create task
task = client.tasks.create(
    name="iPhone Release Monitor",
    search_query="When is the next iPhone being released?",
    condition_description="A specific date has been announced",
    schedule="0 9 * * *",
    notify_behavior="once"
)

# Preview before creating
preview = client.tasks.preview(
    search_query="When is the next iPhone release?",
    condition_description="A specific date has been announced"
)
print(f"Condition met: {preview.condition_met}")
print(f"Answer: {preview.answer}")

# List tasks
tasks = client.tasks.list(active=True)
for task in tasks:
    print(f"{task.name}: {task.state}")

# Get specific task
task = client.tasks.get("550e8400-e29b-41d4-a716-446655440000")

# Update task
task = client.tasks.update(
    "550e8400-e29b-41d4-a716-446655440000",
    schedule="0 */6 * * *"
)

# Delete task
client.tasks.delete("550e8400-e29b-41d4-a716-446655440000")

# Execute manually
execution_id = client.tasks.execute("550e8400-e29b-41d4-a716-446655440000")
```

### JavaScript/TypeScript

```typescript
const response = await fetch('https://api.torale.ai/api/v1/tasks', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${API_KEY}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    search_query: "When is the next iPhone being released?",
    condition_description: "A specific date has been announced",
    schedule: "0 9 * * *"
  })
});

const task = await response.json();
console.log(`Created task: ${task.id}`);
```

### cURL

```bash
# Create task
curl -X POST https://api.torale.ai/api/v1/tasks \
  -H "Authorization: Bearer sk_..." \
  -H "Content-Type: application/json" \
  -d @- <<'EOF'
{
  "name": "iPhone Release Monitor",
  "search_query": "When is the next iPhone being released?",
  "condition_description": "A specific date has been announced",
  "schedule": "0 9 * * *",
  "notify_behavior": "once"
}
EOF

# List tasks
curl -X GET https://api.torale.ai/api/v1/tasks \
  -H "Authorization: Bearer sk_..."

# Update task
curl -X PUT https://api.torale.ai/api/v1/tasks/{id} \
  -H "Authorization: Bearer sk_..." \
  -H "Content-Type: application/json" \
  -d '{"schedule": "0 */6 * * *"}'
```

## Best Practices

### Task Creation

1. **Use Preview first** - Test query before creating task
2. **Start with lower frequency** - Begin with daily checks, increase if needed
3. **Specific queries** - Be clear about what you're monitoring
4. **Objective conditions** - Avoid subjective terms
5. **Appropriate notify behavior** - Choose based on use case

### Task Management

1. **Pause unused tasks** - Set `is_active: false` instead of deleting
2. **Monitor executions** - Check for failures or condition_met status
3. **Update schedules** - Adjust frequency based on results
4. **Clean up old tasks** - Delete tasks no longer needed

### Error Handling

```python
from torale import ToraleClient
from torale.exceptions import ValidationError, NotFoundError

client = ToraleClient(api_key="sk_...")

try:
    task = client.tasks.create(
        search_query="...",
        condition_description="...",
        schedule="invalid"  # Bad cron
    )
except ValidationError as e:
    print(f"Validation failed: {e.detail}")
except NotFoundError:
    print("Task not found")
```

## Rate Limits

- **100 requests/minute** per API key
- **1,000 requests/hour** per API key
- **10,000 requests/day** per API key

See [Authentication](/api/authentication) for rate limit handling.

## Next Steps

- View [Executions API](/api/executions) to check task execution history
- Check [Notifications API](/api/notifications) for notification management
- Read [Error Handling](/api/errors) guide
- See [SDK Documentation](/sdk/installation) for Python client
