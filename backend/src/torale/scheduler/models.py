"""Shared models for scheduler module."""

from pydantic import BaseModel, Field


class GroundingSource(BaseModel):
    """A URL source backing agent evidence."""

    url: str
    title: str


class NotificationContext(BaseModel):
    """Typed context for notification delivery, built from task + user + execution data."""

    task: dict
    execution: dict
    clerk_email: str
    verified_emails: list[str] = []
    notification_channels: list[str] = Field(default_factory=lambda: ["email"])
    webhook_url: str | None = None
    webhook_secret: str | None = None
    webhook_headers: dict[str, str] | None = None


class AgentExecutionResult(BaseModel):
    """Agent output persisted to DB. Constructed in job.py, consumed by persist_execution_result."""

    evidence: str
    notification: str | None = None
    confidence: int
    next_run: str | None = None
    grounding_sources: list[GroundingSource] = []
    activity: list["ActivityStep"] | None = None


class EnrichedExecutionResult(BaseModel):
    """Execution result enriched with notification metadata for delivery functions."""

    execution_id: str
    summary: str
    sources: list[GroundingSource] = []
    notification: str | None = None
    is_first_execution: bool = False
    next_run: str | None = None
    confidence: int | None = None


class ToolAnnotations(BaseModel):
    """Passthrough MCP tool annotations. Unrendered in v1; forward-compat for write-tool UX."""

    readOnlyHint: bool | None = None
    destructiveHint: bool | None = None
    idempotentHint: bool | None = None


class ActivityStep(BaseModel):
    """A single step the agent took during monitoring.

    SYNC: Keep in sync with torale-agent/models.py:ActivityStep
    """

    tool: str = Field(description="Tool name (e.g. perplexity_search, NOTION_SEARCH_NOTION_PAGE)")
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

    SYNC: Keep in sync with torale-agent/models.py:MonitoringResponse
    """

    evidence: str = Field(description="Internal reasoning and audit trail (not user-facing)")
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
