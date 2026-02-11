"""Tests for admin API endpoints - task state management."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from torale.api.routers.admin import (
    AdminTaskStateUpdateRequest,
    admin_update_task_state,
    reset_task_history,
)
from torale.tasks import TaskState
from torale.tasks.service import InvalidTransitionError, TaskService


@pytest.fixture
def mock_admin():
    """Create a mock admin user."""
    admin = MagicMock()
    admin.id = uuid4()
    admin.email = "admin@torale.ai"
    return admin


@pytest.fixture
def mock_db():
    """Create a mock database."""
    db = AsyncMock()
    return db


@pytest.fixture
def sample_task():
    """Sample task data from database."""
    return {
        "id": uuid4(),
        "name": "Test Monitoring Task",
        "state": "active",
        "user_id": uuid4(),
        "next_run": datetime.now(UTC) + timedelta(hours=1),
    }


class TestAdminUpdateTaskState:
    """Tests for admin task state update endpoint."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "from_state,to_state,schedule_action",
        [
            ("active", TaskState.PAUSED, "paused"),
            ("paused", TaskState.ACTIVE, "resumed"),
            ("active", TaskState.COMPLETED, "deleted"),
            ("completed", TaskState.ACTIVE, "created"),
        ],
        ids=["pause", "resume", "complete", "reactivate"],
    )
    async def test_valid_transitions(
        self, mock_admin, mock_db, sample_task, from_state, to_state, schedule_action
    ):
        """Test all valid state transitions work correctly."""
        sample_task["state"] = from_state
        mock_db.fetch_one.return_value = sample_task

        request = AdminTaskStateUpdateRequest(state=to_state)

        with patch.object(TaskService, "transition") as mock_transition:
            mock_transition.return_value = {
                "success": True,
                "schedule_action": schedule_action,
                "error": None,
            }

            result = await admin_update_task_state(
                task_id=sample_task["id"],
                request=request,
                admin=mock_admin,
                db=mock_db,
            )

            # Verify transition was called with correct parameters
            mock_transition.assert_called_once()
            call_kwargs = mock_transition.call_args[1]
            assert call_kwargs["task_id"] == sample_task["id"]
            assert call_kwargs["from_state"] == TaskState(from_state)
            assert call_kwargs["to_state"] == to_state
            assert call_kwargs["user_id"] == sample_task["user_id"]
            assert call_kwargs["task_name"] == sample_task["name"]

            # Verify response format
            assert result["id"] == str(sample_task["id"])
            assert result["state"] == to_state.value
            assert result["previous_state"] == from_state

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "from_state,to_state",
        [
            (TaskState.PAUSED, TaskState.COMPLETED),
            (TaskState.COMPLETED, TaskState.PAUSED),
        ],
        ids=["paused_to_completed", "completed_to_paused"],
    )
    async def test_invalid_transitions_return_400(
        self, mock_admin, mock_db, sample_task, from_state, to_state
    ):
        """Test invalid transitions are rejected with 400 error."""
        sample_task["state"] = from_state.value
        mock_db.fetch_one.return_value = sample_task

        request = AdminTaskStateUpdateRequest(state=to_state)

        with patch.object(TaskService, "transition") as mock_transition:
            mock_transition.side_effect = InvalidTransitionError(
                f"Cannot transition from {from_state.value} to {to_state.value}"
            )

            with pytest.raises(HTTPException) as exc_info:
                await admin_update_task_state(
                    task_id=sample_task["id"],
                    request=request,
                    admin=mock_admin,
                    db=mock_db,
                )

            assert exc_info.value.status_code == 400
            assert "Invalid state transition" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_task_not_found_returns_404(self, mock_admin, mock_db):
        """Test that non-existent task returns 404."""
        mock_db.fetch_one.return_value = None

        request = AdminTaskStateUpdateRequest(state=TaskState.PAUSED)
        task_id = uuid4()

        with pytest.raises(HTTPException) as exc_info:
            await admin_update_task_state(
                task_id=task_id,
                request=request,
                admin=mock_admin,
                db=mock_db,
            )

        assert exc_info.value.status_code == 404
        assert "Task not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_resume_includes_task_name(self, mock_admin, mock_db, sample_task):
        """Test that resuming a task includes task_name parameter."""
        sample_task["state"] = "paused"
        mock_db.fetch_one.return_value = sample_task

        request = AdminTaskStateUpdateRequest(state=TaskState.ACTIVE)

        with patch.object(TaskService, "transition") as mock_transition:
            mock_transition.return_value = {"success": True, "schedule_action": "resumed"}

            await admin_update_task_state(
                task_id=sample_task["id"],
                request=request,
                admin=mock_admin,
                db=mock_db,
            )

            # Verify task_name was passed
            call_kwargs = mock_transition.call_args[1]
            assert call_kwargs["task_name"] == sample_task["name"]

    @pytest.mark.asyncio
    async def test_missing_task_name_returns_400(self, mock_admin, mock_db, sample_task):
        """Test that ValueError (e.g., missing task_name) returns 400."""
        sample_task["state"] = "paused"
        sample_task["name"] = None  # Simulate missing name in DB
        mock_db.fetch_one.return_value = sample_task

        request = AdminTaskStateUpdateRequest(state=TaskState.ACTIVE)

        with patch.object(TaskService, "transition") as mock_transition:
            mock_transition.side_effect = ValueError(
                "Cannot activate task: missing task_name, user_id, or next_run"
            )

            with pytest.raises(HTTPException) as exc_info:
                await admin_update_task_state(
                    task_id=sample_task["id"],
                    request=request,
                    admin=mock_admin,
                    db=mock_db,
                )

            assert exc_info.value.status_code == 400
            assert "Invalid task data" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_scheduler_error_returns_500(self, mock_admin, mock_db, sample_task):
        """Test that scheduler errors return 500 with helpful message."""
        sample_task["state"] = "paused"
        mock_db.fetch_one.return_value = sample_task

        request = AdminTaskStateUpdateRequest(state=TaskState.ACTIVE)

        with patch.object(TaskService, "transition") as mock_transition:
            mock_transition.side_effect = RuntimeError("Scheduler connection failed")

            with pytest.raises(HTTPException) as exc_info:
                await admin_update_task_state(
                    task_id=sample_task["id"],
                    request=request,
                    admin=mock_admin,
                    db=mock_db,
                )

            assert exc_info.value.status_code == 500
            assert "inconsistent state" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_next_run_preserved_when_resuming(self, mock_admin, mock_db, sample_task):
        """Test that next_run is preserved from DB when resuming."""
        sample_task["state"] = "paused"
        original_next_run = datetime.now(UTC) + timedelta(hours=2)
        sample_task["next_run"] = original_next_run
        mock_db.fetch_one.return_value = sample_task

        request = AdminTaskStateUpdateRequest(state=TaskState.ACTIVE)

        with patch.object(TaskService, "transition") as mock_transition:
            mock_transition.return_value = {"success": True, "schedule_action": "resumed"}

            await admin_update_task_state(
                task_id=sample_task["id"],
                request=request,
                admin=mock_admin,
                db=mock_db,
            )

            # Verify next_run was preserved
            call_kwargs = mock_transition.call_args[1]
            assert call_kwargs["next_run"] == original_next_run

    @pytest.mark.asyncio
    async def test_next_run_defaults_when_missing(self, mock_admin, mock_db, sample_task):
        """Test that next_run defaults to 1 minute when not in DB."""
        sample_task["state"] = "completed"
        sample_task["next_run"] = None  # Completed tasks may have null next_run
        mock_db.fetch_one.return_value = sample_task

        request = AdminTaskStateUpdateRequest(state=TaskState.ACTIVE)

        mock_now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        expected_next_run = mock_now + timedelta(minutes=1)

        with patch.object(TaskService, "transition") as mock_transition:
            mock_transition.return_value = {"success": True, "schedule_action": "created"}

            with patch("torale.api.routers.admin.datetime") as mock_dt:
                mock_dt.now.return_value = mock_now

                await admin_update_task_state(
                    task_id=sample_task["id"],
                    request=request,
                    admin=mock_admin,
                    db=mock_db,
                )

            # Verify next_run was set to exactly 1 minute from mocked now
            call_kwargs = mock_transition.call_args[1]
            next_run = call_kwargs["next_run"]
            assert next_run == expected_next_run

    @pytest.mark.asyncio
    async def test_pause_does_not_require_next_run(self, mock_admin, mock_db, sample_task):
        """Test that pausing a task doesn't need next_run parameter."""
        sample_task["state"] = "active"
        mock_db.fetch_one.return_value = sample_task

        request = AdminTaskStateUpdateRequest(state=TaskState.PAUSED)

        with patch.object(TaskService, "transition") as mock_transition:
            mock_transition.return_value = {"success": True, "schedule_action": "paused"}

            await admin_update_task_state(
                task_id=sample_task["id"],
                request=request,
                admin=mock_admin,
                db=mock_db,
            )

            # Verify next_run was None
            call_kwargs = mock_transition.call_args[1]
            assert call_kwargs["next_run"] is None

    @pytest.mark.asyncio
    async def test_error_response_format(self, mock_admin, mock_db, sample_task):
        """Test that error responses include helpful debugging context."""
        sample_task["state"] = "active"
        mock_db.fetch_one.return_value = sample_task

        request = AdminTaskStateUpdateRequest(state=TaskState.PAUSED)

        with patch.object(TaskService, "transition") as mock_transition:
            mock_transition.side_effect = RuntimeError("Database connection lost")

            with pytest.raises(HTTPException) as exc_info:
                await admin_update_task_state(
                    task_id=sample_task["id"],
                    request=request,
                    admin=mock_admin,
                    db=mock_db,
                )

            # Verify error includes actionable message
            assert exc_info.value.status_code == 500
            assert "Failed to update task state" in exc_info.value.detail
            assert "inconsistent state" in exc_info.value.detail


