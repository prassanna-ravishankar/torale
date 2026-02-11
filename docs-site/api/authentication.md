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
- Keys are SHA256 hashed before storage
- Only shown once during creation
- Can be revoked anytime
- Per-user key management

## Getting an API Key

### Web Dashboard

1. **Log in** to [torale.ai](https://torale.ai)
2. **Navigate** to Settings → API Keys
3. **Click** "Generate New Key"
4. **Enter** key name (e.g., "CLI Key", "Production Script")
5. **Copy** key immediately (shown only once)
6. **Save** securely

### Key Management

**List keys:**
- View all your API keys in dashboard
- See last used timestamp
- Identify keys by name

**Revoke key:**
- Click "Revoke" next to key
- Immediate revocation (existing requests may complete)
- Cannot be undone

## Using API Keys

### CLI

**Set API key:**
```bash
torale auth set-api-key
# Paste your key when prompted
```

**Check authentication:**
```bash
torale auth status
# Shows: Authenticated as user@example.com
```

**Logout:**
```bash
torale auth logout
# Removes stored credentials
```

### Python SDK

**Initialize client:**
```python
from torale import ToraleClient

client = ToraleClient(api_key="sk_...")
```

**Using environment variable:**
```python
import os
from torale import ToraleClient

# Set environment variable
os.environ["TORALE_API_KEY"] = "sk_..."

# Client reads from environment
client = ToraleClient()
```

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
    "condition_description": "A specific date has been announced",
    "schedule": "0 9 * * *"
  }'
```

## Authentication Endpoints

### Sync User (Web Dashboard Only)

Create or update user record after Clerk authentication.

**Endpoint:** `POST /auth/sync-user`

**Headers:**
```
Authorization: Bearer {clerk_jwt_token}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "clerk_user_id": "user_2abc...",
  "email": "user@example.com",
  "state": "active",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Note:** Called automatically by frontend on login.

### Get Current User

Get authenticated user information.

**Endpoint:** `GET /auth/me`

**Headers:**
```
Authorization: Bearer {api_key}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "state": "active",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Example:**
```bash
curl -X GET https://api.torale.ai/auth/me \
  -H "Authorization: Bearer sk_..."
```

### Generate API Key

Create a new API key.

**Endpoint:** `POST /auth/api-keys`

**Headers:**
```
Authorization: Bearer {clerk_jwt_token_or_api_key}
```

**Request body:**
```json
{
  "name": "CLI Key"
}
```

**Response:**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "key": "sk_abc123def456ghi789jkl012mno345pq",
  "key_prefix": "sk_...345pq",
  "name": "CLI Key",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Important:** `key` field only appears in creation response. Store securely!

**Example:**
```bash
curl -X POST https://api.torale.ai/auth/api-keys \
  -H "Authorization: Bearer sk_..." \
  -H "Content-Type: application/json" \
  -d '{"name": "CLI Key"}'
```

### List API Keys

Get all your API keys (keys redacted).

**Endpoint:** `GET /auth/api-keys`

**Headers:**
```
Authorization: Bearer {clerk_jwt_token_or_api_key}
```

**Response:**
```json
[
  {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "key_prefix": "sk_...345pq",
    "name": "CLI Key",
    "created_at": "2024-01-15T10:30:00Z",
    "last_used_at": "2024-01-20T15:45:00Z",
    "state": "active"
  },
  {
    "id": "770e8400-e29b-41d4-a716-446655440000",
    "key_prefix": "sk_...xyz89",
    "name": "Production Script",
    "created_at": "2024-01-10T09:00:00Z",
    "last_used_at": "2024-01-20T16:00:00Z",
    "state": "active"
  }
]
```

**Example:**
```bash
curl -X GET https://api.torale.ai/auth/api-keys \
  -H "Authorization: Bearer sk_..."
```

### Revoke API Key

Revoke (deactivate) an API key.

**Endpoint:** `DELETE /auth/api-keys/{id}`

**Headers:**
```
Authorization: Bearer {clerk_jwt_token_or_api_key}
```

**Response:**
```json
{
  "message": "API key revoked successfully"
}
```

**Example:**
```bash
curl -X DELETE https://api.torale.ai/auth/api-keys/660e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer sk_..."
```

## Security Best Practices

### Protecting API Keys

**✓ Do:**
- Store keys in environment variables
- Use secret management services (AWS Secrets Manager, 1Password, etc.)
- Rotate keys periodically
- Use different keys for different environments
- Revoke unused keys

**✗ Don't:**
- Commit keys to version control
- Share keys via email or chat
- Hardcode keys in source code
- Use same key across multiple projects
- Store keys in plain text files

### Environment Variables

**Development (.env file):**
```bash
# .env (add to .gitignore!)
TORALE_API_KEY=sk_...
```

**Production (system environment):**
```bash
# Set in deployment environment
export TORALE_API_KEY=sk_...
```

**Python example:**
```python
import os
from torale import ToraleClient

# Read from environment
api_key = os.getenv("TORALE_API_KEY")

# Verify key exists
if not api_key:
    raise ValueError("TORALE_API_KEY environment variable not set")

client = ToraleClient(api_key=api_key)
```

### Key Rotation

**Best practice:** Rotate keys every 90 days

**Steps:**
1. Generate new key in dashboard
2. Update applications with new key
3. Test that new key works
4. Revoke old key
5. Verify no services using old key

### Rate Limiting

API keys are subject to rate limits:

**Limits:**
- 100 requests per minute per key
- 1000 requests per hour per key
- 10,000 requests per day per key

**Rate limit headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642257600
```

**Handling rate limits:**
```python
from torale import ToraleClient
from torale.exceptions import RateLimitError
import time

client = ToraleClient(api_key="sk_...")

try:
    tasks = client.tasks.list()
except RateLimitError as e:
    # Wait and retry
    retry_after = e.retry_after  # seconds
    time.sleep(retry_after)
    tasks = client.tasks.list()
```

## Error Responses

### Invalid API Key

**Status:** `401 Unauthorized`

**Response:**
```json
{
  "detail": "Invalid API key"
}
```

**Causes:**
- Key doesn't exist
- Key was revoked
- Key format is incorrect

### Missing Authorization

**Status:** `401 Unauthorized`

**Response:**
```json
{
  "detail": "Authorization header missing"
}
```

**Causes:**
- No Authorization header in request
- Header format incorrect (should be `Bearer {key}`)

### Expired Token (Clerk)

**Status:** `401 Unauthorized`

**Response:**
```json
{
  "detail": "Token has expired"
}
```

**Causes:**
- Clerk JWT token expired
- Need to refresh authentication

### Rate Limit Exceeded

**Status:** `429 Too Many Requests`

**Response:**
```json
{
  "detail": "Rate limit exceeded",
  "retry_after": 60
}
```

**Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1642257600
Retry-After: 60
```

## Development Mode (No Auth)

For local development without authentication:

**CLI:**
```bash
export TORALE_NOAUTH=1
torale task list
```

**SDK:**
```python
import os
os.environ["TORALE_NOAUTH"] = "1"

from torale import ToraleClient
client = ToraleClient()  # No API key needed
```

**Note:** Only works with local development API (localhost:8000)

## Next Steps

- Create tasks using [Tasks API](/api/tasks)
- View execution history with [Executions API](/api/executions)
- Check [Error Handling](/api/errors) guide
- Read [SDK Documentation](/sdk/installation)
