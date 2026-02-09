"""Shared test fixtures."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from a2a.types import (
    Artifact,
    DataPart,
    GetTaskResponse,
    GetTaskSuccessResponse,
    Part,
    SendMessageResponse,
    SendMessageSuccessResponse,
    Task,
    TaskState,
    TaskStatus,
    TextPart,
)

JOB_MODULE = "torale.scheduler.job"


# --- A2A test helpers ---


def make_a2a_task(*, artifacts=None, status_state=TaskState.completed, task_id="task-abc"):
    """Build an A2A Task for tests."""
    return Task(
        id=task_id,
        context_id="ctx-test",
        status=TaskStatus(state=status_state),
        artifacts=artifacts,
    )


def text_artifact(text):
    """Create an artifact with a single TextPart."""
    return Artifact(
        artifact_id="art-1",
        parts=[Part(root=TextPart(kind="text", text=text))],
    )


def data_artifact(data):
    """Create an artifact with a single DataPart."""
    return Artifact(
        artifact_id="art-1",
        parts=[Part(root=DataPart(kind="data", data=data))],
    )


def send_success(task):
    """Wrap a Task in a SendMessageResponse success."""
    return SendMessageResponse(root=SendMessageSuccessResponse(id="req-1", result=task))


def poll_success(task):
    """Wrap a Task in a GetTaskResponse success."""
    return GetTaskResponse(root=GetTaskSuccessResponse(id="req-1", result=task))


class MockTransaction:
    """Mock database transaction context manager."""

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def sample_user():
    """Create a sample user."""
    user = MagicMock()
    user.id = uuid4()
    user.clerk_user_id = "user_test123"
    user.email = "user@example.com"
    user.is_active = True
    user.created_at = datetime.now(UTC)
    user.updated_at = datetime.now(UTC)
    return user


@pytest.fixture
def sample_task():
    """Create a sample task."""
    task = MagicMock()
    task.id = uuid4()
    task.user_id = uuid4()
    task.name = "Test Task"
    task.schedule = "0 9 * * *"
    task.search_query = "Test query"
    task.condition_description = "Test condition"
    task.is_active = True
    task.webhook_url = "https://example.com/webhook"
    return task


@pytest.fixture
def sample_execution(sample_task):
    """Create a sample task execution."""
    execution = MagicMock()
    execution.id = uuid4()
    execution.task_id = sample_task.id
    execution.status = "success"
    execution.condition_met = True
    execution.result = {"answer": "Test answer"}
    execution.grounding_sources = [{"url": "https://example.com", "title": "Example"}]
    execution.started_at = datetime.now(UTC)
    execution.completed_at = datetime.now(UTC)
    return execution


@pytest.fixture
def job_mocks():
    """Patch all job.py dependencies, yield a namespace of mocks."""
    with (
        patch(f"{JOB_MODULE}.db") as mock_db,
        patch(f"{JOB_MODULE}.call_agent", new_callable=AsyncMock) as mock_agent,
        patch(f"{JOB_MODULE}.persist_execution_result", new_callable=AsyncMock) as mock_persist,
        patch(f"{JOB_MODULE}.fetch_notification_context", new_callable=AsyncMock) as mock_fetch_ctx,
        patch(f"{JOB_MODULE}.send_email_notification", new_callable=AsyncMock) as mock_email,
        patch(f"{JOB_MODULE}.send_webhook_notification", new_callable=AsyncMock) as mock_webhook,
        patch(f"{JOB_MODULE}.get_scheduler") as mock_scheduler,
        patch(f"{JOB_MODULE}.TaskService") as mock_service_cls,
        patch(f"{JOB_MODULE}.fetch_recent_executions", new_callable=AsyncMock) as mock_recent_execs,
    ):
        mock_db.execute = AsyncMock()
        mock_db.fetch_one = AsyncMock()
        mock_recent_execs.return_value = []

        mocks = MagicMock()
        mocks.db = mock_db
        mocks.agent = mock_agent
        mocks.persist = mock_persist
        mocks.fetch_ctx = mock_fetch_ctx
        mocks.email = mock_email
        mocks.webhook = mock_webhook
        mocks.scheduler = mock_scheduler
        mocks.service_cls = mock_service_cls
        mocks.recent_execs = mock_recent_execs

        yield mocks
