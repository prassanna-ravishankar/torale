---
description: Admin API reference for platform management. User administration, system stats, task controls, and operational endpoints.
---

# Admin Endpoints

Platform monitoring and management endpoints for administrators.

## Overview

Base URL: `https://api.torale.ai/admin`

**Access:** Requires admin role in Clerk `publicMetadata`

## Authentication

### Setting Admin Role

Set `{"role": "admin"}` in user's `publicMetadata` via Clerk Dashboard:

1. Go to Clerk Dashboard → Users
2. Select user
3. Navigate to Metadata → Public Metadata
4. Add:
   ```json
   {
     "role": "admin"
   }
   ```
5. Save

**Authorization header:**
```
Authorization: Bearer {api_key_or_clerk_jwt}
```

## Endpoints

### Platform Statistics

Get overview of platform usage.

**Endpoint:** `GET /admin/stats`

**Response:** `200 OK`

```json
{
  "users": {
    "total": 1250,
    "active_30d": 823,
    "new_7d": 45
  },
  "tasks": {
    "total": 5420,
    "active": 3891,
    "paused": 1529
  },
  "executions": {
    "total_24h": 15623,
    "success_24h": 15201,
    "failed_24h": 422,
    "avg_duration_ms": 4200
  },
  "notifications": {
    "sent_24h": 892,
    "sent_7d": 5234
  },
  "popular_queries": [
    {
      "query": "iPhone release date",
      "count": 234
    },
    {
      "query": "PS5 stock",
      "count": 198
    }
  ]
}
```

**Example:**
```bash
curl -X GET https://api.torale.ai/admin/stats \
  -H "Authorization: Bearer sk_..."
```

### All User Queries

View all user queries with statistics.

**Endpoint:** `GET /admin/queries`

**Query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | integer | Page number (default: 1) |
| `limit` | integer | Results per page (default: 50, max: 100) |

**Response:** `200 OK`

```json
{
  "queries": [
    {
      "search_query": "When is the next iPhone being released?",
      "total_tasks": 234,
      "active_tasks": 189,
      "total_executions": 1456,
      "success_rate": 0.98,
      "avg_duration_ms": 3800
    },
    {
      "search_query": "Is PS5 in stock at Target?",
      "total_tasks": 198,
      "active_tasks": 156,
      "total_executions": 2341,
      "success_rate": 0.95,
      "avg_duration_ms": 4200
    }
  ],
  "total": 1247,
  "page": 1,
  "limit": 50
}
```

**Example:**
```bash
curl -X GET https://api.torale.ai/admin/queries \
  -H "Authorization: Bearer sk_..."
```

### All Executions

View execution history across all users.

**Endpoint:** `GET /admin/executions`

**Query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by: `success`, `failed` |
| `hours` | integer | Last N hours (default: 24) |
| `page` | integer | Page number (default: 1) |
| `limit` | integer | Results per page (default: 50, max: 100) |

**Response:** `200 OK`

```json
{
  "executions": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440000",
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "user_email": "user@example.com",
      "search_query": "When is the next iPhone release?",
      "status": "success",
      "condition_met": true,
      "duration_ms": 4100,
      "started_at": "2024-01-15T09:00:00Z",
      "completed_at": "2024-01-15T09:00:04Z"
    }
  ],
  "total": 15623,
  "page": 1,
  "limit": 50
}
```

**Example:**
```bash
# Get all executions from last 24 hours
curl -X GET https://api.torale.ai/admin/executions \
  -H "Authorization: Bearer sk_..."

# Get failed executions from last 6 hours
curl -X GET "https://api.torale.ai/admin/executions?status=failed&hours=6" \
  -H "Authorization: Bearer sk_..."
```

### Error Monitoring

View recent failed executions for monitoring.

**Endpoint:** `GET /admin/errors`

**Query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `hours` | integer | Last N hours (default: 24) |
| `limit` | integer | Results per page (default: 50, max: 100) |

**Response:** `200 OK`

```json
{
  "errors": [
    {
      "execution_id": "880e8400-e29b-41d4-a716-446655440000",
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "user_email": "user@example.com",
      "search_query": "When is the next iPhone release?",
      "error_message": "Rate limit exceeded for Google Search API",
      "error_type": "RateLimitError",
      "retry_count": 2,
      "will_retry": true,
      "occurred_at": "2024-01-15T10:23:15Z"
    }
  ],
  "total": 422,
  "error_types": {
    "RateLimitError": 312,
    "TimeoutError": 89,
    "ValidationError": 21
  }
}
```

**Example:**
```bash
# Get errors from last 24 hours
curl -X GET https://api.torale.ai/admin/errors \
  -H "Authorization: Bearer sk_..."

# Get errors from last 6 hours
curl -X GET "https://api.torale.ai/admin/errors?hours=6" \
  -H "Authorization: Bearer sk_..."
```

### User Management

List all users with activity statistics.

