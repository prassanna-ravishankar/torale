"""Regression tests for safe admin user-management error responses."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from webwhen.api.routers.admin_routes import users
from webwhen.api.routers.admin_routes.users import BulkUpdateUserRolesRequest
from webwhen.tasks.service import TaskService


@pytest.fixture
def mock_admin():
    admin = MagicMock()
    admin.clerk_user_id = "clerk_admin_123"
    return admin


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.mark.asyncio
async def test_list_users_does_not_expose_clerk_exception(mock_admin, mock_db):
    secret = "private Clerk failure details"
    mock_db.fetch_all.return_value = []
    mock_clerk = MagicMock()
    mock_clerk.users.list_async = AsyncMock(side_effect=RuntimeError(secret))

    with patch.object(users, "clerk_client", mock_clerk):
        result = await users.list_users(admin=mock_admin, db=mock_db)

    assert secret not in repr(result)
    assert result["warnings"] == ["Clerk role fetch failed. Roles may be incomplete."]


@pytest.mark.asyncio
async def test_deactivate_user_does_not_expose_task_exception(mock_admin, mock_db):
    secret = "private scheduler failure details"
    user_id = uuid4()
    task_id = uuid4()
    mock_db.fetch_one.return_value = {"id": user_id}
    mock_db.fetch_all.return_value = [{"id": task_id, "state": "active"}]

    with patch.object(TaskService, "pause", AsyncMock(side_effect=RuntimeError(secret))):
        result = await users.deactivate_user(user_id=user_id, admin=mock_admin, db=mock_db)

    assert secret not in repr(result)
    assert result["tasks_failed"] == [{"task_id": str(task_id), "error": "Failed to pause task"}]


@pytest.mark.asyncio
async def test_bulk_role_update_does_not_expose_clerk_exception(mock_admin, mock_db):
    secret = "private Clerk update failure details"
    user_id = uuid4()
    clerk_user_id = "clerk_target_123"
    mock_db.fetch_all.return_value = [{"id": user_id, "clerk_user_id": clerk_user_id}]

    mock_clerk = MagicMock()
    mock_clerk.users.list_async = AsyncMock(
        return_value=SimpleNamespace(data=[SimpleNamespace(id=clerk_user_id)])
    )
    mock_clerk.users.update_metadata_async = AsyncMock(side_effect=RuntimeError(secret))
    request = BulkUpdateUserRolesRequest(user_ids=[str(user_id)], role="developer")

    with (
        patch.object(users, "clerk_client", mock_clerk),
        patch.object(users.settings, "webwhen_noauth", False),
    ):
        result = await users.bulk_update_user_roles(
            request=request,
            admin=mock_admin,
            db=mock_db,
        )

    assert secret not in repr(result)
    assert result == {
        "updated": 0,
        "failed": 1,
        "errors": [{"user_id": str(user_id), "error": "Failed to update role"}],
    }
