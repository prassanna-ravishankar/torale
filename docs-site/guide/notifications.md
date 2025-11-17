# Notifications

Learn how Torale notifies you when monitoring conditions are met.

## Notification Types

Currently, Torale supports **in-app notifications**. Email and webhook notifications are coming soon.

### In-App Notifications

View notifications in the Torale dashboard when conditions are met.

**Features:**
- Real-time updates
- Full execution details
- Source attribution links
- Change summaries
- Notification history

**Accessing notifications:**
1. Log in to [torale.ai](https://torale.ai)
2. Click Notifications icon (bell) in header
3. View recent notifications
4. Click to see full execution details

## Notification Behaviors

Control when and how often you get notified using the `notify_behavior` setting.

### Once (Default)

Notify **once** when condition first becomes true, then pause task.

```bash
--notify-behavior once
```

**How it works:**
1. Task runs on schedule
2. Condition becomes true → Notify
3. Task automatically pauses
4. No further notifications until reactivated

**When to use:**
- One-time events (product releases)
- Announcements (event dates)
- Registration openings (memberships, appointments)
- First occurrence is what matters

**Example:**
```bash
torale task create \
  --query "When is the next iPhone release?" \
  --condition "A specific date has been announced" \
  --notify-behavior once
```

**Notification timeline:**
```
Day 1: No date → No notification
Day 2: No date → No notification
Day 3: "Sep 12" → ✓ Notify + Pause task
Day 4: Task paused (no execution)
```

### Always

Notify **every time** condition is true, regardless of changes.

```bash
--notify-behavior always
```

**How it works:**
1. Task runs on schedule
2. Condition is true → Notify
3. Task remains active
4. Notifies on every execution where condition is met

**When to use:**
- Price monitoring (want every update)
- Stock alerts (item might sell out again)
- Availability checks (status can change)
- Recurring validation

**Example:**
```bash
torale task create \
  --query "Is PS5 in stock at Target?" \
  --condition "PS5 is available for purchase" \
  --notify-behavior always
```

**Notification timeline:**
```
10 AM: Out of stock → No notification
12 PM: In stock → ✓ Notify
2 PM: In stock → ✓ Notify
4 PM: Out of stock → No notification
6 PM: In stock → ✓ Notify
```

**Note:** You'll get notified at 12 PM, 2 PM, and 6 PM even if nothing changed.

### Track State

Notify only when **meaningful changes** are detected.

```bash
--notify-behavior track_state
```

**How it works:**
1. Task runs and stores results
2. Compares with previous execution
3. Detects meaningful changes (85% similarity threshold)
4. Notifies only if significantly different
5. Task remains active

**When to use:**
- Evolving information (ongoing news stories)
- Status tracking (shipping, construction)
- Price tracking with occasional updates
- Policy monitoring (regulations)

**Example:**
```bash
torale task create \
  --query "What is the status of the GPT-5 release?" \
  --condition "New information is available" \
  --notify-behavior track_state
```

**Notification timeline:**
```
Day 1: "No announcement yet" → ✓ Notify (first run)
Day 2: "No announcement yet" → No notification (same)
Day 3: "Coming in Q2 2024" → ✓ Notify (changed)
Day 4: "Coming in Q2 2024" → No notification (same)
Day 5: "June 15, 2024 confirmed" → ✓ Notify (changed)
```

## Choosing Notification Behavior

### Decision Matrix

| Scenario | Behavior | Reason |
|----------|----------|--------|
| Product release date announced | **once** | One-time event |
| Concert tickets on sale | **once** | Buy once, done |
| Price below threshold | **always** | Want every occurrence |
| Item back in stock | **always** | Might sell out again |
| News story updates | **track_state** | Evolving information |
| Status changes | **track_state** | Track progression |

### Examples by Use Case

**Product Releases → once**
```bash
torale task create \
  --query "When is GPT-5 being released?" \
  --condition "Release date announced" \
  --notify-behavior once
```

**Stock Monitoring → always**
```bash
torale task create \
  --query "Is PS5 in stock at Best Buy?" \
  --condition "Available for purchase" \
  --notify-behavior always
```

**Price Tracking → always or track_state**
```bash
# Get notified every time price is below threshold
torale task create \
  --query "What is the MacBook Pro price?" \
  --condition "Price below $1800" \
  --notify-behavior always

# Get notified only when price changes significantly
torale task create \
  --query "What is the MacBook Pro price?" \
  --condition "Price information is available" \
  --notify-behavior track_state
```

**News Monitoring → track_state**
```bash
torale task create \
  --query "What is the latest on the AI regulation bill?" \
  --condition "New developments are reported" \
  --notify-behavior track_state
```

## Notification Content

Each notification includes:

### Basic Information
- **Task name** - Which monitoring task triggered
- **Timestamp** - When condition was met
- **Status** - Success or error

### Condition Evaluation
- **Condition met?** - Yes/No with explanation
- **Answer** - Concise summary (2-4 sentences)
- **Reasoning** - Why AI decided condition was met

### Source Attribution
- **Grounding sources** - URLs where information was found
- **Domain names** - Clean display (e.g., "apple.com")
- **Clickable links** - Visit sources directly

### Change Summary (track_state only)
- **What changed** - Description of differences
- **Previous state** - What it was before
- **Current state** - What it is now

### Example Notification

```
Task: iPhone 16 Release Monitor
Time: 2024-09-10 14:23:45 UTC
Status: Condition met ✓

Answer:
Apple has officially announced that the iPhone 16 will be
released on September 20, 2024. Pre-orders begin on
September 13, 2024.

Reasoning:
The condition "A specific release date has been announced"
is met because Apple's official press release confirms
September 20, 2024 as the release date.

Sources:
- apple.com
- theverge.com
- macrumors.com

Change: New information (no previous state)
```

## Viewing Notifications

### Web Dashboard

**Notifications Page:**
1. Click bell icon in header
2. See list of recent notifications
3. Filter by task or date
4. Click notification for full details

**Task Details Page:**
1. Navigate to specific task
2. View "Notifications" tab
3. See all notifications for this task
4. Includes execution history

### CLI

```bash
# View notifications for a task
torale task logs <task-id> --notifications-only

# View all executions (including non-notifications)
torale task logs <task-id>
```

### Python SDK

```python
# Get notifications for a task
notifications = client.tasks.get_notifications(task_id="...")

for notif in notifications:
    print(f"Time: {notif.created_at}")
    print(f"Answer: {notif.answer}")
    print(f"Sources: {', '.join(notif.sources)}")

# Get all executions
executions = client.tasks.get_executions(task_id="...")

# Filter to notifications
notifications = [
    e for e in executions
    if e.condition_met
]
```

## Coming Soon: Email Notifications

**Planned features:**
- Email notifications via NotificationAPI
- Customizable email templates
- Digest mode (daily/weekly summaries)
- Rich formatting with images and links

**Configuration (future):**
```bash
torale task create \
  --query "..." \
  --condition "..." \
  --notify-email your@email.com \
  --notify-behavior once
```

## Coming Soon: Webhook Notifications

**Planned features:**
- POST to your webhook URL
- Custom payloads
- Retry logic
- Signature verification

**Configuration (future):**
```bash
torale task create \
  --query "..." \
  --condition "..." \
  --webhook-url https://your-app.com/webhook \
  --notify-behavior track_state
```

**Payload example (future):**
```json
{
  "task_id": "...",
  "task_name": "iPhone Release Monitor",
  "condition_met": true,
  "answer": "...",
  "reasoning": "...",
  "sources": ["..."],
  "timestamp": "2024-09-10T14:23:45Z"
}
```

## Best Practices

### Choose Right Behavior

**Start with `once` for:**
- Events you only care about once
- Announcements and releases
- Registration openings

**Use `always` for:**
- Price drops (want every occurrence)
- Stock monitoring (availability changes)
- Recurring checks

**Use `track_state` for:**
- Ongoing developments
- Price tracking (occasional updates)
- News monitoring

### Manage Notification Volume

**Reduce frequency:**
1. Use `once` instead of `always`
2. Make conditions more specific
3. Reduce check frequency in schedule
4. Use `track_state` for evolving info

**Increase sensitivity:**
1. Use `always` to catch every occurrence
2. Increase check frequency
3. Broaden condition criteria

### Organize Tasks

**Group by priority:**
- Critical: `once` behavior, frequent checks
- Important: `always` behavior, moderate frequency
- Monitoring: `track_state` behavior, daily checks

**Naming convention:**
```
[Priority] Product/Service - Purpose
Examples:
[URGENT] iPhone Release - Announcement
[MONITOR] MacBook Price - Best Buy
[TRACK] AI Regulation - Status Updates
```

## Troubleshooting

### Not Receiving Notifications

**Check task status:**
```bash
torale task get <task-id>
# Verify: is_active = true
```

**Check execution history:**
```bash
torale task logs <task-id>
# Look for condition_met = true
```

**Review condition:**
- Might be too restrictive
- Use Preview to test
- Adjust criteria

### Too Many Notifications

**Problem:** Getting notified too often

**Solutions:**
1. Change to `notify_behavior: once`
2. Reduce schedule frequency
3. Make condition more specific
4. Use `track_state` instead of `always`

### Missing Notifications

**Problem:** Condition met but no notification

**Possible causes:**
1. Task using `track_state` and state didn't change
2. Task paused after first notification (`once` behavior)
3. Similarity threshold too high for `track_state`

**Solutions:**
1. Check task is active
2. Review execution logs
3. Switch to `always` if needed

## Next Steps

- Configure [Scheduling](/guide/scheduling)
- Understand [State Tracking](/guide/state-tracking)
- Read [Creating Tasks](/guide/creating-tasks)
- Check [Troubleshooting Guide](/guide/troubleshooting)
