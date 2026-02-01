"""Tests for TaskService - state transition and orchestration logic."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from torale.tasks import TaskState
from torale.tasks.service import InvalidTransitionError, TaskService


@pytest.fixture
def mock_db_conn():
    conn = MagicMock()
    conn.execute = AsyncMock(return_value="UPDATE 1")
    return conn


@pytest.fixture
def task_data():
    return {
        "task_id": uuid4(),
        "task_name": "Test Task",
        "user_id": uuid4(),
        "schedule": "0 9 * * *",
    }


class TestTaskService:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "from_state,to_state,job_method,job_return",
        [
            (
                TaskState.ACTIVE,
                TaskState.PAUSED,
                "_pause_job",
                {"success": True, "schedule_action": "paused", "error": None},
            ),
            (
                TaskState.ACTIVE,
                TaskState.COMPLETED,
                "_remove_job",
                {"success": True, "schedule_action": "deleted", "error": None},
            ),
            (
                TaskState.PAUSED,
                TaskState.ACTIVE,
                "_add_or_resume_job",
                {"success": True, "schedule_action": "resumed", "error": None},
            ),
            (
                TaskState.COMPLETED,
                TaskState.ACTIVE,
                "_add_or_resume_job",
                {"success": True, "schedule_action": "created", "error": None},
            ),
        ],
    )
    async def test_valid_transitions(
        self, mock_db_conn, task_data, from_state, to_state, job_method, job_return
    ):
        with patch.object(TaskService, job_method) as mock_job:
            mock_job.return_value = job_return

            service = TaskService(db=mock_db_conn)
            result = await service.transition(
                task_id=task_data["task_id"],
                from_state=from_state,
                to_state=to_state,
                user_id=task_data["user_id"],
                task_name=task_data["task_name"],
                schedule=task_data["schedule"],
            )

            assert result["success"] is True
            mock_job.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "from_state,to_state",
        [
            (TaskState.PAUSED, TaskState.COMPLETED),
            (TaskState.COMPLETED, TaskState.PAUSED),
        ],
    )
    async def test_invalid_transitions(self, mock_db_conn, task_data, from_state, to_state):
        service = TaskService(db=mock_db_conn)

        with pytest.raises(InvalidTransitionError) as exc_info:
            await service.transition(
                task_id=task_data["task_id"],
                from_state=from_state,
                to_state=to_state,
            )

        assert f"Cannot transition from {from_state.value} to {to_state.value}" in str(
            exc_info.value
        )

    @pytest.mark.asyncio
    async def test_same_state_transition_is_noop(self, mock_db_conn, task_data):
        service = TaskService(db=mock_db_conn)
        result = await service.transition(
            task_id=task_data["task_id"],
            from_state=TaskState.PAUSED,
            to_state=TaskState.PAUSED,
        )

        assert result["success"] is True
        assert result["schedule_action"] == "none"
        mock_db_conn.execute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_rollback_on_scheduler_error(self, mock_db_conn, task_data):
        with patch.object(TaskService, "_pause_job") as mock_pause:
            mock_pause.side_effect = Exception("Scheduler connection failed")

            service = TaskService(db=mock_db_conn)

            with pytest.raises(Exception) as exc_info:
                await service.transition(
                    task_id=task_data["task_id"],
                    from_state=TaskState.ACTIVE,
                    to_state=TaskState.PAUSED,
                )

            assert "Scheduler connection failed" in str(exc_info.value)

        assert mock_db_conn.execute.await_count == 2

    @pytest.mark.asyncio
    async def test_race_condition_concurrent_state_change(self, task_data):
        mock_db_conn = MagicMock()
        mock_db_conn.execute = AsyncMock(return_value="UPDATE 0")

        service = TaskService(db=mock_db_conn)

        with pytest.raises(InvalidTransitionError) as exc_info:
            await service.transition(
                task_id=task_data["task_id"],
                from_state=TaskState.ACTIVE,
                to_state=TaskState.PAUSED,
            )

        assert "state changed concurrently" in str(exc_info.value).lower()
        assert mock_db_conn.execute.await_count == 1

    @pytest.mark.asyncio
    async def test_db_parsing_error(self, task_data):
        mock_db_conn = MagicMock()
        mock_db_conn.execute = AsyncMock(return_value="INVALID_RESPONSE")

        service = TaskService(db=mock_db_conn)

        with pytest.raises(RuntimeError) as exc_info:
            await service.transition(
                task_id=task_data["task_id"],
                from_state=TaskState.ACTIVE,
                to_state=TaskState.PAUSED,
            )

        assert "Could not parse DB response" in str(exc_info.value)
        assert mock_db_conn.execute.await_count == 1
