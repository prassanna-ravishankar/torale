# Troubleshooting

Common issues and solutions for Torale monitoring tasks.

## Task Creation Issues

### Invalid Cron Expression

**Problem:** "Invalid cron expression" error when creating task

**Cause:** Cron syntax is incorrect

**Solutions:**
1. Use web dashboard's visual schedule builder
2. Verify syntax: `minute hour day month day-of-week`
3. Test with online cron validators (crontab.guru)

**Examples of valid cron:**
```
0 9 * * *       # Daily at 9 AM
0 */4 * * *     # Every 4 hours
*/15 * * * *    # Every 15 minutes
```

**Common mistakes:**
```
9 * * * *       # ✗ Wrong (runs every hour at minute 9)
0 9 * * *       # ✓ Correct (runs daily at 9 AM)

*/4 * * * *     # ✗ Wrong (every 4 minutes)
0 */4 * * *     # ✓ Correct (every 4 hours)
```

### Authentication Failed (CLI/SDK)

**Problem:** "Authentication failed" or "Invalid API key"

**Solutions:**

**CLI:**
```bash
# Set API key
torale auth set-api-key

# Verify authentication
torale auth status

# Generate new key if needed
# Visit torale.ai → Settings → API Keys
```

**SDK:**
```python
from torale import ToraleClient

# Verify API key is correct
client = ToraleClient(api_key="sk_...")

# Test with simple call
try:
    tasks = client.tasks.list()
    print("Authentication successful")
except Exception as e:
    print(f"Auth error: {e}")
```

**Common causes:**
- API key copied incorrectly (missing characters)
- API key was revoked in dashboard
- Using wrong environment (dev vs production)

### Query Too Vague

**Problem:** Preview returns irrelevant results

**Cause:** Search query is too broad or ambiguous

**Solutions:**

**Before:**
```
Query: "iPhone"
Problem: Too vague, what about iPhone?
```

**After:**
```
Query: "When is the next iPhone being released?"
Better: Clear intent, specific question
```

**Tips:**
- Write as a complete question
- Include specific details (product model, location, etc.)
- Focus on one topic per task
- Test with Preview before creating

## Execution Issues

### Condition Never Met

**Problem:** Task runs successfully but condition never triggers

**Diagnosis:**
```bash
# Check execution history
torale task logs <task-id>

# Look for:
# - condition_met: false
# - answer: What is AI finding?
```

**Solutions:**

**1. Use Preview to Test**
```bash
torale task preview \
  --query "Your query" \
  --condition "Your condition"

# Review:
# - What answer does AI provide?
# - Why isn't condition met?
```

**2. Make Condition Less Restrictive**
```
Too restrictive:
"iPhone 16 Pro Max 1TB in Space Black is available"

Better:
"iPhone 16 is available for purchase"
```

**3. Verify Information Exists**
- Search Google manually
- Check if information is publicly available
- Verify websites aren't blocking automated access

**4. Adjust Condition to Match Reality**
```
Before: "Price is exactly $799"
After: "Price is $799 or within $50 of that"

Before: "Release date is Q2 2024"
After: "A release timeframe or date has been announced"
```

### Task Not Running

**Problem:** Task shows as active but no executions

**Diagnosis:**
```bash
# Check task details
torale task get <task-id>

# Verify:
# - is_active: true
# - schedule: valid cron
# - next_run_time: future timestamp
```

**Solutions:**

**1. Verify Task is Active**
```bash
# Activate if needed
torale task update <task-id> --active
```

**2. Check Schedule**
```bash
# View schedule
torale task get <task-id>

# Update if needed
torale task update <task-id> --schedule "0 9 * * *"
```

**3. Run Manually to Test**
```bash
torale task execute <task-id>
```

