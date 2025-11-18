# Managing Tasks

Edit, pause, resume, and delete your monitoring tasks.

## Editing Tasks

Click "Edit" on any task to modify:
- Search query
- Trigger condition
- Schedule (cron expression)
- Notification behavior
- Task name

Changes take effect on the next scheduled run. The Temporal schedule is updated automatically when you modify the cron expression.

## Pausing Tasks

Temporarily disable a task without deleting it. Click "Pause" or toggle the active status.

Paused tasks:
- Don't execute on schedule
- Retain all execution history
- Can be resumed anytime

Resume by toggling the status back to active.

## Deleting Tasks

Remove tasks you no longer need. This action:
- Deletes the task record
- Removes the Temporal schedule
- Preserves execution history for auditing
- Cannot be undone

## Bulk Actions

Select multiple tasks to:
- Pause or resume all at once
- Delete multiple tasks
- Export task configurations

## Next Steps

- View [Execution Results](/user-guide/results)
- Configure [Notifications](/user-guide/notifications)
- Learn about [Creating Tasks](/user-guide/creating-tasks)
