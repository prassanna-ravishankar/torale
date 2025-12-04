"""Tests for TaskStateMachine - state transition validation logic

Unit tests verify that state machine validates transitions correctly.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from torale.core.task_state_machine import InvalidTransitionError, TaskState, TaskStateMachine


@pytest.fixture
def mock_db_conn():
    """Mock database connection"""
    conn = MagicMock()
    conn.execute = AsyncMock(return_value=None)
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


class TestTaskStateMachine:
    """Unit tests for TaskStateMachine state transition logic"""

    @pytest.mark.asyncio
    async def test_valid_transition_active_to_paused(self, mock_db_conn, task_data):
        """Test that ACTIVE → PAUSED is a valid transition"""
        # Mock TaskStateManager to avoid actual Temporal calls
        mock_state_manager = MagicMock()
        mock_state_manager.set_task_active_state = AsyncMock(
            return_value={"success": True, "schedule_action": "paused", "error": None}
        )

        with patch(
            "torale.core.task_state_machine.TaskStateManager", return_value=mock_state_manager
        ):
            machine = TaskStateMachine(db_conn=mock_db_conn)
            result = await machine.transition(
                task_id=task_data["task_id"],
                from_state=TaskState.ACTIVE,
                to_state=TaskState.PAUSED,
            )

        # Should succeed
        assert result["success"] is True
        mock_db_conn.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_valid_transition_active_to_completed(self, mock_db_conn, task_data):
        """Test that ACTIVE → COMPLETED is a valid transition"""
        mock_state_manager = MagicMock()
        mock_state_manager.set_task_active_state = AsyncMock(
            return_value={"success": True, "schedule_action": "paused", "error": None}
        )

        with patch(
            "torale.core.task_state_machine.TaskStateManager", return_value=mock_state_manager
        ):
            machine = TaskStateMachine(db_conn=mock_db_conn)
            result = await machine.transition(
                task_id=task_data["task_id"],
                from_state=TaskState.ACTIVE,
                to_state=TaskState.COMPLETED,
            )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_valid_transition_paused_to_active(self, mock_db_conn, task_data):
        """Test that PAUSED → ACTIVE is a valid transition"""
        mock_state_manager = MagicMock()
        mock_state_manager.set_task_active_state = AsyncMock(
            return_value={"success": True, "schedule_action": "unpaused", "error": None}
        )

        with patch(
            "torale.core.task_state_machine.TaskStateManager", return_value=mock_state_manager
        ):
            machine = TaskStateMachine(db_conn=mock_db_conn)
            result = await machine.transition(
                task_id=task_data["task_id"],
                from_state=TaskState.PAUSED,
                to_state=TaskState.ACTIVE,
                user_id=task_data["user_id"],
                task_name=task_data["task_name"],
                schedule=task_data["schedule"],
            )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_valid_transition_completed_to_active(self, mock_db_conn, task_data):
        """Test that COMPLETED → ACTIVE is a valid transition (reactivation)"""
        mock_state_manager = MagicMock()
        mock_state_manager.set_task_active_state = AsyncMock(
            return_value={"success": True, "schedule_action": "unpaused", "error": None}
        )

        with patch(
            "torale.core.task_state_machine.TaskStateManager", return_value=mock_state_manager
        ):
            machine = TaskStateMachine(db_conn=mock_db_conn)
            result = await machine.transition(
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
        machine = TaskStateMachine(db_conn=mock_db_conn)

        with pytest.raises(InvalidTransitionError) as exc_info:
            await machine.transition(
                task_id=task_data["task_id"],
                from_state=TaskState.PAUSED,
                to_state=TaskState.COMPLETED,
            )

        assert "Cannot transition from paused to completed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_invalid_transition_completed_to_paused(self, mock_db_conn, task_data):
        """Test that COMPLETED → PAUSED is an invalid transition"""
        machine = TaskStateMachine(db_conn=mock_db_conn)

        with pytest.raises(InvalidTransitionError) as exc_info:
            await machine.transition(
                task_id=task_data["task_id"],
                from_state=TaskState.COMPLETED,
                to_state=TaskState.PAUSED,
            )

        assert "Cannot transition from completed to paused" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_same_state_transition_is_valid(self, mock_db_conn, task_data):
        """Test that transitioning to same state is allowed (idempotent)"""
        mock_state_manager = MagicMock()
        mock_state_manager.set_task_active_state = AsyncMock(
            return_value={"success": True, "schedule_action": "paused", "error": None}
        )

        with patch(
            "torale.core.task_state_machine.TaskStateManager", return_value=mock_state_manager
        ):
            machine = TaskStateMachine(db_conn=mock_db_conn)
            result = await machine.transition(
                task_id=task_data["task_id"],
                from_state=TaskState.PAUSED,
                to_state=TaskState.PAUSED,
            )

        # Same-state transitions should succeed
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_rollback_on_temporal_error(self, mock_db_conn, task_data):
        """Test that database is rolled back if Temporal operation fails"""
        # Mock state manager to raise error
        mock_state_manager = MagicMock()
        mock_state_manager.set_task_active_state = AsyncMock(
            side_effect=Exception("Temporal connection failed")
        )

        with patch(
            "torale.core.task_state_machine.TaskStateManager", return_value=mock_state_manager
        ):
            machine = TaskStateMachine(db_conn=mock_db_conn)

            with pytest.raises(Exception) as exc_info:
                await machine.transition(
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
        mock_state_manager = MagicMock()
        mock_state_manager.set_task_active_state = AsyncMock(
            return_value={"success": True, "schedule_action": "paused", "error": None}
        )

        with patch(
            "torale.core.task_state_machine.TaskStateManager", return_value=mock_state_manager
        ):
            machine = TaskStateMachine(db_conn=mock_db_conn)
            result = await machine.pause(
                task_id=task_data["task_id"], current_state=TaskState.ACTIVE
            )

        assert result["success"] is True
        mock_db_conn.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_complete_convenience_method(self, mock_db_conn, task_data):
        """Test the complete() convenience method"""
        mock_state_manager = MagicMock()
        mock_state_manager.set_task_active_state = AsyncMock(
            return_value={"success": True, "schedule_action": "paused", "error": None}
        )

        with patch(
            "torale.core.task_state_machine.TaskStateManager", return_value=mock_state_manager
        ):
            machine = TaskStateMachine(db_conn=mock_db_conn)
            result = await machine.complete(
                task_id=task_data["task_id"], current_state=TaskState.ACTIVE
            )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_activate_convenience_method(self, mock_db_conn, task_data):
        """Test the activate() convenience method"""
        mock_state_manager = MagicMock()
        mock_state_manager.set_task_active_state = AsyncMock(
            return_value={"success": True, "schedule_action": "unpaused", "error": None}
        )

        with patch(
            "torale.core.task_state_machine.TaskStateManager", return_value=mock_state_manager
        ):
            machine = TaskStateMachine(db_conn=mock_db_conn)
            result = await machine.activate(
                task_id=task_data["task_id"],
                current_state=TaskState.PAUSED,
                user_id=task_data["user_id"],
                task_name=task_data["task_name"],
                schedule=task_data["schedule"],
            )

        assert result["success"] is True
