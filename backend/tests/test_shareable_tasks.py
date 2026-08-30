"""Tests for shareable tasks functionality."""

import json
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from webwhen.tasks.service import TaskNotFoundError, TaskService


@pytest.fixture
def mock_user():
    """Create a mock authenticated user."""
    user = MagicMock()
    user.id = uuid4()
    user.email = "user@example.com"
    return user


@pytest.fixture
def mock_db():
    """Create a mock database connection."""
    db = MagicMock()
    db.fetch_one = AsyncMock()
    db.fetch_all = AsyncMock()
    db.execute = AsyncMock()

    # Mock connection with transaction support
    mock_conn = MagicMock()
    mock_conn.execute = AsyncMock()
    mock_conn.fetchrow = AsyncMock()
    mock_conn.fetch = AsyncMock()

    # Mock transaction context manager
    mock_transaction = MagicMock()
    mock_transaction.__aenter__ = AsyncMock(return_value=mock_transaction)
    mock_transaction.__aexit__ = AsyncMock(return_value=None)
    mock_conn.transaction = MagicMock(return_value=mock_transaction)

    # Mock acquire context manager
    mock_acquire = MagicMock()
    mock_acquire.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_acquire.__aexit__ = AsyncMock(return_value=None)
    db.acquire = MagicMock(return_value=mock_acquire)

    return db


