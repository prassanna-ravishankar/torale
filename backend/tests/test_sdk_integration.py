"""Integration tests for Torale Python SDK.

These tests verify the SDK works correctly against a real API instance,
testing all CRUD operations, notifications, and error handling.

Prerequisites:
- Local dev environment running (`just dev`)
- TORALE_NOAUTH=1 environment variable set

Run with:
    # Run all tests (will auto-skip if API not available)
    pytest tests/test_sdk_integration.py -v

    # Run specific test class
    pytest tests/test_sdk_integration.py::TestSDKBasicOperations -v

Note: These tests automatically skip if the API server isn't running (similar to
      test_gemini_integration.py). They're safe to run in CI.
"""

import os
import uuid
from datetime import datetime

import httpx
import pytest

from torale.sdk import Torale
from torale.sdk.exceptions import AuthenticationError, NotFoundError, ValidationError


def check_api_available() -> bool:
    """Check if the API server is available."""
    api_url = os.getenv("TORALE_API_URL", "http://localhost:8000")
    try:
        # Try to connect to the API (any response means it's up)
        httpx.get(f"{api_url}/api/v1/tasks", timeout=2.0, follow_redirects=True)
        # Any HTTP response (even 401/403) means API is running
        return True
    except (httpx.ConnectError, httpx.TimeoutException):
        return False
    except Exception:
        # Other errors (like auth errors) mean API is running
        return True


@pytest.fixture
def sdk_client():
    """Create SDK client with proper cleanup."""
    # Check if API is available
    if not check_api_available():
        pytest.skip("API server not available (start with `just dev`)")

    # Use TORALE_NOAUTH=1 for local testing
    if not os.getenv("TORALE_NOAUTH"):
        pytest.skip("TORALE_NOAUTH not set (required for integration tests)")

    client = Torale()
    yield client
    client.close()


@pytest.fixture
def test_task(sdk_client):
    """Create a test task and clean it up after the test."""
    task = sdk_client.tasks.create(
        name=f"Test Task {uuid.uuid4().hex[:8]}",
        search_query="When is the next iPhone being released?",
        condition_description="A specific release date has been announced",
        schedule="0 9 * * *",
        notify_behavior="once",
    )
    yield task
    # Cleanup
    try:
        sdk_client.tasks.delete(task.id)
    except NotFoundError:
        pass  # Already deleted


