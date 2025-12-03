"""Tests for TaskStateManager - schedule synchronization logic

Unit tests use mocks and run fast without external dependencies.
Integration tests use real Temporal and require TORALE_NOAUTH=1 + `just dev`.

Run tests (integration tests auto-skip if TORALE_NOAUTH not set):
    pytest tests/test_task_state.py -v

Run with integration tests:
    TORALE_NOAUTH=1 pytest tests/test_task_state.py -v
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from torale.core.task_state import TaskStateManager


@pytest.fixture
def task_data():
    """Sample task data for tests"""
    return {
        "task_id": uuid4(),
        "task_name": "Test Task",
        "user_id": uuid4(),
        "schedule": "0 9 * * *",
    }


class TestTaskStateManager:
    """Unit tests for TaskStateManager (with mocks)"""

    @pytest.mark.asyncio
    async def test_deactivate_pauses_schedule(self, task_data):
        """Test that deactivating a task pauses its Temporal schedule"""
        # Mock schedule handle with async pause method
        mock_schedule_handle = MagicMock()
        mock_schedule_handle.pause = AsyncMock(return_value=None)

        # Mock temporal client
        mock_client = MagicMock()
        mock_client.get_schedule_handle = MagicMock(return_value=mock_schedule_handle)

        # Patch _get_temporal_client as an AsyncMock
        with patch.object(
            TaskStateManager, "_get_temporal_client", AsyncMock(return_value=mock_client)
        ):
            manager = TaskStateManager()
            result = await manager.deactivate_task(task_id=task_data["task_id"], reason="manual")

        # Verify pause was called
        mock_schedule_handle.pause.assert_awaited_once()

        # Verify result
        assert result["success"] is True
        assert result["schedule_action"] == "paused"
        assert result["error"] is None

    @pytest.mark.asyncio
    async def test_activate_unpauses_schedule(self, task_data):
        """Test that activating a task unpauses its Temporal schedule"""
        # Mock schedule handle with async unpause method
        mock_schedule_handle = MagicMock()
        mock_schedule_handle.unpause = AsyncMock(return_value=None)

        # Mock temporal client
        mock_client = MagicMock()
        mock_client.get_schedule_handle = MagicMock(return_value=mock_schedule_handle)

        with patch.object(
            TaskStateManager, "_get_temporal_client", AsyncMock(return_value=mock_client)
        ):
            manager = TaskStateManager()
            result = await manager.activate_task(
                task_id=task_data["task_id"],
                task_name=task_data["task_name"],
                user_id=task_data["user_id"],
                schedule=task_data["schedule"],
            )

        # Verify unpause was called
        mock_schedule_handle.unpause.assert_awaited_once()

        # Verify result
        assert result["success"] is True
        assert result["schedule_action"] == "unpaused"
        assert result["error"] is None

    @pytest.mark.asyncio
    async def test_returns_correct_result_structure(self, task_data):
        """Test that methods return expected result dict structure"""
        mock_schedule_handle = MagicMock()
        mock_schedule_handle.pause = AsyncMock(return_value=None)

        mock_client = MagicMock()
        mock_client.get_schedule_handle = MagicMock(return_value=mock_schedule_handle)

        with patch.object(
            TaskStateManager, "_get_temporal_client", AsyncMock(return_value=mock_client)
        ):
            manager = TaskStateManager()
            result = await manager.deactivate_task(task_id=task_data["task_id"], reason="test")

        # Verify result has all expected keys
        assert "success" in result
        assert "schedule_action" in result
        assert "error" in result
        assert isinstance(result["success"], bool)
        assert isinstance(result["schedule_action"], str)



@pytest.mark.integration
class TestTaskStateManagerIntegration:
    """Integration tests with real Temporal server

    These tests verify TaskStateManager works correctly with a real Temporal instance.
    They follow the same pattern as test_sdk_integration.py and test_cli_integration.py.
    """

    @pytest.fixture
    def check_temporal_available(self):
        """Skip if dev environment not running"""
        if not os.getenv("TORALE_NOAUTH"):
            pytest.skip("TORALE_NOAUTH not set (required for integration tests)")

    @pytest.fixture
    def integration_task_data(self):
        """Task data for integration tests with unique IDs"""
        return {
            "task_id": uuid4(),
            "task_name": f"Integration Test Task {uuid4().hex[:8]}",
            "user_id": uuid4(),
            "schedule": "0 0 1 1 *",  # Jan 1st yearly - won't actually run
        }

    @pytest.mark.asyncio
    async def test_deactivate_pauses_real_schedule(
        self, check_temporal_available, integration_task_data
    ):
        """Test deactivating actually pauses a real Temporal schedule"""
        manager = TaskStateManager()

        # First create a schedule by activating
        create_result = await manager.activate_task(
            task_id=integration_task_data["task_id"],
            task_name=integration_task_data["task_name"],
            user_id=integration_task_data["user_id"],
            schedule=integration_task_data["schedule"],
        )

        assert create_result["success"] is True
        assert create_result["schedule_action"] in ["created", "unpaused"]

        # Now deactivate it
        pause_result = await manager.deactivate_task(
            task_id=integration_task_data["task_id"], reason="manual"
        )

        assert pause_result["success"] is True
        assert pause_result["schedule_action"] == "paused"

        # Verify we can query the schedule (it exists)
        from torale.core.config import settings
        from temporalio.client import Client

        if settings.temporal_api_key:
            client = await Client.connect(
                settings.temporal_host,
                namespace=settings.temporal_namespace,
                tls=True,
                api_key=settings.temporal_api_key,
            )
        else:
            client = await Client.connect(
                settings.temporal_host,
                namespace=settings.temporal_namespace,
            )

        schedule_id = f"schedule-{integration_task_data['task_id']}"
        schedule_handle = client.get_schedule_handle(schedule_id)
        desc = await schedule_handle.describe()

        # Schedule should be paused
        assert desc.schedule.state.paused is True

        # Cleanup - delete the schedule
        await schedule_handle.delete()

    @pytest.mark.asyncio
    async def test_activate_creates_real_schedule(
        self, check_temporal_available, integration_task_data
    ):
        """Test activating creates a real schedule in Temporal"""
        manager = TaskStateManager()

        # Activate (should create schedule)
        result = await manager.activate_task(
            task_id=integration_task_data["task_id"],
            task_name=integration_task_data["task_name"],
            user_id=integration_task_data["user_id"],
            schedule=integration_task_data["schedule"],
        )

        assert result["success"] is True
        assert result["schedule_action"] == "created"

        # Verify schedule exists in Temporal
        from torale.core.config import settings
        from temporalio.client import Client

        if settings.temporal_api_key:
            client = await Client.connect(
                settings.temporal_host,
                namespace=settings.temporal_namespace,
                tls=True,
                api_key=settings.temporal_api_key,
            )
        else:
            client = await Client.connect(
                settings.temporal_host,
                namespace=settings.temporal_namespace,
            )

        schedule_id = f"schedule-{integration_task_data['task_id']}"
        schedule_handle = client.get_schedule_handle(schedule_id)
        desc = await schedule_handle.describe()

        # Verify schedule properties
        assert desc.id == schedule_id
        assert desc.schedule.state.paused is False  # Should be active
        assert integration_task_data["schedule"] in str(desc.schedule.spec.cron_expressions)

        # Cleanup
        await schedule_handle.delete()

    @pytest.mark.asyncio
    async def test_reactivate_unpauses_real_schedule(
        self, check_temporal_available, integration_task_data
    ):
        """Test reactivating a paused schedule works"""
        manager = TaskStateManager()

        # Create and pause
        await manager.activate_task(
            task_id=integration_task_data["task_id"],
            task_name=integration_task_data["task_name"],
            user_id=integration_task_data["user_id"],
            schedule=integration_task_data["schedule"],
        )
        await manager.deactivate_task(
            task_id=integration_task_data["task_id"], reason="manual"
        )

        # Now reactivate
        result = await manager.activate_task(
            task_id=integration_task_data["task_id"],
            task_name=integration_task_data["task_name"],
            user_id=integration_task_data["user_id"],
            schedule=integration_task_data["schedule"],
        )

        assert result["success"] is True
        assert result["schedule_action"] == "unpaused"

        # Verify it's unpaused
        from torale.core.config import settings
        from temporalio.client import Client

        if settings.temporal_api_key:
            client = await Client.connect(
                settings.temporal_host,
                namespace=settings.temporal_namespace,
                tls=True,
                api_key=settings.temporal_api_key,
            )
        else:
            client = await Client.connect(
                settings.temporal_host,
                namespace=settings.temporal_namespace,
            )

        schedule_id = f"schedule-{integration_task_data['task_id']}"
        schedule_handle = client.get_schedule_handle(schedule_id)
        desc = await schedule_handle.describe()

        assert desc.schedule.state.paused is False

        # Cleanup
        await schedule_handle.delete()
