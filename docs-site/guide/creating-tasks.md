# Creating Tasks

Learn how to create effective monitoring tasks that reliably detect the conditions you care about.

## Task Components

Every monitoring task has four required components:

### 1. Name
A descriptive label for your task.

**Good names:**
- "iPhone 16 Release Date Monitor"
- "PS5 Target Stock Checker"
- "MacBook Pro Price Tracker - Best Buy"

**Tips:**
- Be specific about what you're monitoring
- Include key details (product, store, purpose)
- Keep it under 100 characters

### 2. Search Query
The question Torale will search for on Google.

**Good queries:**
```
"When is the next iPhone being released?"
"What is the current price of PS5 at Best Buy?"
"Are swimming pool memberships open at SF Rec Center for summer?"
```

**Bad queries:**
```
"iPhone" (too vague)
"news today" (too broad)
"good deals" (unclear intent)
```

**Query Tips:**
- Write as a natural question
- Include specific details (product name, location, timeframe)
- Focus on one topic
- Avoid ambiguous terms

### 3. Condition Description
What you're waiting to happen - the trigger for notification.

**Good conditions:**
```
"Apple has officially announced a specific release date"
"The price is $449 or lower"
"Summer memberships are available for registration"
"The item is in stock"
```

**Bad conditions:**
```
"Something new" (too vague)
"Good price" (subjective)
"Update available" (unclear)
```

**Condition Tips:**
- Be specific and objective
- Include exact thresholds for numbers
- Describe observable facts, not opinions
- Make it binary (true/false) when possible

### 4. Schedule
How often to check (cron expression).

**Common schedules:**
```
0 9 * * *       # Daily at 9:00 AM
0 */4 * * *     # Every 4 hours
0 9 * * 1       # Every Monday at 9:00 AM
0 */2 * * *     # Every 2 hours
```

See [Scheduling Guide](/guide/scheduling) for details.

## Creating Tasks

### Web Dashboard

