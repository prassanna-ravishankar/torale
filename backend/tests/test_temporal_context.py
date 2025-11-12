"""
Tests for temporal context tracking in task execution.

Temporal context allows the executor to know when the last execution occurred,
enabling better change detection and reducing false positive notifications.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from torale.workers.activities import execute_task


class TestTemporalContext:
    """Test suite for temporal context tracking in executor."""

    @pytest.mark.asyncio
    async def test_executor_receives_last_execution_time(self):
        """
        Test that executor receives last execution timestamp.

        Scenario: Task has previous execution.
        Expected: Executor config includes last_execution_time.
        """
        task_id = str(uuid4())
        execution_id = str(uuid4())

        last_execution_time = "2024-11-10T10:00:00Z"

        # Mock task with last execution
        mock_task = {
            "id": task_id,
            "executor_type": "llm_grounded_search",
            "search_query": "test query",
            "condition_description": "test condition",
            "config": json.dumps({"model": "gemini-2.0-flash-exp"}),
            "last_known_state": {"previous": "state"},
            "notify_behavior": "track_state",
        }

        # Mock last execution
        mock_last_execution = {
            "started_at": last_execution_time
        }

        mock_conn = AsyncMock()
        mock_conn.fetchrow.side_effect = [mock_task, None, mock_last_execution]
        mock_conn.execute.return_value = None

        # Mock executor to capture config
        captured_config = None

        async def capture_execute(config):
            nonlocal captured_config
            captured_config = config
            return {
                "condition_met": False,
                "change_summary": "",
                "grounding_sources": [],
                "current_state": {}
            }

        mock_executor = AsyncMock()
        mock_executor.execute.side_effect = capture_execute

        with (
            patch("torale.workers.activities.get_db_connection", return_value=mock_conn),
            patch("torale.workers.activities.GroundedSearchExecutor", return_value=mock_executor),
        ):
            await execute_task(task_id, execution_id)

        # Verify temporal context was passed
        assert captured_config is not None
        assert "last_execution_time" in captured_config
        assert captured_config["last_execution_time"] == last_execution_time

    @pytest.mark.asyncio
    async def test_executor_handles_no_previous_execution(self):
        """
        Test that executor works when there's no previous execution.

        Scenario: First-time task execution.
        Expected: Executor config doesn't include last_execution_time.
        """
        task_id = str(uuid4())
        execution_id = str(uuid4())

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
        # No last execution found
        mock_conn.fetchrow.side_effect = [mock_task, None, None]
        mock_conn.execute.return_value = None

        captured_config = None

        async def capture_execute(config):
            nonlocal captured_config
            captured_config = config
            return {
                "condition_met": False,
                "change_summary": "",
                "grounding_sources": [],
                "current_state": {}
            }

        mock_executor = AsyncMock()
        mock_executor.execute.side_effect = capture_execute

        with (
            patch("torale.workers.activities.get_db_connection", return_value=mock_conn),
            patch("torale.workers.activities.GroundedSearchExecutor", return_value=mock_executor),
        ):
            await execute_task(task_id, execution_id)

        # Should work fine without last_execution_time
        assert captured_config is not None
        assert "last_execution_time" not in captured_config or captured_config.get("last_execution_time") is None

    @pytest.mark.asyncio
    async def test_temporal_context_with_track_state_behavior(self):
        """
        Test temporal context is provided for track_state notify behavior.

        Scenario: Task uses track_state notification behavior.
        Expected: Executor receives temporal context for change detection.
        """
        task_id = str(uuid4())
        execution_id = str(uuid4())
        last_execution_time = "2024-11-10T10:00:00Z"

        mock_task = {
            "id": task_id,
            "executor_type": "llm_grounded_search",
            "search_query": "test query",
            "condition_description": "test condition",
            "config": json.dumps({"model": "gemini-2.0-flash-exp"}),
            "last_known_state": {"previous": "info"},
            "notify_behavior": "track_state",  # Important: track_state behavior
        }

        mock_last_execution = {"started_at": last_execution_time}

        mock_conn = AsyncMock()
        mock_conn.fetchrow.side_effect = [mock_task, None, mock_last_execution]
        mock_conn.execute.return_value = None

        captured_config = None

        async def capture_execute(config):
            nonlocal captured_config
            captured_config = config
            return {
                "condition_met": True,
                "change_summary": "Information changed",
                "grounding_sources": [],
                "current_state": {"new": "info"}
            }

        mock_executor = AsyncMock()
        mock_executor.execute.side_effect = capture_execute

        with (
            patch("torale.workers.activities.get_db_connection", return_value=mock_conn),
            patch("torale.workers.activities.GroundedSearchExecutor", return_value=mock_executor),
        ):
            await execute_task(task_id, execution_id)

        # Temporal context should be provided for change detection
        assert captured_config is not None
        assert captured_config.get("last_execution_time") == last_execution_time
        assert captured_config.get("last_known_state") == {"previous": "info"}


class TestRunImmediately:
    """Test suite for run_immediately flag."""

    @pytest.mark.asyncio
    async def test_create_task_with_run_immediately(self):
        """
        Test that task with run_immediately=True triggers instant execution.

        Scenario: User creates task with run_immediately flag.
        Expected: Task is created AND workflow is started immediately.
        """
        from torale.api.routers.tasks import create_task
        from torale.core.database import Database
        from torale.core.models import TaskCreate

        task_id = uuid4()
        user_id = uuid4()

        mock_user = MagicMock()
        mock_user.id = user_id

        # Mock database
        mock_db = AsyncMock(spec=Database)
        mock_db.fetch_one.side_effect = [
            {"id": task_id, "name": "Test", "user_id": user_id, "is_active": True},  # Task creation
            {"id": uuid4()},  # Execution creation
        ]

        # Mock Temporal client
        mock_client = AsyncMock()
        mock_client.start_workflow.return_value = MagicMock(id="workflow-123")

        task_data = TaskCreate(
            name="Test Task",
            search_query="test query",
            condition_description="test condition",
            schedule="0 9 * * *",
            run_immediately=True
        )

        with patch("torale.api.routers.tasks.get_temporal_client", return_value=mock_client):
            await create_task(task_data, mock_user, mock_db)

        # Should start workflow
        assert mock_client.start_workflow.called
        # Workflow should have suppress_notifications=True for immediate execution
        call_kwargs = mock_client.start_workflow.call_args.kwargs
        assert call_kwargs.get("suppress_notifications") is True
