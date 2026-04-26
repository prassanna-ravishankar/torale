"""Tests for task execution orchestrator (job.py).

Unit tests verify agent call orchestration, notification dispatch,
auto-completion logic, and error handling.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from torale.scheduler.history import ExecutionRecord
from torale.scheduler.job import _execute, execute_task_job
from torale.scheduler.models import MonitoringResponse, NotificationContext

TASK_ID = str(uuid4())
EXECUTION_ID = str(uuid4())
USER_ID = str(uuid4())
TASK_NAME = "Test Monitor"

MODULE = "torale.scheduler.job"

FUTURE = "2099-01-01T00:00:00Z"


def _make_task_row(attached_connector_slugs=None):
    return {
        "search_query": "iPhone release date",
        "condition_description": "Release date announced",
        "name": TASK_NAME,
        "notification_channels": ["email"],
        "state": "active",
        "user_id": USER_ID,
        "attached_connector_slugs": attached_connector_slugs or [],
    }


def _make_notification_context(channels=None):
    return NotificationContext(
        task={"id": TASK_ID, "name": TASK_NAME},
        execution={"id": EXECUTION_ID},
        clerk_email="test@example.com",
        notification_channels=channels or ["email"],
    )


def _make_agent_response(notification=None, evidence="no changes", next_run=FUTURE):
    return MonitoringResponse(
        evidence=evidence,
        notification=notification,
        sources=["https://example.com"],
        confidence=85,
        next_run=next_run,
        topic=None,
    )


class TestExecute:
    @pytest.mark.asyncio
    async def test_no_notification_skips_notify(self, job_mocks):
        """Agent returns no notification -> no notifications sent."""
        job_mocks.db.fetch_one = AsyncMock(return_value=_make_task_row())
        job_mocks.agent.return_value = _make_agent_response()

        await _execute(TASK_ID, EXECUTION_ID, USER_ID, TASK_NAME)

        job_mocks.persist.assert_awaited_once()
        job_mocks.email.assert_not_awaited()
        job_mocks.webhook.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_next_run_none_completes_task(self, job_mocks):
        """Agent returns next_run=null -> task completed after notification."""
        job_mocks.db.fetch_one = AsyncMock(return_value=_make_task_row())
        job_mocks.agent.return_value = _make_agent_response(
            notification="Release date is Sept 9", next_run=None
        )
        job_mocks.fetch_ctx.return_value = _make_notification_context()
        job_mocks.email.return_value = True

        mock_service = MagicMock()
        mock_service.complete = AsyncMock()
        job_mocks.service_cls.return_value = mock_service

        await _execute(TASK_ID, EXECUTION_ID, USER_ID, TASK_NAME)

        job_mocks.email.assert_awaited_once()
        mock_service.complete.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_next_run_set_does_not_complete(self, job_mocks):
        """Agent returns next_run -> notification sent, NOT completed."""
        job_mocks.db.fetch_one = AsyncMock(return_value=_make_task_row())
        job_mocks.agent.return_value = _make_agent_response(notification="Price dropped")
        job_mocks.fetch_ctx.return_value = _make_notification_context()
        job_mocks.email.return_value = True

        await _execute(TASK_ID, EXECUTION_ID, USER_ID, TASK_NAME)

        job_mocks.email.assert_awaited_once()
        job_mocks.service_cls.assert_not_called()

    @pytest.mark.asyncio
    async def test_notification_failure_still_reschedules(self, job_mocks):
        """Notification raises -> execution still succeeds, next run still scheduled."""
        job_mocks.db.fetch_one = AsyncMock(return_value=_make_task_row())
        job_mocks.agent.return_value = _make_agent_response(notification="Condition met")
        job_mocks.fetch_ctx.return_value = _make_notification_context()
        job_mocks.email.side_effect = RuntimeError("SMTP error")

        mock_sched = MagicMock()
        job_mocks.scheduler.return_value = mock_sched

        await _execute(TASK_ID, EXECUTION_ID, USER_ID, TASK_NAME)

        job_mocks.service_cls.assert_not_called()
        mock_sched.add_job.assert_called_once()

    @pytest.mark.asyncio
    async def test_next_run_none_completes_even_if_notification_fails(self, job_mocks):
        """next_run=null + notification failure -> task still completes."""
        job_mocks.db.fetch_one = AsyncMock(return_value=_make_task_row())
        job_mocks.agent.return_value = _make_agent_response(
            notification="Condition met", next_run=None
        )
        job_mocks.fetch_ctx.return_value = _make_notification_context()
        job_mocks.email.side_effect = RuntimeError("SMTP error")

        mock_service = MagicMock()
        mock_service.complete = AsyncMock()
        job_mocks.service_cls.return_value = mock_service

        await _execute(TASK_ID, EXECUTION_ID, USER_ID, TASK_NAME)

        mock_service.complete.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_agent_failure_marks_failed(self, job_mocks):
        """call_agent raises -> execution marked as retrying or failed (no exception raised)."""
        job_mocks.db.fetch_one = AsyncMock(return_value=_make_task_row())
        job_mocks.agent.side_effect = RuntimeError("Agent unreachable")

        # Should not raise - error is handled and retry is scheduled
        await _execute(TASK_ID, EXECUTION_ID, USER_ID, TASK_NAME)

        # Check that execution was marked as retrying or failed
        execute_calls = job_mocks.db.execute.call_args_list
        assert any("retrying" in str(call) or "failed" in str(call) for call in execute_calls)

    @pytest.mark.asyncio
    async def test_double_failure_logged(self, job_mocks):
        """Agent raises + DB update raises -> DB error propagates, execution update fails."""
        job_mocks.db.fetch_one = AsyncMock(return_value=_make_task_row())
        job_mocks.db.execute = AsyncMock(side_effect=[None, Exception("DB down")])
        job_mocks.agent.side_effect = RuntimeError("Agent error")

        # DB error should be raised when we can't persist the failure state
        with pytest.raises(Exception, match="DB down"):
            await _execute(TASK_ID, EXECUTION_ID, USER_ID, TASK_NAME)

    @pytest.mark.asyncio
    async def test_dynamic_reschedule(self, job_mocks):
        """Agent returns next_run -> scheduler.add_job called with DateTrigger."""
        job_mocks.db.fetch_one = AsyncMock(return_value=_make_task_row())
        future_time = (datetime.now(UTC) + timedelta(hours=2)).isoformat()
        job_mocks.agent.return_value = _make_agent_response(next_run=future_time)

        mock_sched = MagicMock()
        job_mocks.scheduler.return_value = mock_sched

        await _execute(TASK_ID, EXECUTION_ID, USER_ID, TASK_NAME)

        mock_sched.add_job.assert_called_once()
        call_kwargs = mock_sched.add_job.call_args
        assert call_kwargs.kwargs["id"] == f"task-{TASK_ID}"

    @pytest.mark.asyncio
    async def test_running_transition_clears_prior_error_fields(self, job_mocks):
        """On entry to _execute, the RUNNING-state UPDATE must clear error fields.

        Regression: retries reuse execution_id, so the row still holds
        error_message / internal_error / error_category from the failed prior
        attempt. If a retry then succeeds, persist_execution_result updates
        status but doesn't touch the error columns, leaving the success row
        with a stale user-facing error message.
        """
        job_mocks.db.fetch_one = AsyncMock(return_value=_make_task_row())
        job_mocks.agent.return_value = _make_agent_response()

        await _execute(TASK_ID, EXECUTION_ID, USER_ID, TASK_NAME)

        # The first db.execute call should be the RUNNING state transition,
        # and it must clear error fields, completed_at, and stale result flags.
        first_sql = job_mocks.db.execute.call_args_list[0].args[0]
        assert "status = $2" in first_sql
        assert "error_message = NULL" in first_sql
        assert "internal_error = NULL" in first_sql
        assert "error_category = NULL" in first_sql
        assert "completed_at = NULL" in first_sql
        assert "result = '{}'::jsonb" in first_sql

    @pytest.mark.asyncio
    async def test_retry_path_preserves_execution_id(self, job_mocks):
        """Failed-attempt retries must share a row by forwarding execution_id.

        Locks in the intentional asymmetry with the success path: a retry is
        the same logical attempt and should reuse the task_executions row, so
        the user sees one row per lifecycle rather than one row per retry
        delay. Only successful follow-ups get a fresh row (see
        test_successful_scheduled_run_does_not_forward_execution_id).
        """
        job_mocks.db.fetch_one = AsyncMock(return_value=_make_task_row())
        job_mocks.agent.side_effect = RuntimeError("Transient agent failure")

        mock_sched = MagicMock()
        job_mocks.scheduler.return_value = mock_sched

        await _execute(TASK_ID, EXECUTION_ID, USER_ID, TASK_NAME, retry_count=0)

        # An UNKNOWN error at retry_count=0 is retried, so the scheduler must
        # get called with a retry job whose APScheduler args still hold the
        # current execution_id (unlike the success path).
        mock_sched.add_job.assert_called_once()
        args = mock_sched.add_job.call_args.kwargs["args"]
        assert args[0] == TASK_ID
        assert args[3] == 1  # retry_count incremented
        assert args[4] == EXECUTION_ID  # execution_id IS forwarded on retries

    @pytest.mark.asyncio
    async def test_successful_scheduled_run_does_not_forward_execution_id(self, job_mocks):
        """Successful scheduled runs must not reuse execution_id for the next run.

        Regression: previously the success path passed the current execution_id
        to _schedule_next_run, which persisted it into APScheduler args. The
        next scheduled run would then overwrite the same task_executions row,
        leaving started_at from the first run and clobbering completed_at on
        every subsequent run -- producing multi-day "durations" and collapsing
        execution history onto one row per task.
        """
        job_mocks.db.fetch_one = AsyncMock(return_value=_make_task_row())
        future_time = (datetime.now(UTC) + timedelta(hours=2)).isoformat()
        job_mocks.agent.return_value = _make_agent_response(next_run=future_time)

        mock_sched = MagicMock()
        job_mocks.scheduler.return_value = mock_sched

        await _execute(TASK_ID, EXECUTION_ID, USER_ID, TASK_NAME)

        # APScheduler job args are [task_id, user_id, task_name, retry_count, execution_id]
        args = mock_sched.add_job.call_args.kwargs["args"]
        assert args[0] == TASK_ID
        assert args[3] == 0  # retry_count reset
        assert args[4] is None  # execution_id NOT forwarded

    @pytest.mark.asyncio
    async def test_execute_task_job_delegates_to_execute(self, job_mocks):
        """execute_task_job delegates to _execute with execution_id=None."""
        job_mocks.db.fetch_one = AsyncMock(return_value=_make_task_row())
        job_mocks.agent.return_value = _make_agent_response()

        with patch(f"{MODULE}.create_execution_record", new_callable=AsyncMock) as mock_create_exec:
            mock_create_exec.return_value = EXECUTION_ID

            await execute_task_job(TASK_ID, USER_ID, TASK_NAME)

            mock_create_exec.assert_awaited_once_with(TASK_ID)
            job_mocks.agent.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_execution_history_in_prompt(self, job_mocks):
        """Recent executions -> prompt includes execution history block with safety tags."""
        job_mocks.db.fetch_one = AsyncMock(return_value=_make_task_row())
        job_mocks.agent.return_value = _make_agent_response()
        job_mocks.recent_execs.return_value = [
            ExecutionRecord(
                completed_at="2026-02-05T14:30:00+00:00",
                confidence=72,
                notification=None,
                evidence="No official announcement found",
                sources=["https://macrumors.com"],
            ),
            ExecutionRecord(
                completed_at="2026-02-04T09:15:00+00:00",
                confidence=45,
                notification="Early rumors suggest September launch",
                evidence="Checked Apple newsroom",
                sources=["https://apple.com/newsroom"],
            ),
        ]

        await _execute(TASK_ID, EXECUTION_ID, USER_ID, TASK_NAME)

        prompt = job_mocks.agent.call_args[0][0]
        assert "<execution-history>" in prompt
        assert "</execution-history>" in prompt
        assert "data only" in prompt.lower()
        assert "Run 1 | 2026-02-05T14:30:00+00:00 | confidence: 72" in prompt
        assert "Evidence: No official announcement found" in prompt
        assert "Sources: https://macrumors.com" in prompt
        assert "Run 2 | 2026-02-04T09:15:00+00:00 | confidence: 45" in prompt
        assert "Notification sent: Early rumors suggest September launch" in prompt

    @pytest.mark.asyncio
    async def test_first_execution_sets_flag(self, job_mocks):
        """First successful execution -> is_first_execution=True in enriched_result."""
        job_mocks.db.fetch_one = AsyncMock(return_value=_make_task_row())
        job_mocks.agent.return_value = _make_agent_response(notification="Condition met")
        job_mocks.fetch_ctx.return_value = _make_notification_context()
        job_mocks.email.return_value = True
        job_mocks.db.fetch_val = AsyncMock(return_value=1)

        await _execute(TASK_ID, EXECUTION_ID, USER_ID, TASK_NAME)

        enriched_result = job_mocks.email.call_args[0][3]
        assert enriched_result.is_first_execution is True

    @pytest.mark.asyncio
    async def test_first_run_no_history(self, job_mocks):
        """No previous executions -> no history block in prompt."""
        job_mocks.db.fetch_one = AsyncMock(return_value=_make_task_row())
        job_mocks.agent.return_value = _make_agent_response()
        job_mocks.recent_execs.return_value = []

        await _execute(TASK_ID, EXECUTION_ID, USER_ID, TASK_NAME)

        prompt = job_mocks.agent.call_args[0][0]
        assert "Execution History" not in prompt