class TestSDKBasicOperations:
    """Test basic CRUD operations."""

    def test_create_task_minimal(self, sdk_client):
        """Test creating a task with minimal required fields."""
        task = sdk_client.tasks.create(
            name="Minimal Test Task",
            search_query="Test query",
            condition_description="Test condition",
        )

        assert task.id is not None
        assert task.name == "Minimal Test Task"
        assert task.search_query == "Test query"
        assert task.condition_description == "Test condition"
        assert task.schedule == "0 9 * * *"  # Default schedule
        assert task.is_active is True
        assert task.created_at is not None

        # Cleanup
        sdk_client.tasks.delete(task.id)

    def test_create_task_with_webhook(self, sdk_client):
        """Test creating a task with webhook notification."""
        task = sdk_client.tasks.create(
            name="Webhook Test Task",
            search_query="Test query",
            condition_description="Test condition",
            notifications=[{"type": "webhook", "url": "https://webhook.site/test"}],
        )

        assert task.notifications is not None
        assert len(task.notifications) == 1
        # NotificationConfig objects use attribute access
        assert task.notifications[0].type == "webhook"
        assert task.notifications[0].url == "https://webhook.site/test"

        # Cleanup
        sdk_client.tasks.delete(task.id)

    def test_create_task_with_email(self, sdk_client):
        """Test creating a task with email notification."""
        task = sdk_client.tasks.create(
            name="Email Test Task",
            search_query="Test query",
            condition_description="Test condition",
            notifications=[{"type": "email", "address": "test@example.com"}],
        )

        assert task.notifications is not None
        assert len(task.notifications) == 1
        # NotificationConfig objects use attribute access
        assert task.notifications[0].type == "email"
        assert task.notifications[0].address == "test@example.com"

        # Cleanup
        sdk_client.tasks.delete(task.id)

    def test_create_task_with_multiple_notification_types(self, sdk_client):
        """Test creating a task with both email and webhook."""
        task = sdk_client.tasks.create(
            name="Multi-Notification Test Task",
            search_query="Test query",
            condition_description="Test condition",
            notifications=[
                {"type": "email", "address": "test@example.com"},
                {"type": "webhook", "url": "https://webhook.site/test"},
            ],
        )

        assert task.notifications is not None
        assert len(task.notifications) == 2

        # NotificationConfig objects use attribute access
        notification_types = {n.type for n in task.notifications}
        assert "email" in notification_types
        assert "webhook" in notification_types

        # Cleanup
        sdk_client.tasks.delete(task.id)

    def test_list_tasks(self, sdk_client, test_task):
        """Test listing tasks."""
        tasks = sdk_client.tasks.list()

        assert isinstance(tasks, list)
        assert len(tasks) > 0
        assert any(t.id == test_task.id for t in tasks)

    def test_list_tasks_active_filter(self, sdk_client, test_task):
        """Test listing only active tasks."""
        # Deactivate the test task
        sdk_client.tasks.update(test_task.id, is_active=False)

        # List active tasks - should not include our deactivated task
        active_tasks = sdk_client.tasks.list(active=True)
        assert not any(t.id == test_task.id for t in active_tasks)

        # List all tasks - should include our deactivated task
        all_tasks = sdk_client.tasks.list()
        assert any(t.id == test_task.id for t in all_tasks)

    def test_get_task(self, sdk_client, test_task):
        """Test getting a specific task."""
        task = sdk_client.tasks.get(test_task.id)

        assert task.id == test_task.id
        assert task.name == test_task.name
        assert task.search_query == test_task.search_query
        assert task.condition_description == test_task.condition_description

    def test_update_task_name(self, sdk_client, test_task):
        """Test updating task name."""
        new_name = f"Updated Task {uuid.uuid4().hex[:8]}"
        updated_task = sdk_client.tasks.update(test_task.id, name=new_name)

        assert updated_task.id == test_task.id
        assert updated_task.name == new_name

    def test_update_task_schedule(self, sdk_client, test_task):
        """Test updating task schedule."""
        new_schedule = "0 */6 * * *"  # Every 6 hours
        updated_task = sdk_client.tasks.update(test_task.id, schedule=new_schedule)

        assert updated_task.schedule == new_schedule

    def test_update_task_active_status(self, sdk_client, test_task):
        """Test activating/deactivating task."""
        # Deactivate
        updated_task = sdk_client.tasks.update(test_task.id, is_active=False)
        assert updated_task.is_active is False

        # Reactivate
        updated_task = sdk_client.tasks.update(test_task.id, is_active=True)
        assert updated_task.is_active is True

    def test_delete_task(self, sdk_client):
        """Test deleting a task."""
        # Create a task to delete
        task = sdk_client.tasks.create(
            name="Task to Delete",
            search_query="Test query",
            condition_description="Test condition",
        )

        task_id = task.id

        # Delete it
        sdk_client.tasks.delete(task_id)

        # Verify it's gone
        with pytest.raises(NotFoundError):
            sdk_client.tasks.get(task_id)


