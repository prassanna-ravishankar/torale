"""Tests for scheduler activities (persist_execution_result)."""

import json
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

MODULE = "torale.scheduler.activities"

TASK_ID = str(uuid4())
EXECUTION_ID = str(uuid4())


def _make_agent_result():
    return {
        "evidence": "No changes detected",
        "notification": None,
        "confidence": "high",
        "next_run": None,
        "change_summary": "No changes detected",
        "grounding_sources": [{"url": "https://example.com"}],
    }


def _setup_db_mock(mock_db):
    """Set up mock_db with acquire() -> conn with transaction() context manager."""
    mock_conn = AsyncMock()

    @asynccontextmanager
    async def fake_transaction():
        yield

    mock_conn.transaction = fake_transaction

    acq = MagicMock()
    acq.__aenter__ = AsyncMock(return_value=mock_conn)
    acq.__aexit__ = AsyncMock(return_value=False)
    mock_db.acquire.return_value = acq

    return mock_conn


class TestPersistExecutionResult:
    @pytest.mark.asyncio
    @patch(f"{MODULE}.db")
    async def test_writes_to_both_tables(self, mock_db):
        """Writes to both task_executions and tasks tables atomically."""
        mock_conn = _setup_db_mock(mock_db)

        from torale.scheduler.activities import persist_execution_result

        await persist_execution_result(TASK_ID, EXECUTION_ID, _make_agent_result())

        assert mock_conn.execute.await_count == 2
        mock_db.acquire.assert_called_once()
        first_call = mock_conn.execute.call_args_list[0]
        assert "task_executions" in first_call[0][0]
        second_call = mock_conn.execute.call_args_list[1]
        assert "tasks" in second_call[0][0]

    @pytest.mark.asyncio
    @patch(f"{MODULE}.db")
    async def test_field_mapping(self, mock_db):
        """evidence -> last_known_state, notification/change_summary/grounding_sources mapped."""
        mock_conn = _setup_db_mock(mock_db)

        agent_result = _make_agent_result()
        agent_result["evidence"] = "Price is $999"
        agent_result["notification"] = "Price dropped!"
        agent_result["change_summary"] = "Price dropped"
        agent_result["grounding_sources"] = [{"url": "https://apple.com"}]

        from torale.scheduler.activities import persist_execution_result

        await persist_execution_result(TASK_ID, EXECUTION_ID, agent_result)

        exec_call = mock_conn.execute.call_args_list[0]
        exec_args = exec_call[0]
        assert exec_args[4] == "Price dropped!"  # notification
        assert exec_args[5] == "Price dropped"  # change_summary
        assert json.loads(exec_args[6]) == [{"url": "https://apple.com"}]

        task_call = mock_conn.execute.call_args_list[1]
        task_args = task_call[0]
        assert json.loads(task_args[1]) == {"evidence": "Price is $999"}
