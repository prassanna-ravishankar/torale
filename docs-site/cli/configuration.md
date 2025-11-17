# CLI Configuration

Configure the Torale CLI for your environment.

## Configuration File

Location: `~/.torale/config.json`

**Default structure:**
```json
{
  "api_key": "sk_...",
  "api_url": "https://api.torale.ai",
  "output_format": "table"
}
```

## Setting API Key

### Interactive

```bash
torale auth set-api-key
# Prompts for API key
```

### Non-Interactive

```bash
torale auth set-api-key --key sk_...
```

## API URL

### Hosted (Default)

```bash
# Uses https://api.torale.ai
torale task list
```

### Self-Hosted

```bash
# Set in config
export TORALE_API_URL=http://localhost:8000

# Or use flag
torale task list --api-url http://localhost:8000
```

## Output Formats

### Table (Default)

```bash
torale task list
```

```
ID                    Name                 Active
───────────────────────────────────────────────
550e8400...           iPhone Monitor       Yes
```

### JSON

```bash
torale task list --json
```

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "iPhone Monitor",
    "is_active": true
  }
]
```

### YAML

```bash
torale task list --yaml
```

```yaml
- id: 550e8400-e29b-41d4-a716-446655440000
  name: iPhone Monitor
  is_active: true
```

## Environment Variables

### TORALE_API_KEY

```bash
export TORALE_API_KEY=sk_...
torale task list
```

### TORALE_API_URL

```bash
export TORALE_API_URL=http://localhost:8000
torale task list
```

### TORALE_NOAUTH

Development mode without authentication:

```bash
export TORALE_NOAUTH=1
export TORALE_API_URL=http://localhost:8000
torale task list
```

## Configuration Priority

1. Command-line flags (highest)
2. Environment variables
3. Config file (`~/.torale/config.json`)
4. Defaults (lowest)

**Example:**
```bash
# Config file: sk_config123
# Environment: sk_env456
# Flag: sk_flag789

torale task list --api-key sk_flag789
# Uses: sk_flag789 (flag takes precedence)

unset TORALE_API_KEY
torale task list
# Uses: sk_config123 (from config file)
```

## Debug Mode

Enable verbose logging:

```bash
torale --debug task list
```

Output includes:
- HTTP requests/responses
- API endpoints called
- Response times
- Error details

## Proxy Configuration

### HTTP Proxy

```bash
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080
torale task list
```

### No Proxy

```bash
export NO_PROXY=localhost,127.0.0.1
```

## Timeout Settings

Default timeout: 30 seconds

### Custom Timeout

```bash
torale task list --timeout 60
```

### In Code

Edit `~/.torale/config.json`:
```json
{
  "api_key": "sk_...",
  "timeout": 60
}
```

## Shell Aliases

Add to `~/.bashrc` or `~/.zshrc`:

```bash
# Short aliases
alias t='torale'
alias tl='torale task list'
alias tc='torale task create'
alias tg='torale task get'
alias td='torale task delete'

# Common operations
alias task-active='torale task list --active'
alias task-inactive='torale task list --inactive'
alias task-notifications='torale task logs --notifications-only'
```

Usage:
```bash
tl --active
tc -q "..." -c "..." -s "0 9 * * *"
```

## Scripts

### Monitor Task Health

```bash
#!/bin/bash
# check-tasks.sh

echo "Task Health Report"
echo "=================="

# Get failed executions
for task_id in $(torale task list --json | jq -r '.[].id'); do
  task_name=$(torale task get $task_id --json | jq -r '.name')
  failures=$(torale task logs $task_id --status failed --json | jq 'length')

  if [ $failures -gt 0 ]; then
    echo "⚠️  $task_name: $failures failures"
  fi
done
```

### Bulk Create Tasks

```bash
#!/bin/bash
# bulk-create.sh

queries=(
  "When is the next iPhone release?|A date has been announced"
  "Is PS5 in stock?|Item is available"
  "What is MacBook price?|Price below $1800"
)

for query_pair in "${queries[@]}"; do
  IFS='|' read -r query condition <<< "$query_pair"

  torale task create \
    --query "$query" \
    --condition "$condition" \
    --schedule "0 9 * * *"

  echo "Created: $query"
done
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Monitor Tasks

on:
  schedule:
    - cron: '0 */6 * * *'

jobs:
  check-tasks:
    runs-on: ubuntu-latest
    steps:
      - name: Install Torale CLI
        run: pip install torale

      - name: Check task health
        env:
          TORALE_API_KEY: ${{ secrets.TORALE_API_KEY }}
        run: |
          torale task list --json | jq '.[] | select(.is_active == false)'
```

### GitLab CI

```yaml
check_tasks:
  script:
    - pip install torale
    - torale task list --active
  variables:
    TORALE_API_KEY: $CI_TORALE_API_KEY
```

## Troubleshooting

### Config File Not Found

```bash
torale task list
# Error: No API key configured
```

**Solution:**
```bash
torale auth set-api-key
```

### Permission Denied

```bash
torale auth set-api-key
# Error: Permission denied
```

**Solution:**
```bash
mkdir -p ~/.torale
chmod 700 ~/.torale
torale auth set-api-key
```

### Invalid JSON in Config

```bash
torale task list
# Error: Invalid config file
```

**Solution:**
```bash
# Reset config
rm ~/.torale/config.json
torale auth set-api-key
```

## Best Practices

### 1. Use Environment Variables in CI/CD

```bash
# ✓ Good
env:
  TORALE_API_KEY: ${{ secrets.TORALE_API_KEY }}

# ✗ Bad
torale auth set-api-key --key sk_hardcoded_key
```

### 2. Separate Keys for Different Environments

```bash
# Development
export TORALE_API_KEY=sk_dev_...

# Production
export TORALE_API_KEY=sk_prod_...
```

### 3. Use --json for Scripts

```bash
# ✓ Good - Parse JSON
torale task list --json | jq -r '.[].id'

# ✗ Bad - Parse table output
torale task list | awk '{print $1}'
```

## Next Steps

- Learn [Task Commands](/cli/tasks)
- Set up [Authentication](/cli/authentication)
- Read [API Reference](/api/tasks)
