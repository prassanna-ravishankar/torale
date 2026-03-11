---
description: API authentication with API keys and bearer tokens. Generate keys, secure credential storage, and authentication best practices.
---

# Authentication

Torale supports two authentication methods: Clerk OAuth for web applications and API keys for programmatic access.

## Authentication Methods

### 1. Clerk OAuth (Web Dashboard)

Used for browser-based authentication in the web dashboard.

**Supported providers:**
- Google OAuth
- GitHub OAuth
- Email/Password

**How it works:**
1. User logs in via Clerk at torale.ai
2. Clerk issues JWT token
3. Frontend includes token in API requests
4. Backend verifies token with Clerk

**No manual setup required** - handled automatically by the web dashboard.

### 2. API Keys (CLI & SDK)

Used for programmatic access via CLI or Python SDK.

**Key format:**
```
sk_[32 random characters]
Example: sk_abc123def456ghi789jkl012mno345pq
```

**Security:**
- Keys are bcrypt hashed before storage
- Only shown once during creation
- Can be revoked anytime
- One active key per user (revoke before creating new)

**Requires developer role:** API key creation requires `"role": "developer"` or `"role": "admin"` in Clerk `publicMetadata`.

## Getting an API Key

### Web Dashboard

1. **Log in** to [torale.ai](https://torale.ai)
2. **Navigate** to Settings -> API Keys
3. **Click** "Generate New Key"
4. **Enter** key name (e.g., "CLI Key", "Production Script")
5. **Copy** key immediately (shown only once)
6. **Save** securely

### Key Management

**List keys:**
- View all your API keys in dashboard
- See last used timestamp
- Identify keys by name and prefix

**Revoke key:**
- Click "Revoke" next to key
- Immediate revocation
- Cannot be undone

## Using API Keys

### HTTP Requests

**Include in Authorization header:**
```bash
curl -X GET https://api.torale.ai/api/v1/tasks \
  -H "Authorization: Bearer sk_..."
```

**Example with cURL:**
```bash
API_KEY="sk_..."

curl -X POST https://api.torale.ai/api/v1/tasks \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "iPhone Release Monitor",
    "search_query": "When is the next iPhone release?",
    "condition_description": "A specific date has been announced"
  }'
```

## Authentication Endpoints

### Sync User (Web Dashboard Only)

Create or update user record after Clerk authentication. Called automatically by frontend on login.

**Endpoint:** `POST /auth/sync-user`

**Headers:**
```
Authorization: Bearer {clerk_jwt_token}
```

**Response:** `200 OK`
```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "clerk_user_id": "user_2abc...",
    "email": "user@example.com",
    "first_name": "Jane",
    "username": null,
    "is_active": true,
    "has_seen_welcome": false,
    "created_at": "2025-01-15T10:30:00Z"
  },
  "created": true
}
```

### Get Current User

**Endpoint:** `GET /auth/me`

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "clerk_user_id": "user_2abc...",
  "email": "user@example.com",
  "first_name": "Jane",
  "username": "jane",
  "is_active": true,
  "has_seen_welcome": true,
  "created_at": "2025-01-15T10:30:00Z"
}
```

### Mark Welcome Seen

Mark that the user has completed the welcome flow.

**Endpoint:** `POST /auth/mark-welcome-seen`

**Response:** `200 OK`
```json
{
  "status": "success"
}
```

### Generate API Key

Create a new API key. Requires developer role.

**Endpoint:** `POST /auth/api-keys`

**Request body:**
```json
{
  "name": "CLI Key"
}
```

**Response:** `200 OK`
```json
{
  "key": "sk_abc123def456ghi789jkl012mno345pq",
  "key_info": {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "key_prefix": "sk_abc123def456...",
    "name": "CLI Key",
    "created_at": "2025-01-15T10:30:00Z",
    "last_used_at": null,
    "is_active": true
  }
}
```

**Errors:**
- `400` if user already has an active key (revoke first)
- `404` if user not synced yet

### List API Keys

**Endpoint:** `GET /auth/api-keys`

**Response:** `200 OK`
```json
[
  {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "key_prefix": "sk_abc123def456...",
    "name": "CLI Key",
    "created_at": "2025-01-15T10:30:00Z",
    "last_used_at": "2025-01-20T15:45:00Z",
    "is_active": true
  }
]
```

### Revoke API Key

**Endpoint:** `DELETE /auth/api-keys/{id}`

**Response:** `200 OK`
```json
{
  "status": "revoked"
}
```

Returns `404` if key not found or doesn't belong to user.

## Security Best Practices

### Protecting API Keys

**Do:**
- Store keys in environment variables
- Use secret management services (AWS Secrets Manager, 1Password, etc.)
- Rotate keys periodically
- Revoke unused keys

**Don't:**
- Commit keys to version control
- Share keys via email or chat
- Hardcode keys in source code
- Store keys in plain text files

### Environment Variables

```bash
# .env (add to .gitignore!)
TORALE_API_KEY=sk_...
```

## Development Mode (No Auth)

For local development without authentication:

```bash
export TORALE_NOAUTH=1
```

Only works with local development API (`localhost:8000`). The backend uses a test user for all requests.

## Error Responses

### Invalid API Key

**Status:** `401 Unauthorized`
```json
{
  "detail": "Invalid API key"
}
```

### Missing Authorization

**Status:** `401 Unauthorized`
```json
{
  "detail": "Authorization header missing"
}
```

### Expired Token (Clerk)

**Status:** `401 Unauthorized`
```json
{
  "detail": "Token has expired"
}
```

## Next Steps

- Create tasks using [Tasks API](/api/tasks)
- View execution history with [Executions API](/api/executions)
- Check [Error Handling](/api/errors) guide
