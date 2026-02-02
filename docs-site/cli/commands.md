# Task Commands

Manage monitoring tasks via CLI.

## Create Task

```bash
torale task create \
  --query "When is the next iPhone release?" \
  --condition "A specific date has been announced" \
  --schedule "0 9 * * *"
```

**Options:**

| Flag | Required | Description |
|------|----------|-------------|
| `--query`, `-q` | Yes | Search query |
| `--condition`, `-c` | Yes | Condition description |
| `--schedule`, `-s` | Yes | Cron expression |
| `--name`, `-n` | No | Task name (auto-generated if omitted) |
| `--notify-behavior` | No | `once` or `always` (default: `once`) |
| `--run-immediately` | No | Execute immediately after creation |

**Examples:**

```bash
# Basic task
torale task create \
  -q "When is GPT-5 being released?" \
  -c "Release date announced" \
  -s "0 9 * * *"

# With all options
torale task create \
  --name "iPhone Release Monitor" \
  --query "When is the next iPhone release?" \
  --condition "Apple has announced a specific date" \
  --schedule "0 9 * * *" \
  --notify-behavior once \
  --run-immediately

# Price monitoring
torale task create \
  -q "What is the PS5 price at Best Buy?" \
  -c "Price is $449 or lower" \
  -s "0 */4 * * *" \
  --notify-behavior always
```

## Preview Task

Test query without creating task:

```bash
torale task preview \
  --query "When is the next iPhone release?" \
  --condition "A specific date has been announced"
```

**Output:**
```json
{
  "condition_met": true,
  "answer": "Apple has announced iPhone 16 will be released on September 20, 2024",
  "reasoning": "Official announcement confirms specific date",
  "sources": [
    "https://www.apple.com/newsroom/...",
    "https://www.theverge.com/..."
  ]
}
```

## List Tasks

```bash
# List all tasks
torale task list

# Filter active only
torale task list --active

# Filter inactive only
torale task list --inactive

# JSON output
torale task list --json

# Limit results
torale task list --limit 10
```

**Output:**
```
ID                                   Name                     Active  Condition Met
─────────────────────────────────────────────────────────────────────────────────
550e8400-e29b-41d4-a716-446655440000 iPhone Release Monitor   Yes     Yes
660e8400-e29b-41d4-a716-446655440000 PS5 Stock Alert          Yes     No
770e8400-e29b-41d4-a716-446655440000 MacBook Price Tracker    No      No
```

## Get Task Details

```bash
torale task get <task-id>

# JSON output
torale task get <task-id> --json
```

**Output:**
```
Task Details
─────────────────────────────────────────
ID:               550e8400-e29b-41d4-a716-446655440000
Name:             iPhone Release Monitor
Search Query:     When is the next iPhone release?
Condition:        A specific date has been announced
Schedule:         0 9 * * * (Daily at 9:00 AM)
Notify Behavior:  once
Status:           Active
Condition Met:    Yes
Last Notified:    2024-01-15 14:23:45 UTC
Created:          2024-01-15 10:30:00 UTC
```

## Update Task

```bash
# Update schedule
torale task update <task-id> --schedule "0 */6 * * *"

# Change notification behavior
torale task update <task-id> --notify-behavior always

# Update name
torale task update <task-id> --name "New Task Name"

# Pause task
torale task update <task-id> --inactive

# Activate task
torale task update <task-id> --active

# Multiple updates
torale task update <task-id> \
  --schedule "0 9 * * *" \
  --notify-behavior once \
  --active
```

## Delete Task

```bash
# Delete with confirmation
torale task delete <task-id>

# Skip confirmation
torale task delete <task-id> --yes

# Delete multiple
torale task delete <task-id-1> <task-id-2> --yes
```

## Execute Task

Trigger immediate execution:

```bash
torale task execute <task-id>
```

**Output:**
```
✓ Task execution initiated
Execution ID: 880e8400-e29b-41d4-a716-446655440000

Check status with:
  torale task logs <task-id>
```

## View Execution Logs

```bash
# View all executions
torale task logs <task-id>

# Filter by status
torale task logs <task-id> --status success
torale task logs <task-id> --status failed

# Show only notifications (condition_met = true)
torale task logs <task-id> --notifications-only

# Limit results
torale task logs <task-id> --limit 10

# JSON output
torale task logs <task-id> --json
```

**Output:**
```
Execution History for: iPhone Release Monitor
───────────────────────────────────────────────────────────────────

2024-01-15 09:00:05 UTC | SUCCESS | Condition Met: Yes
Answer: Apple has announced iPhone 16 will be released on September 20, 2024
Sources: apple.com, theverge.com
Duration: 4.2s

2024-01-14 09:00:03 UTC | SUCCESS | Condition Met: No
Answer: No official release date has been announced yet
Duration: 3.8s

2024-01-13 09:00:04 UTC | SUCCESS | Condition Met: No
Answer: No official release date has been announced yet
Duration: 4.1s
```

## Common Workflows

### Create and Test

```bash
# Preview first
torale task preview \
  -q "When is the next iPhone release?" \
  -c "A date has been announced"

# If results look good, create
torale task create \
  -q "When is the next iPhone release?" \
  -c "A date has been announced" \
  -s "0 9 * * *" \
  --run-immediately

# Check execution
torale task logs <task-id> --limit 1
```

### Monitor Task Health

```bash
# View task status
torale task get <task-id>

# Check recent executions
torale task logs <task-id> --limit 5

# Check for failures
torale task logs <task-id> --status failed
```

### Bulk Operations

```bash
# Pause all tasks
for task_id in $(torale task list --json | jq -r '.[].id'); do
  torale task update $task_id --inactive
done

# Delete inactive tasks
for task_id in $(torale task list --inactive --json | jq -r '.[].id'); do
  torale task delete $task_id --yes
done
```

## Troubleshooting

### Invalid Cron Expression

```bash
torale task create -q "..." -c "..." -s "invalid"
# Error: Invalid cron expression
```

**Solution:** Use valid cron syntax. Test at crontab.guru

### Task Not Found

```bash
torale task get wrong-id
# Error: Task not found
```

**Solution:** Verify task ID with `torale task list`

### Rate Limited

```bash
torale task create ...
# Error: Rate limit exceeded. Retry after 60 seconds
```

**Solution:** Wait 60 seconds and retry

## Output Formats

### Human-Readable (Default)

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
    "state": "active",
    ...
  }
]
```

### Scripting with jq

```bash
# Get task IDs
torale task list --json | jq -r '.[].id'

# Filter active tasks
torale task list --json | jq '.[] | select(.state == "active")'

# Count tasks
torale task list --json | jq 'length'
```

## Next Steps

- Configure [Settings](/cli/configuration)
- Set up [Authentication](/cli/authentication)
- Read [API Reference](/api/tasks)
