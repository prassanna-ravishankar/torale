"""Tests for TaskService - state transition and orchestration logic

Unit tests verify that TaskService validates transitions and orchestrates DB+Temporal correctly.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from torale.tasks import InvalidTransitionError, TaskService, TaskState


@pytest.fixture
def mock_db_conn():
    """Mock database connection"""
    conn = MagicMock()
    # Return PostgreSQL-style result string indicating 1 row was updated
    conn.execute = AsyncMock(return_value="UPDATE 1")
    return conn


@pytest.fixture
def task_data():
    """Sample task data for tests"""
    return {
        "task_id": uuid4(),
        "task_name": "Test Task",
        "user_id": uuid4(),
        "schedule": "0 9 * * *",
    }


class TestTaskService:
    """Unit tests for TaskService state transition logic"""

    @pytest.mark.asyncio
    async def test_valid_transition_active_to_paused(self, mock_db_conn, task_data):
        """Test that ACTIVE → PAUSED is a valid transition"""
        # Mock _set_temporal_state to avoid actual Temporal calls
        with patch.object(
            TaskService, "_set_temporal_state", new_callable=AsyncMock
        ) as mock_set_temporal:
            mock_set_temporal.return_value = {
                "success": True,
                "schedule_action": "paused",
                "error": None,
            }

            service = TaskService(db=mock_db_conn)
            result = await service.transition(
                task_id=task_data["task_id"],
                from_state=TaskState.ACTIVE,
                to_state=TaskState.PAUSED,
            )

            # Should succeed
            assert result["success"] is True
            # DB update called
            mock_db_conn.execute.assert_awaited_once()
            # Temporal update called with correct args
            mock_set_temporal.assert_awaited_once_with(
                task_data["task_id"],
                is_active=False,
            )

    @pytest.mark.asyncio
    async def test_valid_transition_active_to_completed(self, mock_db_conn, task_data):
        """Test that ACTIVE → COMPLETED is a valid transition and deletes schedule"""
        with patch.object(
            TaskService, "_delete_schedule", new_callable=AsyncMock
        ) as mock_delete_schedule:
            mock_delete_schedule.return_value = {
                "success": True,
                "schedule_action": "deleted",
                "error": None,
            }

            service = TaskService(db=mock_db_conn)
            result = await service.transition(
                task_id=task_data["task_id"],
                from_state=TaskState.ACTIVE,
                to_state=TaskState.COMPLETED,
            )

            assert result["success"] is True
            assert result["schedule_action"] == "deleted"
            mock_delete_schedule.assert_awaited_once_with(task_data["task_id"])

    @pytest.mark.asyncio
    async def test_valid_transition_paused_to_active(self, mock_db_conn, task_data):
        """Test that PAUSED → ACTIVE is a valid transition"""
        with patch.object(
            TaskService, "_set_temporal_state", new_callable=AsyncMock
        ) as mock_set_temporal:
            mock_set_temporal.return_value = {
                "success": True,
                "schedule_action": "unpaused",
                "error": None,
            }

            service = TaskService(db=mock_db_conn)
            result = await service.transition(
                task_id=task_data["task_id"],
                from_state=TaskState.PAUSED,
                to_state=TaskState.ACTIVE,
                user_id=task_data["user_id"],
                task_name=task_data["task_name"],
                schedule=task_data["schedule"],
            )

            assert result["success"] is True
            mock_set_temporal.assert_awaited_once_with(
                task_data["task_id"],
                is_active=True,
                task_name=task_data["task_name"],
                user_id=task_data["user_id"],
                schedule=task_data["schedule"],
            )

    @pytest.mark.asyncio
    async def test_valid_transition_completed_to_active(self, mock_db_conn, task_data):
        """Test that COMPLETED → ACTIVE is a valid transition (reactivation)"""
        with patch.object(
            TaskService, "_set_temporal_state", new_callable=AsyncMock
        ) as mock_set_temporal:
            mock_set_temporal.return_value = {
                "success": True,
                "schedule_action": "unpaused",
                "error": None,
            }

            service = TaskService(db=mock_db_conn)
            result = await service.transition(
                task_id=task_data["task_id"],
                from_state=TaskState.COMPLETED,
                to_state=TaskState.ACTIVE,
                user_id=task_data["user_id"],
                task_name=task_data["task_name"],
                schedule=task_data["schedule"],
            )

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_invalid_transition_paused_to_completed(self, mock_db_conn, task_data):
        """Test that PAUSED → COMPLETED is an invalid transition"""
        service = TaskService(db=mock_db_conn)

        with pytest.raises(InvalidTransitionError) as exc_info:
            await service.transition(
                task_id=task_data["task_id"],
                from_state=TaskState.PAUSED,
                to_state=TaskState.COMPLETED,
            )

        assert "Cannot transition from paused to completed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_invalid_transition_completed_to_paused(self, mock_db_conn, task_data):
        """Test that COMPLETED → PAUSED is an invalid transition"""
        service = TaskService(db=mock_db_conn)

        with pytest.raises(InvalidTransitionError) as exc_info:
            await service.transition(
                task_id=task_data["task_id"],
                from_state=TaskState.COMPLETED,
                to_state=TaskState.PAUSED,
            )

        assert "Cannot transition from completed to paused" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_same_state_transition_is_valid(self, mock_db_conn, task_data):
        """Test that transitioning to same state is allowed (idempotent)"""
        with patch.object(
            TaskService, "_set_temporal_state", new_callable=AsyncMock
        ) as mock_set_temporal:
            mock_set_temporal.return_value = {
                "success": True,
                "schedule_action": "none",
                "error": None,
            }

            service = TaskService(db=mock_db_conn)
            result = await service.transition(
                task_id=task_data["task_id"],
                from_state=TaskState.PAUSED,
                to_state=TaskState.PAUSED,
            )

            # Same-state transitions should succeed
            assert result["success"] is True
            assert result["schedule_action"] == "none"

    @pytest.mark.asyncio
    async def test_rollback_on_temporal_error(self, mock_db_conn, task_data):
        """Test that database is rolled back if Temporal operation fails"""
        with patch.object(
            TaskService, "_set_temporal_state", new_callable=AsyncMock
        ) as mock_set_temporal:
            mock_set_temporal.side_effect = Exception("Temporal connection failed")

            service = TaskService(db=mock_db_conn)

            with pytest.raises(Exception) as exc_info:
                await service.transition(
                    task_id=task_data["task_id"],
                    from_state=TaskState.ACTIVE,
                    to_state=TaskState.PAUSED,
                )

            assert "Temporal connection failed" in str(exc_info.value)

        # Database should be updated twice: once forward, once rollback
        assert mock_db_conn.execute.await_count == 2

    @pytest.mark.asyncio
    async def test_pause_convenience_method(self, mock_db_conn, task_data):
        """Test the pause() convenience method"""
        with patch.object(
            TaskService, "_set_temporal_state", new_callable=AsyncMock
        ) as mock_set_temporal:
            mock_set_temporal.return_value = {
                "success": True,
                "schedule_action": "paused",
                "error": None,
            }

            service = TaskService(db=mock_db_conn)
            result = await service.pause(
                task_id=task_data["task_id"], current_state=TaskState.ACTIVE
            )

            assert result["success"] is True
            mock_db_conn.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_complete_convenience_method(self, mock_db_conn, task_data):
        """Test the complete() convenience method"""
        with patch.object(TaskService, "_delete_schedule", new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = {
                "success": True,
                "schedule_action": "deleted",
                "error": None,
            }

            service = TaskService(db=mock_db_conn)
            result = await service.complete(
                task_id=task_data["task_id"], current_state=TaskState.ACTIVE
            )

            assert result["success"] is True
            assert result["schedule_action"] == "deleted"
            mock_delete.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_activate_convenience_method(self, mock_db_conn, task_data):
        """Test the activate() convenience method"""
        with patch.object(
            TaskService, "_set_temporal_state", new_callable=AsyncMock
        ) as mock_set_temporal:
            mock_set_temporal.return_value = {
                "success": True,
                "schedule_action": "unpaused",
                "error": None,
            }

            service = TaskService(db=mock_db_conn)
            result = await service.activate(
                task_id=task_data["task_id"],
                current_state=TaskState.PAUSED,
                user_id=task_data["user_id"],
                task_name=task_data["task_name"],
                schedule=task_data["schedule"],
            )

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_race_condition_concurrent_state_change(self, task_data):
        """Test that concurrent state changes are detected (UPDATE affects 0 rows)"""
        # Mock db_conn to return "UPDATE 0" (no rows affected)
        mock_db_conn = MagicMock()
        mock_db_conn.execute = AsyncMock(return_value="UPDATE 0")

        service = TaskService(db=mock_db_conn)

        # Should raise InvalidTransitionError due to race condition
        with pytest.raises(InvalidTransitionError) as exc_info:
            await service.transition(
                task_id=task_data["task_id"],
                from_state=TaskState.ACTIVE,
                to_state=TaskState.PAUSED,
            )

        assert "state changed concurrently" in str(exc_info.value).lower()
        # Verify we only attempted the conditional update once (no rollback)
        assert mock_db_conn.execute.await_count == 1

    @pytest.mark.asyncio
    async def test_db_parsing_error(self, task_data):
        """Test that unparseable DB responses are handled gracefully"""
        # Mock db_conn to return an unparseable result
        mock_db_conn = MagicMock()
        mock_db_conn.execute = AsyncMock(return_value="INVALID_RESPONSE")

        service = TaskService(db=mock_db_conn)

        # Should raise RuntimeError due to parsing failure
        with pytest.raises(RuntimeError) as exc_info:
            await service.transition(
                task_id=task_data["task_id"],
                from_state=TaskState.ACTIVE,
                to_state=TaskState.PAUSED,
            )

        assert "Could not parse DB response" in str(exc_info.value)
        # Verify we only attempted the update once (no rollback on parsing error)
        assert mock_db_conn.execute.await_count == 1