class TestSDKExecution:
    """Test task execution operations."""

    def test_execute_task(self, sdk_client, test_task):
        """Test manually executing a task."""
        execution = sdk_client.tasks.execute(test_task.id)

        assert execution.id is not None
        assert execution.task_id == test_task.id
        assert execution.status in ["pending", "running", "success", "failed"]
        assert execution.started_at is not None

    def test_get_executions(self, sdk_client, test_task):
        """Test getting execution history."""
        # Execute the task first
        sdk_client.tasks.execute(test_task.id)

        # Get executions
        executions = sdk_client.tasks.executions(test_task.id, limit=10)

        assert isinstance(executions, list)
        assert len(executions) > 0
        assert all(e.task_id == test_task.id for e in executions)

    def test_get_executions_with_limit(self, sdk_client, test_task):
        """Test getting executions with limit."""
        # Execute multiple times
        for _ in range(3):
            sdk_client.tasks.execute(test_task.id)

        # Get only 2 executions
        executions = sdk_client.tasks.executions(test_task.id, limit=2)

        assert len(executions) <= 2

    def test_get_notifications(self, sdk_client, test_task):
        """Test getting notifications (executions where condition was met)."""
        # Execute the task
        sdk_client.tasks.execute(test_task.id)

        # Get notifications
        notifications = sdk_client.tasks.notifications(test_task.id, limit=10)

        # Should return empty or contain executions with condition_met=True
        assert isinstance(notifications, list)
        if len(notifications) > 0:
            assert all(n.condition_met is True for n in notifications)


