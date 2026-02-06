"""Test execution_id preservation across retries."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from torale.scheduler.job import _schedule_next_run, execute_task_job

TASK_ID = str(uuid4())
EXECUTION_ID = str(uuid4())
USER_ID = str(uuid4())
TASK_NAME = "Test Monitor"


@pytest.mark.asyncio
async def test_schedule_next_run_passes_execution_id():
    """Verify that _schedule_next_run passes execution_id to APScheduler."""
    with (
        patch("torale.scheduler.job.get_scheduler") as mock_get_scheduler,
        patch("torale.scheduler.job.db") as mock_db,
    ):
        mock_scheduler = MagicMock()
        mock_get_scheduler.return_value = mock_scheduler
        mock_db.execute = AsyncMock()

        next_run_dt = datetime.now(UTC)
        retry_count = 2

        await _schedule_next_run(
            task_id=TASK_ID,
            user_id=USER_ID,
            task_name=TASK_NAME,
            next_run_dt=next_run_dt,
            execution_id=EXECUTION_ID,
            retry_count=retry_count,
        )

        # Verify APScheduler job was created with execution_id in args
        mock_scheduler.add_job.assert_called_once()
        call_kwargs = mock_scheduler.add_job.call_args.kwargs
        args = call_kwargs["args"]

        # Args should be: [task_id, user_id, task_name, retry_count, execution_id]
        assert len(args) == 5
        assert args[0] == TASK_ID
        assert args[1] == USER_ID
        assert args[2] == TASK_NAME
        assert args[3] == retry_count
        assert args[4] == EXECUTION_ID, "execution_id must be passed as 5th argument"


@pytest.mark.asyncio
async def test_execute_task_job_accepts_execution_id():
    """Verify execute_task_job accepts and passes execution_id parameter."""
    with patch("torale.scheduler.job._execute") as mock_execute:
        mock_execute.return_value = AsyncMock()

        await execute_task_job(
            task_id=TASK_ID,
            user_id=USER_ID,
            task_name=TASK_NAME,
            retry_count=1,
            execution_id=EXECUTION_ID,
        )

        # Verify _execute was called with execution_id
        mock_execute.assert_awaited_once()
        call_kwargs = mock_execute.call_args.kwargs
        assert call_kwargs["execution_id"] == EXECUTION_ID, "execution_id must be passed to _execute"
        assert call_kwargs["retry_count"] == 1


@pytest.mark.asyncio
async def test_execute_task_job_defaults_to_none():
    """Verify execute_task_job defaults execution_id to None for new executions."""
    with patch("torale.scheduler.job._execute") as mock_execute:
        mock_execute.return_value = AsyncMock()

        # Call without execution_id (new execution)
        await execute_task_job(
            task_id=TASK_ID,
            user_id=USER_ID,
            task_name=TASK_NAME,
            retry_count=0,
        )

        # Verify _execute was called with execution_id=None
        mock_execute.assert_awaited_once()
        call_kwargs = mock_execute.call_args.kwargs
        assert call_kwargs["execution_id"] is None, "execution_id should default to None for new executions"
        assert call_kwargs["retry_count"] == 0
