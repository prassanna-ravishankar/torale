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


def _mock_db(task_row):
    """Return a mock db with fetch_one returning task_row on second call."""
    mock = MagicMock()
    mock.execute = AsyncMock()
    # First call: UPDATE status to running (no return needed)
    # Second call: SELECT task row
    mock.fetch_one = AsyncMock(side_effect=[None, task_row])
    return mock


class TestExecute:
    @pytest.mark.asyncio
    @patch(f"{MODULE}.TaskService")
    @patch(f"{MODULE}.get_scheduler")
    @patch(f"{MODULE}.send_webhook_notification", new_callable=AsyncMock)
    @patch(f"{MODULE}.send_email_notification", new_callable=AsyncMock)
    @patch(f"{MODULE}.fetch_notification_context", new_callable=AsyncMock)
    @patch(f"{MODULE}.persist_execution_result", new_callable=AsyncMock)
    @patch(f"{MODULE}.call_agent", new_callable=AsyncMock)
    @patch(f"{MODULE}.db")
    async def test_condition_not_met(
        self,
        mock_db,
        mock_agent,
        mock_persist,
        mock_fetch_ctx,
        mock_email,
        mock_webhook,
        mock_scheduler,
        mock_service_cls,
    ):
        """Agent returns no notification -> no notifications sent, no completion."""
        mock_db.execute = AsyncMock()
        mock_db.fetch_one = AsyncMock(return_value=_make_task_row())
        mock_agent.return_value = _make_agent_response(notification=None)

        from torale.scheduler.job import _execute

        await _execute(TASK_ID, EXECUTION_ID, USER_ID, TASK_NAME)

        mock_persist.assert_awaited_once()
        agent_result = mock_persist.call_args.kwargs["agent_result"]
        assert agent_result["condition_met"] is False
        mock_email.assert_not_awaited()
        mock_webhook.assert_not_awaited()
        mock_service_cls.assert_not_called()

    @pytest.mark.asyncio
    @patch(f"{MODULE}.TaskService")
    @patch(f"{MODULE}.get_scheduler")
    @patch(f"{MODULE}.send_webhook_notification", new_callable=AsyncMock)
    @patch(f"{MODULE}.send_email_notification", new_callable=AsyncMock)
    @patch(f"{MODULE}.fetch_notification_context", new_callable=AsyncMock)
    @patch(f"{MODULE}.persist_execution_result", new_callable=AsyncMock)
    @patch(f"{MODULE}.call_agent", new_callable=AsyncMock)
    @patch(f"{MODULE}.db")
    async def test_condition_met_once_completes(
        self,
        mock_db,
        mock_agent,
        mock_persist,
        mock_fetch_ctx,
        mock_email,
        mock_webhook,
        mock_scheduler,
        mock_service_cls,
    ):
        """notify_behavior=once + condition met -> notification sent + task completed."""
        mock_db.execute = AsyncMock()
        mock_db.fetch_one = AsyncMock(return_value=_make_task_row(notify_behavior="once"))
        mock_agent.return_value = _make_agent_response(notification="Release date is Sept 9")
        mock_fetch_ctx.return_value = {"notification_channels": ["email"]}
        mock_email.return_value = True

        mock_service = MagicMock()
        mock_service.complete = AsyncMock()
        mock_service_cls.return_value = mock_service

        from torale.scheduler.job import _execute

        await _execute(TASK_ID, EXECUTION_ID, USER_ID, TASK_NAME)

        mock_email.assert_awaited_once()
        mock_service.complete.assert_awaited_once()

    @pytest.mark.asyncio
    @patch(f"{MODULE}.TaskService")
    @patch(f"{MODULE}.get_scheduler")
    @patch(f"{MODULE}.send_webhook_notification", new_callable=AsyncMock)
    @patch(f"{MODULE}.send_email_notification", new_callable=AsyncMock)
    @patch(f"{MODULE}.fetch_notification_context", new_callable=AsyncMock)
    @patch(f"{MODULE}.persist_execution_result", new_callable=AsyncMock)
    @patch(f"{MODULE}.call_agent", new_callable=AsyncMock)
    @patch(f"{MODULE}.db")
    async def test_condition_met_always_no_complete(
        self,
        mock_db,
        mock_agent,
        mock_persist,
        mock_fetch_ctx,
        mock_email,
        mock_webhook,
        mock_scheduler,
        mock_service_cls,
    ):
        """notify_behavior=always + condition met -> notification sent, NOT completed."""
        mock_db.execute = AsyncMock()
        mock_db.fetch_one = AsyncMock(return_value=_make_task_row(notify_behavior="always"))
        mock_agent.return_value = _make_agent_response(notification="Price dropped")
        mock_fetch_ctx.return_value = {"notification_channels": ["email"]}
        mock_email.return_value = True

        from torale.scheduler.job import _execute

        await _execute(TASK_ID, EXECUTION_ID, USER_ID, TASK_NAME)

        mock_email.assert_awaited_once()
        mock_service_cls.assert_not_called()

    @pytest.mark.asyncio
    @patch(f"{MODULE}.TaskService")
    @patch(f"{MODULE}.get_scheduler")
    @patch(f"{MODULE}.send_webhook_notification", new_callable=AsyncMock)
    @patch(f"{MODULE}.send_email_notification", new_callable=AsyncMock)
    @patch(f"{MODULE}.fetch_notification_context", new_callable=AsyncMock)
    @patch(f"{MODULE}.persist_execution_result", new_callable=AsyncMock)
    @patch(f"{MODULE}.call_agent", new_callable=AsyncMock)
    @patch(f"{MODULE}.db")
    async def test_notification_failure_blocks_complete(
        self,
        mock_db,
        mock_agent,
        mock_persist,
        mock_fetch_ctx,
        mock_email,
        mock_webhook,
        mock_scheduler,
        mock_service_cls,
    ):
        """Notification raises -> task NOT completed."""
        mock_db.execute = AsyncMock()
        mock_db.fetch_one = AsyncMock(return_value=_make_task_row(notify_behavior="once"))
        mock_agent.return_value = _make_agent_response(notification="Condition met")
        mock_fetch_ctx.return_value = {"notification_channels": ["email"]}
        mock_email.side_effect = RuntimeError("SMTP error")

        from torale.scheduler.job import _execute

        await _execute(TASK_ID, EXECUTION_ID, USER_ID, TASK_NAME)

        mock_service_cls.assert_not_called()

    @pytest.mark.asyncio
    @patch(f"{MODULE}.TaskService")
    @patch(f"{MODULE}.get_scheduler")
    @patch(f"{MODULE}.send_webhook_notification", new_callable=AsyncMock)
    @patch(f"{MODULE}.send_email_notification", new_callable=AsyncMock)
    @patch(f"{MODULE}.fetch_notification_context", new_callable=AsyncMock)
    @patch(f"{MODULE}.persist_execution_result", new_callable=AsyncMock)
    @patch(f"{MODULE}.call_agent", new_callable=AsyncMock)
    @patch(f"{MODULE}.db")
    async def test_agent_failure_marks_failed(
        self,
        mock_db,
        mock_agent,
        mock_persist,
        mock_fetch_ctx,
        mock_email,
        mock_webhook,
        mock_scheduler,
        mock_service_cls,
    ):
        """call_agent raises -> execution marked failed."""
        mock_db.execute = AsyncMock()
        mock_db.fetch_one = AsyncMock(return_value=_make_task_row())
        mock_agent.side_effect = RuntimeError("Agent unreachable")

        from torale.scheduler.job import _execute

        with pytest.raises(RuntimeError, match="Agent unreachable"):
            await _execute(TASK_ID, EXECUTION_ID, USER_ID, TASK_NAME)

        # Should have tried to mark execution as failed
        fail_call = mock_db.execute.call_args_list[-1]
        assert "failed" in str(fail_call)

    @pytest.mark.asyncio
    @patch(f"{MODULE}.TaskService")
    @patch(f"{MODULE}.get_scheduler")
    @patch(f"{MODULE}.send_webhook_notification", new_callable=AsyncMock)
    @patch(f"{MODULE}.send_email_notification", new_callable=AsyncMock)
    @patch(f"{MODULE}.fetch_notification_context", new_callable=AsyncMock)
    @patch(f"{MODULE}.persist_execution_result", new_callable=AsyncMock)
    @patch(f"{MODULE}.call_agent", new_callable=AsyncMock)
    @patch(f"{MODULE}.db")
    async def test_double_failure_logged(
        self,
        mock_db,
        mock_agent,
        mock_persist,
        mock_fetch_ctx,
        mock_email,
        mock_webhook,
        mock_scheduler,
        mock_service_cls,
    ):
        """Agent raises + DB update raises -> both logged, no unhandled crash."""
        mock_db.fetch_one = AsyncMock(return_value=_make_task_row())
        # First execute call succeeds (set running), second fails (mark failed)
        mock_db.execute = AsyncMock(side_effect=[None, Exception("DB down")])
        mock_agent.side_effect = RuntimeError("Agent error")

        from torale.scheduler.job import _execute

        with pytest.raises(RuntimeError, match="Agent error"):
            await _execute(TASK_ID, EXECUTION_ID, USER_ID, TASK_NAME)

    @pytest.mark.asyncio
    @patch(f"{MODULE}.TaskService")
    @patch(f"{MODULE}.get_scheduler")
    @patch(f"{MODULE}.send_webhook_notification", new_callable=AsyncMock)
    @patch(f"{MODULE}.send_email_notification", new_callable=AsyncMock)
    @patch(f"{MODULE}.fetch_notification_context", new_callable=AsyncMock)
    @patch(f"{MODULE}.persist_execution_result", new_callable=AsyncMock)
    @patch(f"{MODULE}.call_agent", new_callable=AsyncMock)
    @patch(f"{MODULE}.db")
    async def test_dynamic_reschedule(
        self,
        mock_db,
        mock_agent,
        mock_persist,
        mock_fetch_ctx,
        mock_email,
        mock_webhook,
        mock_scheduler,
        mock_service_cls,
    ):
        """Agent returns next_run -> scheduler.modify_job called with correct datetime."""
        mock_db.execute = AsyncMock()
        mock_db.fetch_one = AsyncMock(return_value=_make_task_row(notify_behavior="always"))
        future_time = (datetime.now(UTC) + timedelta(hours=2)).isoformat()
        mock_agent.return_value = _make_agent_response(notification=None, next_run=future_time)

        mock_sched = MagicMock()
        mock_scheduler.return_value = mock_sched

        from torale.scheduler.job import _execute

        await _execute(TASK_ID, EXECUTION_ID, USER_ID, TASK_NAME)

        mock_sched.modify_job.assert_called_once()
        call_kwargs = mock_sched.modify_job.call_args
        assert call_kwargs[0][0] == f"task-{TASK_ID}"

    @pytest.mark.asyncio
    @patch(f"{MODULE}.create_execution_record", new_callable=AsyncMock)
    @patch(f"{MODULE}.TaskService")
    @patch(f"{MODULE}.get_scheduler")
    @patch(f"{MODULE}.send_webhook_notification", new_callable=AsyncMock)
    @patch(f"{MODULE}.send_email_notification", new_callable=AsyncMock)
    @patch(f"{MODULE}.fetch_notification_context", new_callable=AsyncMock)
    @patch(f"{MODULE}.persist_execution_result", new_callable=AsyncMock)
    @patch(f"{MODULE}.call_agent", new_callable=AsyncMock)
    @patch(f"{MODULE}.db")
    async def test_execute_task_job_delegates_to_execute(
        self,
        mock_db,
        mock_agent,
        mock_persist,
        mock_fetch_ctx,
        mock_email,
        mock_webhook,
        mock_scheduler,
        mock_service_cls,
        mock_create_exec,
    ):
        """execute_task_job delegates to _execute with execution_id=None."""
        mock_db.execute = AsyncMock()
        mock_db.fetch_one = AsyncMock(return_value=_make_task_row())
        mock_agent.return_value = _make_agent_response()
        mock_create_exec.return_value = EXECUTION_ID

        from torale.scheduler.job import execute_task_job

        await execute_task_job(TASK_ID, USER_ID, TASK_NAME)

        # Should have called create_execution_record since execution_id=None
        mock_create_exec.assert_awaited_once_with(TASK_ID)
        mock_agent.assert_awaited_once()

    @pytest.mark.asyncio
    @patch(f"{MODULE}.TaskService")
    @patch(f"{MODULE}.get_scheduler")
    @patch(f"{MODULE}.send_webhook_notification", new_callable=AsyncMock)
    @patch(f"{MODULE}.send_email_notification", new_callable=AsyncMock)
    @patch(f"{MODULE}.fetch_notification_context", new_callable=AsyncMock)
    @patch(f"{MODULE}.persist_execution_result", new_callable=AsyncMock)
    @patch(f"{MODULE}.call_agent", new_callable=AsyncMock)
    @patch(f"{MODULE}.db")
    async def test_last_known_state_in_prompt(
        self,
        mock_db,
        mock_agent,
        mock_persist,
        mock_fetch_ctx,
        mock_email,
        mock_webhook,
        mock_scheduler,
        mock_service_cls,
    ):
        """Task with last_known_state -> prompt includes previous evidence."""
        mock_db.execute = AsyncMock()
        mock_db.fetch_one = AsyncMock(
            return_value=_make_task_row(last_known_state="No announcement yet")
        )
        mock_agent.return_value = _make_agent_response()

        from torale.scheduler.job import _execute

        await _execute(TASK_ID, EXECUTION_ID, USER_ID, TASK_NAME)

        prompt = mock_agent.call_args[0][0]
        assert "Previous evidence: No announcement yet" in prompt
