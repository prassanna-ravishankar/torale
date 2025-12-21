from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

# LLM Response Models (for structured outputs)


class InferredCondition(BaseModel):
    """LLM response for inferring monitoring condition from search query."""

    condition: str = Field(
        description="Clear, 1-sentence description of what triggers a notification"
    )


class ConditionEvaluation(BaseModel):
    """LLM response for evaluating if a monitoring condition is met."""

    condition_met: bool = Field(
        description="Whether the condition is definitively met based on search results"
    )
    explanation: str = Field(description="Brief explanation of why the condition is/isn't met")
    current_state: Any = Field(
        description=(
            "Extracted facts as structured data. Should include _metadata with "
            "captured_at (date) and state_hash (for change detection)"
        )
    )


# Provider/Pipeline Models


class MonitoringResult(BaseModel):
    """
    Result from monitoring execution - minimal schema approach.

    This is the contract that all monitoring providers must return.
    Emphasizes natural language summary over rigid boolean fields.
    """

    summary: str = Field(
        description="Agent's natural language summary for the user. Should explain what was found and what changed."
    )
    sources: list[dict] = Field(
        description="Grounding sources with url and title",
        default_factory=list,
    )
    actions: list[str] = Field(
        description="Actions taken during execution (e.g., ['searched', 'extracted', 'compared'])",
        default_factory=list,
    )
    metadata: dict = Field(
        description="Optional provider-specific metadata (changed, current_state, schema, etc.)",
        default_factory=dict,
    )


class StateChange(BaseModel):
    """Result of semantic state comparison."""

    changed: bool = Field(description="Whether meaningful change occurred between states")
    explanation: str = Field(
        description="Human-readable explanation of what changed or why nothing changed"
    )


class SearchResult(BaseModel):
    """Result from grounded search execution."""

    answer: str = Field(description="Answer from search")
    sources: list[dict] = Field(description="Grounding sources", default_factory=list)
    temporal_note: str | None = Field(
        description="Note about temporal context (e.g., 'No new updates since last check')",
        default=None,
    )


class ExecutionContext(BaseModel):
    """Context passed to monitoring providers."""

    previous_state: dict | list | None = Field(
        description="Previous extracted state (None if first execution). Can be dict or list depending on extraction schema.",
        default=None,
    )
    last_execution_datetime: datetime | None = Field(
        description="Timestamp of last successful execution",
        default=None,
    )
    task_config: dict = Field(
        description="Task configuration",
        default_factory=dict,
    )


class EnrichedMonitoringResult(MonitoringResult):
    """
    Monitoring result enriched with execution context.

    Extends MonitoringResult with task/execution metadata needed for notifications.
    """

    task_id: str = Field(description="Task ID")
    execution_id: str = Field(description="Execution ID")
    search_query: str = Field(description="Search query used")
    is_first_execution: bool = Field(description="Whether this is the first execution")