**Endpoint:** `GET /admin/users`

**Query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `active_only` | boolean | Show only active users (default: false) |
| `page` | integer | Page number (default: 1) |
| `limit` | integer | Results per page (default: 50, max: 100) |

**Response:** `200 OK`

```json
{
  "users": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "clerk_user_id": "user_2abc...",
      "state": "active",
      "tasks_count": 8,
      "active_tasks_count": 5,
      "executions_24h": 45,
      "notifications_7d": 12,
      "created_at": "2024-01-10T08:30:00Z",
      "last_login": "2024-01-15T09:00:00Z"
    }
  ],
  "total": 1250,
  "page": 1,
  "limit": 50
}
```

**Example:**
```bash
# Get all users
curl -X GET https://api.torale.ai/admin/users \
  -H "Authorization: Bearer sk_..."

# Get only active users
curl -X GET "https://api.torale.ai/admin/users?active_only=true" \
  -H "Authorization: Bearer sk_..."
```

### Deactivate User

Deactivate a user account (soft delete).

**Endpoint:** `PATCH /admin/users/{id}/deactivate`

**Response:** `200 OK`

```json
{
  "message": "User deactivated successfully",
  "user_id": "660e8400-e29b-41d4-a716-446655440000",
  "tasks_paused": 8
}
```

**Example:**
```bash
curl -X PATCH https://api.torale.ai/admin/users/660e8400-e29b-41d4-a716-446655440000/deactivate \
  -H "Authorization: Bearer sk_..."
```

**Effects:**
- User can no longer log in
- All tasks paused
- API keys revoked
- No data deleted (soft delete)

## Usage Examples

### Python

```python
from torale import ToraleClient

# Client with admin API key
client = ToraleClient(api_key="sk_admin_...")

# Get platform stats
stats = client.admin.get_stats()
print(f"Total users: {stats['users']['total']}")
print(f"Active tasks: {stats['tasks']['active']}")

# Get recent errors
errors = client.admin.get_errors(hours=6)
for error in errors['errors']:
    print(f"Error: {error['error_message']}")
    print(f"User: {error['user_email']}")
    print(f"Will retry: {error['will_retry']}")

# Get all user queries
queries = client.admin.get_queries()
for query in queries['queries']:
    print(f"Query: {query['search_query']}")
    print(f"Tasks: {query['total_tasks']}")
    print(f"Success rate: {query['success_rate']:.1%}")

```

### Dashboard Monitoring

```python
import time
from torale import ToraleClient

client = ToraleClient(api_key="sk_admin_...")

def monitor_platform():
    while True:
        # Get stats
        stats = client.admin.get_stats()

        # Check error rate
        executions_24h = stats['executions']['total_24h']
        failed_24h = stats['executions']['failed_24h']
        error_rate = failed_24h / executions_24h if executions_24h > 0 else 0

        print(f"Error rate: {error_rate:.1%}")

        if error_rate > 0.05:  # Alert if >5% errors
            print("⚠️  High error rate detected!")

            # Get recent errors
            errors = client.admin.get_errors(hours=1)
            print(f"Errors in last hour: {errors['total']}")
            print(f"Error types: {errors['error_types']}")

        time.sleep(300)  # Check every 5 minutes

monitor_platform()
```

## Error Responses

### Forbidden

**Status:** `403 Forbidden`

**Response:**
```json
{
  "detail": "Admin access required"
}
```

**Cause:** User doesn't have admin role in Clerk metadata.

### Unauthorized

**Status:** `401 Unauthorized`

**Response:**
```json
{
  "detail": "Invalid API key"
}
```

## Security

### Admin Access Control

- Admin role stored in Clerk `publicMetadata`
- Backend verifies role on every request
- Regular users cannot access admin endpoints

### Audit Logging

All admin actions are logged:
- User deactivations
- Bulk operations
- Data access

### Rate Limiting

Admin endpoints have higher rate limits:
- 1,000 requests/minute
- 10,000 requests/hour

## Monitoring Best Practices

### Key Metrics to Track

1. **Error Rate**
   ```python
   error_rate = failed_executions / total_executions
   alert_threshold = 0.05  # 5%
   ```

2. **Average Duration**
   ```python
   avg_duration = stats['executions']['avg_duration_ms']
   alert_threshold = 10000  # 10 seconds
   ```

3. **User Growth**
   ```python
   new_users_7d = stats['users']['new_7d']
   ```

### Alerting Thresholds

| Metric | Threshold | Action |
|--------|-----------|--------|
| Error rate | > 5% | Investigate recent errors |
| Avg duration | > 10s | Check AI API latency |
| Failed executions | > 1000/hr | Check rate limits, API status |
| New errors | > 100/hr | Review error logs |

## Next Steps

- Check [Tasks API](/api/tasks) for task management
- View [Executions API](/api/executions) for execution details
- Read [Error Handling](/api/errors) guide
- See [Architecture Documentation](/architecture/overview)
