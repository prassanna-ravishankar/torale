---
description: Install and use Torale CLI for terminal-based task management. Full API access from the command line with authentication and configuration guide.
---

# CLI

Install and use the Torale command-line interface.

## Installation

```bash
pip install torale
```

Verify installation:

```bash
torale --version
```

## Authentication

Generate an API key:

1. Log in to [torale.ai](https://torale.ai)
2. Navigate to Settings → API Keys
3. Create new key
4. Copy the key (shown only once)

Configure the CLI:

```bash
torale auth set-api-key
# Paste your API key when prompted
```

Verify authentication:

```bash
torale auth status
```

## Create a Task

```bash
torale task create \
  --query "When is the iPhone 17 being released?" \
  --condition "Apple has announced a specific release date" \
  --schedule "0 9 * * *"
```

## Preview Before Creating

Test your query without creating a task:

```bash
torale task preview \
  --query "When is the iPhone 17 being released?" \
  --condition "Apple has announced a specific release date"
```

## Manage Tasks

```bash
# List all tasks
torale task list

# Get task details
torale task get <task-id>

# Update schedule
torale task update <task-id> --schedule "0 */6 * * *"

# Pause task
torale task update <task-id> --inactive

# Delete task
torale task delete <task-id>
```

## View Results

```bash
# View execution history
torale task logs <task-id>

# View only notifications (condition met)
torale task logs <task-id> --notifications-only
```

## Next Steps

- See all [CLI Commands](/cli/commands)
- Learn about [Configuration](/cli/configuration)
- Read [Authentication Details](/cli/authentication)
