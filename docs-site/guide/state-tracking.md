# State Tracking

Learn how Torale remembers previous results to avoid duplicate notifications and detect meaningful changes.

## What is State Tracking?

State tracking is Torale's memory system. After each execution, Torale stores the results and compares them with future executions to detect changes.

**Key benefits:**
- Prevents duplicate notifications
- Detects meaningful changes
- Reduces notification noise
- Tracks information evolution

## How It Works

### Storage

After every execution, Torale stores:

```json
{
  "last_known_state": {
    "answer": "The iPhone 16 will be released on September 20, 2024",
    "condition_met": true,
    "sources": ["apple.com", "theverge.com"],
    "timestamp": "2024-09-10T14:23:45Z"
  }
}
```

### Comparison

On next execution, Torale:

1. **Runs search** - Gets current information
2. **Compares** - Checks against `last_known_state`
3. **Evaluates** - Determines if change is meaningful
4. **Decides** - Whether to notify based on `notify_behavior`

### Change Detection

**Simple comparison:**
- Has condition status changed? (false → true or true → false)

**Advanced comparison (track_state behavior):**
- Calculate text similarity between answers
- Use 85% threshold
- Notify if similarity < 85% (i.e., 15%+ different)

## State Tracking by Notification Behavior

### Once

**State tracking: Minimal**

Tracks only whether condition has ever been met.

```python
if condition_met and not previously_met:
    notify()
    pause_task()
```

**Stored state:**
```json
{
  "condition_met": true,
  "last_notified_at": "2024-09-10T14:23:45Z"
}
```

**Example flow:**
```
Execution 1: Condition = false → No notification
Execution 2: Condition = false → No notification
Execution 3: Condition = true → ✓ Notify + Pause
(No further executions - task paused)
```

### Always

**State tracking: None**

No state comparison. Notifies every time condition is true.

```python
if condition_met:
    notify()
```

**Stored state:**
```json
{
  "condition_met": true,
  "last_execution": "2024-09-10T14:23:45Z"
}
```

**Example flow:**
```
Execution 1: Condition = true → ✓ Notify
Execution 2: Condition = true → ✓ Notify
Execution 3: Condition = false → No notification
Execution 4: Condition = true → ✓ Notify
```

### Track State

**State tracking: Full**

Compares complete answer text to detect meaningful changes.

```python
if condition_met:
    current_answer = get_answer()
    previous_answer = last_known_state["answer"]

    similarity = calculate_similarity(current_answer, previous_answer)

    if similarity < 0.85:  # Less than 85% similar
        notify()
        update_state(current_answer)
```

**Stored state:**
```json
{
  "answer": "Full answer text from AI",
  "condition_met": true,
  "sources": ["url1", "url2"],
  "timestamp": "2024-09-10T14:23:45Z"
}
```

**Example flow:**
```
Day 1: "No release date announced"
       → ✓ Notify (first run)

Day 2: "No release date announced"
       → No notification (same, 100% similar)

Day 3: "Coming in Q2 2024"
       → ✓ Notify (changed, <85% similar)

Day 4: "Coming in Q2 2024"
       → No notification (same)

Day 5: "June 15, 2024 confirmed"
       → ✓ Notify (changed significantly)
```

## Similarity Calculation

### How Similarity Works

Torale uses semantic similarity to compare text:

**High similarity (>85%):**
```
Previous: "iPhone 16 will be released on September 20, 2024"
Current: "Apple confirmed iPhone 16 launches September 20, 2024"
Similarity: ~92% → No notification
```

**Low similarity (<85%):**
```
Previous: "No release date announced yet"
Current: "iPhone 16 releases September 20, 2024"
Similarity: ~35% → Notification sent
```

**Medium similarity (~85%):**
```
Previous: "Price is $799 for 128GB"
Current: "Price is $799 for 128GB, $899 for 256GB"
Similarity: ~82% → Notification sent
```

### What Counts as Different?

**Triggers notification:**
- New information added
- Dates/prices changed
- Status changed (available → unavailable)
- Significant details altered

**Doesn't trigger notification:**
- Minor rewording
- Same information, different phrasing
- Punctuation changes
- Insignificant updates

## Viewing State History

### Web Dashboard

**Task Details Page:**
1. Navigate to task
2. View "Executions" tab
3. See execution history
4. Click execution to see state at that time

**State comparison:**
```
Previous State (Day 3):
"Coming in Q2 2024"

Current State (Day 5):
"June 15, 2024 confirmed"

Change Detected: Yes
Similarity: 68%
Notification Sent: Yes
```

### CLI

```bash
# View execution history with states
torale task logs <task-id>
```

Output:
```
Execution 1 (2024-09-08):
  Status: Success
  Condition Met: No
  Answer: "No release date announced"

Execution 2 (2024-09-09):
  Status: Success
  Condition Met: No
  Answer: "No release date announced"
  Change: None (100% similar)

Execution 3 (2024-09-10):
  Status: Success
  Condition Met: Yes
  Answer: "Coming in Q2 2024"
  Change: Significant (45% similar)
  Notified: Yes
```

### SDK

```python
# Get execution history
executions = client.tasks.get_executions(task_id="...")

for execution in executions:
    print(f"Time: {execution.created_at}")
    print(f"Answer: {execution.result.get('answer')}")
    print(f"Condition met: {execution.condition_met}")
    if execution.change_summary:
        print(f"Changes: {execution.change_summary}")
    print("---")
```

