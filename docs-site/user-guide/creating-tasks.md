---
description: Learn how to create monitoring tasks with conditions, schedules, and notifications. Master Torale's task creation interface with templates or custom configuration.
---

# Creating Tasks

Create monitoring tasks through the web dashboard.

## Task Wizard

The multi-step wizard guides you through task creation with validation at each step.

### Step 1: Choose Method

**Use Template** - Pre-configured for common scenarios like product releases, price tracking, and stock availability. Select a template, customize placeholders, and create.

**Start from Scratch** - Full control over all parameters. Configure query, condition, schedule, and notification behavior manually.

### Step 2: Configure Query

Enter your search query as a natural language question. The system will use this to search the web via Google Search.

Write specific questions rather than vague terms. Include relevant details like product names, locations, or timeframes. For example, "When is the iPhone 17 being released?" works better than "iPhone news".

### Step 3: Define Condition

Describe what you're waiting to happen - the trigger that should send a notification. Make conditions objective and measurable.

Good conditions specify exact criteria: "Apple has announced a specific release date" or "The price is $1799 or lower". Avoid vague or subjective terms like "good price" or "interesting news".

### Step 4: Set Schedule

Configure when the task runs using the visual schedule builder or custom cron expression.

Common patterns:
- Daily at 9 AM for regular checks
- Every 2-4 hours for price and stock monitoring
- Every hour for time-sensitive items like ticket sales

The preview shows the next 5 execution times in your local timezone.

### Step 5: Preview (Optional)

Test your query before creating the task. The preview runs a real search and shows whether your condition would be met based on current information.

Review the answer, check the sources, and verify the evaluation makes sense. Adjust your query or condition if needed.

### Step 6: Review

Confirm all settings before creating the task. You can edit any field before final creation.

## Task Components

**Name** - Descriptive label for the task (auto-generated if omitted)

**Search Query** - Natural language question to search for

**Condition** - Trigger criteria that must be met for notification

**Schedule** - When the task runs (cron expression)

**Notification Behavior** - How often to notify:
- **once** - Notify when condition first becomes true, then pause
- **always** - Notify every time condition is met

## Run Immediately

Check "Run immediately after creation" to execute the task right away for testing. This helps verify your query and condition work as expected before waiting for the scheduled run.

## Next Steps

- Use [Task Templates](/user-guide/templates) for quick setup
- Learn about [Managing Tasks](/user-guide/managing-tasks)
- Understand [Viewing Results](/user-guide/results)
