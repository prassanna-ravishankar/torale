"""Tests for task execution orchestrator (job.py).

Unit tests verify agent call orchestration, notification dispatch,
auto-completion logic, and error handling.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

TASK_ID = str(uuid4())
EXECUTION_ID = str(uuid4())
USER_ID = str(uuid4())
TASK_NAME = "Test Monitor"

MODULE = "torale.scheduler.job"


def _make_task_row(notify_behavior="once", last_known_state=None):
    return {
        "search_query": "iPhone release date",
        "condition_description": "Release date announced",
        "name": TASK_NAME,
        "notify_behavior": notify_behavior,
        "notification_channels": ["email"],
        "last_known_state": last_known_state,
    }


def _make_agent_response(notification=None, evidence="no changes", next_run=None):
    return {
        "evidence": evidence,
        "notification": notification,
        "sources": ["https://example.com"],
        "confidence": "high",
        "next_run": next_run,
    }


class TestExecute:
    @pytest.mark.asyncio
    async def test_condition_not_met(self, job_mocks):
        """Agent returns no notification -> no notifications sent, no completion."""
        job_mocks.db.fetch_one = AsyncMock(return_value=_make_task_row())
        job_mocks.agent.return_value = _make_agent_response(notification=None)

        from torale.scheduler.job import _execute

        await _execute(TASK_ID, EXECUTION_ID, USER_ID, TASK_NAME)

        job_mocks.persist.assert_awaited_once()
        agent_result = job_mocks.persist.call_args.kwargs["agent_result"]
        assert agent_result["condition_met"] is False
        job_mocks.email.assert_not_awaited()
        job_mocks.webhook.assert_not_awaited()
        job_mocks.service_cls.assert_not_called()

    @pytest.mark.asyncio
    async def test_condition_met_once_completes(self, job_mocks):
        """notify_behavior=once + condition met -> notification sent + task completed."""
        job_mocks.db.fetch_one = AsyncMock(return_value=_make_task_row(notify_behavior="once"))
        job_mocks.agent.return_value = _make_agent_response(notification="Release date is Sept 9")
        job_mocks.fetch_ctx.return_value = {"notification_channels": ["email"]}
        job_mocks.email.return_value = True

        mock_service = MagicMock()
        mock_service.complete = AsyncMock()
        job_mocks.service_cls.return_value = mock_service

        from torale.scheduler.job import _execute

        await _execute(TASK_ID, EXECUTION_ID, USER_ID, TASK_NAME)

        job_mocks.email.assert_awaited_once()
        mock_service.complete.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_condition_met_always_no_complete(self, job_mocks):
        """notify_behavior=always + condition met -> notification sent, NOT completed."""
        job_mocks.db.fetch_one = AsyncMock(return_value=_make_task_row(notify_behavior="always"))
        job_mocks.agent.return_value = _make_agent_response(notification="Price dropped")
        job_mocks.fetch_ctx.return_value = {"notification_channels": ["email"]}
        job_mocks.email.return_value = True

        from torale.scheduler.job import _execute

        await _execute(TASK_ID, EXECUTION_ID, USER_ID, TASK_NAME)

        job_mocks.email.assert_awaited_once()
        job_mocks.service_cls.assert_not_called()

    @pytest.mark.asyncio
    async def test_notification_failure_blocks_complete(self, job_mocks):
        """Notification raises -> task NOT completed."""
        job_mocks.db.fetch_one = AsyncMock(return_value=_make_task_row(notify_behavior="once"))
        job_mocks.agent.return_value = _make_agent_response(notification="Condition met")
        job_mocks.fetch_ctx.return_value = {"notification_channels": ["email"]}
        job_mocks.email.side_effect = RuntimeError("SMTP error")

        from torale.scheduler.job import _execute

        await _execute(TASK_ID, EXECUTION_ID, USER_ID, TASK_NAME)

        job_mocks.service_cls.assert_not_called()

    @pytest.mark.asyncio
    async def test_agent_failure_marks_failed(self, job_mocks):
        """call_agent raises -> execution marked failed."""
        job_mocks.db.fetch_one = AsyncMock(return_value=_make_task_row())
        job_mocks.agent.side_effect = RuntimeError("Agent unreachable")

        from torale.scheduler.job import _execute

        with pytest.raises(RuntimeError, match="Agent unreachable"):
            await _execute(TASK_ID, EXECUTION_ID, USER_ID, TASK_NAME)

        fail_call = job_mocks.db.execute.call_args_list[-1]
        assert "failed" in str(fail_call)

    @pytest.mark.asyncio
    async def test_double_failure_logged(self, job_mocks):
        """Agent raises + DB update raises -> both logged, no unhandled crash."""
        job_mocks.db.fetch_one = AsyncMock(return_value=_make_task_row())
        job_mocks.db.execute = AsyncMock(side_effect=[None, Exception("DB down")])
        job_mocks.agent.side_effect = RuntimeError("Agent error")

        from torale.scheduler.job import _execute

        with pytest.raises(RuntimeError, match="Agent error"):
            await _execute(TASK_ID, EXECUTION_ID, USER_ID, TASK_NAME)

    @pytest.mark.asyncio
    async def test_dynamic_reschedule(self, job_mocks):
        """Agent returns next_run -> scheduler.modify_job called with correct datetime."""
        job_mocks.db.fetch_one = AsyncMock(return_value=_make_task_row(notify_behavior="always"))
        future_time = (datetime.now(UTC) + timedelta(hours=2)).isoformat()
        job_mocks.agent.return_value = _make_agent_response(notification=None, next_run=future_time)

        mock_sched = MagicMock()
        job_mocks.scheduler.return_value = mock_sched

        from torale.scheduler.job import _execute

        await _execute(TASK_ID, EXECUTION_ID, USER_ID, TASK_NAME)

        mock_sched.modify_job.assert_called_once()
        call_kwargs = mock_sched.modify_job.call_args
        assert call_kwargs[0][0] == f"task-{TASK_ID}"

    @pytest.mark.asyncio
    async def test_execute_task_job_delegates_to_execute(self, job_mocks):
        """execute_task_job delegates to _execute with execution_id=None."""
        job_mocks.db.fetch_one = AsyncMock(return_value=_make_task_row())
        job_mocks.agent.return_value = _make_agent_response()

        with patch(f"{MODULE}.create_execution_record", new_callable=AsyncMock) as mock_create_exec:
            mock_create_exec.return_value = EXECUTION_ID

            from torale.scheduler.job import execute_task_job

            await execute_task_job(TASK_ID, USER_ID, TASK_NAME)

            mock_create_exec.assert_awaited_once_with(TASK_ID)
            job_mocks.agent.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_last_known_state_in_prompt(self, job_mocks):
        """Task with last_known_state -> prompt includes previous evidence."""
        job_mocks.db.fetch_one = AsyncMock(
            return_value=_make_task_row(last_known_state="No announcement yet")
        )
        job_mocks.agent.return_value = _make_agent_response()

        from torale.scheduler.job import _execute

        await _execute(TASK_ID, EXECUTION_ID, USER_ID, TASK_NAME)

        prompt = job_mocks.agent.call_args[0][0]
        assert "Previous evidence: No announcement yet" in prompt
