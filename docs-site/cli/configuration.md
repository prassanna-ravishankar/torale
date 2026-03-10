---
description: Configure Torale CLI with config files and environment variables. Set API keys, API URLs, and development mode.
---

# CLI Configuration

Configure the Torale CLI for your environment.

## Configuration File

Location: `~/.torale/config.json`

```json
{
  "api_key": "sk_...",
  "api_url": "https://api.torale.ai"
}
```

Created automatically by `torale auth set-api-key`.

## View Current Config

```bash
torale config
```

Displays all settings in a table. API keys are partially masked.

## Setting API Key

```bash
torale auth set-api-key
# Prompts for API key (hidden input)
```

You can also specify a custom API URL:

```bash
torale auth set-api-key --api-url http://localhost:8000
```

## Environment Variables

### TORALE_API_KEY

```bash
export TORALE_API_KEY=sk_...
torale task list
```

### TORALE_API_URL

Override the API URL:

```bash
export TORALE_API_URL=http://localhost:8000
torale task list
```

### TORALE_NOAUTH

Skip authentication entirely (local development only):

```bash
export TORALE_NOAUTH=1
torale task list
```

When set, the API URL defaults to `http://localhost:8000` unless `TORALE_API_URL` is also set.

### TORALE_DEV

Local development with auth enabled. Sets API URL to `http://localhost:8000`:

```bash
export TORALE_DEV=1
torale task list
```

## Resolution Priority

### API Key

1. `TORALE_API_KEY` environment variable (highest)
2. `~/.torale/config.json` `api_key` field

### API URL

1. `TORALE_API_URL` environment variable (highest)
2. `TORALE_DEV=1` or `TORALE_NOAUTH=1` -> `http://localhost:8000`
3. `~/.torale/config.json` `api_url` field
4. Default: `https://api.torale.ai`

## CI/CD Integration

### GitHub Actions

```yaml
name: Monitor Tasks

jobs:
  check-tasks:
    runs-on: ubuntu-latest
    steps:
      - name: Install Torale CLI
        run: pip install torale

      - name: List active tasks
        env:
          TORALE_API_KEY: ${{ secrets.TORALE_API_KEY }}
        run: torale task list --active
```

Use `TORALE_API_KEY` as an environment variable -- no need to run `set-api-key` in CI.

## Shell Aliases

Add to `~/.bashrc` or `~/.zshrc`:

```bash
alias tl='torale task list'
alias tc='torale task create'
alias tg='torale task get'
```

## Troubleshooting

### Config File Not Found

```
No configuration found. Please run 'torale auth set-api-key' first.
```

**Solution:**
```bash
torale auth set-api-key
```

### Permission Denied

```bash
mkdir -p ~/.torale
chmod 700 ~/.torale
torale auth set-api-key
```

### Invalid JSON in Config

```bash
rm ~/.torale/config.json
torale auth set-api-key
```

## Next Steps

- Learn [Task Commands](/cli/commands)
- Set up [Authentication](/cli/authentication)
