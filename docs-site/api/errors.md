---
description: API error responses and status codes. HTTP error codes, error message formats, common errors, and troubleshooting guide.
---

# Error Handling

Understanding and handling errors in Torale API.

## HTTP Status Codes

| Code | Status | Meaning |
|------|--------|---------|
| 200 | OK | Request successful |
| 204 | No Content | Successful deletion |
| 400 | Bad Request | Invalid request (bad state transition, invalid notification, etc.) |
| 401 | Unauthorized | Missing or invalid authentication |
| 404 | Not Found | Resource doesn't exist or not accessible |
| 409 | Conflict | Resource conflict (task already running, duplicate entry, etc.) |
| 422 | Unprocessable Entity | Validation error (missing/invalid fields) |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Dependency unavailable (e.g., Clerk client) |

## Error Response Format

All errors use FastAPI's standard format:

```json
{
  "detail": "Error message"
}
```

For validation errors (422), FastAPI returns field-level details:

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "search_query"],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```

## Common Errors

### Authentication Errors

#### Invalid API Key

**Status:** `401 Unauthorized`

```json
{
  "detail": "Invalid API key"
}
```

**Causes:** Key doesn't exist, was revoked, or format is incorrect.

#### Missing Authorization

**Status:** `401 Unauthorized`

```json
{
  "detail": "Authorization header missing"
}
```

**Fix:** Include `Authorization: Bearer {key}` header.

### Resource Errors

#### Not Found

**Status:** `404 Not Found`

```json
{
  "detail": "Task not found"
}
```

Returned when a resource doesn't exist or when a non-owner tries to access a private task. Torale returns 404 (not 403) for private resources to avoid leaking existence information.

#### Conflict

**Status:** `409 Conflict`

```json
{
  "detail": "Task is already running or pending. Use force=true to override."
}
```

Returned when trying to execute a task that already has a running/pending execution, or when a waitlist email already exists.

### Validation Errors

#### Missing Required Fields

**Status:** `422 Unprocessable Entity`

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "search_query"],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```

Required fields for task creation: `search_query`.

#### Invalid Field Values

**Status:** `422 Unprocessable Entity`

```json
{
  "detail": [
    {
      "type": "enum",
      "loc": ["body", "state"],
      "msg": "Input should be 'active', 'paused' or 'completed'",
      "input": "invalid"
    }
  ]
}
```

### Business Logic Errors

#### Invalid State Transition

**Status:** `400 Bad Request`

```json
{
  "detail": "Invalid state transition: paused -> completed"
}
```

Valid state transitions:
- `active` <-> `paused`
- `active` -> `completed`
- `completed` -> `active`

#### Invalid Notification Configuration

**Status:** `400 Bad Request`

```json
{
  "detail": "Invalid notification: ..."
}
```

#### Duplicate Notification Types

**Status:** `400 Bad Request`

```json
{
  "detail": "Multiple notifications of the same type are not supported. Please provide at most one email and one webhook notification."
}
```

#### Username Already Set

**Status:** `400 Bad Request`

```json
{
  "detail": "Username cannot be changed once set. This protects your public task URLs from breaking."
}
```

#### Missing Username for Public Tasks

**Status:** `400 Bad Request`

```json
{
  "detail": "You must set a username before making tasks public"
}
```

### Rate Limit Errors

**Status:** `429 Too Many Requests`

Rate limits are applied per-IP on public endpoints:
- Public tasks listing: 10/minute
- Public task by ID: 20/minute
- Task RSS feed: 10/minute
- Waitlist join: 5/minute

### Server Errors

#### Internal Server Error

**Status:** `500 Internal Server Error`

```json
{
  "detail": "Failed to change task state: ... Task update rolled back."
}
```

When a state transition fails after other fields were updated, the entire update is rolled back and the error is returned.

#### Service Unavailable

**Status:** `503 Service Unavailable`

```json
{
  "detail": "Clerk client not initialized"
}
```

Returned when an external dependency (like Clerk) is unavailable.

## Debugging

### Check Response Status

```bash
# Verbose curl output shows status code and headers
curl -v -X GET https://api.torale.ai/api/v1/tasks \
  -H "Authorization: Bearer sk_..."
```

### Common Mistakes

1. **Sending `schedule` in create/update** - Schedule is not user-settable, it's determined by the agent
2. **Expecting pagination wrapper on list endpoints** - `GET /api/v1/tasks` and executions return bare arrays
3. **Using `GET /api/v1/notifications`** - This endpoint doesn't exist. Use `/api/v1/notifications/sends` for send history or `/api/v1/tasks/{id}/notifications` for task-scoped condition matches
4. **Trying to access private tasks without auth** - Returns 404, not 403

## Next Steps

- Review [Authentication](/api/authentication) for auth setup
- Check [Tasks API](/api/tasks) for endpoint details
- View [API Overview](/api/overview) for complete endpoint listing
