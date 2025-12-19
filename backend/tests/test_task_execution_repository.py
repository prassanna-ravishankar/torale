from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from torale.repositories.task_execution import TaskExecutionRepository


@pytest.fixture
def mock_db():
    """Create a mock database instance."""
    return AsyncMock()


@pytest.fixture
def execution_repo(mock_db):
    """Create a TaskExecutionRepository instance with mock database."""
    return TaskExecutionRepository(mock_db)


class TestTaskExecutionRepositoryCreateOperations:
    """Tests for execution creation operations."""

    @pytest.mark.asyncio
    async def test_create_execution_default_pending(self, execution_repo, mock_db):
        """Test creating an execution with default pending status."""
        task_id = uuid4()
        created_execution = {
            "id": uuid4(),
            "task_id": task_id,
            "status": "pending",
        }
        mock_db.fetch_one.return_value = created_execution

        result = await execution_repo.create_execution(task_id)

        assert result == created_execution
        mock_db.fetch_one.assert_called_once()
        call_args = mock_db.fetch_one.call_args[0]
        assert "INSERT INTO" in call_args[0]

    @pytest.mark.asyncio
    async def test_create_execution_custom_status(self, execution_repo, mock_db):
        """Test creating an execution with custom status."""
        task_id = uuid4()
        created_execution = {
            "id": uuid4(),
            "task_id": task_id,
            "status": "running",
        }
        mock_db.fetch_one.return_value = created_execution

        result = await execution_repo.create_execution(task_id, status="running")

        assert result["status"] == "running"


class TestTaskExecutionRepositoryUpdateOperations:
    """Tests for execution update operations."""

    @pytest.mark.asyncio
    async def test_update_execution_status(self, execution_repo, mock_db):
        """Test updating execution status."""
        execution_id = uuid4()
        updated_execution = {
            "id": execution_id,
            "status": "success",
        }
        mock_db.fetch_one.return_value = updated_execution

        result = await execution_repo.update_execution(execution_id, status="success")

        assert result["status"] == "success"
        mock_db.fetch_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_execution_with_result(self, execution_repo, mock_db):
        """Test updating execution with result."""
        execution_id = uuid4()
        updated_execution = {
            "id": execution_id,
            "status": "success",
            "result": {"data": "test"},
        }
        mock_db.fetch_one.return_value = updated_execution

        result = await execution_repo.update_execution(
            execution_id, status="success", result={"data": "test"}
        )

        assert result["result"] == {"data": "test"}

    @pytest.mark.asyncio
    async def test_update_execution_with_error(self, execution_repo, mock_db):
        """Test updating execution with error."""
        execution_id = uuid4()
        updated_execution = {
            "id": execution_id,
            "status": "failed",
            "error_message": "Something went wrong",
        }
        mock_db.fetch_one.return_value = updated_execution

        result = await execution_repo.update_execution(
            execution_id, status="failed", error_message="Something went wrong"
        )

        assert result["status"] == "failed"
        assert result["error_message"] == "Something went wrong"

    @pytest.mark.asyncio
    async def test_update_execution_with_now_timestamp(self, execution_repo, mock_db):
        """Test updating execution with NOW() for completed_at."""
        execution_id = uuid4()
        updated_execution = {
            "id": execution_id,
            "status": "success",
            "completed_at": "2024-01-01T00:00:00Z",
        }
        mock_db.fetch_one.return_value = updated_execution

        result = await execution_repo.update_execution(
            execution_id, status="success", completed_at="NOW()"
        )

        assert result == updated_execution
        call_args = mock_db.fetch_one.call_args[0]
        # PyPika generates no spaces around = sign
        assert "completed_at" in call_args[0] and "NOW()" in call_args[0]

    @pytest.mark.asyncio
    async def test_update_execution_condition_met(self, execution_repo, mock_db):
        """Test updating execution with condition_met flag."""
        execution_id = uuid4()
        updated_execution = {
            "id": execution_id,
            "condition_met": True,
            "change_summary": "Condition was met",
        }
        mock_db.fetch_one.return_value = updated_execution

        result = await execution_repo.update_execution(
            execution_id, condition_met=True, change_summary="Condition was met"
        )

        assert result["condition_met"] is True
        assert result["change_summary"] == "Condition was met"

    @pytest.mark.asyncio
    async def test_update_execution_grounding_sources(self, execution_repo, mock_db):
        """Test updating execution with grounding sources."""
        execution_id = uuid4()
        sources = [{"url": "https://example.com", "title": "Example"}]
        updated_execution = {
            "id": execution_id,
            "grounding_sources": sources,
        }
        mock_db.fetch_one.return_value = updated_execution

        result = await execution_repo.update_execution(execution_id, grounding_sources=sources)

        assert result["grounding_sources"] == sources


