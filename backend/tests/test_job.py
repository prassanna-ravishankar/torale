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

TASK_ID = str(uuid4())
EXECUTION_ID = str(uuid4())
USER_ID = str(uuid4())
TASK_NAME = "Test Monitor"

MODULE = "torale.scheduler.job"

FUTURE = "2099-01-01T00:00:00Z"


def _make_task_row():
    return {
        "search_query": "iPhone release date",
        "condition_description": "Release date announced",
        "name": TASK_NAME,
        "notify_behavior": "once",
        "notification_channels": ["email"],
        "state": "active",
    }


def _make_agent_response(notification=None, evidence="no changes", next_run=FUTURE):
    return {
        "evidence": evidence,
        "notification": notification,
        "sources": ["https://example.com"],
        "confidence": "high",
        "next_run": next_run,
    }


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
        job_mocks.fetch_ctx.return_value = {"notification_channels": ["email"]}
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
        job_mocks.fetch_ctx.return_value = {"notification_channels": ["email"]}
        job_mocks.email.return_value = True

        await _execute(TASK_ID, EXECUTION_ID, USER_ID, TASK_NAME)

        job_mocks.email.assert_awaited_once()
        job_mocks.service_cls.assert_not_called()

    @pytest.mark.asyncio
    async def test_notification_failure_still_reschedules(self, job_mocks):
        """Notification raises -> execution still succeeds, next run still scheduled."""
        job_mocks.db.fetch_one = AsyncMock(return_value=_make_task_row())
        job_mocks.agent.return_value = _make_agent_response(notification="Condition met")
        job_mocks.fetch_ctx.return_value = {"notification_channels": ["email"]}
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
        job_mocks.fetch_ctx.return_value = {"notification_channels": ["email"]}
        job_mocks.email.side_effect = RuntimeError("SMTP error")

        mock_service = MagicMock()
        mock_service.complete = AsyncMock()
        job_mocks.service_cls.return_value = mock_service

        await _execute(TASK_ID, EXECUTION_ID, USER_ID, TASK_NAME)

        mock_service.complete.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_agent_failure_marks_failed(self, job_mocks):
        """call_agent raises -> execution marked failed."""
        job_mocks.db.fetch_one = AsyncMock(return_value=_make_task_row())
        job_mocks.agent.side_effect = RuntimeError("Agent unreachable")

        with pytest.raises(RuntimeError, match="Agent unreachable"):
            await _execute(TASK_ID, EXECUTION_ID, USER_ID, TASK_NAME)

        execute_calls = job_mocks.db.execute.call_args_list
        assert any("failed" in str(call) for call in execute_calls)

    @pytest.mark.asyncio
    async def test_double_failure_logged(self, job_mocks):
        """Agent raises + DB update raises -> both logged, no unhandled crash."""
        job_mocks.db.fetch_one = AsyncMock(return_value=_make_task_row())
        job_mocks.db.execute = AsyncMock(side_effect=[None, Exception("DB down")])
        job_mocks.agent.side_effect = RuntimeError("Agent error")

        with pytest.raises(RuntimeError, match="Agent error"):
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
    async def test_first_run_no_history(self, job_mocks):
        """No previous executions -> no history block in prompt."""
        job_mocks.db.fetch_one = AsyncMock(return_value=_make_task_row())
        job_mocks.agent.return_value = _make_agent_response()
        job_mocks.recent_execs.return_value = []

        await _execute(TASK_ID, EXECUTION_ID, USER_ID, TASK_NAME)

        prompt = job_mocks.agent.call_args[0][0]
        assert "Execution History" not in prompt