1. **Navigate to Tasks**
   - Log in to [torale.ai](https://torale.ai)
   - Click "New Task" button

2. **Choose Creation Method**
   - **Use Template** - Pre-configured for common scenarios
   - **Start From Scratch** - Full customization

3. **Configure Task**
   - Enter search query
   - Describe condition
   - Set schedule (use visual builder or cron)
   - Choose notification behavior

4. **Preview (Optional)**
   - Test your query before creating
   - See what the AI finds
   - Verify condition evaluation

5. **Create & Activate**
   - Review configuration
   - Click "Create Task"
   - Task starts running on schedule

### CLI

```bash
# Basic task creation
torale task create \
  --query "When is the next iPhone release?" \
  --condition "A specific date has been announced" \
  --schedule "0 9 * * *"

# With all options
torale task create \
  --name "iPhone Release Monitor" \
  --query "When is the next iPhone being released?" \
  --condition "Apple has officially announced a release date" \
  --schedule "0 9 * * *" \
  --notify-behavior once \
  --run-immediately
```

**CLI Options:**
- `--name` - Task name (optional, generated if omitted)
- `--query` - Search query (required)
- `--condition` - Condition description (required)
- `--schedule` - Cron expression (required)
- `--notify-behavior` - `once`, `always`, or `track_state` (default: once)
- `--run-immediately` - Execute immediately after creation (optional)

### Python SDK

```python
from torale import ToraleClient

client = ToraleClient(api_key="your-api-key")

# Create task
task = client.tasks.create(
    name="iPhone Release Monitor",
    search_query="When is the next iPhone being released?",
    condition_description="Apple has officially announced a specific release date",
    schedule="0 9 * * *",
    notify_behavior="once",
    run_immediately=True  # Optional: execute right away
)

print(f"Created task: {task.id}")
print(f"Status: {task.is_active}")
```

## Task Templates

Templates provide pre-configured tasks for common scenarios.

### Using Templates (Web Dashboard)

1. Click "New Task"
2. Select "Use Template"
3. Browse categories:
   - Product Releases
   - Price Tracking
   - Stock Availability
   - Event Tickets
   - News Monitoring
4. Choose template
5. Customize placeholders (product name, price, etc.)
6. Create task

### Popular Templates

**Product Release Monitor**
```
Query: "When is {product} being released?"
Condition: "An official release date has been announced"
Schedule: Daily at 9 AM
```

**Price Drop Alert**
```
Query: "What is the current price of {product} at {store}?"
Condition: "The price is {target_price} or lower"
Schedule: Every 4 hours
```

**Stock Availability**
```
Query: "Is {product} in stock at {store}?"
Condition: "The item is available for purchase"
Schedule: Every 2 hours
```

**Event Tickets**
```
Query: "Are {event} tickets on sale?"
Condition: "Tickets are available for purchase"
Schedule: Every hour
```

See [Task Templates Guide](/guide/task-templates) for complete list.

## Notification Behaviors

Control when you get notified:

### Once (Default)
Best for one-time events.

```bash
--notify-behavior once
```

**Behavior:**
- Notify when condition first becomes true
- Pause task after notification
- Prevents duplicate alerts

**Use cases:**
- Product release announcements
- Event ticket sales opening
- Service registration opening

### Always
Best for recurring checks.

```bash
--notify-behavior always
```

**Behavior:**
- Notify every time condition is true
- No state comparison
- Task remains active

**Use cases:**
- Price monitoring (want every update)
- Stock alerts (might sell out again)
- Recurring availability checks

### Track State
Best for evolving information.

```bash
--notify-behavior track_state
```

**Behavior:**
- Compare current results with previous
- Notify only on meaningful changes
- Uses 85% similarity threshold

**Use cases:**
- News monitoring (ongoing story)
- Status updates (shipping, construction)
- Policy tracking (regulations, guidelines)

## Advanced Options

### Run Immediately
Execute task right after creation to test it.

**Web Dashboard:**
- Check "Run immediately after creation"

**CLI:**
```bash
torale task create ... --run-immediately
```

**SDK:**
```python
task = client.tasks.create(..., run_immediately=True)
```

### Preview Before Creating
Test your query and condition without creating a task.

**Web Dashboard:**
- Enter query and condition
- Click "Preview"
- Review results
- Adjust if needed

**CLI:**
```bash
torale task preview \
  --query "When is the next iPhone release?" \
  --condition "A specific date has been announced"
```

**SDK:**
```python
preview = client.tasks.preview(
    search_query="When is the next iPhone release?",
    condition_description="A specific date has been announced"
)

print(f"Condition met: {preview.condition_met}")
print(f"Answer: {preview.answer}")
```

## Best Practices

### Query Writing

1. **Be Specific**
   ```
   ✓ "When is the iPhone 16 Pro being released?"
   ✗ "iPhone news"
   ```

2. **Include Context**
   ```
   ✓ "What is the price of MacBook Pro M3 at Best Buy?"
   ✗ "MacBook price"
   ```

3. **Natural Language**
   ```
   ✓ "Are Taylor Swift tickets on sale for Los Angeles?"
   ✗ "Taylor Swift tickets LA status"
   ```

### Condition Writing

1. **Objective Criteria**
   ```
   ✓ "The price is $1799 or lower"
   ✗ "The price is good"
   ```

2. **Specific Thresholds**
   ```
   ✓ "Release date is announced for Q2 2024"
   ✗ "Release date is soon"
   ```

3. **Binary Evaluation**
   ```
   ✓ "The item is in stock and available for purchase"
   ✗ "The item might be available"
   ```

### Schedule Selection

**Time-Sensitive:**
```
0 */1 * * *     # Every hour (ticket drops, limited items)
```

**Regular Monitoring:**
```
0 */4 * * *     # Every 4 hours (price tracking)
```

**Daily Checks:**
```
0 9 * * *       # Once daily at 9 AM (news, announcements)
```

**Weekly Checks:**
```
0 9 * * 1       # Every Monday at 9 AM (job postings)
```

## Troubleshooting

### Condition Never Met

**Problem:** Task runs but condition never triggers.

**Solutions:**
1. Use Preview to test query
2. Make condition less restrictive
3. Check if information exists online
4. Verify search results contain needed data

### Too Many Notifications

**Problem:** Getting notified too frequently.

**Solutions:**
1. Change to `notify_behavior: once`
2. Reduce check frequency in schedule
3. Use `track_state` for evolving information
4. Make condition more specific

### No Results Found

**Problem:** Search returns no results.

**Solutions:**
1. Broaden search query
2. Remove overly specific terms
3. Check spelling and product names
4. Verify information is publicly available

### False Positives

**Problem:** Condition met but information is incorrect.

**Solutions:**
1. Make condition more specific
2. Add more context to query
3. Include specific dates, prices, or details
4. Use more precise language

## Next Steps

- Explore [Task Templates](/guide/task-templates)
- Configure [Scheduling](/guide/scheduling)
- Set up [Notifications](/guide/notifications)
- Understand [State Tracking](/guide/state-tracking)
- Read [Troubleshooting Guide](/guide/troubleshooting)
