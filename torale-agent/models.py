"""Shared data models for the monitoring agent."""

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ActivityStep(BaseModel):
    """A single step the agent took during monitoring."""

    tool: str = Field(description="Tool name (e.g. perplexity_search, fetch_url)")
    detail: str = Field(description="Human-readable summary of what was done")


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

    parallel: Any
    perplexity: Any
    mem0: Any


class MonitoringDeps(BaseModel):
    """Dependencies for monitoring agent containing user and task identifiers."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    user_id: str
    task_id: str
    clients: Clients | None = None
