"""Shared data models for the monitoring agent."""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

import httpx
from mem0 import AsyncMemoryClient
from parallel import AsyncParallel
from perplexity import AsyncPerplexity
from pydantic import BaseModel, ConfigDict, Field

DEFAULT_MODEL = "google-gla:gemini-3.1-flash-lite-preview"


class ToolAnnotations(BaseModel):
    """Passthrough MCP tool annotations. Unrendered in v1; forward-compat for write-tool UX."""

    readOnlyHint: bool | None = None
    destructiveHint: bool | None = None
    idempotentHint: bool | None = None


class ActivityStep(BaseModel):
    """A single step the agent took during monitoring.

    SYNC: Keep in sync with backend/src/torale/scheduler/models.py:ActivityStep
    """

    tool: str = Field(
        description="Tool name (e.g. perplexity_search, NOTION_SEARCH_NOTION_PAGE)"
    )
    detail: str = Field(description="Human-readable summary of what was done")
    connector_slug: str | None = Field(
        default=None,
        description="Toolkit slug (e.g. 'notion') for MCP tools, None for built-ins",
    )
    annotations: ToolAnnotations | None = Field(
        default=None,
        description="MCP tool annotations passthrough (readOnlyHint etc.)",
    )


class MonitoringResponse(BaseModel):
    """Response from monitoring check.

    SYNC: Keep in sync with backend/src/torale/scheduler/models.py:MonitoringResponse
    """

    evidence: str = Field(
        description="Internal reasoning and audit trail (not user-facing)"
    )
    sources: list[str] = Field(description="URLs backing the evidence")
    confidence: int = Field(ge=0, le=100, description="Confidence level 0-100")
    next_run: str | None = Field(
        default=None,
        description="ISO timestamp for next check, or null if monitoring is complete",
    )
    notification: str | None = Field(
        default=None,
        description="Markdown message for the user, or null if nothing to report",
    )
    topic: str | None = Field(
        default=None,
        description="A short, specific 3-5 word title for this monitor (e.g. 'iPhone 16 Release'), if one is needed.",
    )
    activity: list[ActivityStep] | None = Field(
        default=None,
        description="Steps the agent took during this run (tool calls made)",
    )


@dataclass
class Clients:
    """Async HTTP clients for external services."""

    parallel: AsyncParallel
    perplexity: AsyncPerplexity
    mem0: AsyncMemoryClient
    twitter: httpx.AsyncClient


@asynccontextmanager
async def create_clients() -> AsyncIterator[Clients]:
    """Create and manage async HTTP client lifecycles."""
    async with (
        AsyncParallel() as parallel,
        AsyncPerplexity() as perplexity,
        AsyncMemoryClient() as mem0,
        httpx.AsyncClient(
            base_url="https://api.twitterapi.io",
            headers={"X-API-Key": os.environ["TWITTERIO_API_KEY"]},
            timeout=15,
        ) as twitter,
    ):
        yield Clients(
            parallel=parallel, perplexity=perplexity, mem0=mem0, twitter=twitter
        )


class MonitoringDeps(BaseModel):
    """Dependencies for monitoring agent containing user and task identifiers."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    user_id: str
    task_id: str
    clients: Clients | None = None
