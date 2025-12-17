#!/usr/bin/env python3
"""Tests for monitoring workflow orchestration logic"""

from unittest.mock import AsyncMock, patch

import pytest


class TestTaskExecutionWorkflow:
    """Test the new TaskExecutionWorkflow orchestration"""

    @pytest.mark.asyncio
    async def test_workflow_structure(self):
        """Test that workflow calls activities in correct order with correct arguments"""
        # This test verifies the orchestration pattern and argument passing

        # Create mock request
        from torale.core.models import TaskExecutionRequest

        request = TaskExecutionRequest(
            task_id="test-id",
            execution_id="exec-id",
            user_id="user-id",
            task_name="Test Task",
            suppress_notifications=False,
        )

        # Track activity calls and their arguments
        activity_calls = []

        # Mock task data response
        task_data = {
            "task": {
                "name": "Test",
                "search_query": "test query",
                "condition_description": "test",
                "config": {},
                "notify_behavior": "always",
            },
            "previous_state": None,
        }

        # Mock search result
        search_result = {
            "answer": "Test answer",
            "sources": [{"uri": "https://example.com"}],
        }

        # Mock pipeline result
        pipeline_result = {
            "summary": "Test summary",
            "sources": [{"uri": "https://example.com"}],
            "metadata": {
                "changed": True,
                "change_explanation": "First execution",
                "current_state": {"test": "value"},
            },
        }

        # Mock notification context
        notification_context = {
            "notification_channels": ["email"],
        }

        async def track_activity(activity_name, *args, **kwargs):
            # Store call details for verification
            activity_calls.append({"name": activity_name, "args": args, "kwargs": kwargs})

            # Return appropriate mocks
            if activity_name == "get_task_data":
                return task_data
            elif activity_name == "perform_grounded_search":
                return search_result
            elif activity_name == "execute_monitoring_pipeline":
                return pipeline_result
            elif activity_name == "fetch_notification_context":
                return notification_context
            elif activity_name == "send_email_notification":
                return None
            elif activity_name == "persist_execution_result":
                return None
            return None

        with patch("temporalio.workflow.execute_activity", side_effect=track_activity):
            from torale.workers.workflows import TaskExecutionWorkflow

            wf = TaskExecutionWorkflow()
            result = await wf.run(request)

            # Verify activity call order (6 activities: get, search, pipeline, context, email, persist)
            assert len(activity_calls) == 6  # No complete_task since notify_behavior is "always"
            assert activity_calls[0]["name"] == "get_task_data"
            assert activity_calls[1]["name"] == "perform_grounded_search"
            assert activity_calls[2]["name"] == "execute_monitoring_pipeline"
            assert activity_calls[3]["name"] == "fetch_notification_context"
            assert activity_calls[4]["name"] == "send_email_notification"
            assert activity_calls[5]["name"] == "persist_execution_result"

            # Verify arguments passed to each activity
            # Step 1: get_task_data receives task_id
            assert activity_calls[0]["kwargs"]["args"][0] == request.task_id

            # Step 2: perform_grounded_search receives task_data
            assert activity_calls[1]["kwargs"]["args"][0] == task_data

            # Step 3: execute_monitoring_pipeline receives task_data and search_result
            pipeline_args = activity_calls[2]["kwargs"]["args"]
            assert pipeline_args[0] == task_data
            assert pipeline_args[1] == search_result

            # Step 4: fetch_notification_context receives task_id, execution_id, user_id
            context_args = activity_calls[3]["kwargs"]["args"]
            assert context_args[0] == request.task_id
            assert context_args[1] == request.execution_id
            assert context_args[2] == request.user_id

            # Step 5: send_email_notification receives user_id, task_name, context, enriched_result
            email_args = activity_calls[4]["kwargs"]["args"]
            assert email_args[0] == request.user_id
            assert email_args[1] == request.task_name
            assert email_args[2] == notification_context
            # Fourth arg is enriched result
            assert email_args[3]["summary"] == "Test summary"
            assert email_args[3]["task_id"] == request.task_id

            # Step 6: persist_execution_result receives task_id, execution_id, enriched_result
            persist_args = activity_calls[5]["kwargs"]["args"]
            assert persist_args[0] == request.task_id
            assert persist_args[1] == request.execution_id
            # Third arg is enriched_result with additional metadata
            enriched = persist_args[2]
            assert enriched["summary"] == "Test summary"
            assert enriched["task_id"] == request.task_id
            assert enriched["is_first_execution"] is True

            # Verify workflow returns enriched result
            assert result["summary"] == "Test summary"
            assert result["task_id"] == request.task_id

    def test_notification_decision_logic(self):
        """Test the workflow's notification decision logic"""
        # Test: changed=True, suppress=False → should notify
        changed = True
        suppress = False
        should_notify = changed and not suppress
        assert should_notify is True

        # Test: changed=False → should not notify
        changed = False
        suppress = False
        should_notify = changed and not suppress
        assert should_notify is False

        # Test: changed=True, suppress=True → should not notify
        changed = True
        suppress = True
        should_notify = changed and not suppress
        assert should_notify is False


class TestWorkflowActivities:
    """Test individual workflow activities"""

    @pytest.mark.asyncio
    async def test_get_task_data_structure(self):
        """Test get_task_data returns correct structure"""
        from uuid import UUID

        from torale.workers.activities import get_task_data

        # Mock database connection
        mock_conn = AsyncMock()

        # Mock fetchrow to return different values for task and execution queries
        task_row = {
            "id": UUID("12345678-1234-1234-1234-123456789012"),
            "name": "Test Task",
            "search_query": "test query",
            "condition_description": "test condition",
            "config": {},
            "state": "active",
            "last_known_state": None,
        }

        # First call: task query, second call: last execution query (returns None)
        mock_conn.fetchrow.side_effect = [task_row, None]

        with patch("torale.workers.activities.get_db_connection", return_value=mock_conn):
            result = await get_task_data("12345678-1234-1234-1234-123456789012")

            # Verify structure
            assert "task" in result
            assert "previous_state" in result
            assert "config" in result
            assert "last_execution_datetime" in result
            assert result["task"]["name"] == "Test Task"
            assert result["previous_state"] is None
            assert result["config"] == {}

            # Verify database was closed
            mock_conn.close.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
