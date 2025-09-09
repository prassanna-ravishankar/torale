from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class ExecutorType(str, Enum):
    LLM_TEXT = "llm_text"
    LLM_WEB_SEARCH = "llm_web_search"
    LLM_BROWSER = "llm_browser"
    WEBHOOK = "webhook"
    API_CALL = "api_call"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class TaskBase(BaseModel):
    name: str
    schedule: str
    executor_type: ExecutorType = ExecutorType.LLM_TEXT
    config: dict
    is_active: bool = True


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    name: str | None = None
    schedule: str | None = None
    config: dict | None = None
    is_active: bool | None = None


class Task(TaskBase):
    id: UUID
    user_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class TaskExecutionBase(BaseModel):
    task_id: UUID
    status: TaskStatus = TaskStatus.PENDING
    result: dict | None = None
    error_message: str | None = None


class TaskExecution(TaskExecutionBase):
    id: UUID
    started_at: datetime
    completed_at: datetime | None = None

    class Config:
        from_attributes = True