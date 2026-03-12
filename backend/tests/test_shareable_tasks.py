"""Tests for shareable tasks functionality."""

import json
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from torale.api.routers.tasks import (
    ForkTaskRequest,
    VisibilityUpdateRequest,
    fork_task,
    get_task,
    update_task_visibility,
)


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


class TestTaskVisibilityToggle:
    """Tests for task visibility endpoint."""

    @pytest.mark.asyncio
    async def test_make_task_public(self, mock_user, mock_db):
        """Test making task public."""
        task_id = uuid4()
        request = VisibilityUpdateRequest(is_public=True)

        # Mock task query
        mock_db.fetch_one.return_value = {
            "id": task_id,
            "is_public": False,
        }

        result = await update_task_visibility(task_id, request, mock_user, mock_db)

        assert result.is_public is True
        mock_db.execute.assert_called()

    @pytest.mark.asyncio
    async def test_make_task_private(self, mock_user, mock_db):
        """Test making task private."""
        task_id = uuid4()
        request = VisibilityUpdateRequest(is_public=False)

        mock_db.fetch_one.return_value = {
            "id": task_id,
            "is_public": True,
        }

        result = await update_task_visibility(task_id, request, mock_user, mock_db)

        assert result.is_public is False
        mock_db.execute.assert_called()


class TestPublicTaskAccess:
    """Tests for public task access."""

    @pytest.mark.asyncio
    async def test_get_public_task_unauthenticated(self, mock_db):
        """Test accessing public task without authentication."""
        from datetime import UTC, datetime

        task_id = uuid4()
        user_id = uuid4()
        now = datetime.now(UTC)

        # Complete mock task with all required fields for _parse_task_with_execution
        # Note: For public viewers, sensitive fields should be None (scrubbed)
        mock_task_row = {
            "id": task_id,
            "user_id": user_id,
            "name": "Public Task",
            "is_public": True,
            "view_count": 0,
            "subscriber_count": 0,
            "last_known_state": None,
            "notifications": "[]",
            "schedule": "0 9 * * *",
            "search_query": "test query",
            "condition_description": "test condition",
            "notify_behavior": "always",
            "notification_channels": [],
            "notification_email": None,  # These will be scrubbed for public viewers
            "webhook_url": None,
            "webhook_secret": None,
            "state": "active",
            "forked_from_task_id": None,
            "created_at": now,
            "updated_at": now,
            "state_changed_at": now,
            "last_execution_id": None,
            # Execution fields (LEFT JOIN result - no execution)
            "exec_id": None,
            "exec_notification": None,
            "exec_started_at": None,
            "exec_completed_at": None,
            "exec_status": None,
            "exec_result": None,
            "exec_grounding_sources": None,
        }

        mock_db.fetch_one.return_value = mock_task_row

        # Call with no user (OptionalUser = None) - should succeed for public tasks
        result = await get_task(task_id, None, mock_db)

        # Verify public task is accessible
        assert result.id == task_id
        assert result.name == "Public Task"
        assert result.is_public is True
        # Verify sensitive fields are scrubbed for public viewers
        assert result.notification_email is None
        assert result.webhook_url is None
        assert result.notifications == []

    @pytest.mark.asyncio
    async def test_get_private_task_unauthenticated(self, mock_db):
        """Test accessing private task without authentication - should fail."""
        task_id = uuid4()
        user_id = uuid4()

        mock_db.fetch_one.return_value = {
            "id": task_id,
            "user_id": user_id,
            "is_public": False,
        }

        with pytest.raises(HTTPException) as exc_info:
            await get_task(task_id, None, mock_db)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_own_private_task_authenticated(self, mock_user, mock_db):
        """Test owner can access their own private task."""
        from datetime import UTC, datetime

        task_id = uuid4()
        now = datetime.now(UTC)

        # Complete mock task with all required fields for _parse_task_with_execution
        mock_task_row = {
            "id": task_id,
            "user_id": mock_user.id,  # Owner
            "name": "Private Task",
            "is_public": False,
            "view_count": 0,
            "subscriber_count": 0,
            "last_known_state": None,
            "notifications": "[]",
            "schedule": "0 9 * * *",
            "search_query": "test query",
            "condition_description": "test condition",
            "notify_behavior": "always",
            "notification_channels": [],
            "notification_email": None,
            "webhook_url": None,
            "webhook_secret": None,
            "state": "active",
            "forked_from_task_id": None,
            "created_at": now,
            "updated_at": now,
            "state_changed_at": now,
            "last_execution_id": None,
            # Execution fields (LEFT JOIN result - no execution)
            "exec_id": None,
            "exec_notification": None,
            "exec_started_at": None,
            "exec_completed_at": None,
            "exec_status": None,
            "exec_result": None,
            "exec_grounding_sources": None,
        }

        mock_db.fetch_one.return_value = mock_task_row

        # Should not raise exception (owner can access own private tasks)
        result = await get_task(task_id, mock_user, mock_db)

        # Verify owner can access their own private task
        assert result.id == task_id
        assert result.name == "Private Task"
        assert result.is_public is False


