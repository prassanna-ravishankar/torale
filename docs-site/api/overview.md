---
description: webwhen REST API overview. HTTP endpoints, authentication, request and response formats, and API usage patterns.
---

# API Overview

webwhen exposes a REST API for programmatic access to every platform feature.

::: tip Naming during the transition
The API host is `api.webwhen.ai` (`api.torale.ai` still 301-redirects for legacy clients). Watches are addressed as `tasks` in URLs (`/api/v1/tasks`) — the resource rename is a later phase. Endpoint paths below reflect the current shipping API.
:::

## Base URL

```
https://api.webwhen.ai
```

## Interactive API documentation

For interactive API exploration with detailed request and response schemas:

- [OpenAPI Documentation (ReDoc)](https://api.webwhen.ai/redoc) — full API reference with schemas
- [OpenAPI Specification (JSON)](https://api.webwhen.ai/openapi.json) — machine-readable spec

::: tip Try it out
The ReDoc interface provides detailed examples and schema information for every endpoint.
:::

## Authentication

All authenticated requests need an API key or Clerk JWT in the `Authorization` header:

```bash
curl -H "Authorization: Bearer sk_..." \
  https://api.webwhen.ai/api/v1/tasks
```

Generate API keys at [webwhen.ai/settings/api-keys](https://webwhen.ai/settings/api-keys).

## Core endpoints

### Watches

```
POST   /api/v1/tasks                       # Create a watch
GET    /api/v1/tasks                       # List your watches
GET    /api/v1/tasks/{id}                  # Get an owned or public watch (auth required)
PUT    /api/v1/tasks/{id}                  # Update a watch
DELETE /api/v1/tasks/{id}                  # Delete a watch
PATCH  /api/v1/tasks/{id}/visibility       # Toggle public/private
POST   /api/v1/tasks/{id}/execute          # Execute immediately
POST   /api/v1/tasks/{id}/fork             # Fork a public watch
```

### Executions and triggers

```
GET    /api/v1/tasks/{id}/executions       # Execution history
GET    /api/v1/tasks/{id}/notifications    # Filtered: condition met only
GET    /api/v1/notifications/sends         # Notification send history
```

### Public watches (no auth required)

```
GET    /api/v1/public/tasks                        # Discover public watches
GET    /api/v1/public/tasks/id/{task_id}           # Get a public watch by UUID
```

Public endpoints always return a scrubbed representation. Supplying an
`Authorization` header does not expose owner-only fields; use the authenticated
`/api/v1/tasks/{id}` route for the owner view.

### Authentication and user management

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

### Email verification

```
POST   /api/v1/email-verification/send                          # Send verification code
POST   /api/v1/email-verification/verify                        # Verify email with code
GET    /api/v1/email-verification/verified-emails               # List verified emails
DELETE /api/v1/email-verification/verified-emails/{email}       # Remove verified email
```

### Waitlist (public)

```
POST   /public/waitlist                    # Join waitlist (no auth)
```

## Response format

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
  { "id": "uuid-1", "name": "Watch 1" },
  { "id": "uuid-2", "name": "Watch 2" }
]
```

Some public-watch endpoints wrap results with metadata:

```json
{
  "tasks": [],
  "total": 100,
  "offset": 0,
  "limit": 20
}
```

## Error handling

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

## Rate limits

Public endpoints have per-IP rate limits:

- Public watches: 10 requests/minute
- Vanity URL lookups: 20 requests/minute
- Waitlist join: 5 requests/minute

## Next steps

- Read [Authentication](/api/authentication) for API-key setup
- See the [Watches API](/api/tasks) for watch-management endpoints
- Check [Error Handling](/api/errors) for error codes
