"""Shared data models for the monitoring agent."""

from typing import Optional

from pydantic import BaseModel, Field


class MonitoringResponse(BaseModel):
    evidence: str = Field(description="Internal reasoning and audit trail (not user-facing)")
    sources: list[str] = Field(description="URLs backing the evidence")
    confidence: int = Field(ge=0, le=100, description="Confidence level 0-100")
    next_run: Optional[str] = Field(default=None, description="ISO timestamp for next check, or null if monitoring is complete")
    notification: Optional[str] = Field(default=None, description="Markdown message for the user, or null if nothing to report")
    topic: Optional[str] = Field(default=None, description="A short, specific 3-5 word title for this monitor (e.g. 'iPhone 16 Release'), if one is needed.")


class MonitoringDeps(BaseModel):
    """Dependencies for monitoring agent containing user and task identifiers."""
    user_id: str
    task_id: str
