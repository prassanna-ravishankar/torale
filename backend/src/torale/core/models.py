from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ExecutorType(str, Enum):
    LLM_GROUNDED_SEARCH = "llm_grounded_search"


class NotifyBehavior(str, Enum):
    ONCE = "once"  # Notify once and auto-disable task
    ALWAYS = "always"  # Notify every time condition is met
    TRACK_STATE = "track_state"  # Notify only when state changes


class TaskState(str, Enum):
    """Task state enum - represents what the task is currently doing."""

    ACTIVE = "active"  # Monitoring on schedule
    PAUSED = "paused"  # User manually stopped
    COMPLETED = "completed"  # Auto-stopped after notify_behavior="once" success


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


# Temporal Workflow Models


@dataclass
class TaskExecutionRequest:
    """Request to execute a task via Temporal workflow."""

    task_id: str
    execution_id: str
    user_id: str
    task_name: str
    suppress_notifications: bool = False  # For preview/manual runs


# Notification Models
class NotificationConfig(BaseModel):
    """Configuration for a notification channel."""

    type: Literal["email", "webhook"]

    # Email-specific fields
    address: str | None = None
    template: str | None = None

    # Webhook-specific fields
    url: str | None = None
    method: str = "POST"
    headers: dict[str, str] | None = None


class TaskBase(BaseModel):
    name: str
    schedule: str
    executor_type: ExecutorType = ExecutorType.LLM_GROUNDED_SEARCH
    config: dict
    state: TaskState = TaskState.ACTIVE

    # Grounded search fields
    search_query: str | None = None
    condition_description: str | None = None
    notify_behavior: NotifyBehavior = NotifyBehavior.ONCE

    # Notification configuration
    notifications: list[NotificationConfig] = Field(default_factory=list)


class TaskCreate(TaskBase):
    """Create task - requires search_query and condition for grounded search"""

    search_query: str  # Make required for creation
    condition_description: str  # Make required for creation
    run_immediately: bool = False  # Execute task immediately after creation


class TaskUpdate(BaseModel):
    name: str | None = None
    schedule: str | None = None
    config: dict | None = None
    state: TaskState | None = None
    search_query: str | None = None
    condition_description: str | None = None
    notify_behavior: NotifyBehavior | None = None
    notifications: list[NotificationConfig] | None = None


class Task(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    state_changed_at: datetime  # When task state last changed

    # Grounded search state tracking
    condition_met: bool = False  # DEPRECATED: Will be removed, use last_execution.condition_met
    last_known_state: dict | None = None
    last_notified_at: datetime | None = None  # DEPRECATED: Will be removed

    # Latest execution reference (replaces sticky condition_met)
    last_execution_id: UUID | None = None
    last_execution: "TaskExecution | None" = None  # Embedded from API query

    # Shareable tasks fields
    is_public: bool = False
    slug: str | None = None
    view_count: int = 0
    subscriber_count: int = 0
    forked_from_task_id: UUID | None = None


class TaskExecutionBase(BaseModel):
    task_id: UUID
    status: TaskStatus = TaskStatus.PENDING
    result: dict | None = None
    error_message: str | None = None

    # Grounded search execution fields
    condition_met: bool | None = None
    change_summary: str | None = None
    grounding_sources: list[dict] | None = None


class TaskExecution(TaskExecutionBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    started_at: datetime
    completed_at: datetime | None = None
    created_at: datetime | None = None


# Task Template Models
class TaskTemplateBase(BaseModel):
    name: str
    description: str
    category: str
    icon: str | None = None
    search_query: str
    condition_description: str
    schedule: str
    notify_behavior: NotifyBehavior = NotifyBehavior.TRACK_STATE
    config: dict = {"model": "gemini-2.5-flash"}


class TaskTemplateCreate(TaskTemplateBase):
    """Create template"""

    pass


class TaskTemplate(TaskTemplateBase):
    """Template read from database"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    state: TaskState = TaskState.ACTIVE
    created_at: datetime
    updated_at: datetime | None = None


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


class StateComparison(BaseModel):
    """LLM response for comparing previous and current states."""

    changed: bool = Field(
        description="Whether factual information has meaningfully changed between states"
    )
    summary: str | None = Field(
        description="1-2 sentence summary of what changed, or null if nothing changed"
    )
