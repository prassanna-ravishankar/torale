---
description: Authenticate Torale CLI with API keys. Generate keys in web dashboard, configure CLI authentication, and check auth status.
---

# CLI Authentication

Authenticate the Torale CLI with your account.

## Setting Up Authentication

### Generate API Key

1. Log in to [torale.ai](https://torale.ai)
2. Navigate to Settings -> API Keys
3. Click "Generate New Key"
4. Enter a name (e.g., "CLI Key")
5. Copy the key immediately (shown only once)

API keys start with `sk_`.

### Configure CLI

```bash
torale auth set-api-key
# Paste your API key when prompted
```

You can also specify a custom API URL (useful for local development):

```bash
torale auth set-api-key --api-url http://localhost:8000
```

The key and URL are stored in `~/.torale/config.json`.

## Check Authentication Status

```bash
torale auth status
```

**Output (authenticated):**
```
Authenticated with API key
API Key: sk_abc12345...
API URL: https://api.torale.ai
```

**Output (no-auth mode):**
```
Running in NOAUTH mode (TORALE_NOAUTH=1)
Authentication is disabled for local development.
```

## Logout

Remove stored credentials:

```bash
torale auth logout
```

## Authentication Priority

The SDK resolves credentials in this order:

1. `TORALE_API_KEY` environment variable
2. `~/.torale/config.json` file

## Environment Variable

Set the API key via environment variable instead of the config file:

```bash
export TORALE_API_KEY=sk_...
torale task list
```

This is useful for CI/CD pipelines where you don't want to run `set-api-key`.

## Development Mode (No Auth)

For local development without authentication:

```bash
export TORALE_NOAUTH=1
torale task list
```

When `TORALE_NOAUTH=1` is set, the CLI skips authentication entirely and the API URL defaults to `http://localhost:8000` (unless overridden by `TORALE_API_URL`).

## Troubleshooting

### Invalid API Key

```
Not authenticated.
```

**Solutions:**
1. Regenerate key in the dashboard
2. Run `torale auth set-api-key` with the new key
3. Verify key format starts with `sk_`

### Missing Configuration

```
No configuration found. Please run 'torale auth set-api-key' first.
```

**Solution:**
```bash
torale auth set-api-key
```

## Security Best Practices

1. **Don't commit credentials** -- add `.torale/` to your `.gitignore`
2. **Rotate keys regularly** -- generate a new key, configure CLI, revoke the old one
3. **Use separate keys** for development vs production vs CI/CD
4. **Use environment variables** in CI/CD rather than config files

## Next Steps

- Learn [Task Commands](/cli/commands)
- Configure [Settings](/cli/configuration)
