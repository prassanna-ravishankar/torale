# Scheduling

Control when your monitoring tasks run using cron expressions.

## Understanding Cron Syntax

Cron expressions define when tasks execute. Format:

```
* * * * *
│ │ │ │ │
│ │ │ │ └─── Day of week (0-7, Sun=0 or 7)
│ │ │ └───── Month (1-12)
│ │ └─────── Day of month (1-31)
│ └───────── Hour (0-23)
└─────────── Minute (0-59)
```

## Common Schedules

### Every Hour
```
0 * * * *        # At minute 0 of every hour
30 * * * *       # At minute 30 of every hour
*/15 * * * *     # Every 15 minutes
```

### Specific Times Daily
```
0 9 * * *        # Daily at 9:00 AM
0 9,17 * * *     # Daily at 9 AM and 5 PM
30 14 * * *      # Daily at 2:30 PM
0 0 * * *        # Daily at midnight
```

### Multiple Times Per Day
```
0 */2 * * *      # Every 2 hours (12 times/day)
0 */4 * * *      # Every 4 hours (6 times/day)
0 */6 * * *      # Every 6 hours (4 times/day)
0 8,12,16,20 * * *  # 8 AM, 12 PM, 4 PM, 8 PM
```

### Weekly
```
0 9 * * 1        # Every Monday at 9 AM
0 9 * * 1,3,5    # Mon, Wed, Fri at 9 AM
0 9 * * 0        # Every Sunday at 9 AM
0 14 * * 6       # Every Saturday at 2 PM
```

### Monthly
```
0 9 1 * *        # First day of month at 9 AM
0 9 15 * *       # 15th of month at 9 AM
0 9 1,15 * *     # 1st and 15th at 9 AM
0 9 * * 1#1      # First Monday of month at 9 AM
```

## Quick Presets

Use the web dashboard's visual builder for these common patterns:

| Preset | Schedule | Use Case |
|--------|----------|----------|
| Every 15 min | `*/15 * * * *` | Urgent alerts, ticket drops |
| Every hour | `0 * * * *` | Stock monitoring, limited items |
| Every 2 hours | `0 */2 * * *` | Stock alerts, price checks |
| Every 4 hours | `0 */4 * * *` | Price monitoring |
| Every 6 hours | `0 */6 * * *` | Regular updates |
| Once daily | `0 9 * * *` | News, announcements |
| Twice daily | `0 9,17 * * *` | Morning & evening checks |
| Weekdays | `0 9 * * 1-5` | Business days only |
| Weekends | `0 9 * * 0,6` | Sat & Sun only |
| Weekly | `0 9 * * 1` | Monday morning |

## Schedule Recommendations by Use Case

### Time-Sensitive (Every 15-60 min)
Perfect for events that fill quickly or change rapidly.

```
*/15 * * * *     # Every 15 minutes
```

**Use cases:**
- Concert ticket drops
- Limited edition sneaker releases
- Flash sales
- Highly competitive product launches

### Frequent Monitoring (Every 1-2 hours)
For items with moderate urgency.

```
0 */2 * * *      # Every 2 hours
```

**Use cases:**
- Stock availability (gaming consoles, etc.)
- Appointment availability (DMV, passport)
- Event ticket general sales
- High-demand products

### Regular Checks (Every 4-6 hours)
For daily tracking without urgency.

```
0 */4 * * *      # Every 4 hours
```

**Use cases:**
- Price monitoring
- Deal tracking
- Travel prices
- Real estate listings

### Daily Monitoring (Once or twice per day)
For information that changes daily or less frequently.

```
0 9 * * *        # Daily at 9 AM
0 9,17 * * *     # Morning and evening
```

**Use cases:**
- News announcements
- Product release dates
- Policy updates
- Weather conditions
- Job postings

### Weekly Checks (1-3 times per week)
For low-frequency updates.

```
0 9 * * 1,3,5    # Mon, Wed, Fri
```

**Use cases:**
- Job board monitoring
- Weekly deals
- Conference announcements
- Research paper releases

## Setting Schedules

### Web Dashboard

**Visual Builder:**
1. Select common preset, or
2. Use dropdowns to build custom schedule:
   - Frequency (Every hour, Every 4 hours, Daily, etc.)
   - Time of day
   - Days of week
3. Preview shows next 5 execution times
4. See human-readable description

**Manual Entry:**
1. Click "Custom cron expression"
2. Enter cron syntax
3. Validation shows if valid
4. Preview displays schedule

### CLI

