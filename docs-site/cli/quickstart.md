---
description: Torale CLI quickstart. Install the CLI, authenticate with API keys, and create your first monitoring task from the command line in minutes.
---

# CLI Quickstart

Get started with the Torale CLI in 5 minutes.

## Install

```bash
pip install torale
```

## Authenticate

Get an API key from [torale.ai/settings/api-keys](https://torale.ai/settings/api-keys), then:

```bash
torale auth set-api-key
# Paste your key when prompted
```

## Create a Task

```bash
torale task create \
  --query "When is the iPhone 17 being released?" \
  --condition "Apple has announced a specific release date" \
  --schedule "0 9 * * *"
```

## Preview First

Test your query without creating a task:

```bash
torale task preview \
  --query "When is the iPhone 17 being released?" \
  --condition "Apple has announced a specific release date"
```

## View Tasks

```bash
torale task list
```

## Check Results

```bash
torale task logs <task-id>
```

## Next Steps

- See all [Commands](/cli/commands)
- Configure [Authentication](/cli/authentication)
- Read [Configuration Guide](/cli/configuration)
