# Viewing Results

View execution history and check when your conditions are met.

## Execution History

The Executions tab shows every time a task ran, with:
- Execution timestamp
- Status (success/failed)
- Duration
- Whether condition was met
- Full results with answer and reasoning

Click any execution to see detailed results including grounding sources and change summaries.

## Notifications View

The Notifications tab filters to show only executions where your condition was met, making it easy to see when you got alerted without scrolling through all executions.

Each notification includes:
- Concise answer (2-4 sentences)
- Reasoning for why the condition was met
- Source URLs where information was found
- Change summary (for track_state behavior)

## Grounding Sources

Every execution includes sources - the web pages where information was found. Click source URLs to verify information directly.

The system filters out infrastructure redirect URLs to show only clean domain names like "apple.com" or "theverge.com".

## Next Steps

- Configure [Notifications](/user-guide/notifications)
- Learn about [Managing Tasks](/user-guide/managing-tasks)
