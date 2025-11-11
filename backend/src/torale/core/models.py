from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ExecutorType(str, Enum):
    LLM_GROUNDED_SEARCH = "llm_grounded_search"


class NotifyBehavior(str, Enum):
    ONCE = "once"  # Notify once and auto-disable task
    ALWAYS = "always"  # Notify every time condition is met
    TRACK_STATE = "track_state"  # Notify only when state changes


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


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
    is_active: bool = True

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


class TaskUpdate(BaseModel):
    name: str | None = None
    schedule: str | None = None
    config: dict | None = None
    is_active: bool | None = None
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

    # Grounded search state tracking
    condition_met: bool = False
    last_known_state: dict | None = None
    last_notified_at: datetime | None = None


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
    is_active: bool = True
    created_at: datetime
    updated_at: datetime | None = None
