---
name: torale
description: Monitor the web for conditions using AI-powered grounded search and get notified when they're met
metadata: {"openclaw": {"requires": {"env": ["TORALE_API_KEY"]}, "primaryEnv": "TORALE_API_KEY", "emoji": "👁️"}}
---

# Torale - Web Monitoring

Monitor the web for specific conditions using AI-powered grounded search.
Torale watches for things so you don't have to. When a condition is met, it sends a webhook notification.

## Setup

1. Sign up at https://torale.ai and get an API key from Settings
2. Set `TORALE_API_KEY` environment variable to your API key

## API

Base URL: `https://api.torale.ai/api/v1`

All requests require the header: `Authorization: Bearer {TORALE_API_KEY}`

### Create a monitor

When a user wants to watch for something on the web, create a task:

```
POST /tasks
Content-Type: application/json

{
  "name": "<short descriptive name>",
  "search_query": "<what to search for>",
  "condition_description": "<specific condition that triggers notification>",
  "notifications": [
    {
      "type": "webhook",
      "url": "<webhook URL to receive notifications>",
      "headers": {"Authorization": "Bearer <webhook auth token if needed>"}
    }
  ],
  "context": {
    "source": "claude-code",
    "original_prompt": "<the user's original request>",
    "action": "<what the user wants done when condition is met>"
  }
}
```

Response includes `id` (task UUID).

The `context.action` field is delivered back in the webhook payload when the condition triggers, so include what the user wants you to do (e.g. "draft a tweet", "send a summary to Slack").

Webhook URLs must use HTTPS. If your endpoint is local, expose it via Tailscale or a reverse proxy with TLS.

### List monitors

```
GET /tasks
```

Returns all tasks for the authenticated user.

### Check status

```
GET /tasks/{task_id}
```

Returns task details including last execution result.

### Pause a monitor

```
PATCH /tasks/{task_id}
Content-Type: application/json

{"state": "paused"}
```

### Resume a monitor

```
PATCH /tasks/{task_id}
Content-Type: application/json

{"state": "active"}
```

### Delete a monitor

```
DELETE /tasks/{task_id}
```

## Incoming webhook payload

When Torale detects the condition is met, it POSTs to the configured webhook URL:

```json
{
  "event_type": "task.condition_met",
  "data": {
    "task": {
      "id": "uuid",
      "name": "Task Name",
      "search_query": "what was searched",
      "condition_description": "what triggered"
    },
    "execution": {
      "notification": "Human-readable summary of what was found"
    },
    "result": {
      "answer": "Detailed evidence and analysis",
      "grounding_sources": [{"url": "...", "title": "..."}]
    },
    "context": {
      "source": "claude-code",
      "original_prompt": "...",
      "action": "what the user wanted done"
    }
  }
}
```

When you receive this webhook, read `data.context.action` to know what the user wants, and use `data.execution.notification` and `data.result` as your source material.

## Examples

User: "Let me know when Apple announces iPhone 17"
- search_query: "Apple iPhone 17 announcement release date"
- condition_description: "Apple officially announces iPhone 17 with confirmed release date"
- context.action: "notify me with the key details"

User: "Watch for when Next.js 15 is released and summarize the changelog"
- search_query: "Next.js 15 release"
- condition_description: "Next.js 15 stable version is officially released"
- context.action: "summarize the changelog and key new features"

User: "Monitor competitor pricing for Acme Widget and alert me if they drop below $50"
- search_query: "Acme Widget price"
- condition_description: "Acme Widget price drops below $50"
- context.action: "alert me with the new price and where to buy"
