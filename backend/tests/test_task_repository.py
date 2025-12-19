from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from torale.core.models import TaskState
from torale.repositories.task import TaskRepository


@pytest.fixture
def mock_db():
    """Create a mock database instance."""
    return AsyncMock()


@pytest.fixture
def task_repo(mock_db):
    """Create a TaskRepository instance with mock database."""
    return TaskRepository(mock_db)


class TestTaskRepositoryCreateOperations:
    """Tests for task creation operations."""

    @pytest.mark.asyncio
    async def test_create_task_minimal(self, task_repo, mock_db):
        """Test creating a task with minimal required fields."""
        user_id = uuid4()
        created_task = {
            "id": uuid4(),
            "user_id": user_id,
            "name": "Test Task",
            "schedule": "0 0 * * *",
            "state": "active",
        }
        mock_db.fetch_one.return_value = created_task

        result = await task_repo.create_task(
            user_id=user_id,
            name="Test Task",
            schedule="0 0 * * *",
            executor_type="llm_grounded_search",
            config={"model": "gemini-2.5-flash"},
            state="active",
            search_query="test query",
            condition_description="test condition",
            notify_behavior="once",
            notifications=[],
            notification_channels=["email"],
            notification_email="test@example.com",
            webhook_url=None,
            webhook_secret=None,
        )

        assert result == created_task
        mock_db.fetch_one.assert_called_once()
        call_args = mock_db.fetch_one.call_args[0]
        assert "INSERT INTO" in call_args[0]

    @pytest.mark.asyncio
    async def test_create_task_with_webhook(self, task_repo, mock_db):
        """Test creating a task with webhook configuration."""
        user_id = uuid4()
        created_task = {
            "id": uuid4(),
            "webhook_url": "https://example.com/webhook",
            "webhook_secret": "secret_123",
        }
        mock_db.fetch_one.return_value = created_task

        result = await task_repo.create_task(
            user_id=user_id,
            name="Webhook Task",
            schedule="0 0 * * *",
            executor_type="llm_grounded_search",
            config={"model": "gemini-2.5-flash"},
            state="active",
            search_query="test",
            condition_description="test",
            notify_behavior="always",
            notifications=[],
            notification_channels=["webhook"],
            notification_email=None,
            webhook_url="https://example.com/webhook",
            webhook_secret="secret_123",
        )

        assert result["webhook_url"] == "https://example.com/webhook"
        assert result["webhook_secret"] == "secret_123"


class TestTaskRepositoryFindOperations:
    """Tests for task find operations."""

    @pytest.mark.asyncio
    async def test_find_by_user_all_tasks(self, task_repo, mock_db):
        """Test finding all tasks for a user."""
        user_id = uuid4()
        expected_tasks = [
            {"id": uuid4(), "name": "Task 1", "state": "active"},
            {"id": uuid4(), "name": "Task 2", "state": "paused"},
        ]
        mock_db.fetch_all.return_value = expected_tasks

        result = await task_repo.find_by_user(user_id)

        assert result == expected_tasks
        mock_db.fetch_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_user_filtered_by_state(self, task_repo, mock_db):
        """Test finding tasks filtered by state."""
        user_id = uuid4()
        expected_tasks = [{"id": uuid4(), "name": "Active Task", "state": "active"}]
        mock_db.fetch_all.return_value = expected_tasks

        result = await task_repo.find_by_user(user_id, state=TaskState.ACTIVE)

        assert result == expected_tasks
        call_args = mock_db.fetch_all.call_args[0]
        assert "active" in call_args

    @pytest.mark.asyncio
    async def test_find_by_id_with_execution(self, task_repo, mock_db):
        """Test finding task by ID with execution embedded."""
        task_id = uuid4()
        expected_task = {
            "id": task_id,
            "name": "Task",
            "exec_id": uuid4(),
            "exec_status": "success",
        }
        mock_db.fetch_one.return_value = expected_task

        result = await task_repo.find_by_id_with_execution(task_id)

        assert result == expected_task
        assert "exec_id" in result


