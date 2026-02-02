"""Shared test fixtures."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

JOB_MODULE = "torale.scheduler.job"


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
    ):
        mock_db.execute = AsyncMock()
        mock_db.fetch_one = AsyncMock()

        mocks = MagicMock()
        mocks.db = mock_db
        mocks.agent = mock_agent
        mocks.persist = mock_persist
        mocks.fetch_ctx = mock_fetch_ctx
        mocks.email = mock_email
        mocks.webhook = mock_webhook
        mocks.scheduler = mock_scheduler
        mocks.service_cls = mock_service_cls

        yield mocks
