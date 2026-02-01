# Executions API

View task execution history and results.

## Overview

Base URL: `https://api.torale.ai/api/v1/tasks/{task_id}/executions`

All endpoints require authentication via API key or Clerk JWT token.

## Endpoints

### Get Execution History

Get all executions for a specific task.

**Endpoint:** `GET /api/v1/tasks/{task_id}/executions`

**Headers:**
```
Authorization: Bearer {api_key}
```

**Query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status: `pending`, `running`, `success`, `failed` |
| `page` | integer | Page number (default: 1) |
| `limit` | integer | Results per page (default: 20, max: 100) |

**Response:** `200 OK`

```json
{
  "executions": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440000",
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "success",
      "started_at": "2024-01-15T09:00:00Z",
      "completed_at": "2024-01-15T09:00:05Z",
      "condition_met": true,
      "result": {
        "answer": "Apple has officially announced that the iPhone 16 will be released on September 20, 2024.",
        "reasoning": "The condition is met because Apple's official press release confirms a specific release date.",
        "condition_met": true
      },
      "change_summary": "New information: Release date announced as September 20, 2024",
      "grounding_sources": [
        {
          "uri": "https://www.apple.com/newsroom/2024/09/apple-announces-iphone-16/",
          "title": "Apple announces iPhone 16"
        }
      ],
      "error_message": null,
      "created_at": "2024-01-15T09:00:00Z"
    }
  ],
  "total": 15,
  "page": 1,
  "limit": 20
}
```

**Examples:**
```bash
# Get all executions
curl -X GET https://api.torale.ai/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/executions \
  -H "Authorization: Bearer sk_..."

# Filter by status
curl -X GET "https://api.torale.ai/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/executions?status=success" \
  -H "Authorization: Bearer sk_..."

# Pagination
curl -X GET "https://api.torale.ai/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/executions?page=2&limit=10" \
  -H "Authorization: Bearer sk_..."
```

### Get Single Execution

Get details for a specific execution.

**Endpoint:** `GET /api/v1/tasks/{task_id}/executions/{execution_id}`

**Headers:**
```
Authorization: Bearer {api_key}
```

**Response:** `200 OK`

```json
{
  "id": "770e8400-e29b-41d4-a716-446655440000",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "success",
  "started_at": "2024-01-15T09:00:00Z",
  "completed_at": "2024-01-15T09:00:05Z",
  "condition_met": true,
  "result": {
    "answer": "Apple has officially announced that the iPhone 16 will be released on September 20, 2024. Pre-orders begin on September 13, 2024.",
    "reasoning": "The condition is met because Apple's official press release confirms a specific release date of September 20, 2024.",
    "condition_met": true,
    "sources_count": 3
  },
  "change_summary": "New information: Release date announced as September 20, 2024. Previous state indicated no official date.",
  "grounding_sources": [
    {
      "uri": "https://www.apple.com/newsroom/2024/09/apple-announces-iphone-16/",
      "title": "Apple announces iPhone 16",
      "snippet": "Apple today announced iPhone 16 will be available starting Friday, September 20..."
    },
    {
      "uri": "https://www.theverge.com/2024/9/10/iphone-16-announcement",
      "title": "iPhone 16 release date confirmed for September 20",
      "snippet": "Following today's announcement, iPhone 16 will launch on September 20..."
    }
  ],
  "error_message": null,
  "created_at": "2024-01-15T09:00:00Z"
}
```

**Example:**
```bash
curl -X GET https://api.torale.ai/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/executions/770e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer sk_..."
```

## Execution Object Schema

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique execution identifier |
| `task_id` | UUID | Parent task ID |
| `status` | enum | `pending`, `running`, `success`, `failed` |
| `started_at` | timestamp | When execution started |
| `completed_at` | timestamp | When execution completed (null if running) |
| `condition_met` | boolean | Whether trigger condition was met |
| `result` | object | Execution result with answer, reasoning, etc. |
| `grounding_sources` | array | Source URLs with metadata |
| `error_message` | string | Error details if status is `failed` |
| `created_at` | timestamp | Execution creation time |

### Result Object

```json
{
  "answer": "Concise answer to search query (2-4 sentences)",
  "reasoning": "Why the condition was or wasn't met",
  "condition_met": true,
  "sources_count": 3
}
```

### Grounding Source Object

```json
{
  "uri": "https://example.com/article",
  "title": "Article Title",
  "snippet": "Relevant excerpt from the source..."
}
```

## Execution Statuses

### pending
Initial state before execution starts.

**Typical duration:** < 1 second

### running
Execution in progress (searching, evaluating condition).

**Typical duration:** 2-10 seconds

### success
Execution completed successfully.

**Result available:** Yes
**condition_met:** Indicates if condition was satisfied

### failed
Execution encountered an error.

**error_message:** Contains error details
**Retry behavior:** Failed executions will be retried on the next scheduled run

## Usage Examples

### Python SDK

