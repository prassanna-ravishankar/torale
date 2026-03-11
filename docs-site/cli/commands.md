---
description: Complete Torale CLI command reference. Create tasks, list monitors, view executions, and manage notifications from the terminal.
---

# Commands Reference

## Global Commands

### `torale version`

Show version information.

```bash
torale version
```

### `torale config`

Show current configuration from `~/.torale/config.json`. Displays settings in a table, with API keys partially masked.

```bash
torale config
```

---

## Auth Commands

### `torale auth set-api-key`

Save an API key to `~/.torale/config.json`. Prompts for the key interactively (input is hidden).

```bash
torale auth set-api-key
```

**Options:**

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--api-key` | Yes (prompted) | -- | API key (prompted interactively, hidden input) |
| `--api-url` | No | `https://api.torale.ai` | API URL |

The key must start with `sk_` or it will be rejected.

### `torale auth status`

Check authentication status. Reports whether you're authenticated via API key or running in no-auth mode.

```bash
torale auth status
```

### `torale auth logout`

Clear stored credentials by deleting `~/.torale/config.json`.

```bash
torale auth logout
```

---

## Task Commands

### `torale task create`

Create a new monitoring task.

```bash
torale task create \
  --query "When is the iPhone 17 being released?" \
  --condition "Apple has announced a specific release date"
```

**Options:**

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--query`, `-q` | Yes | -- | What to monitor (search query) |
| `--condition`, `-c` | Yes | -- | When to trigger notification |
| `--name`, `-n` | No | Auto-generated | Task name |
| `--notify-behavior` | No | `once` | `once` or `always` |
| `--webhook`, `-w` | No | -- | Webhook URL to call when condition is met |

**Examples:**

```bash
# Minimal
torale task create \
  -q "When is GPT-5 being released?" \
  -c "Release date announced"

# With name and webhook
torale task create \
  --name "iPhone Release Monitor" \
  --query "When is the next iPhone release?" \
  --condition "Apple has announced a specific date" \
  --webhook "https://myapp.com/alert"

# Notify every time condition is met
torale task create \
  -q "What is the PS5 price at Best Buy?" \
  -c "Price is $449 or lower" \
  --notify-behavior always
```

If `--name` is omitted, the name is auto-generated from the query (e.g., "Monitor: When is GPT-5 being released?").

### `torale task list`

List all monitoring tasks in a table.

```bash
torale task list
```

**Options:**

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--active` | No | `false` | Show only active tasks |

**Examples:**

```bash
# All tasks
torale task list

# Active tasks only
torale task list --active
```

**Output:**
```
        Your Monitoring Tasks
ID          Name                  Query                      Active  Created
────────────────────────────────────────────────────────────────────────────
550e8400... iPhone Release Monitor When is the next iPhone... ✓      2024-01-15 10:30:00
660e8400... PS5 Stock Alert       Is PS5 in stock at Best... ✗      2024-01-14 08:00:00
```

### `torale task get`

Get details of a specific task.

```bash
torale task get <task-id>
```

**Output:**
```
Task Details
ID: 550e8400-e29b-41d4-a716-446655440000
Name: iPhone Release Monitor
Query: When is the next iPhone release?
Condition: A specific date has been announced
State: active
Notify Behavior: once
Created: 2024-01-15 10:30:00
```

If the task has notifications configured or a last known state, those are displayed as well.

### `torale task update`

Update a monitoring task. Only `--name` and `--active/--inactive` are supported.

```bash
torale task update <task-id> --name "New Name"
```

**Options:**

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--name`, `-n` | No | -- | New task name |
| `--active/--inactive` | No | -- | Set task state to active or paused |

**Examples:**

```bash
# Rename
torale task update <task-id> --name "Updated Monitor"

# Pause
torale task update <task-id> --inactive

# Reactivate
torale task update <task-id> --active

# Both at once
torale task update <task-id> --name "Renamed" --active
```

If no flags are provided, the command prints a warning and does nothing.

### `torale task delete`

Delete a monitoring task. Prompts for confirmation unless `--yes` is passed.

```bash
torale task delete <task-id>
```

**Options:**

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--yes`, `-y` | No | `false` | Skip confirmation prompt |

**Examples:**

```bash
# With confirmation prompt
torale task delete <task-id>

# Skip confirmation
torale task delete <task-id> --yes
```

### `torale task execute`

Manually trigger a task execution (test run).

```bash
torale task execute <task-id>
```

**Output:**
```
Task execution started!
Execution ID: 880e8400-e29b-41d4-a716-446655440000
Status: pending
```

### `torale task logs`

View execution logs for a task.

```bash
torale task logs <task-id>
```

**Options:**

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--limit`, `-l` | No | `10` | Number of executions to show |

**Examples:**

```bash
# Default (last 10)
torale task logs <task-id>

# Last 25
torale task logs <task-id> --limit 25
```

**Output:**
```
     Execution Logs (Task: 550e8400...)
Execution ID  Status   Notification                      Started              Completed
──────────────────────────────────────────────────────────────────────────────────────────
880e8400...   success  iPhone 16 releases September 20   2024-01-15 09:00:05  2024-01-15 09:00:09
990e8400...   success  -                                 2024-01-14 09:00:03  2024-01-14 09:00:07
```

### `torale task notifications`

View notifications (executions where the condition was met) for a task.

```bash
torale task notifications <task-id>
```

**Options:**

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--limit`, `-l` | No | `10` | Number of notifications to show |

**Examples:**

```bash
torale task notifications <task-id>
torale task notifications <task-id> --limit 5
```

---

## Common Workflows

### Create and Test

```bash
# Create
torale task create \
  -q "When is the next iPhone release?" \
  -c "A date has been announced"

# Trigger a manual run
torale task execute <task-id>

# Check execution result
torale task logs <task-id> --limit 1
```

### Monitor Task Health

```bash
# View task status
torale task get <task-id>

# Check recent executions
torale task logs <task-id> --limit 5
```

### Pause and Resume

```bash
# Pause
torale task update <task-id> --inactive

# Resume
torale task update <task-id> --active
```

## Troubleshooting

### Task Not Found

```
Failed to get task: ...
```

**Solution:** Verify the task ID with `torale task list`.

## Next Steps

- Configure [Settings](/cli/configuration)
- Set up [Authentication](/cli/authentication)
