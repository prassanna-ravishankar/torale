"""Agent tool definitions: search, memory, fetch, and activity extraction."""

import asyncio
import json
import socket
from ipaddress import ip_address
from urllib.parse import urlparse

from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import ModelResponse, ToolCallPart

from models import ActivityStep, Clients, MonitoringDeps, MonitoringResponse

_NO_CLIENTS = json.dumps({"error": "No context available"})


def _get_clients(ctx: RunContext[MonitoringDeps]) -> Clients | None:
    """Extract clients from context, returning None if unavailable."""
    return ctx.deps.clients if ctx.deps else None


PARALLEL_SEARCH_MAX_RESULTS = 10
PARALLEL_SEARCH_MAX_CHARS = 5000
PARALLEL_SEARCH_BETAS = ("search-extract-2025-10-10",)
PARALLEL_SEARCH_MAX_EXCERPTS = 2

FETCH_MAX_CHARS = 5000
FETCH_TIMEOUT = 15.0

_TOOL_INPUT_KEYS: dict[str, str] = {
    "perplexity_search": "query",
    "parallel_search": "query",
    "fetch_url": "url",
    "search_memories": "query",
    "add_memory": "text",
}


async def _is_safe_url(url: str) -> bool:
    """Check that a URL doesn't resolve to internal/private network resources."""
    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname or parsed.scheme not in ("http", "https"):
        return False

    try:
        loop = asyncio.get_running_loop()
        addrinfo = await loop.getaddrinfo(hostname, None, family=socket.AF_UNSPEC)
        return all(ip_address(addr[4][0]).is_global for addr in addrinfo)
    except (socket.gaierror, ValueError):
        return False


async def _fetch_and_extract(url: str) -> dict:
    """Fetch a URL using Lightpanda headless browser and return content as markdown."""
    if not await _is_safe_url(url):
        return {"url": url, "error": "URL blocked: private or internal address"}

    proc = await asyncio.create_subprocess_exec(
        "lightpanda",
        "fetch",
        "--dump",
        "markdown",
        "--strip_mode",
        "js,css",
        "--http_timeout",
        str(int(FETCH_TIMEOUT * 1000)),
        url,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=FETCH_TIMEOUT + 5
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return {"url": url, "error": "Fetch timed out"}

    if proc.returncode != 0:
        error_msg = (
            stderr.decode().strip() if stderr else f"Exit code {proc.returncode}"
        )
        return {"url": url, "error": error_msg}

    content = stdout.decode()
    content = "\n".join(line for line in content.splitlines() if line.strip())

    full_length = len(content)
    truncated = full_length > FETCH_MAX_CHARS

    return {
        "url": url,
        "content": content[:FETCH_MAX_CHARS],
        "content_length": full_length,
        "truncated": truncated,
    }


def register_tools(agent: Agent[MonitoringDeps, MonitoringResponse]) -> None:
    """Attach monitoring tools (search_memories, add_memory, perplexity_search, parallel_search, fetch_url) to an agent."""

    @agent.tool
    async def search_memories(ctx: RunContext[MonitoringDeps], query: str) -> str:
        """Search previous monitoring memories for this task. Use to recall what was found in earlier runs."""
        if (clients := _get_clients(ctx)) is None:
            return _NO_CLIENTS
        results = await clients.mem0.search(
            query,
            filters={
                "AND": [{"user_id": ctx.deps.user_id}, {"app_id": ctx.deps.task_id}]
            },
            top_k=10,
        )
        return json.dumps(results, default=str)

    @agent.tool
    async def add_memory(ctx: RunContext[MonitoringDeps], text: str) -> str:
        """Store a new meta-knowledge memory for this task. Only store patterns and source insights, not individual check results."""
        if (clients := _get_clients(ctx)) is None:
            return _NO_CLIENTS
        result = await clients.mem0.add(
            [{"role": "user", "content": text}],
            user_id=ctx.deps.user_id,
            app_id=ctx.deps.task_id,
        )
        return json.dumps(result, default=str)

    @agent.tool
    async def perplexity_search(ctx: RunContext[MonitoringDeps], query: str) -> str:
        """Search the web using Perplexity for current information. Include the current year in queries for time-sensitive topics."""
        if (clients := _get_clients(ctx)) is None:
            return _NO_CLIENTS
        response = await clients.perplexity.search.create(query=query)
        results = [
            {
                "title": r.title,
                "url": r.url,
                "snippet": r.snippet,
                "date": r.date,
                "last_updated": r.last_updated,
            }
            for r in response.results
        ]
        return json.dumps(results)

    @agent.tool
    async def parallel_search(ctx: RunContext[MonitoringDeps], query: str) -> str:
        """Search the web using Parallel for current information. Returns structured results with URLs, titles, and content excerpts. Often finds different authoritative sources than Perplexity."""
        if (clients := _get_clients(ctx)) is None:
            return _NO_CLIENTS
        result = await clients.parallel.beta.search(
            objective=query,
            search_queries=[query],
            max_results=PARALLEL_SEARCH_MAX_RESULTS,
            max_chars_per_result=PARALLEL_SEARCH_MAX_CHARS,
            betas=PARALLEL_SEARCH_BETAS,
        )
        results = [
            {
                "title": r.title,
                "url": r.url,
                "excerpts": r.excerpts[:PARALLEL_SEARCH_MAX_EXCERPTS]
                if r.excerpts
                else [],
            }
            for r in (result.results or [])
        ]
        return json.dumps(results)

    @agent.tool_plain
    async def fetch_url(url: str) -> str:
        """Fetch a URL directly and extract its content as markdown. Uses a headless browser, so JS-rendered pages work. Useful when search snippets are stale or you need to check the source."""
        try:
            result = await _fetch_and_extract(url)
            return json.dumps(result)
        except Exception as e:
            return json.dumps({"url": url, "error": str(e)})


def extract_activity(messages: list) -> list[ActivityStep]:
    """Extract tool call activity from Pydantic AI message history."""
    steps: list[ActivityStep] = []
    for msg in messages:
        if not isinstance(msg, ModelResponse):
            continue
        for part in msg.parts:
            if not isinstance(part, ToolCallPart):
                continue
            tool = part.tool_name
            args = part.args if isinstance(part.args, dict) else {}
            key = _TOOL_INPUT_KEYS.get(tool, "")
            input_val = args.get(key, "") if key else ""
            steps.append(ActivityStep(tool=tool, detail=input_val))
    return steps