```python
from torale import ToraleClient

client = ToraleClient(api_key="sk_...")

# Get all executions
executions = client.tasks.get_executions(
    task_id="550e8400-e29b-41d4-a716-446655440000"
)

for execution in executions:
    print(f"Status: {execution.status}")
    print(f"Condition met: {execution.condition_met}")
    if execution.result:
        print(f"Answer: {execution.result.get('answer')}")

# Filter by status
success_executions = client.tasks.get_executions(
    task_id="550e8400-e29b-41d4-a716-446655440000",
    status="success"
)

# Get specific execution
execution = client.tasks.get_execution(
    task_id="550e8400-e29b-41d4-a716-446655440000",
    execution_id="770e8400-e29b-41d4-a716-446655440000"
)

print(f"Answer: {execution.result.get('answer')}")
print(f"Sources: {len(execution.grounding_sources)}")
```

### JavaScript/TypeScript

```typescript
const response = await fetch(
  `https://api.torale.ai/api/v1/tasks/${taskId}/executions`,
  {
    headers: {
      'Authorization': `Bearer ${API_KEY}`
    }
  }
);

const data = await response.json();
data.executions.forEach(execution => {
  console.log(`Status: ${execution.status}`);
  if (execution.condition_met) {
    console.log(`Answer: ${execution.result.answer}`);
  }
});
```

### cURL

```bash
# Get executions
curl -X GET https://api.torale.ai/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/executions \
  -H "Authorization: Bearer sk_..."

# Filter successful executions only
curl -X GET "https://api.torale.ai/api/v1/tasks/550e8400-e29b-41d4-a716-446655440000/executions?status=success" \
  -H "Authorization: Bearer sk_..."
```

## Understanding Execution Results

### Condition Met

When `condition_met: true`:

```json
{
  "status": "success",
  "condition_met": true,
  "result": {
    "answer": "iPhone 16 releases September 20, 2024",
    "reasoning": "Official announcement confirms specific date",
    "condition_met": true
  }
}
```

**What this means:**
- Search completed successfully
- AI determined condition was satisfied
- Notification sent (depending on notify_behavior)
- Task state updated

### Condition Not Met

When `condition_met: false`:

```json
{
  "status": "success",
  "condition_met": false,
  "result": {
    "answer": "No official iPhone 16 release date has been announced yet",
    "reasoning": "Search results show speculation but no confirmed date from Apple",
    "condition_met": false
  }
}
```

**What this means:**
- Search completed successfully
- Condition criteria not satisfied
- No notification sent
- Task continues on schedule

### Failed Execution

When `status: "failed"`:

```json
{
  "status": "failed",
  "condition_met": null,
  "result": null,
  "error_message": "Rate limit exceeded for Google Search API"
}
```

**What this means:**
- Execution encountered an error
- Failed executions will be retried on the next scheduled run
- Check error_message for details

## Grounding Sources

Sources are filtered to remove Vertex AI infrastructure URLs and show only clean domain names.

**Example sources:**
```json
{
  "grounding_sources": [
    {
      "uri": "https://www.apple.com/newsroom/2024/09/apple-announces-iphone-16/",
      "title": "Apple announces iPhone 16",
      "snippet": "Apple today announced iPhone 16..."
    },
    {
      "uri": "https://www.theverge.com/2024/9/10/iphone-16-announcement",
      "title": "iPhone 16 release date confirmed",
      "snippet": "Following today's announcement..."
    }
  ]
}
```

**Verification:**
- Click URI to view source
- Verify information is accurate
- Check source credibility

## Error Responses

### Not Found

**Status:** `404 Not Found`

**Response:**
```json
{
  "detail": "Execution not found"
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
  "detail": "Not authorized to access this execution"
}
```

## Common Patterns

### Check Latest Execution

```python
executions = client.tasks.get_executions(task_id, limit=1)
latest = executions[0]

if latest.condition_met:
    print(f"Condition met! {latest.result.get('answer')}")
else:
    print("Condition not yet met")
```

### Monitor for Changes

```python
# Get recent executions
executions = client.tasks.get_executions(task_id, limit=5)

# Check for state changes
for execution in executions:
    if execution.change_summary:
        print(f"Change detected: {execution.change_summary}")
```

### Check for Errors

```python
# Get failed executions
failed = client.tasks.get_executions(task_id, status="failed")

for execution in failed:
    print(f"Error: {execution.error_message}")
    print(f"Time: {execution.started_at}")
```

## Best Practices

### Monitoring Executions

1. **Check regularly** - Monitor execution history for failures
2. **Review sources** - Verify grounding sources are reputable
3. **Analyze changes** - Use change_summary to understand evolution
4. **Track status** - Watch for failed executions

### Debugging

1. **Check latest execution** - View most recent result
2. **Review error messages** - Understand failure causes
3. **Verify condition logic** - Ensure condition is achievable
4. **Check sources** - Confirm information is available

### Performance

1. **Use pagination** - Don't fetch all executions at once
2. **Filter by status** - Get only relevant executions
3. **Limit results** - Fetch only what you need

## Next Steps

- View [Notifications API](/api/notifications) for filtered notification view
- Check [Tasks API](/api/tasks) for task management
- Read [Error Handling](/api/errors) guide
- See [SDK Documentation](/sdk/installation)
