---
description: Torale REST API overview. HTTP endpoints, authentication, request/response formats, and API usage patterns for programmatic access.
---

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

All authenticated requests require an API key or Clerk JWT in the Authorization header:

```bash
curl -H "Authorization: Bearer sk_..." \
  https://api.torale.ai/api/v1/tasks
```

Generate API keys at [torale.ai/settings/api-keys](https://torale.ai/settings/api-keys).

## Core Endpoints

### Tasks

```
POST   /api/v1/tasks                       # Create task
GET    /api/v1/tasks                       # List user's tasks
GET    /api/v1/tasks/{id}                  # Get task (public or owned)
PUT    /api/v1/tasks/{id}                  # Update task
DELETE /api/v1/tasks/{id}                  # Delete task
PATCH  /api/v1/tasks/{id}/visibility       # Toggle public/private
POST   /api/v1/tasks/{id}/execute          # Execute immediately
POST   /api/v1/tasks/{id}/fork             # Fork a public task
```

### Executions & Notifications

```
GET    /api/v1/tasks/{id}/executions       # Execution history
GET    /api/v1/tasks/{id}/notifications    # Filtered: condition met only
GET    /api/v1/notifications/sends         # Notification send history
```

### Public Tasks (no auth required)

```
GET    /api/v1/public/tasks                        # Discover public tasks
GET    /api/v1/public/tasks/{username}/{slug}       # Get task by vanity URL
GET    /api/v1/public/tasks/id/{task_id}            # Get public task by UUID
```

### Authentication & User Management

```
POST   /auth/sync-user                     # Sync Clerk user to DB
GET    /auth/me                            # Current user info
POST   /auth/mark-welcome-seen             # Mark welcome flow seen
POST   /auth/api-keys                      # Generate API key
GET    /auth/api-keys                      # List API keys
DELETE /auth/api-keys/{id}                 # Revoke API key
```

### Users

```
GET    /api/v1/users/username/available     # Check username availability
PATCH  /api/v1/users/me/username            # Set username
```

### Email Verification

```
POST   /api/v1/email-verification/send           # Send verification code
POST   /api/v1/email-verification/verify          # Verify email with code
GET    /api/v1/email-verification/verified-emails  # List verified emails
DELETE /api/v1/email-verification/verified-emails/{email}  # Remove verified email
```

### Admin (requires admin role, hidden from OpenAPI schema)

```
GET    /admin/stats                        # Platform statistics
GET    /admin/queries                      # All user queries
GET    /admin/executions                   # All executions
GET    /admin/scheduler/jobs               # APScheduler jobs
GET    /admin/errors                       # Failed executions
GET    /admin/users                        # User management
PATCH  /admin/users/{id}/deactivate        # Deactivate user
PATCH  /admin/users/{id}/role              # Update user role
PATCH  /admin/users/roles                  # Bulk update roles
GET    /admin/waitlist                     # List waitlist entries
GET    /admin/waitlist/stats               # Waitlist statistics
PATCH  /admin/waitlist/{id}                # Update waitlist entry
DELETE /admin/waitlist/{id}                # Delete waitlist entry
POST   /admin/tasks/{id}/execute           # Execute any task
PATCH  /admin/tasks/{id}/state             # Change task state
DELETE /admin/tasks/{id}/reset             # Reset task history
```

### Waitlist (public)

```
POST   /public/waitlist                    # Join waitlist (no auth)
```

## Response Format

Responses use JSON. Most endpoints return the resource directly:

```json
{
  "id": "uuid",
  "field": "value",
  "created_at": "2025-01-15T10:30:00Z"
}
```

List endpoints like `GET /api/v1/tasks` return a bare JSON array:

```json
[
  { "id": "uuid-1", "name": "Task 1", ... },
  { "id": "uuid-2", "name": "Task 2", ... }
]
```

Some admin and public task endpoints wrap results with metadata:

```json
{
  "tasks": [...],
  "total": 100,
  "offset": 0,
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

Validation errors (422) include field-level details:

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

## Rate Limits

Public endpoints have per-IP rate limits:

- Public tasks: 10 requests/minute
- Vanity URL lookups: 20 requests/minute
- Waitlist join: 5 requests/minute

## Next Steps

- Read [Authentication](/api/authentication) for API key setup
- View [Tasks API](/api/tasks) for task management endpoints
- Check [Error Handling](/api/errors) for error codes