class TestAdminResetTaskHistory:
    """Tests for admin task history reset endpoint."""

    @pytest.mark.asyncio
    async def test_successful_reset_and_deletion(self, mock_admin):
        """Test successful reset deletes executions and resets task state."""
        task_id = uuid4()
        days = 1

        # Mock session with successful DB operations
        mock_session = AsyncMock()

        # Mock task exists check
        check_result = MagicMock()
        check_result.first.return_value = {"id": task_id}

        # Mock deletion with 3 executions deleted
        delete_result = MagicMock()
        delete_result.fetchall.return_value = [{"id": uuid4()} for _ in range(3)]

        mock_session.execute.side_effect = [
            check_result,  # Task exists check
            delete_result,  # Delete executions
            AsyncMock(),  # Update task state
        ]

        result = await reset_task_history(
            task_id=task_id,
            days=days,
            admin=mock_admin,
            session=mock_session,
        )

        # Verify response
        assert result["status"] == "reset"
        assert result["task_id"] == str(task_id)
        assert result["executions_deleted"] == 3
        assert result["days"] == days

        # Verify DB operations
        assert mock_session.execute.call_count == 3
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_not_called()

    @pytest.mark.asyncio
    async def test_reset_with_no_executions(self, mock_admin, caplog):
        """Test reset with no recent executions logs warning."""
        task_id = uuid4()
        days = 7

        mock_session = AsyncMock()

        # Mock task exists
        check_result = MagicMock()
        check_result.first.return_value = {"id": task_id}

        # Mock no executions deleted
        delete_result = MagicMock()
        delete_result.fetchall.return_value = []

        mock_session.execute.side_effect = [
            check_result,
            delete_result,
            AsyncMock(),
        ]

        result = await reset_task_history(
            task_id=task_id,
            days=days,
            admin=mock_admin,
            session=mock_session,
        )

        # Verify response shows 0 deletions
        assert result["executions_deleted"] == 0
        assert result["status"] == "reset"

        # Verify warning was logged
        assert any("found no executions" in record.message for record in caplog.records)

        # Verify commit still happened
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_nonexistent_task_returns_404(self, mock_admin):
        """Test resetting a non-existent task returns 404."""
        task_id = uuid4()

        mock_session = AsyncMock()

        # Mock task doesn't exist
        check_result = MagicMock()
        check_result.first.return_value = None
        mock_session.execute.return_value = check_result

        with pytest.raises(HTTPException) as exc_info:
            await reset_task_history(
                task_id=task_id,
                days=1,
                admin=mock_admin,
                session=mock_session,
            )

        # Verify 404 error
        assert exc_info.value.status_code == 404
        assert "Task not found" in exc_info.value.detail

        # Verify rollback was called
        mock_session.rollback.assert_called_once()
        mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_database_error_triggers_rollback(self, mock_admin):
        """Test database errors trigger rollback and return 500."""
        task_id = uuid4()

        mock_session = AsyncMock()

        # Mock task exists check succeeds
        check_result = MagicMock()
        check_result.first.return_value = {"id": task_id}

        # Mock deletion fails with database error
        mock_session.execute.side_effect = [
            check_result,
            RuntimeError("Database connection lost"),
        ]

        with pytest.raises(HTTPException) as exc_info:
            await reset_task_history(
                task_id=task_id,
                days=1,
                admin=mock_admin,
                session=mock_session,
            )

        # Verify 500 error
        assert exc_info.value.status_code == 500
        assert "Failed to reset task history" in exc_info.value.detail

        # Verify rollback was called
        mock_session.rollback.assert_called_once()
        mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_days_parameter_validation(self, mock_admin):
        """Test days parameter is passed correctly to SQL query."""
        task_id = uuid4()
        days = 14  # Custom days value

        mock_session = AsyncMock()

        check_result = MagicMock()
        check_result.first.return_value = {"id": task_id}

        delete_result = MagicMock()
        delete_result.fetchall.return_value = [{"id": uuid4()}]

        mock_session.execute.side_effect = [
            check_result,
            delete_result,
            AsyncMock(),
        ]

        result = await reset_task_history(
            task_id=task_id,
            days=days,
            admin=mock_admin,
            session=mock_session,
        )

        # Verify days parameter in response
        assert result["days"] == 14

        # Verify days was used in deletion query (check execute calls)
        delete_call = mock_session.execute.call_args_list[1]
        assert delete_call[0][1]["task_id"] == task_id
        # Cutoff calculation happens inside function, so we just verify it was called

    @pytest.mark.asyncio
    async def test_reset_clears_task_state_fields(self, mock_admin):
        """Test reset properly clears last_execution_id, last_known_state, and updates state_changed_at."""
        task_id = uuid4()

        mock_session = AsyncMock()

        check_result = MagicMock()
        check_result.first.return_value = {"id": task_id}

        delete_result = MagicMock()
        delete_result.fetchall.return_value = []

        update_result = AsyncMock()

        mock_session.execute.side_effect = [
            check_result,
            delete_result,
            update_result,
        ]

        await reset_task_history(
            task_id=task_id,
            days=1,
            admin=mock_admin,
            session=mock_session,
        )

        # Verify UPDATE query was called (3rd execute call)
        assert mock_session.execute.call_count == 3
        update_call = mock_session.execute.call_args_list[2]

        # Verify it's updating the tasks table with task_id
        query_text = str(update_call[0][0])
        assert "UPDATE tasks" in query_text
        assert "last_execution_id = NULL" in query_text
        assert "last_known_state = NULL" in query_text
        assert "state_changed_at = NOW()" in query_text
        assert update_call[0][1]["task_id"] == task_id
