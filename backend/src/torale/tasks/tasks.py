from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class NotifyBehavior(str, Enum):
    ONCE = "once"  # Notify once and auto-disable task
    ALWAYS = "always"  # Notify every time condition is met


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
    name: str = "New Monitor"
    schedule: str = "0 */6 * * *"
    state: TaskState = TaskState.ACTIVE

    # Grounded search fields
    search_query: str | None = None
    condition_description: str | None = None
    notify_behavior: NotifyBehavior = NotifyBehavior.ONCE

    # Notification configuration
    notifications: list[NotificationConfig] = Field(default_factory=list)


class TaskCreate(TaskBase):
    """Create task - requires search_query for grounded search"""

    search_query: str
    condition_description: str | None = None
    run_immediately: bool = False  # Execute task immediately after creation


class TaskUpdate(BaseModel):
    name: str | None = None
    schedule: str | None = None
    state: TaskState | None = None
    search_query: str | None = None
    condition_description: str | None = None
    notify_behavior: NotifyBehavior | None = None
    notifications: list[NotificationConfig] | None = None


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


class Task(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    state_changed_at: datetime  # When task state last changed

    # Grounded search state tracking
    last_known_state: dict | list | None = None

    # Latest execution reference
    last_execution_id: UUID | None = None
    last_execution: TaskExecution | None = None  # Embedded from API query

    # Immediate execution error (only set when run_immediately fails during creation)
    immediate_execution_error: str | None = None

    # Shareable tasks fields
    is_public: bool = False
    slug: str | None = None
    view_count: int = 0
    subscriber_count: int = 0
    forked_from_task_id: UUID | None = None
    creator_username: str | None = None  # Username of the task creator


# Task Template Models
class TaskTemplateBase(BaseModel):
    name: str
    description: str
    category: str
    icon: str | None = None
    search_query: str
    condition_description: str
    schedule: str
    notify_behavior: NotifyBehavior = NotifyBehavior.ALWAYS


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
