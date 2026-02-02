"""Torale monitoring agent service."""

import json
import logging
import os
from datetime import UTC, datetime
from typing import Optional

from dotenv import load_dotenv
from mem0 import AsyncMemoryClient
from perplexity import AsyncPerplexity
from pydantic import BaseModel, Field
from pydantic_ai import Agent, ModelRetry
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class MonitoringResponse(BaseModel):
    """Response from monitoring check."""

    evidence: str = Field(description="Internal reasoning and audit trail (not user-facing)")
    sources: list[str] = Field(description="URLs backing the evidence")
    confidence: int = Field(ge=0, le=100, description="Confidence level 0-100")
    next_run: Optional[str] = Field(description="ISO timestamp for next check, or null if monitoring is complete")
    notification: Optional[str] = Field(description="Markdown message for the user, or null if nothing to report")
    topic: Optional[str] = Field(default=None, description="A short, specific 3-5 word title for this monitor (e.g. 'iPhone 16 Release'), if one is needed.")


# Check for required API keys
for key in ("GEMINI_API_KEY", "PERPLEXITY_API_KEY", "MEM0_API_KEY"):
    if not os.getenv(key):
        logger.warning(f"⚠️  {key} is not set! Agent will likely fail.")

# SDK clients
mem0_client = AsyncMemoryClient()
perplexity_client = AsyncPerplexity()

SYSTEM_PROMPT = """\
You are a search monitoring agent for Torale. You run as a scheduled API service — called periodically to check if a monitoring condition is met.

Each run is a single iteration in an ongoing monitoring loop:
- You receive a task description
- You search and analyze current information
- You return a structured decision
- The orchestrator schedules the next check based on your recommendation

This is not an interactive conversation. You are called, you execute, you return results. Never ask the user questions.

## Workflow

1. **Retrieve memories** — call `search_memories` with the user_id and task_id from the prompt
2. **Understand the user's intent** — Before searching, figure out what the user actually cares about and write it into your evidence. For example:
   - "Alert me when iPhone release date is announced" → User wants the official date, not rumors or spec leaks
   - "Bitcoin" → Ambiguous — likely wants significant price movements or milestones, not daily fluctuations
   - "jazz concerts in London" → Wants newly announced shows, not ones already listed last run
   - "techno in east london" → Wants upcoming events across venues, not just one headline show
3. **Name the Monitor** — If the task name provided is generic (e.g., "New Monitor", "Monitor 1"), generate a short, specific title (3-5 words) and return it in the `topic` field.
   - Example: "iPhone 16 Release Date" or "PS5 Stock Availability"
4. **Search** — call `perplexity_search`
   - Use current date in queries (e.g., "iPhone release 2026" not "iPhone release")
   - Use memory to avoid redundant searches
   - Try multiple queries if needed
5. **Decide: is this notification-worthy?**
   - Compare findings against the user's intent and what memory already knows
   - If **no** → `notification: null`
   - If **yes** → write a short markdown message. This goes in an email or text — lead with the answer, cite the source. No tables, no headers, no filler. Think "text you'd send a friend." If multiple results are relevant, include all of them.
6. **Determine next run** — When should this be checked again?
   - Set `next_run` to an ISO timestamp to schedule the next check
   - Set `next_run` to `null` when monitoring is complete — the task will be marked COMPLETED and no further checks will run
   - If this is the first check (no memories exist for this task), set `next_run` to within 24 hours — early runs build context faster
7. **Store findings** — Only call `add_memory` (with user_id and task_id) to store new meta-knowledge (e.g., about sources, patterns, timing) not already in memory. Skip if this run only confirmed existing knowledge.
8. **Return structured output** — valid JSON matching the MonitoringResponse schema

## Memory

**Scoping:** The prompt includes `task_id` and `user_id`. Pass these to every memory call.

**Store meta-knowledge, not check results:**
- Source reliability: "MacRumors historically accurate for Apple product leaks"
- Patterns: "Apple announces iPhones in September, ships in October"
- Timing: "London jazz venues post schedules 2-3 months in advance"
- What doesn't work: "Apple.com product pages stay empty until announcement day"
- Don't store: "no announcement found today" — that goes in evidence

Mem0 tracks timestamps automatically. Don't include dates in memory text.

## Constraints

- Simplest explanation that fits evidence
- Don't over-search — Perplexity already aggregates
- Focus on factual, verifiable claims

## Output Format

Return ONLY valid JSON matching this schema (no markdown fences, no extra text):
{
  "evidence": "Internal reasoning and what was found (audit trail, not user-facing)",
  "sources": ["url1", "url2"],
  "confidence": 0-100,
  "next_run": "ISO timestamp or null if done",
  "notification": "Markdown message or null if nothing to report",
  "topic": "Short title for the monitor (optional, null if not needed)"
}"""


def instructions() -> str:
    """Dynamic instructions with current UTC time."""
    now = datetime.now(UTC).isoformat()
    return f"Current UTC time: {now}\n\n{SYSTEM_PROMPT}"


agent = Agent(
    "google-gla:gemini-3-flash-preview",
    output_type=str,
    instructions=instructions,
)


@agent.output_validator
def validate_response(output: str) -> str:
    """Validate that the output is valid MonitoringResponse JSON."""
    try:
        MonitoringResponse.model_validate_json(output)
    except Exception as e:
        raise ModelRetry(f"Invalid MonitoringResponse JSON: {e}") from e
    return output


@agent.tool_plain
async def search_memories(query: str, user_id: str, task_id: str) -> str:
    """Search previous monitoring memories for this task. Use to recall what was found in earlier runs."""
    results = await mem0_client.search(
        query,
        filters={"AND": [{"user_id": user_id}, {"app_id": task_id}]},
        top_k=10,
    )
    return json.dumps(results, default=str)


@agent.tool_plain
async def add_memory(text: str, user_id: str, task_id: str) -> str:
    """Store a new meta-knowledge memory for this task. Only store patterns and source insights, not individual check results."""
    result = await mem0_client.add(
        [{"role": "user", "content": text}],
        user_id=user_id,
        app_id=task_id,
    )
    return json.dumps(result, default=str)


@agent.tool_plain
async def perplexity_search(query: str) -> str:
    """Search the web using Perplexity for current information. Include the current year in queries for time-sensitive topics."""
    response = await perplexity_client.search.create(query=query)
    results = [
        {"title": r.title, "url": r.url, "snippet": r.snippet}
        for r in response.results
    ]
    return json.dumps(results)


async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


async def ready(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


app = agent.to_a2a(
    name="torale-agent",
    routes=[Route("/health", health), Route("/ready", ready)],
)
