# Getting Started

Welcome to Torale! This guide will help you get started with grounded search monitoring in minutes.

## What is Torale?

Torale is a **grounded search monitoring platform** that uses AI to watch the web for you. Instead of manually checking websites every day, you create monitoring tasks that:

1. Search the web using Google Search
2. Use AI (Gemini) to understand the results
3. Evaluate if your specific condition is met
4. Notify you when conditions are satisfied

## Quick Start

### Option 1: Web Dashboard (Recommended)

The fastest way to get started is using our hosted platform:

1. **Sign up** at [torale.ai](https://torale.ai)
   - Use Google or GitHub OAuth
   - Or sign up with email/password

2. **Create your first task**
   - Click "New Task" or choose a template
   - Enter your search query (e.g., "When is the next iPhone release?")
   - Describe your condition (e.g., "A specific date has been announced")
   - Set a schedule (e.g., daily at 9 AM)

3. **Monitor and get notified**
   - View execution history in the dashboard
   - Check notifications when conditions are met
   - Update tasks as needed

### Option 2: CLI

For command-line users or automation workflows:

1. **Install the CLI**
   ```bash
   pip install torale
   ```

2. **Generate an API key**
   - Log in to [torale.ai](https://torale.ai)
   - Navigate to Settings → API Keys
   - Create a new key and copy it

3. **Authenticate**
   ```bash
   torale auth set-api-key
   # Paste your API key when prompted
   ```

4. **Create a monitoring task**
   ```bash
   torale task create \
     --query "When is the next iPhone being released?" \
     --condition "A specific release date has been officially announced" \
     --schedule "0 9 * * *"
   ```

5. **View your tasks**
   ```bash
   torale task list
   ```

### Option 3: Python SDK

For programmatic integration:

1. **Install the SDK**
   ```bash
   pip install torale
   ```

2. **Create a task with Python**
   ```python
   from torale import ToraleClient

   client = ToraleClient(api_key="your-api-key")

   task = client.tasks.create(
       name="iPhone Release Monitor",
       search_query="When is the next iPhone being released?",
       condition_description="A specific release date has been officially announced",
       schedule="0 9 * * *",  # Daily at 9 AM
       notify_behavior="once"
   )

   print(f"Created task: {task.id}")
   ```

3. **Check executions**
   ```python
   executions = client.tasks.get_executions(task.id)
   for execution in executions:
       print(f"Status: {execution.status}")
       if execution.condition_met:
           print(f"Condition met! {execution.result}")
   ```

## Understanding Key Concepts

### Search Queries
Your search query is what Torale will search for on Google. Make it:
- **Specific** - "iPhone 17 release date" instead of "phone news"
- **Natural** - Write like you're asking a person
- **Focused** - One topic per task

**Good Examples:**
- "When is the next iPhone being released?"
- "What is the current price of PS5 at Best Buy?"
- "Are swimming pool memberships open at SF Rec Center?"

**Bad Examples:**
- "news" (too broad)
- "iPhone" (unclear intent)
- "tech releases and prices" (multiple topics)

### Conditions
Your condition describes what you're watching for. The AI evaluates if this condition is met based on search results.

**Good Conditions:**
- "A specific release date or month has been officially announced"
- "The price has dropped below $450"
- "Registration is now open"
- "The product is in stock"

**Bad Conditions:**
- "Something changed" (too vague)
- "Good news" (subjective)
- "Update available" (unclear)

### Schedules
Use cron syntax to control when checks happen:

| Schedule | Meaning |
|----------|---------|
| `0 9 * * *` | Daily at 9:00 AM |
| `0 */4 * * *` | Every 4 hours |
| `0 9 * * 1` | Every Monday at 9:00 AM |
| `0 9 1 * *` | First day of month at 9:00 AM |

**Tip:** Use our schedule builder in the web dashboard for easy configuration.

### Notification Behaviors

Control how often you get notified:

- **once** (default) - Notify once when condition is first met, then pause task
- **always** - Notify every time condition is met (useful for price tracking)
- **track_state** - Notify only when meaningful changes are detected

## Example Use Cases

### Monitor Product Release
```bash
torale task create \
  --query "When is GPT-5 being released?" \
  --condition "An official release date has been announced" \
  --schedule "0 9 * * *" \
  --notify-behavior once
```

### Track Price Drops
```bash
torale task create \
  --query "What is the current price of MacBook Pro M3 at Best Buy?" \
  --condition "Price is below $1800" \
  --schedule "0 */6 * * *" \
  --notify-behavior always
```

### Check Stock Availability
```bash
torale task create \
  --query "Is PlayStation 5 in stock at Target?" \
  --condition "PS5 is available for purchase" \
  --schedule "0 */2 * * *" \
  --notify-behavior once
```

### Monitor Event Tickets
```bash
torale task create \
  --query "Are Taylor Swift Eras Tour tickets on sale?" \
  --condition "Tickets are available for purchase" \
  --schedule "0 */1 * * *" \
  --notify-behavior once
```

## What's Next?

- Learn about [Task Templates](/guide/task-templates) for quick setup
- Understand [How Torale Works](/guide/how-it-works) under the hood
- Explore [Creating Tasks](/guide/creating-tasks) in depth
- Configure [Notifications](/guide/notifications)
- Master [Scheduling](/guide/scheduling) with cron

## Need Help?

- Check our [Troubleshooting Guide](/guide/troubleshooting)
- View [API Reference](/api/authentication)
- Join our [GitHub Discussions](https://github.com/torale-ai/torale/discussions)
- Report issues on [GitHub Issues](https://github.com/torale-ai/torale/issues)
