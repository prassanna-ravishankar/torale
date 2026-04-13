---
description: Integrate Torale with OpenClaw to add web monitoring to your AI assistant. Watch for conditions and trigger actions when they're met.
---

# OpenClaw Integration

Use Torale as a web monitoring backend for [OpenClaw](https://openclaw.ai). Torale watches for conditions on the web; OpenClaw acts when they're met.

## How It Works

```
You (via chat) → OpenClaw → Torale API (create monitor)
                                  ↓
                    Torale checks periodically
                                  ↓
                    Condition met → webhook → OpenClaw acts
```

1. You tell OpenClaw to watch for something
2. OpenClaw creates a Torale task via API
3. Torale monitors the web on a schedule
4. When the condition is met, Torale sends a webhook to OpenClaw
5. OpenClaw receives the notification and takes action

## Setup

### 1. Get a Torale API Key

Sign up at [torale.ai](https://torale.ai) and create an API key in Settings.

### 2. Install the Skill

For Claude Code:
```bash
/plugin marketplace add prassanna-ravishankar/torale-openclaw
/plugin install torale@torale
```

For OpenClaw:
```bash
openclaw skills install torale
```

### 3. Configure the API Key

```bash
openclaw config set skills.entries.torale.apiKey "sk_your_key_here"
```

### 4. Enable Webhooks in OpenClaw

Make sure hooks are enabled in your `~/.openclaw/openclaw.json`:

```json5
{
  hooks: {
    enabled: true,
    token: "your-hook-secret",
    path: "/hooks",
  },
}
```

## Usage

Once configured, tell OpenClaw what to watch for:

- "Watch for when Apple announces iPhone 17"
- "Monitor when Bitcoin crosses $100k and alert me"
- "Let me know when the Next.js 15 release notes are published, then summarize the changelog"

OpenClaw creates the monitor and Torale handles the rest.

## API Reference

All requests go to `https://api.torale.ai/api/v1` with `Authorization: Bearer sk_...`.

### Create a Monitor

```bash
curl -X POST https://api.torale.ai/api/v1/tasks \
  -H "Authorization: Bearer sk_..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "iPhone 17 Announcement",
    "search_query": "Apple iPhone 17 announcement",
    "condition_description": "Apple officially announces iPhone 17",
    "notifications": [{
      "type": "webhook",
      "url": "https://your-openclaw:18789/hooks/agent",
      "headers": {"Authorization": "Bearer your-hook-token"}
    }],
    "context": {
      "source": "openclaw",
      "action": "notify me with key details"
    }
  }'
```

### List Monitors

```bash
curl https://api.torale.ai/api/v1/tasks \
  -H "Authorization: Bearer sk_..."
```

### Delete a Monitor

```bash
curl -X DELETE https://api.torale.ai/api/v1/tasks/{task_id} \
  -H "Authorization: Bearer sk_..."
```

## Webhook Payload

When the condition is met, Torale POSTs to your OpenClaw webhook:

```json
{
  "event_type": "task.condition_met",
  "data": {
    "task": {
      "id": "uuid",
      "name": "iPhone 17 Announcement",
      "search_query": "Apple iPhone 17 announcement",
      "condition_description": "Apple officially announces iPhone 17"
    },
    "execution": {
      "notification": "Apple has officially announced the iPhone 17..."
    },
    "result": {
      "answer": "Detailed analysis with evidence...",
      "grounding_sources": [
        {"url": "https://apple.com/...", "title": "Apple Newsroom"}
      ]
    },
    "context": {
      "source": "openclaw",
      "action": "notify me with key details"
    }
  }
}
```

The `context` object is passed through from task creation, so OpenClaw knows what action to take.

## HTTPS Requirement

Torale requires webhook URLs to use HTTPS. If your OpenClaw instance runs locally on HTTP, expose it via [Tailscale](https://docs.openclaw.ai/gateway/tailscale) or a reverse proxy with TLS.

## Authentication

Torale uses HMAC-SHA256 signing (Stripe-compatible) on all webhook deliveries. The signature is in the `X-Torale-Signature` header. OpenClaw authenticates via the `Authorization: Bearer` header you configure in the notification.

## Rate Limits

- Task creation: 10 per minute
- Maximum active tasks: 50 per user