class TestTaskForking:
    """Tests for task forking endpoint."""

    @pytest.mark.asyncio
    async def test_fork_public_task(self, mock_user, mock_db):
        """Test forking a public task."""
        from datetime import UTC, datetime

        source_task_id = uuid4()
        other_user_id = uuid4()
        request = ForkTaskRequest(name="My Fork")
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
            "notify_behavior": "always",
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
            "notify_behavior": "always",
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

        result = await fork_task(source_task_id, request, mock_user, mock_db)

        # Verify operations were called within transaction
        assert mock_conn.execute.call_count >= 1  # increment subscriber count
        assert result.name == "My Fork"
        assert result.forked_from_task_id == source_task_id

    @pytest.mark.asyncio
    async def test_fork_private_task_fails(self, mock_user, mock_db):
        """Test forking a private task - should fail."""
        source_task_id = uuid4()
        other_user_id = uuid4()
        request = ForkTaskRequest()

        mock_db.fetch_one.return_value = {
            "id": source_task_id,
            "user_id": other_user_id,
            "is_public": False,  # Private task
        }

        with pytest.raises(HTTPException) as exc_info:
            await fork_task(source_task_id, request, mock_user, mock_db)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_fork_own_task_succeeds(self, mock_user, mock_db):
        """Test forking your own task - should succeed (duplicate behavior)."""
        from datetime import UTC, datetime

        task_id = uuid4()
        request = ForkTaskRequest(name="My Duplicate")
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
            "notify_behavior": "always",
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
            "notify_behavior": "always",
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

        result = await fork_task(task_id, request, mock_user, mock_db)

        # Should succeed and create a duplicate
        assert result.name == "My Duplicate"
        assert result.forked_from_task_id == task_id
        # Owner duplicating their own task - subscriber count should NOT be incremented
        assert mock_conn.execute.call_count == 0

    @pytest.mark.asyncio
    async def test_fork_uses_default_name(self, mock_user, mock_db):
        """Test forking without custom name uses default."""
        from datetime import UTC, datetime

        source_task_id = uuid4()
        other_user_id = uuid4()
        request = ForkTaskRequest()  # No custom name
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
            "notify_behavior": "always",
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
            "notify_behavior": "always",
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

        result = await fork_task(source_task_id, request, mock_user, mock_db)

        assert result.name == "Original Task (Copy)"

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
        request = ForkTaskRequest(name="Forked Task")
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
            "notify_behavior": "always",
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
            "notify_behavior": "always",
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

        result = await fork_task(source_task_id, request, mock_user, mock_db)

        # Verify task was still forked successfully
        assert result.name == "Forked Task"
        assert result.forked_from_task_id == source_task_id

        # Verify the INSERT call passed scrubbed values (not the original sensitive data)
        # Check the args passed to conn.fetchrow within the transaction
        insert_call = mock_conn.fetchrow.call_args_list[0]
        insert_args = insert_call[0]  # Positional args

        # The first arg is the query string. The subsequent args are the values.
        # Positional args to fetchrow after query: user_id(1), name(2), state(3),
        # search_query(4), condition_description(5), notify_behavior(6),
        # notifications(7), notification_channels(8), notification_email(9), webhook_url(10), webhook_secret(11)
        assert insert_args[7] == json.dumps(
            []
        )  # notifications should be an empty JSON array string
        assert insert_args[8] == []  # notification_channels should be empty list
        assert insert_args[9] is None  # notification_email should be None
        assert insert_args[10] is None  # webhook_url should be None
        assert insert_args[11] is None  # webhook_secret should be None
