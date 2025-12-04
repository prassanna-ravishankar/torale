# CLI Authentication

Authenticate the Torale CLI with your account.

## Setting Up Authentication

### Generate API Key

1. Log in to [torale.ai](https://torale.ai)
2. Navigate to Settings → API Keys
3. Click "Generate New Key"
4. Enter name (e.g., "CLI Key")
5. Copy key immediately (shown only once)

### Configure CLI

```bash
torale auth set-api-key
# Paste your API key when prompted
```

The key is stored securely in `~/.torale/config.json`.

## Verify Authentication

```bash
torale auth status
```

**Output:**
```
✓ Authenticated as user@example.com
API Key: sk_...xyz89
```

## Check Current User

```bash
torale auth whoami
```

**Output:**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "state": "active"
}
```

## Logout

```bash
torale auth logout
```

Removes stored credentials from `~/.torale/config.json`.

## Environment Variable

Alternatively, use environment variable:

```bash
export TORALE_API_KEY=sk_...
torale task list
```

**Priority:**
1. `--api-key` flag (highest)
2. `TORALE_API_KEY` environment variable
3. `~/.torale/config.json` file (lowest)

## Using --api-key Flag

```bash
torale task list --api-key sk_...
```

Useful for:
- CI/CD pipelines
- Temporary access
- Multiple accounts

## Development Mode (No Auth)

For local development without authentication:

```bash
export TORALE_NOAUTH=1
export TORALE_API_URL=http://localhost:8000

torale task list
```

**Note:** Only works with local development API.

## Troubleshooting

### Invalid API Key

```bash
torale task list
# Error: Invalid API key
```

**Solutions:**
1. Regenerate key in dashboard
2. Run `torale auth set-api-key` with new key
3. Verify key format: `sk_[32 characters]`

### Missing Configuration

```bash
torale task list
# Error: No API key configured
```

**Solution:**
```bash
torale auth set-api-key
```

### Connection Refused

```bash
torale task list
# Error: Connection refused
```

**Causes:**
- API is down
- Network issue
- Wrong API URL (if self-hosted)

**For self-hosted:**
```bash
export TORALE_API_URL=http://localhost:8000
```

## Security Best Practices

### 1. Don't Share API Keys

```bash
# ✗ Bad - Don't commit to git
git add .torale/config.json

# ✓ Good - Add to .gitignore
echo ".torale/" >> ~/.gitignore
```

### 2. Rotate Keys Regularly

```bash
# Generate new key in dashboard
torale auth set-api-key
# Paste new key

# Revoke old key in dashboard
```

### 3. Use Separate Keys

- Development: `Dev CLI Key`
- Production: `Production CLI Key`
- CI/CD: `GitHub Actions Key`

### 4. Revoke Unused Keys

Visit torale.ai → Settings → API Keys → Revoke

## Next Steps

- Learn [Task Commands](/cli/commands)
- Configure [Settings](/cli/configuration)
- Read [API Reference](/api/authentication)
