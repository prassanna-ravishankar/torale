# API Overview

Torale provides a REST API for programmatic access to all platform functionality.

## Base URL

```
https://api.torale.ai
```

## Interactive API Documentation

For interactive API exploration with detailed request/response schemas:

- [OpenAPI Documentation (ReDoc)](https://api.torale.ai/redoc) - Full API reference with schemas
- [OpenAPI Specification (JSON)](https://api.torale.ai/openapi.json) - Machine-readable API spec

::: tip Try It Out
The ReDoc interface provides detailed examples and schema information for every endpoint.
:::

## Authentication

All requests require authentication via API key in the Authorization header:

```bash
curl -H "Authorization: Bearer sk_..." \
  https://api.torale.ai/api/v1/tasks
```

Generate API keys at [torale.ai/settings/api-keys](https://torale.ai/settings/api-keys).

## Core Endpoints

### Tasks

```
POST   /api/v1/tasks                    # Create task
POST   /api/v1/tasks/suggest            # Get suggested task from query
GET    /api/v1/tasks                    # List tasks
GET    /api/v1/tasks/{id}               # Get task
PUT    /api/v1/tasks/{id}               # Update task
DELETE /api/v1/tasks/{id}               # Delete task
PATCH  /api/v1/tasks/{id}/visibility    # Update task visibility
POST   /api/v1/tasks/{id}/execute       # Execute immediately
POST   /api/v1/tasks/{id}/fork          # Fork task
```

### Executions

```
GET    /api/v1/tasks/{id}/executions    # Execution history
GET    /api/v1/tasks/{id}/notifications # Filtered: condition_met only
```

### Authentication

```
POST   /auth/sync-user                  # Sync Clerk user
GET    /auth/me                         # Current user
POST   /auth/api-keys                   # Generate key
GET    /auth/api-keys                   # List keys
DELETE /auth/api-keys/{id}              # Revoke key
```

### Admin (requires admin role)

```
GET    /admin/stats                     # Platform statistics
GET    /admin/queries                   # All user queries
GET    /admin/executions                # All executions
GET    /admin/temporal/workflows        # Temporal workflows
GET    /admin/temporal/schedules        # Active schedules
GET    /admin/errors                    # Failed executions
GET    /admin/users                     # User management
PATCH  /admin/users/{id}/deactivate     # Deactivate user
```

## Response Format

All responses use JSON with consistent structure:

```json
{
  "id": "uuid",
  "field": "value",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

Lists include pagination metadata:

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "limit": 20
}
```

## Error Handling

Errors follow standard HTTP status codes with detail messages:

```json
{
  "detail": "Error description"
}
```

Validation errors include field-level details:

```json
{
  "detail": [
    {
      "loc": ["body", "schedule"],
      "msg": "Invalid cron expression"
    }
  ]
}
```

## Rate Limits

- 100 requests/minute per API key
- 1,000 requests/hour per API key
- 10,000 requests/day per API key

Rate limit headers included in responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1737024000
```

## Next Steps

- Read [Authentication](/api/authentication) for API key setup
- View [Tasks API](/api/tasks) for task management endpoints
- Check [Error Handling](/api/errors) for error codes