class TestTaskServiceForking:
    """Tests for task forking domain behavior."""

    @pytest.mark.asyncio
    async def test_fork_public_task(self, mock_user, mock_db):
        """Test forking a public task."""
        from datetime import UTC, datetime

        source_task_id = uuid4()
        other_user_id = uuid4()
        now = datetime.now(UTC)

        # Mock source task query (uses db.fetch_one)
        mock_db.fetch_one.return_value = {
            "id": source_task_id,
            "user_id": other_user_id,  # Not the current user
            "name": "Original Task",
            "is_public": True,
            "schedule": "0 9 * * *",
            "search_query": "test query",
            "condition_description": "test condition",
            "notifications": "[]",
            "notification_channels": [],
            "notification_email": None,
            "webhook_url": None,
            "webhook_secret": None,
        }

        # Mock forked task returned from INSERT (uses conn.fetchrow within transaction)
        mock_conn = await mock_db.acquire().__aenter__()
        mock_conn.fetchrow.return_value = {
            "id": uuid4(),
            "user_id": mock_user.id,
            "name": "My Fork",
            "schedule": "0 9 * * *",
            "state": "paused",
            "search_query": "test query",
            "condition_description": "test condition",
            "notifications": "[]",
            "notification_channels": [],
            "notification_email": None,
            "webhook_url": None,
            "webhook_secret": None,
            "is_public": False,
            "view_count": 0,
            "subscriber_count": 0,
            "forked_from_task_id": source_task_id,
            "created_at": now,
            "updated_at": now,
            "state_changed_at": now,
            "last_execution_id": None,
            "last_known_state": None,
        }

        result = await TaskService(mock_db).fork(source_task_id, mock_user.id, "My Fork")

        # Verify operations were called within transaction
        assert mock_conn.execute.call_count >= 1  # increment subscriber count
        assert result["name"] == "My Fork"
        assert result["forked_from_task_id"] == source_task_id

    @pytest.mark.asyncio
    async def test_fork_private_task_rejects_non_owner(self, mock_user, mock_db):
        source_task_id = uuid4()
        mock_db.fetch_one.return_value = {
            "id": source_task_id,
            "user_id": uuid4(),
            "is_public": False,
        }

        with pytest.raises(TaskNotFoundError, match="Task not found"):
            await TaskService(mock_db).fork(source_task_id, mock_user.id, None)

    @pytest.mark.asyncio
    async def test_fork_own_task_succeeds(self, mock_user, mock_db):
        """Test forking your own task - should succeed (duplicate behavior)."""
        from datetime import UTC, datetime

        task_id = uuid4()
        now = datetime.now(UTC)

        # Mock source task query
        mock_db.fetch_one.return_value = {
            "id": task_id,
            "user_id": mock_user.id,  # Own task
            "name": "Original Task",
            "is_public": True,
            "schedule": "0 9 * * *",
            "search_query": "test query",
            "condition_description": "test condition",
            "notifications": "[]",
            "notification_channels": [],
            "notification_email": None,
            "webhook_url": None,
            "webhook_secret": None,
        }

        # Mock forked task returned from INSERT within transaction
        mock_conn = await mock_db.acquire().__aenter__()
        mock_conn.fetchrow.return_value = {
            "id": uuid4(),
            "user_id": mock_user.id,
            "name": "My Duplicate",
            "schedule": "0 9 * * *",
            "state": "paused",
            "search_query": "test query",
            "condition_description": "test condition",
            "notifications": "[]",
            "notification_channels": [],
            "notification_email": None,
            "webhook_url": None,
            "webhook_secret": None,
            "is_public": False,
            "view_count": 0,
            "subscriber_count": 0,
            "forked_from_task_id": task_id,
            "created_at": now,
            "updated_at": now,
            "state_changed_at": now,
            "last_execution_id": None,
            "last_known_state": None,
        }

        result = await TaskService(mock_db).fork(task_id, mock_user.id, "My Duplicate")

        # Should succeed and create a duplicate
        assert result["name"] == "My Duplicate"
        assert result["forked_from_task_id"] == task_id
        # Owner duplicating their own task - subscriber count should NOT be incremented
        assert mock_conn.execute.call_count == 0

    @pytest.mark.asyncio
    async def test_fork_uses_default_name(self, mock_user, mock_db):
        """Test forking without custom name uses default."""
        from datetime import UTC, datetime

        source_task_id = uuid4()
        other_user_id = uuid4()
        now = datetime.now(UTC)

        # Mock source task query
        mock_db.fetch_one.return_value = {
            "id": source_task_id,
            "user_id": other_user_id,
            "name": "Original Task",
            "is_public": True,
            "schedule": "0 9 * * *",
            "search_query": "test",
            "condition_description": "test",
            "notifications": "[]",
            "notification_channels": [],
            "notification_email": None,
            "webhook_url": None,
            "webhook_secret": None,
        }

        # Mock forked task returned from INSERT
        mock_conn = await mock_db.acquire().__aenter__()
        mock_conn.fetchrow.return_value = {
            "id": uuid4(),
            "user_id": mock_user.id,
            "name": "Original Task (Copy)",
            "notifications": "[]",
            "schedule": "0 9 * * *",
            "state": "paused",
            "search_query": "test",
            "condition_description": "test",
            "notification_channels": [],
            "notification_email": None,
            "webhook_url": None,
            "webhook_secret": None,
            "is_public": False,
            "view_count": 0,
            "subscriber_count": 0,
            "forked_from_task_id": source_task_id,
            "created_at": now,
            "updated_at": now,
            "state_changed_at": now,
            "last_execution_id": None,
            "last_known_state": None,
        }

        result = await TaskService(mock_db).fork(source_task_id, mock_user.id, None)

        assert result["name"] == "Original Task (Copy)"

        # Verify the INSERT call includes the default name
        mock_conn.fetchrow.assert_called_once()
        insert_args = mock_conn.fetchrow.call_args[0]
        assert insert_args[2] == "Original Task (Copy)"

    @pytest.mark.asyncio
    async def test_fork_scrubs_sensitive_fields(self, mock_user, mock_db):
        """Test forking another user's task scrubs webhook secrets and email."""
        from datetime import UTC, datetime

        source_task_id = uuid4()
        other_user_id = uuid4()
        now = datetime.now(UTC)

        # Mock source task with sensitive data
        mock_db.fetch_one.return_value = {
            "id": source_task_id,
            "user_id": other_user_id,  # Not the current user
            "name": "Original Task",
            "is_public": True,
            "schedule": "0 9 * * *",
            "search_query": "test query",
            "condition_description": "test condition",
            "notifications": '[{"type": "email", "address": "owner@example.com"}]',
            "notification_channels": ["email", "webhook"],
            "notification_email": "owner@example.com",  # Should be scrubbed
            "webhook_url": "https://example.com/webhook",  # Should be scrubbed
            "webhook_secret": "super_secret_token",  # Should be scrubbed
        }

        # Mock forked task returned from INSERT within transaction
        mock_conn = await mock_db.acquire().__aenter__()
        mock_conn.fetchrow.return_value = {
            "id": uuid4(),
            "user_id": mock_user.id,
            "name": "Forked Task",
            "schedule": "0 9 * * *",
            "state": "paused",
            "search_query": "test query",
            "condition_description": "test condition",
            "notifications": '[{"type": "email", "address": "owner@example.com"}]',
            "notification_channels": [],  # Scrubbed
            "notification_email": None,  # Scrubbed
            "webhook_url": None,  # Scrubbed
            "webhook_secret": None,  # Scrubbed
            "is_public": False,
            "view_count": 0,
            "subscriber_count": 0,
            "forked_from_task_id": source_task_id,
            "created_at": now,
            "updated_at": now,
            "state_changed_at": now,
            "last_execution_id": None,
            "last_known_state": None,
        }

        result = await TaskService(mock_db).fork(source_task_id, mock_user.id, "Forked Task")

        # Verify task was still forked successfully
        assert result["name"] == "Forked Task"
        assert result["forked_from_task_id"] == source_task_id

        # Verify the INSERT call passed scrubbed values (not the original sensitive data)
        # Check the args passed to conn.fetchrow within the transaction
        insert_call = mock_conn.fetchrow.call_args_list[0]
        insert_args = insert_call[0]  # Positional args

        # The first arg is the query string. The subsequent args are the values.
        # Positional args to fetchrow after query: user_id(1), name(2), state(3),
        # search_query(4), condition_description(5), notifications(6),
        # notification_channels(7), notification_email(8), webhook_url(9), webhook_secret(10)
        assert insert_args[6] == json.dumps(
            []
        )  # notifications should be an empty JSON array string
        assert insert_args[7] == []  # notification_channels should be empty list
        assert insert_args[8] is None  # notification_email should be None
        assert insert_args[9] is None  # webhook_url should be None
        assert insert_args[10] is None  # webhook_secret should be None