class TestSDKValidation:
    """Test validation and error handling."""

    def test_duplicate_webhook_notifications_rejected(self, sdk_client):
        """Test that multiple webhooks are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            sdk_client.tasks.create(
                name="Duplicate Webhook Test",
                search_query="Test query",
                condition_description="Test condition",
                notifications=[
                    {"type": "webhook", "url": "https://example.com/hook1"},
                    {"type": "webhook", "url": "https://example.com/hook2"},
                ],
            )

        assert "same type" in str(exc_info.value).lower()

    def test_duplicate_email_notifications_rejected(self, sdk_client):
        """Test that multiple emails are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            sdk_client.tasks.create(
                name="Duplicate Email Test",
                search_query="Test query",
                condition_description="Test condition",
                notifications=[
                    {"type": "email", "address": "test1@example.com"},
                    {"type": "email", "address": "test2@example.com"},
                ],
            )

        assert "same type" in str(exc_info.value).lower()

    def test_invalid_email_format_rejected(self, sdk_client):
        """Test that invalid email format is rejected."""
        # Invalid email should be caught by backend validation
        with pytest.raises((ValidationError, Exception)) as exc_info:
            sdk_client.tasks.create(
                name="Invalid Email Test",
                search_query="Test query",
                condition_description="Test condition",
                notifications=[{"type": "email", "address": "not-an-email"}],
            )

        # Check error message contains validation info
        error_msg = str(exc_info.value).lower()
        assert "email" in error_msg or "invalid" in error_msg or "format" in error_msg

    def test_http_webhook_rejected(self, sdk_client):
        """Test that non-HTTPS webhooks are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            sdk_client.tasks.create(
                name="HTTP Webhook Test",
                search_query="Test query",
                condition_description="Test condition",
                notifications=[{"type": "webhook", "url": "http://example.com/hook"}],
            )

        assert "https" in str(exc_info.value).lower()

    def test_get_nonexistent_task_raises_not_found(self, sdk_client):
        """Test that getting a non-existent task raises NotFoundError."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        with pytest.raises(NotFoundError):
            sdk_client.tasks.get(fake_id)

    def test_delete_nonexistent_task_raises_not_found(self, sdk_client):
        """Test that deleting a non-existent task raises NotFoundError."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        with pytest.raises(NotFoundError):
            sdk_client.tasks.delete(fake_id)

    def test_execute_nonexistent_task_raises_not_found(self, sdk_client):
        """Test that executing a non-existent task raises NotFoundError."""
        fake_id = "00000000-0000-0000-0000-000000000000"

        with pytest.raises(NotFoundError):
            sdk_client.tasks.execute(fake_id)


class TestSDKContextManager:
    """Test context manager functionality."""

    def test_context_manager_basic(self):
        """Test basic context manager usage."""
        # Skip if API not available or NOAUTH not set
        if not check_api_available():
            pytest.skip("API server not available (start with `just dev`)")
        if not os.getenv("TORALE_NOAUTH"):
            pytest.skip("TORALE_NOAUTH not set (required for integration tests)")

        with Torale() as client:
            tasks = client.tasks.list()
            assert isinstance(tasks, list)

    def test_context_manager_creates_task(self):
        """Test creating a task within context manager."""
        # Skip if API not available or NOAUTH not set
        if not check_api_available():
            pytest.skip("API server not available (start with `just dev`)")
        if not os.getenv("TORALE_NOAUTH"):
            pytest.skip("TORALE_NOAUTH not set (required for integration tests)")

        task_id = None

        with Torale() as client:
            task = client.tasks.create(
                name="Context Manager Test",
                search_query="Test query",
                condition_description="Test condition",
            )
            task_id = task.id
            assert task.id is not None

        # Cleanup (need new client since context manager closed)
        cleanup_client = Torale()
        try:
            cleanup_client.tasks.delete(task_id)
        finally:
            cleanup_client.close()

    def test_multiple_sequential_context_managers(self):
        """Test using multiple context managers sequentially."""
        # Skip if API not available or NOAUTH not set
        if not check_api_available():
            pytest.skip("API server not available (start with `just dev`)")
        if not os.getenv("TORALE_NOAUTH"):
            pytest.skip("TORALE_NOAUTH not set (required for integration tests)")

        task_id = None

        # Create task in first context
        with Torale() as client1:
            task = client1.tasks.create(
                name="Sequential Context Test",
                search_query="Test query",
                condition_description="Test condition",
            )
            task_id = task.id

        # Verify task exists in second context
        with Torale() as client2:
            retrieved_task = client2.tasks.get(task_id)
            assert retrieved_task.id == task_id

        # Cleanup in third context
        with Torale() as client3:
            client3.tasks.delete(task_id)


class TestSDKConfiguration:
    """Test SDK configuration and initialization."""

    def test_sdk_respects_api_url_env_var(self, monkeypatch):
        """Test that SDK respects TORALE_API_URL environment variable."""
        # Need NOAUTH for client initialization
        if not os.getenv("TORALE_NOAUTH"):
            pytest.skip("TORALE_NOAUTH not set (required for integration tests)")

        custom_url = "http://custom-api:9000"
        monkeypatch.setenv("TORALE_API_URL", custom_url)

        client = Torale()
        assert client.api_url == custom_url
        client.close()

    def test_sdk_respects_api_key_env_var(self, monkeypatch):
        """Test that SDK respects TORALE_API_KEY environment variable."""
        # Remove NOAUTH if set
        monkeypatch.delenv("TORALE_NOAUTH", raising=False)

        custom_key = "sk_test_custom_key_12345"
        monkeypatch.setenv("TORALE_API_KEY", custom_key)

        # This will fail auth unless NOAUTH is set, but we're just testing initialization
        try:
            client = Torale()
            # In real scenario with auth, this would use the API key
            client.close()
        except AuthenticationError:
            # Expected if no valid auth is configured
            pass

    def test_sdk_with_explicit_api_url(self):
        """Test creating SDK client with explicit api_url."""
        # Need NOAUTH for client initialization
        if not os.getenv("TORALE_NOAUTH"):
            pytest.skip("TORALE_NOAUTH not set (required for integration tests)")

        client = Torale(api_url="http://localhost:8000")
        assert client.api_url == "http://localhost:8000"
        client.close()

    def test_sdk_with_explicit_api_key(self):
        """Test creating SDK client with explicit api_key."""
        # This will fail auth in tests, but we're testing initialization
        try:
            client = Torale(api_key="sk_test_explicit_key")
            client.close()
        except AuthenticationError:
            # Expected if TORALE_NOAUTH is not set
            pass


class TestSDKDataTypes:
    """Test that SDK properly handles different data types."""

    def test_task_timestamps_are_datetime(self, sdk_client, test_task):
        """Test that timestamps are properly parsed as datetime objects."""
        task = sdk_client.tasks.get(test_task.id)

        assert isinstance(task.created_at, datetime)
        assert isinstance(task.updated_at, datetime)

    def test_execution_timestamps_are_datetime(self, sdk_client, test_task):
        """Test that execution timestamps are datetime objects."""
        execution = sdk_client.tasks.execute(test_task.id)

        assert isinstance(execution.started_at, datetime)
        # completed_at might be None if still running
        if execution.completed_at is not None:
            assert isinstance(execution.completed_at, datetime)

    def test_task_config_is_dict(self, sdk_client, test_task):
        """Test that task config is properly returned as dict."""
        task = sdk_client.tasks.get(test_task.id)

        assert isinstance(task.config, dict)
        assert "model" in task.config

    def test_notifications_are_list_of_notification_config(self, sdk_client):
        """Test that notifications are returned as list of NotificationConfig objects."""
        task = sdk_client.tasks.create(
            name="Notifications Type Test",
            search_query="Test query",
            condition_description="Test condition",
            notifications=[{"type": "webhook", "url": "https://example.com/hook"}],
        )

        assert isinstance(task.notifications, list)
        assert len(task.notifications) > 0
        # Notifications are NotificationConfig objects, not dicts
        assert hasattr(task.notifications[0], "type")
        assert task.notifications[0].type == "webhook"

        # Cleanup
        sdk_client.tasks.delete(task.id)


class TestSDKEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_create_task_with_empty_notifications_list(self, sdk_client):
        """Test creating a task with empty notifications list."""
        task = sdk_client.tasks.create(
            name="No Notifications Test",
            search_query="Test query",
            condition_description="Test condition",
            notifications=[],
        )

        assert task.notifications == []

        # Cleanup
        sdk_client.tasks.delete(task.id)

    def test_create_task_with_custom_schedule(self, sdk_client):
        """Test creating a task with custom cron schedule."""
        custom_schedule = "*/15 * * * *"  # Every 15 minutes

        task = sdk_client.tasks.create(
            name="Custom Schedule Test",
            search_query="Test query",
            condition_description="Test condition",
            schedule=custom_schedule,
        )

        assert task.schedule == custom_schedule

        # Cleanup
        sdk_client.tasks.delete(task.id)

    def test_update_task_with_no_changes(self, sdk_client, test_task):
        """Test updating a task with no actual changes."""
        # Get original values
        original = sdk_client.tasks.get(test_task.id)

        # Update with same values (effectively no change)
        updated = sdk_client.tasks.update(
            test_task.id, name=original.name, schedule=original.schedule
        )

        assert updated.name == original.name
        assert updated.schedule == original.schedule

    def test_list_tasks_when_empty(self, sdk_client):
        """Test listing tasks when no tasks exist (cleanup all first)."""
        # Get all tasks
        all_tasks = sdk_client.tasks.list()

        # Delete all tasks
        for task in all_tasks:
            try:
                sdk_client.tasks.delete(task.id)
            except NotFoundError:
                pass

        # List should return empty list, not error
        tasks = sdk_client.tasks.list()
        assert isinstance(tasks, list)
        assert len(tasks) == 0

    def test_very_long_task_name(self, sdk_client):
        """Test creating a task with a very long name."""
        long_name = "A" * 255  # 255 characters

        task = sdk_client.tasks.create(
            name=long_name,
            search_query="Test query",
            condition_description="Test condition",
        )

        assert task.name == long_name

        # Cleanup
        sdk_client.tasks.delete(task.id)

    def test_special_characters_in_task_name(self, sdk_client):
        """Test creating a task with special characters in name."""
        special_name = "Test 🚀 Task with émojis and spëcial çhars!"

        task = sdk_client.tasks.create(
            name=special_name,
            search_query="Test query",
            condition_description="Test condition",
        )

        assert task.name == special_name

        # Cleanup
        sdk_client.tasks.delete(task.id)


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
