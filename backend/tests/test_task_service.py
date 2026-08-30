"""Tests for TaskService - state transition and orchestration logic."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, create_autospec, patch
from uuid import uuid4

import pytest

from webwhen.tasks import TaskCreate, TaskState, TaskUpdate
from webwhen.tasks.repository import TaskRepository
from webwhen.tasks.service import (
    ActiveTaskLimitError,
    InvalidTransitionError,
    TaskScheduleError,
    TaskService,
    TaskTransitionError,
)


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
        "next_run": datetime.now(UTC) + timedelta(hours=24),
    }


@pytest.fixture
def service_and_repository(mock_db_conn):
    service = TaskService(db=mock_db_conn)
    repository = create_autospec(TaskRepository, instance=True)
    service.repository = repository
    return service, repository


class TestTaskService:
    @pytest.mark.asyncio
    async def test_create_paused_watch_skips_limit_and_schedule(self, service_and_repository):
        service, repository = service_and_repository
        task_id = uuid4()
        repository.create_task.return_value = {"id": task_id, "state": "paused"}
        service.create_schedule_for_new_task = AsyncMock()

        result = await service.create(
            TaskCreate(
                name="Paused watch",
                search_query="something happened",
                state=TaskState.PAUSED,
            ),
            uuid4(),
            max_active_tasks=0,
            next_run=datetime.now(UTC),
        )

        assert result["id"] == task_id
        repository.count_active_by_user.assert_not_awaited()
        service.create_schedule_for_new_task.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_create_rejects_active_watch_before_persistence(self, service_and_repository):
        service, repository = service_and_repository
        repository.count_active_by_user.return_value = 3
        service.create_schedule_for_new_task = AsyncMock()

        with pytest.raises(ActiveTaskLimitError, match="Maximum of 3 active tasks"):
            await service.create(
                TaskCreate(name="Active watch", search_query="something happened"),
                uuid4(),
                max_active_tasks=3,
                next_run=datetime.now(UTC),
            )

        repository.create_task.assert_not_awaited()
        service.create_schedule_for_new_task.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_empty_update_returns_existing_row_without_write(self, service_and_repository):
        service, repository = service_and_repository
        task_id = uuid4()
        user_id = uuid4()
        repository.find_owned.return_value = {
            "id": task_id,
            "user_id": user_id,
            "name": "Unchanged",
            "state": "paused",
        }

        result = await service.update(task_id, user_id, TaskUpdate())

        assert result.row["name"] == "Unchanged"
        assert result.includes_execution is False
        repository.update_owned_fields.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_create_compensates_when_schedule_creation_fails(self, mock_db_conn):
        service = TaskService(db=mock_db_conn)
        service.repository = MagicMock()
        service.repository.count_active_by_user = AsyncMock(return_value=0)
        task_id = uuid4()
        service.repository.create_task = AsyncMock(return_value={"id": task_id})
        service.repository.delete_by_id = AsyncMock(return_value=True)
        service.create_schedule_for_new_task = AsyncMock(side_effect=RuntimeError("offline"))

        with pytest.raises(TaskScheduleError, match="offline"):
            await service.create(
                TaskCreate(name="New watch", search_query="something happened"),
                uuid4(),
                max_active_tasks=5,
                next_run=datetime.now(UTC),
            )

        service.repository.delete_by_id.assert_awaited_once_with(task_id)

    @pytest.mark.asyncio
    async def test_update_restores_changed_fields_when_transition_fails(self, mock_db_conn):
        service = TaskService(db=mock_db_conn)
        service.repository = MagicMock()
        task_id = uuid4()
        user_id = uuid4()
        service.repository.find_owned = AsyncMock(
            return_value={
                "id": task_id,
                "name": "Old name",
                "state": "active",
                "webhook_url": None,
            }
        )
        service.repository.update_owned_fields = AsyncMock(
            return_value={"id": task_id, "name": "New name", "state": "active"}
        )
        service.repository.restore_fields = AsyncMock()
        service.transition = AsyncMock(side_effect=RuntimeError("scheduler unavailable"))

        with pytest.raises(TaskTransitionError, match="rolled back"):
            await service.update(
                task_id,
                user_id,
                TaskUpdate(name="New name", state=TaskState.PAUSED),
            )

        service.repository.restore_fields.assert_awaited_once_with(
            task_id, {"state": "active", "name": "Old name"}
        )

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
                next_run=task_data["next_run"],
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