**4. Check Temporal Status (Self-Hosted)**
- Visit Temporal UI (default: http://localhost:8080)
- Search for task workflow
- Check for errors

### Execution Fails with Error

**Problem:** Task status shows "failed"

**Diagnosis:**
```bash
# View error message
torale task logs <task-id>

# Check most recent execution
# Look at error_message field
```

**Common errors:**

**1. Rate Limit Exceeded**
```
Error: "Rate limit exceeded for Google Search API"

Solution:
- Reduce check frequency
- Wait and retry (Temporal auto-retries)
- Contact support if persistent
```

**2. Timeout**
```
Error: "Request timeout after 30 seconds"

Solution:
- Simplify search query
- Issue will auto-resolve on retry
- Check internet connection (self-hosted)
```

**3. Invalid Configuration**
```
Error: "Invalid task configuration"

Solution:
- Review task config
- Ensure required fields present
- Update task with correct config
```

## Notification Issues

### Not Receiving Notifications

**Problem:** Condition met but no notification received

**Diagnosis:**
```bash
# Check executions
torale task logs <task-id>

# Look for:
# - condition_met: true
# - Was notification sent?
```

**Possible causes:**

**1. Notify Behavior is `once` and Already Notified**
```bash
# Check task status
torale task get <task-id>

# If last_notified_at is set and task paused:
# Task already notified and auto-paused

# To get notified again:
torale task update <task-id> --active
```

**2. Using `track_state` and No Change Detected**
```bash
# View execution logs
torale task logs <task-id>

# Check similarity scores
# If >85% similar, no notification sent

# Solutions:
# - Switch to "always" behavior
# - Wait for more significant change
```

**3. Task is Inactive**
```bash
# Verify and activate
torale task update <task-id> --active
```

### Too Many Notifications

**Problem:** Getting notified too frequently

**Solutions:**

**1. Change Notification Behavior**
```bash
# From "always" to "once"
torale task update <task-id> --notify-behavior once

# Or use state tracking
torale task update <task-id> --notify-behavior track_state
```

**2. Reduce Check Frequency**
```bash
# From every 2 hours to every 6 hours
torale task update <task-id> --schedule "0 */6 * * *"

# Or daily
torale task update <task-id> --schedule "0 9 * * *"
```

**3. Make Condition More Specific**
```
Too broad:
"Price changed"

More specific:
"Price dropped by at least $50"
```

### False Positives

**Problem:** Condition met but information seems incorrect

**Solutions:**

**1. Review Sources**
```bash
# Check grounding sources in execution details
torale task logs <task-id>

# Sources shown in result:
# - Are they reputable?
# - Do they actually contain that information?
```

**2. Make Query More Specific**
```
Vague:
"iPhone release date"

Specific:
"When is the iPhone 16 officially being released by Apple?"
```

**3. Add Context to Condition**
```
Ambiguous:
"A release date exists"

Clear:
"Apple has officially announced a specific release date, not rumors"
```

**4. Use Preview to Test**
```bash
torale task preview \
  --query "Refined query" \
  --condition "More specific condition"
```

## CLI Issues

### Command Not Found

**Problem:** `torale: command not found`

**Solutions:**

**Install torale:**
```bash
pip install torale
```

**Verify installation:**
```bash
which torale
torale --version
```

**If using virtual environment:**
```bash
# Activate venv first
source venv/bin/activate
torale --version
```

### API Connection Error

**Problem:** "Connection refused" or "Cannot reach API"

**Possible causes:**

**1. Wrong API URL (Self-Hosted)**
```bash
# Set correct API URL
export TORALE_API_URL=http://localhost:8000
```

**2. Network Issues**
```bash
# Test API accessibility
curl https://api.torale.ai/health

# For self-hosted:
curl http://localhost:8000/health
```

**3. API Service Down (Self-Hosted)**
```bash
# Check if API is running
just dev

# Or:
docker-compose ps
```

## Performance Issues

### Slow Execution

**Problem:** Task takes longer than expected to run

**Normal timing:**
- Simple search: 2-5 seconds
- Complex evaluation: 5-10 seconds
- With state comparison: +1 second

**If consistently slow (>15 seconds):**

**Solutions:**
1. **Simplify query** - Remove unnecessary details
2. **Check API status** - Visit status.torale.ai (coming soon)
3. **Verify model** - Gemini Flash is fastest

### High Costs

**Problem:** Unexpected costs from frequent executions

**Analysis:**
```bash
# Check execution frequency
torale task logs <task-id>

# Count executions per day
```

**Cost optimization:**

**1. Reduce Frequency**
```bash
# From every hour to every 4 hours
--schedule "0 */4 * * *"

# Saves: 18 executions/day
# Cost reduction: ~$0.018/day
```

**2. Use Efficient Notify Behavior**
```bash
# Use "once" for one-time events
--notify-behavior once
# Task pauses after notification
```

**3. Pause Unused Tasks**
```bash
# Temporarily disable
torale task update <task-id> --inactive

# Re-enable when needed
torale task update <task-id> --active
```

## Self-Hosting Issues

### Docker Compose Fails

**Problem:** `docker-compose up` fails

**Solutions:**

**1. Check Docker is Running**
```bash
docker ps
```

**2. Port Conflicts**
```bash
# Check if ports already in use
lsof -i :8000  # API
lsof -i :5432  # PostgreSQL
lsof -i :7233  # Temporal

# Stop conflicting services or change ports
```

**3. Missing Environment Variables**
```bash
# Verify .env exists
ls -la .env

# Check required variables
cat .env | grep -E "DATABASE_URL|GOOGLE_API_KEY|CLERK_SECRET_KEY"
```

**4. View Logs**
```bash
# Check service logs
docker-compose logs api
docker-compose logs worker
docker-compose logs postgres
```

### Database Migration Failed

**Problem:** "Database migration error"

**Solutions:**

**1. Check Database Connection**
```bash
# Test connection
docker-compose exec postgres psql -U torale -d torale
```

**2. Run Migrations Manually**
```bash
# Enter API container
docker-compose exec api bash

# Run migrations
alembic upgrade head
```

**3. Reset Database (Development Only)**
```bash
# WARNING: Deletes all data
docker-compose down -v
docker-compose up -d
```

### Temporal Connection Failed

**Problem:** Workers can't connect to Temporal

**Solutions:**

**1. Verify Temporal is Running**
```bash
docker-compose ps temporal

# Should show "Up"
```

**2. Check Temporal UI**
Visit http://localhost:8080

**3. Verify Configuration**
```bash
# Check environment variables
echo $TEMPORAL_HOST
echo $TEMPORAL_NAMESPACE

# Should be:
# TEMPORAL_HOST=localhost:7233
# TEMPORAL_NAMESPACE=default
```

## Getting Help

### Before Asking for Help

Collect this information:

1. **Task ID**
   ```bash
   torale task list
   ```

2. **Recent Execution Logs**
   ```bash
   torale task logs <task-id>
   ```

3. **Task Configuration**
   ```bash
   torale task get <task-id>
   ```

4. **Error Messages**
   - Full error text
   - When it occurred
   - What you were trying to do

### Support Channels

**GitHub Issues:**
- Bug reports: [github.com/torale-ai/torale/issues](https://github.com/torale-ai/torale/issues)
- Feature requests: Same link
- Include: OS, version, error logs

**GitHub Discussions:**
- Questions: [github.com/torale-ai/torale/discussions](https://github.com/torale-ai/torale/discussions)
- General help
- Community support

**Documentation:**
- Check docs: [docs.torale.ai](https://docs.torale.ai)
- Search for your issue
- Review related guides

## Quick Fixes Summary

| Issue | Quick Fix |
|-------|-----------|
| Condition never met | Use Preview, broaden condition |
| Task not running | Check `is_active`, verify schedule |
| No notifications | Check notify behavior, verify task active |
| Too many notifications | Change to `once` or `track_state` |
| Auth failed | Regenerate API key, verify in dashboard |
| Slow execution | Simplify query, check API status |
| False positives | Make query more specific, review sources |
| CLI not found | `pip install torale` |

## Next Steps

- Review [Creating Tasks](/guide/creating-tasks) guide
- Understand [State Tracking](/guide/state-tracking)
- Configure [Notifications](/guide/notifications)
- Master [Scheduling](/guide/scheduling)
- Check [API Reference](/api/authentication)
