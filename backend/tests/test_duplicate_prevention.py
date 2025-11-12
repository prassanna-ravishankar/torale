"""
Tests for duplicate execution prevention logic.

The system prevents race conditions by checking for recent running executions
before starting new ones. This ensures tasks don't execute multiple times
concurrently when triggered rapidly.
"""

import json
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from torale.workers.activities import execute_task


class TestDuplicateExecutionPrevention:
    """Test suite for duplicate execution prevention logic."""

    @pytest.mark.asyncio
    async def test_skips_duplicate_within_30_seconds(self):
        """
        Test that duplicate execution is prevented within 30-second window.

        Scenario: Task execution triggered twice within 30 seconds.
        Expected: Second execution is skipped with appropriate message.
        """
        task_id = str(uuid4())
        execution_id = str(uuid4())
        recent_execution_id = str(uuid4())

        # Mock task data
        mock_task = {
            "id": task_id,
            "executor_type": "llm_grounded_search",
            "search_query": "test query",
            "condition_description": "test condition",
            "config": json.dumps({"model": "gemini-2.0-flash-exp"}),
        }

        # Mock recent running execution (within 30 seconds)
        recent_execution = {
            "id": recent_execution_id,
            "started_at": "2024-01-01 12:00:00",
            "status": "running"
        }

        mock_conn = AsyncMock()
        # First call: get task, Second call: check recent running (found!)
        mock_conn.fetchrow.side_effect = [mock_task, recent_execution]

        with patch("torale.workers.activities.get_db_connection", return_value=mock_conn):
            result = await execute_task(task_id, execution_id)

        # Should skip execution
        assert result["status"] == "skipped"
        assert result["reason"] == "Recent execution already in progress"
        assert result["existing_execution_id"] == recent_execution_id

    @pytest.mark.asyncio
    async def test_allows_execution_after_30_seconds(self):
        """
        Test that execution is allowed after 30-second window expires.

        Scenario: Last execution was more than 30 seconds ago.
        Expected: New execution proceeds normally.
        """
        task_id = str(uuid4())
        execution_id = str(uuid4())

        # Mock task data
        mock_task = {
            "id": task_id,
            "executor_type": "llm_grounded_search",
            "search_query": "test query",
            "condition_description": "test condition",
            "config": json.dumps({"model": "gemini-2.0-flash-exp"}),
            "last_known_state": None,
            "notify_behavior": "once",
        }

        mock_conn = AsyncMock()
        # No recent running execution found
        mock_conn.fetchrow.side_effect = [mock_task, None, None]
        mock_conn.execute.return_value = None

        # Mock executor
        mock_executor_result = {
            "condition_met": False,
            "change_summary": "",
            "grounding_sources": [],
            "current_state": {}
        }

        mock_executor = AsyncMock()
        mock_executor.execute.return_value = mock_executor_result

        with (
            patch("torale.workers.activities.get_db_connection", return_value=mock_conn),
            patch("torale.workers.activities.GroundedSearchExecutor", return_value=mock_executor),
        ):
            result = await execute_task(task_id, execution_id)

        # Should execute normally
        assert result == mock_executor_result
        assert result.get("status") != "skipped"

    @pytest.mark.asyncio
    async def test_handles_pending_executions(self):
        """
        Test that pending executions are also considered duplicates.

        Scenario: A pending execution exists (not yet running).
        Expected: New execution is skipped.
        """
        task_id = str(uuid4())
        execution_id = str(uuid4())
        pending_execution_id = str(uuid4())

        mock_task = {
            "id": task_id,
            "executor_type": "llm_grounded_search",
            "search_query": "test query",
            "condition_description": "test condition",
            "config": json.dumps({"model": "gemini-2.0-flash-exp"}),
        }

        # Mock pending execution
        pending_execution = {
            "id": pending_execution_id,
            "started_at": None,  # Pending executions have NULL started_at
            "status": "pending"
        }

        mock_conn = AsyncMock()
        mock_conn.fetchrow.side_effect = [mock_task, pending_execution]

        with patch("torale.workers.activities.get_db_connection", return_value=mock_conn):
            result = await execute_task(task_id, execution_id)

        # Should skip execution
        assert result["status"] == "skipped"
        assert result["existing_execution_id"] == pending_execution_id
