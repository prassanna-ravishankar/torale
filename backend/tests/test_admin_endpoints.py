"""Tests for admin API endpoints - task state management."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

from torale.api.routers.admin import AdminTaskStateUpdateRequest, admin_update_task_state
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