class TestTaskRepositoryUpdateOperations:
    """Tests for task update operations."""

    @pytest.mark.asyncio
    async def test_update_task_name(self, task_repo, mock_db):
        """Test updating a task's name."""
        task_id = uuid4()
        updated_task = {"id": task_id, "name": "Updated Name"}
        mock_db.fetch_one.return_value = updated_task

        result = await task_repo.update_task(task_id, name="Updated Name")

        assert result["name"] == "Updated Name"
        mock_db.fetch_one.assert_called_once()
        call_args = mock_db.fetch_one.call_args[0]
        assert "UPDATE" in call_args[0]

    @pytest.mark.asyncio
    async def test_update_task_multiple_fields(self, task_repo, mock_db):
        """Test updating multiple task fields."""
        task_id = uuid4()
        updated_task = {
            "id": task_id,
            "name": "New Name",
            "schedule": "0 12 * * *",
        }
        mock_db.fetch_one.return_value = updated_task

        result = await task_repo.update_task(task_id, name="New Name", schedule="0 12 * * *")

        assert result["name"] == "New Name"
        assert result["schedule"] == "0 12 * * *"

    @pytest.mark.asyncio
    async def test_update_task_no_changes(self, task_repo, mock_db):
        """Test updating a task with no changes returns current task."""
        task_id = uuid4()
        current_task = {"id": task_id, "name": "Current"}
        mock_db.fetch_one.return_value = current_task

        result = await task_repo.update_task(task_id)

        assert result == current_task

    @pytest.mark.asyncio
    async def test_update_last_execution(self, task_repo, mock_db):
        """Test updating task's last execution reference."""
        task_id = uuid4()
        execution_id = uuid4()
        updated_task = {
            "id": task_id,
            "last_execution_id": execution_id,
        }
        mock_db.fetch_one.return_value = updated_task

        result = await task_repo.update_last_execution(
            task_id, execution_id, {"status": "complete"}
        )

        assert result["last_execution_id"] == execution_id

    @pytest.mark.asyncio
    async def test_update_state(self, task_repo, mock_db):
        """Test updating task state."""
        task_id = uuid4()
        updated_task = {"id": task_id, "state": "paused"}
        mock_db.fetch_one.return_value = updated_task

        result = await task_repo.update_state(task_id, "paused")

        assert result["state"] == "paused"
        call_args = mock_db.fetch_one.call_args[0]
        assert "state_changed_at" in call_args[0]


class TestTaskRepositoryVisibilityOperations:
    """Tests for public/private task operations."""

    @pytest.mark.asyncio
    async def test_update_visibility_make_public(self, task_repo, mock_db):
        """Test making a task public with slug."""
        task_id = uuid4()
        updated_task = {
            "id": task_id,
            "is_public": True,
            "slug": "my-task-slug",
        }
        mock_db.fetch_one.return_value = updated_task

        result = await task_repo.update_visibility(task_id, is_public=True, slug="my-task-slug")

        assert result["is_public"] is True
        assert result["slug"] == "my-task-slug"

    @pytest.mark.asyncio
    async def test_update_visibility_make_private(self, task_repo, mock_db):
        """Test making a task private."""
        task_id = uuid4()
        updated_task = {"id": task_id, "is_public": False}
        mock_db.fetch_one.return_value = updated_task

        result = await task_repo.update_visibility(task_id, is_public=False)

        assert result["is_public"] is False

    @pytest.mark.asyncio
    async def test_increment_view_count(self, task_repo, mock_db):
        """Test incrementing task view count."""
        task_id = uuid4()

        await task_repo.increment_view_count(task_id)

        mock_db.execute.assert_called_once()
        call_args = mock_db.execute.call_args[0]
        assert "view_count = view_count + 1" in call_args[0]

    @pytest.mark.asyncio
    async def test_increment_subscriber_count(self, task_repo, mock_db):
        """Test incrementing task subscriber count."""
        task_id = uuid4()

        await task_repo.increment_subscriber_count(task_id)

        mock_db.execute.assert_called_once()
        call_args = mock_db.execute.call_args[0]
        assert "subscriber_count = subscriber_count + 1" in call_args[0]


class TestTaskRepositoryPublicTasksOperations:
    """Tests for public task discovery."""

    @pytest.mark.asyncio
    async def test_find_public_tasks(self, task_repo, mock_db):
        """Test finding public tasks."""
        expected_tasks = [
            {"id": uuid4(), "is_public": True, "name": "Public Task 1"},
            {"id": uuid4(), "is_public": True, "name": "Public Task 2"},
        ]
        mock_db.fetch_all.return_value = expected_tasks

        result = await task_repo.find_public_tasks(limit=10)

        assert result == expected_tasks
        mock_db.fetch_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_public_tasks_with_search(self, task_repo, mock_db):
        """Test finding public tasks with search filter."""
        expected_tasks = [{"id": uuid4(), "name": "iPhone Release"}]
        mock_db.fetch_all.return_value = expected_tasks

        result = await task_repo.find_public_tasks(search="iPhone")

        assert result == expected_tasks
        call_args = mock_db.fetch_all.call_args[0]
        assert "%iPhone%" in call_args

    @pytest.mark.asyncio
    async def test_find_by_slug(self, task_repo, mock_db):
        """Test finding task by slug."""
        expected_task = {
            "id": uuid4(),
            "slug": "my-task",
            "is_public": True,
        }
        mock_db.fetch_one.return_value = expected_task

        result = await task_repo.find_by_slug("my-task")

        assert result == expected_task

    @pytest.mark.asyncio
    async def test_slug_exists_true(self, task_repo, mock_db):
        """Test slug_exists when slug is taken."""
        mock_db.fetch_val.return_value = 1

        result = await task_repo.slug_exists("taken-slug")

        assert result is True

    @pytest.mark.asyncio
    async def test_slug_exists_false(self, task_repo, mock_db):
        """Test slug_exists when slug is available."""
        mock_db.fetch_val.return_value = 0

        result = await task_repo.slug_exists("available-slug")

        assert result is False
