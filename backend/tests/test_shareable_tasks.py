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
from torale.api.routers.usernames import (
    SetUsernameRequest,
    check_username_availability,
    set_username,
)
from torale.utils.slug import generate_unique_slug
from torale.utils.username import check_username_available, validate_username


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


class TestUsernameValidation:
    """Tests for username validation."""

    @pytest.mark.asyncio
    async def test_valid_username(self, mock_db):
        """Test valid username formats."""
        mock_db.fetch_one.return_value = None  # Not reserved

        valid_usernames = [
            "alice",
            "bob123",
            "user_name",
            "test-user",
            "a1b2c3",
        ]
        for username in valid_usernames:
            is_valid, error = await validate_username(username, mock_db)
            assert is_valid, f"Username '{username}' should be valid but got error: {error}"
            assert error == ""

    @pytest.mark.asyncio
    async def test_username_too_short(self, mock_db):
        """Test username shorter than 3 characters."""
        is_valid, error = await validate_username("ab", mock_db)
        assert not is_valid
        assert "at least 3 characters" in error

    @pytest.mark.asyncio
    async def test_username_too_long(self, mock_db):
        """Test username longer than 30 characters."""
        is_valid, error = await validate_username("a" * 31, mock_db)
        assert not is_valid
        assert "30 characters or less" in error

    @pytest.mark.asyncio
    async def test_username_invalid_start(self, mock_db):
        """Test username not starting with letter."""
        invalid_starts = ["1user", "_user", "-user"]
        for username in invalid_starts:
            is_valid, error = await validate_username(username, mock_db)
            assert not is_valid
            assert "start with a letter" in error

    @pytest.mark.asyncio
    async def test_username_invalid_characters(self, mock_db):
        """Test username with invalid characters."""
        invalid_usernames = [
            "user@name",
            "user.name",
            "user name",
            "user!",
        ]
        for username in invalid_usernames:
            is_valid, error = await validate_username(username, mock_db)
            assert not is_valid

    @pytest.mark.asyncio
    async def test_reserved_username(self, mock_db):
        """Test reserved usernames are rejected."""
        # Mock database returning reserved username match
        mock_db.fetch_one.return_value = {"username": "admin"}

        reserved = ["admin", "api", "explore", "settings", "support"]
        for username in reserved:
            is_valid, error = await validate_username(username, mock_db)
            assert not is_valid
            assert "reserved" in error


class TestUsernameAvailability:
    """Tests for username availability checking."""

    @pytest.mark.asyncio
    async def test_username_available(self, mock_db):
        """Test checking available username."""
        mock_db.fetch_one.return_value = None  # No existing user

        available = await check_username_available("newuser", mock_db)

        assert available is True

    @pytest.mark.asyncio
    async def test_username_taken(self, mock_db):
        """Test checking taken username."""
        mock_db.fetch_one.return_value = {"id": uuid4()}  # Existing user

        available = await check_username_available("existinguser", mock_db)

        assert available is False

    @pytest.mark.asyncio
    async def test_username_available_exclude_self(self, mock_db):
        """Test checking username availability excluding current user."""
        user_id = uuid4()
        mock_db.fetch_one.return_value = None  # No other user with this username

        available = await check_username_available("myusername", mock_db, exclude_user_id=user_id)

        assert available is True


class TestUsernameEndpoints:
    """Tests for username API endpoints."""

    @pytest.mark.asyncio
    async def test_check_availability_endpoint(self, mock_db):
        """Test GET /api/v1/users/username/available."""
        # First call: reserved check (None = not reserved)
        # Second call: availability check (None = available)
        mock_db.fetch_one.side_effect = [None, None]

        result = await check_username_availability(None, "newuser", mock_db)

        assert result.available is True
        assert result.error is None

    @pytest.mark.asyncio
    async def test_check_availability_invalid_format(self, mock_db):
        """Test availability check with invalid username format."""
        result = await check_username_availability(None, "ab", mock_db)

        assert result.available is False
        assert "at least 3 characters" in result.error

    @pytest.mark.asyncio
    async def test_set_username_success(self, mock_user, mock_db):
        """Test PATCH /api/v1/users/me/username - successful update."""
        request = SetUsernameRequest(username="newusername")
        # First call: existing username check (None = no username set yet)
        # Second call: reserved check (None = not reserved)
        # Third call: availability check (None = available)
        mock_db.fetch_one.side_effect = [None, None, None]

        result = await set_username(request, mock_user, mock_db)

        assert result.username == "newusername"
        assert result.updated is True
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_username_taken(self, mock_user, mock_db):
        """Test setting username that's already taken."""
        request = SetUsernameRequest(username="takenname")
        # First call: existing username check (None = no username set yet)
        # Second call: reserved check (None = not reserved)
        # Third call: availability check (user found = taken)
        mock_db.fetch_one.side_effect = [None, None, {"id": uuid4()}]

        with pytest.raises(HTTPException) as exc_info:
            await set_username(request, mock_user, mock_db)

        assert exc_info.value.status_code == 400
        assert "already taken" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_set_username_invalid(self, mock_user, mock_db):
        """Test setting invalid username."""
        request = SetUsernameRequest(username="admin")  # Reserved
        # Reserved username found in DB
        mock_db.fetch_one.return_value = {"username": "admin"}

        with pytest.raises(HTTPException) as exc_info:
            await set_username(request, mock_user, mock_db)

        assert exc_info.value.status_code == 400


