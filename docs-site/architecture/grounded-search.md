---
title: Grounded Search
description: How webwhen keeps search retrieval independent from model reasoning while preserving typed evidence and source attribution.
---

# Grounded Search

webwhen combines live evidence with an LLM that decides whether a watch's condition has been met. Search and reasoning are deliberately separate: changing the reasoning model does not silently change how evidence is retrieved.

## Retrieval boundary

The Pydantic AI agent can choose among explicit tools defined in `torale-agent/tools.py`:

- **Perplexity Search** — synthesized current results with citations and freshness metadata.
- **Parallel Search** — structured result excerpts that often surface primary sources missed by aggregated search.
- **Twitter Search** — recent public posts for announcements and fast-moving conversation.
- **Fetch URL** — direct page content when a search excerpt is stale or incomplete.

The primary reasoning model is Gemini, but webwhen does not use Gemini's native Google Search grounding. This is an evaluated product boundary rather than a framework limitation. A November 2025 comparison found Perplexity more accurate for webwhen's monitoring cases, and Parallel was later added after it improved primary-source coverage without reducing trigger accuracy.

Keeping retrieval explicit also means an eval can compare reasoning models against the same evidence tools. Provider-native search should only replace this boundary after a monitoring-specific evaluation shows a material improvement.

## Execution loop

Each run follows the same evidence-driven loop:

1. Review previous executions and task-specific search memories.
2. Select an appropriate search tool and query for current information.
3. Fetch promising source pages when snippets are insufficient.
4. Compare new evidence with the user's condition and prior notifications.
5. Return a typed `MonitoringResponse` containing evidence, source URLs, confidence, an optional notification, and the next run time.

Search and fetch tools return typed, provider-shaped results. Pydantic AI includes their return schemas in the tool definitions, so the model sees the actual fields without webwhen flattening provider capabilities into a lowest-common-denominator result.

## Runtime guardrails

Pydantic AI enforces per-run limits of 20 model requests, 40 tool calls, and 100,000 total tokens. Each successful production, CLI, and evaluation run emits request, tool-call, and token usage to Logfire in addition to the normal Pydantic AI spans.

Perplexity and Parallel retain their SDK-native bounded HTTP retries. Direct page fetching has a hard timeout and returns a structured failure the agent can act on.

## Response shape

The agent and backend share this application contract:

```json
{
  "evidence": "Apple's newsroom confirms a specific release date.",
  "sources": ["https://www.apple.com/newsroom/…"],
  "confidence": 96,
  "next_run": "2026-09-20T00:07:00Z",
  "notification": "Apple announced the iPhone 17 release date as September 19.",
  "topic": "iPhone 17 release date",
  "activity": []
}
```

`notification` is omitted when there is nothing worth telling the user. `next_run` remains populated because watch lifecycle changes belong to the user or an administrator, not to an individual agent run. If the model nevertheless returns `null`, the backend schedules a fallback rather than completing the watch.

## Related

- [Self-Scheduling Agents](/architecture/self-scheduling-agents) — how evidence gathering composes with scheduling
- [Watch State Machine](/architecture/task-state-machine) — user-controlled watch lifecycle