class TestTaskExecutionRepositoryFindOperations:
    """Tests for execution find operations."""

    @pytest.mark.asyncio
    async def test_find_by_task(self, execution_repo, mock_db):
        """Test finding executions for a task."""
        task_id = uuid4()
        expected_executions = [
            {"id": uuid4(), "task_id": task_id, "status": "success"},
            {"id": uuid4(), "task_id": task_id, "status": "failed"},
        ]
        mock_db.fetch_all.return_value = expected_executions

        result = await execution_repo.find_by_task(task_id)

        assert result == expected_executions
        mock_db.fetch_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_task_with_status_filter(self, execution_repo, mock_db):
        """Test finding executions filtered by status."""
        task_id = uuid4()
        expected_executions = [{"id": uuid4(), "task_id": task_id, "status": "success"}]
        mock_db.fetch_all.return_value = expected_executions

        result = await execution_repo.find_by_task(task_id, status="success")

        assert result == expected_executions
        call_args = mock_db.fetch_all.call_args[0]
        assert "success" in call_args

    @pytest.mark.asyncio
    async def test_find_by_task_with_pagination(self, execution_repo, mock_db):
        """Test finding executions with pagination."""
        task_id = uuid4()
        expected_executions = [{"id": uuid4(), "task_id": task_id}]
        mock_db.fetch_all.return_value = expected_executions

        result = await execution_repo.find_by_task(task_id, limit=10, offset=20)

        assert result == expected_executions
        call_args = mock_db.fetch_all.call_args[0]
        assert "LIMIT" in call_args[0]
        assert "OFFSET" in call_args[0]

    @pytest.mark.asyncio
    async def test_find_notifications(self, execution_repo, mock_db):
        """Test finding executions where condition was met."""
        task_id = uuid4()
        expected_executions = [{"id": uuid4(), "condition_met": True, "task_id": task_id}]
        mock_db.fetch_all.return_value = expected_executions

        result = await execution_repo.find_notifications(task_id)

        assert result == expected_executions
        call_args = mock_db.fetch_all.call_args[0]
        assert "condition_met" in call_args[0]

    @pytest.mark.asyncio
    async def test_get_last_successful(self, execution_repo, mock_db):
        """Test getting last successful execution."""
        task_id = uuid4()
        expected_execution = {
            "id": uuid4(),
            "task_id": task_id,
            "status": "success",
        }
        mock_db.fetch_one.return_value = expected_execution

        result = await execution_repo.get_last_successful(task_id)

        assert result == expected_execution
        call_args = mock_db.fetch_one.call_args[0]
        assert "success" in call_args

    @pytest.mark.asyncio
    async def test_get_last_successful_none(self, execution_repo, mock_db):
        """Test getting last successful execution when none exist."""
        task_id = uuid4()
        mock_db.fetch_one.return_value = None

        result = await execution_repo.get_last_successful(task_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_count_by_task(self, execution_repo, mock_db):
        """Test counting executions for a task."""
        task_id = uuid4()
        mock_db.fetch_val.return_value = 5

        result = await execution_repo.count_by_task(task_id)

        assert result == 5

    @pytest.mark.asyncio
    async def test_count_by_task_with_status(self, execution_repo, mock_db):
        """Test counting executions filtered by status."""
        task_id = uuid4()
        mock_db.fetch_val.return_value = 3

        result = await execution_repo.count_by_task(task_id, status="failed")

        assert result == 3