class TestSlugGeneration:
    """Tests for slug generation utility."""

    @pytest.mark.asyncio
    async def test_generate_unique_slug_simple(self, mock_db):
        """Test generating slug from task name."""
        mock_db.fetch_all.return_value = []  # No existing slugs

        slug = await generate_unique_slug("My Cool Task", uuid4(), mock_db)

        assert slug == "my-cool-task"

    @pytest.mark.asyncio
    async def test_generate_unique_slug_with_collision(self, mock_db):
        """Test slug generation with collision handling."""
        user_id = uuid4()

        # Return existing slug "my-task", so next available is "my-task-2"
        mock_db.fetch_all.return_value = [{"slug": "my-task"}]

        slug = await generate_unique_slug("My Task", user_id, mock_db)

        assert slug == "my-task-2"

    @pytest.mark.asyncio
    async def test_generate_slug_from_special_characters(self, mock_db):
        """Test slug generation with special characters."""
        mock_db.fetch_all.return_value = []  # No existing slugs

        slug = await generate_unique_slug("Task: #1 @home!", uuid4(), mock_db)

        assert slug == "task-1-home"


class TestTaskVisibilityToggle:
    """Tests for task visibility endpoint."""

    @pytest.mark.asyncio
    async def test_make_task_public_with_username(self, mock_user, mock_db):
        """Test making task public when user has username."""
        task_id = uuid4()
        request = VisibilityUpdateRequest(is_public=True)

        # Mock task query
        mock_db.fetch_one.side_effect = [
            {"id": task_id, "name": "Test Task", "slug": None, "is_public": False},  # Task
            {"username": "testuser"},  # User has username
            None,  # Slug availability check (no collision)
        ]

        result = await update_task_visibility(task_id, request, mock_user, mock_db)

        assert result.is_public is True
        assert result.slug is not None
        mock_db.execute.assert_called()

    @pytest.mark.asyncio
    async def test_make_task_public_without_username(self, mock_user, mock_db):
        """Test making task public without username - should fail."""
        task_id = uuid4()
        request = VisibilityUpdateRequest(is_public=True)

        mock_db.fetch_one.side_effect = [
            {"id": task_id, "name": "Test Task", "slug": None, "is_public": False},  # Task
            {"username": None},  # User has no username
        ]

        with pytest.raises(HTTPException) as exc_info:
            await update_task_visibility(task_id, request, mock_user, mock_db)

        assert exc_info.value.status_code == 400
        assert "username" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_make_task_private(self, mock_user, mock_db):
        """Test making task private."""
        task_id = uuid4()
        request = VisibilityUpdateRequest(is_public=False)

        mock_db.fetch_one.return_value = {
            "id": task_id,
            "name": "Test Task",
            "slug": "test-task",
            "is_public": True,
        }

        result = await update_task_visibility(task_id, request, mock_user, mock_db)

        assert result.is_public is False
        mock_db.execute.assert_called()

    @pytest.mark.asyncio
    async def test_make_task_public_already_has_slug(self, mock_user, mock_db):
        """Test making task public when slug already exists."""
        task_id = uuid4()
        request = VisibilityUpdateRequest(is_public=True)

        mock_db.fetch_one.side_effect = [
            {"id": task_id, "name": "Test Task", "slug": "existing-slug", "is_public": False},
            {"username": "testuser"},
        ]

        result = await update_task_visibility(task_id, request, mock_user, mock_db)

        assert result.is_public is True
        assert result.slug == "existing-slug"


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
            "slug": "public-task",
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
            "creator_username": "testuser",  # Add missing creator_username field
            # Execution fields (LEFT JOIN result - no execution)
            "exec_id": None,
            "exec_notification": None,
            "exec_started_at": None,
            "exec_completed_at": None,
            "exec_status": None,
            "exec_result": None,
            "exec_change_summary": None,
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
            "slug": None,
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
            "creator_username": "testuser",  # Add missing creator_username field
            # Execution fields (LEFT JOIN result - no execution)
            "exec_id": None,
            "exec_notification": None,
            "exec_started_at": None,
            "exec_completed_at": None,
            "exec_status": None,
            "exec_result": None,
            "exec_change_summary": None,
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
            "slug": None,
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
            "slug": None,
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
            "slug": None,
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
            "slug": None,
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
        # Positional args to fetchrow after query: user_id(1), name(2), schedule(3),
        # state(4), search_query(5), condition_description(6), notify_behavior(7),
        # notifications(8), notification_channels(9), notification_email(10), webhook_url(11), webhook_secret(12)
        assert insert_args[8] == json.dumps(
            []
        )  # notifications should be an empty JSON array string
        assert insert_args[9] == []  # notification_channels should be empty list
        assert insert_args[10] is None  # notification_email should be None
        assert insert_args[11] is None  # webhook_url should be None
        assert insert_args[12] is None  # webhook_secret should be None