```bash
# Use cron expression
torale task create \
  --query "..." \
  --condition "..." \
  --schedule "0 */4 * * *"

# Common examples
--schedule "0 9 * * *"          # Daily 9 AM
--schedule "0 */2 * * *"        # Every 2 hours
--schedule "*/15 * * * *"       # Every 15 minutes
```

### Python SDK

```python
client.tasks.create(
    search_query="...",
    condition_description="...",
    schedule="0 */4 * * *"  # Every 4 hours
)
```

## Updating Schedules

You can change task schedules at any time.

### Web Dashboard

1. Navigate to task details
2. Click "Edit Schedule"
3. Update using visual builder or cron expression
4. Save changes

**Note:** Changes take effect for next scheduled run.

### CLI

```bash
torale task update <task-id> --schedule "0 */6 * * *"
```

### SDK

```python
client.tasks.update(
    task_id="...",
    schedule="0 */6 * * *"
)
```

## Schedule Best Practices

### Balance Frequency with Cost

More frequent checks = more API calls = higher cost (though still very low).

**Recommendations:**
- Start with lower frequency
- Increase if you're missing updates
- Decrease if condition rarely met

**Cost per execution:** ~$0.001

| Frequency | Daily Cost | Monthly Cost |
|-----------|-----------|--------------|
| Every 15 min | $0.096 | ~$2.88 |
| Every hour | $0.024 | ~$0.72 |
| Every 4 hours | $0.006 | ~$0.18 |
| Daily | $0.001 | ~$0.03 |

### Match Urgency to Frequency

**High urgency:**
```
*/15 * * * *     # Every 15 minutes
```
Limited tickets, competitive items, time-sensitive

**Medium urgency:**
```
0 */2 * * *      # Every 2 hours
```
Stock monitoring, appointments, general sales

**Low urgency:**
```
0 9 * * *        # Once daily
```
News, announcements, weekly updates

### Avoid Off-Hours for Non-Urgent Tasks

Save resources by scheduling during relevant hours:

```
0 9-17 * * *     # Every hour, 9 AM - 5 PM only
```

```
0 8,12,16,20 * * *   # 8 AM, 12 PM, 4 PM, 8 PM
```

### Time Zone Considerations

All schedules use **UTC timezone**.

**Convert from your local time:**

| Your Time | UTC Equivalent |
|-----------|---------------|
| 9 AM PST | 5 PM UTC |
| 9 AM EST | 2 PM UTC |
| 9 AM CET | 8 AM UTC |

**Web Dashboard:** Automatically converts to your local time
**CLI/SDK:** Use UTC when specifying cron

### Business Hours Only

For work-related monitoring:

```
0 9-17 * * 1-5   # Every hour, 9 AM-5 PM, Mon-Fri
```

```
0 9 * * 1-5      # 9 AM on weekdays only
```

## Troubleshooting

### Task Not Running

**Check schedule validity:**
```bash
# CLI validates automatically
torale task create --schedule "0 9 * * *"

# Invalid schedule shows error
torale task create --schedule "invalid"
# Error: Invalid cron expression
```

**Verify task is active:**
```bash
torale task get <task-id>
# Check: is_active = true
```

**Check execution history:**
```bash
torale task logs <task-id>
# Shows recent executions
```

### Unexpected Timing

**Remember UTC timezone:**
- Web dashboard converts automatically
- CLI/SDK require UTC

**Check next execution:**
```bash
torale task get <task-id>
# Shows next_run_time
```

### Too Many/Few Executions

**Verify cron expression:**
```
0 */4 * * *      # Every 4 hours = 6/day
0 9 * * *        # Once daily = 1/day
*/15 * * * *     # Every 15 min = 96/day
```

**Use cron validator:**
- Web dashboard shows preview
- Third-party tools: crontab.guru

## Advanced Scheduling

### Complex Patterns

**First Monday of month:**
```
0 9 * * 1#1      # 9 AM, first Monday
```

**Last day of month:**
```
0 9 28-31 * *    # 9 AM, day 28-31
# Note: Runs on all days 28-31, not just last day
```

**Specific months:**
```
0 9 * 6,7,8 *    # Daily in Jun, Jul, Aug only
```

### Pausing Execution

**Pause task without deleting:**

Web Dashboard:
1. Navigate to task
2. Click "Pause" or toggle to inactive

CLI:
```bash
torale task update <task-id> --inactive
```

SDK:
```python
client.tasks.update(task_id="...", is_active=False)
```

**Resume execution:**

```bash
torale task update <task-id> --active
```

## Next Steps

- Learn about [Notifications](/guide/notifications)
- Understand [State Tracking](/guide/state-tracking)
- Read [Troubleshooting Guide](/guide/troubleshooting)
- See [Creating Tasks](/guide/creating-tasks)