## State Tracking Use Cases

### Product Release Monitoring

**Scenario:** Track evolving release information

**Best approach:** `track_state`

**Why:** Information evolves from "coming soon" to "Q2 2024" to "June 15, 2024"

**Example:**
```bash
torale task create \
  --query "When is the next iPhone release?" \
  --condition "Release information is available" \
  --notify-behavior track_state
```

**State evolution:**
```
Week 1: "Expected in fall 2024"
Week 2: "Expected in fall 2024" (no change → no notification)
Week 3: "September event announced" (changed → notify)
Week 4: "September 20 release date" (changed → notify)
```

### Price Tracking

**Scenario:** Monitor price changes

**Approach 1 - All updates:** `always`
```bash
torale task create \
  --query "What is the PS5 price at Best Buy?" \
  --condition "Price is below $450" \
  --notify-behavior always
```

**Approach 2 - Changes only:** `track_state`
```bash
torale task create \
  --query "What is the PS5 price at Best Buy?" \
  --condition "Price information is available" \
  --notify-behavior track_state
```

**State tracking with track_state:**
```
Day 1: "$499" → Notify
Day 2: "$499" → No notification (same)
Day 3: "$449" → Notify (price dropped)
Day 4: "$449" → No notification (same)
Day 5: "$479" → Notify (price increased)
```

### Stock Availability

**Scenario:** Item availability changes frequently

**Best approach:** `once` or `always`

**Why:** Binary state (in/out of stock) changes often

**Example with `always`:**
```bash
torale task create \
  --query "Is PS5 in stock at Target?" \
  --condition "PS5 is available" \
  --notify-behavior always
```

**State pattern:**
```
10 AM: Out of stock → No notification
12 PM: In stock → Notify
2 PM: In stock → Notify
4 PM: Out of stock → No notification
6 PM: In stock → Notify
```

You get notified at 12 PM, 2 PM, and 6 PM to ensure you don't miss restock windows.

### News Monitoring

**Scenario:** Track ongoing story developments

**Best approach:** `track_state`

**Example:**
```bash
torale task create \
  --query "What is the latest on AI regulation bill?" \
  --condition "New developments are reported" \
  --notify-behavior track_state
```

**State evolution:**
```
Week 1: "Bill introduced in Senate"
Week 2: "Bill introduced in Senate" (no change)
Week 3: "Bill passes Senate, moves to House" (changed → notify)
Week 4: "House committee reviewing bill" (changed → notify)
Week 5: "Bill signed into law" (changed → notify)
```

## Adjusting Sensitivity

### Make More Sensitive (More Notifications)

1. **Use `always` instead of `track_state`**
   ```bash
   --notify-behavior always
   ```

2. **Broaden condition**
   ```
   Before: "Price is exactly $449"
   After: "Price information is available"
   ```

3. **Increase check frequency**
   ```
   Before: 0 9 * * *  (daily)
   After: 0 */2 * * *  (every 2 hours)
   ```

### Make Less Sensitive (Fewer Notifications)

1. **Use `track_state` instead of `always`**
   ```bash
   --notify-behavior track_state
   ```

2. **Use `once` for one-time events**
   ```bash
   --notify-behavior once
   ```

3. **Make condition more specific**
   ```
   Before: "Price changed"
   After: "Price dropped by at least $50"
   ```

4. **Reduce check frequency**
   ```
   Before: 0 */2 * * *  (every 2 hours)
   After: 0 9 * * *  (daily)
   ```

## Best Practices

### Choose Right Behavior for Use Case

| Use Case | Behavior | Reason |
|----------|----------|--------|
| One-time event | `once` | Event happens once |
| Binary state (in/out of stock) | `always` | Want every occurrence |
| Evolving information | `track_state` | Track changes over time |
| Price threshold | `always` | Catch every time below threshold |
| Price monitoring | `track_state` | Track price evolution |

### Understand Trade-offs

**`always`:**
- ✓ Never miss an occurrence
- ✗ May get duplicate notifications
- ✓ Simple, predictable

**`track_state`:**
- ✓ Only meaningful changes
- ✗ Might miss rapid changes
- ✓ Reduces noise

### Testing State Tracking

**Use Preview:**
```bash
torale task preview \
  --query "..." \
  --condition "..."
```

**Run immediately after creation:**
```bash
torale task create ... --run-immediately
```

**Monitor first few executions:**
- Check if notifications make sense
- Verify change detection working
- Adjust behavior if needed

## Troubleshooting

### Not Getting Notified

**Problem:** State tracking preventing notifications

**Solution:**
1. Switch to `always` temporarily
2. Check execution logs for similarity scores
3. Verify information is actually changing

### Too Many Notifications

**Problem:** Getting notified for minor changes

**Solution:**
1. Switch from `always` to `track_state`
2. Make condition more specific
3. Reduce check frequency

### State Seems Wrong

**Problem:** Stored state doesn't match current info

**Solution:**
1. Check execution logs
2. View most recent execution
3. Task will correct itself on next run

## Next Steps

- Learn about [Notification Behaviors](/guide/notifications)
- Understand [Creating Tasks](/guide/creating-tasks)
- Read [Troubleshooting Guide](/guide/troubleshooting)
- Explore [Use Cases](/guide/use-cases)
