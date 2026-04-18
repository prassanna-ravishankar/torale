---
title: Grounded Search
description: How Torale combines Google Search with LLM evaluation to monitor web conditions. Pydantic AI agent, Gemini grounding, source attribution, and condition evaluation.
---

# Grounded Search

Torale monitors conditions on the open web by combining **live search results** with an **LLM that evaluates** whether the condition is met. The combination is called _grounded search_: answers are grounded in current search data rather than the model's training cutoff.

## Why grounded search

A pure LLM cannot answer "did Apple announce an iPhone release date today?" — its training data is stale and it cannot browse. A pure scraper cannot answer "is the announced date before Q2 2027?" — it has no reasoning. Torale's pipeline does both:

- **Current information** from Google Search at execution time
- **Source attribution** — each answer cites the pages it came from
- **Condition evaluation** — the LLM decides whether the user's condition is satisfied
- **Execution awareness** — the agent knows when a task last ran and focuses on what's new

## Pipeline

Each task execution runs the following loop inside the monitoring agent:

1. **Search.** The agent issues Google Search queries (via Gemini's built-in grounding, and/or Parallel Search for broader coverage) derived from the user's `search_query`.
2. **Read.** Top results are fetched and excerpted. The agent can follow citations when extra context is needed.
3. **Reason.** Using the gathered evidence, the agent writes a short, user-readable answer to the query.
4. **Evaluate.** The agent decides whether the user's `condition_description` is satisfied based on the answer + evidence.
5. **Attribute.** The agent returns a structured response with the answer, reasoning, and a filtered list of source URLs.

The output is a typed `MonitoringResponse` (see `torale-agent/models.py`) that the backend persists and optionally uses to fire notifications.

## Agent runtime

The agent is built with [Pydantic AI](https://ai.pydantic.dev/) on top of Gemini (primary) with graceful degradation to the paid tier when the free tier returns a 503 under load (see `backend/src/torale/scheduler/`).

Two capabilities drive the loop:

- **Google grounding** — Gemini's native search integration returns results with citations the agent can reason over.
- **Tools** — defined in `torale-agent/tools.py`. Include parallel search (multi-query web search), page fetch (read a specific URL), and activity logging (so the frontend can replay the agent's steps).

The agent runs with `retries=3` and, for supported models, extended thinking enabled.

## Source filtering

Gemini's grounding responses sometimes include Vertex AI redirect URLs rather than the actual source page. Before returning a result the backend filters these out so the user sees canonical domains (e.g. `apple.com`) in notifications rather than `vertexaisearch.cloud.google.com/...` redirects.

## Response shape

A completed execution returns:

```json
{
  "condition_met": true,
  "answer": "Apple announced iPhone 17 will be released on September 19, 2026. Pre-orders begin September 12.",
  "reasoning": "Apple's official newsroom post confirms a specific release date, satisfying the condition.",
  "sources": [
    { "uri": "https://www.apple.com/newsroom/…", "title": "Apple announces iPhone 17" }
  ],
  "next_run": "2026-09-20T00:00:00Z"
}
```

`next_run` drives the scheduler. When the agent returns `next_run=null`, the backend transitions the task to `completed` (see [Task State Machine](/architecture/task-state-machine)).

## Execution context

The backend passes execution context to the agent each run:

- `last_executed_at` — so the agent can prioritise _new_ information since last check
- `previous_answer` — so small phrasing changes don't fire false-positive notifications
- `notify_behavior` — `once` vs `always`, which affects how aggressively the agent declares a match

This context plus typed outputs is what distinguishes Torale from a plain cron + LLM setup.

## Tuning the query

The query and condition are independent knobs. A good query is specific and search-engine-shaped; a good condition is objectively evaluable.

- Query: "iPhone 17 release date announcement"
- Condition: "Apple has publicly stated a specific release date"

If impressions look high but the agent reports no match, the condition is probably too strict. If matches happen every run, the condition is too loose.

## Related

- [Task State Machine](/architecture/task-state-machine) — how task execution is scheduled and terminated
