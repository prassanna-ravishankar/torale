"""HTTP-level contracts for authenticated and public task access."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from webwhen.access.auth import get_current_user
from webwhen.access.auth_provider import User
from webwhen.api.main import app
from webwhen.core.database import get_db
from webwhen.tasks.service import ForkNameConflictError, TaskNotFoundError


def _task_row(*, task_id, user_id, is_public, **overrides):
    now = datetime.now(UTC)
    row = {
        "id": task_id,
        "user_id": user_id,
        "name": "Access contract watch",
        "is_public": is_public,
        "view_count": 0,
        "subscriber_count": 0,
        "last_known_state": None,
        "notifications": '[{"type":"email","address":"owner@example.com"}]',
        "search_query": "test query",
        "condition_description": "test condition",
        "notification_channels": ["email", "webhook"],
        "notification_email": "owner@example.com",
        "webhook_url": "https://example.com/private-hook",
        "webhook_secret": "private-secret",
        "attached_connector_slugs": [],
        "context": None,
        "state": "active",
        "next_run": None,
        "forked_from_task_id": None,
        "created_at": now,
        "updated_at": now,
        "state_changed_at": now,
        "last_execution_id": None,
        "exec_id": None,
        "exec_notification": None,
        "exec_started_at": None,
        "exec_completed_at": None,
        "exec_status": None,
        "exec_result": None,
        "exec_grounding_sources": None,
    }
    row.update(overrides)
    return row


@pytest.fixture
def route_client():
    db = AsyncMock()
    owner_id = uuid4()
    current_user = User(
        user_id="clerk_owner",
        email="owner@example.com",
        db_user_id=owner_id,
    )

    async def override_db():
        return db

    async def override_user():
        return current_user

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_user
    try:
        yield TestClient(app), db, current_user
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize(
    "is_owner,is_public,expected_status",
    [
        (True, False, 200),
        (False, False, 404),
        (False, True, 200),
    ],
    ids=["owner-private", "other-private", "other-public"],
)
def test_authenticated_task_access_contract(route_client, is_owner, is_public, expected_status):
    client, db, current_user = route_client
    task_id = uuid4()
    task_owner_id = current_user.id if is_owner else uuid4()
    db.fetch_one.return_value = _task_row(
        task_id=task_id,
        user_id=task_owner_id,
        is_public=is_public,
    )

    with patch("webwhen.api.routers.tasks.increment_view") as increment_view:
        response = client.get(f"/api/v1/tasks/{task_id}")

    assert response.status_code == expected_status
    if expected_status == 200:
        body = response.json()
        assert body["id"] == str(task_id)
        if not is_owner:
            assert body["notifications"] == []
            increment_view.assert_called_once_with(task_id)


@pytest.mark.parametrize("is_public,expected_status", [(True, 200), (False, 404)])
def test_public_task_route_requires_public_visibility(route_client, is_public, expected_status):
    client, db, _ = route_client
    task_id = uuid4()
    db.fetch_one.return_value = _task_row(
        task_id=task_id,
        user_id=uuid4(),
        is_public=is_public,
    )

    response = client.get(f"/api/v1/public/tasks/id/{task_id}")

    assert response.status_code == expected_status
    if expected_status == 200:
        body = response.json()
        assert "user_id" not in body
        assert body["notifications"] == []
        assert body.get("notification_email") is None
        assert body.get("webhook_url") is None


def test_task_route_enforces_auth_dependency(route_client):
    client, _, _ = route_client

    async def reject_authentication():
        raise HTTPException(status_code=401, detail="Not authenticated")

    app.dependency_overrides[get_current_user] = reject_authentication

    response = client.get(f"/api/v1/tasks/{uuid4()}")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.parametrize(
    "updated_row,is_public,expected_status",
    [({"id": "updated"}, True, 200), (None, False, 404)],
    ids=["owner", "not-owner"],
)
def test_visibility_route_enforces_ownership(route_client, updated_row, is_public, expected_status):
    client, db, _ = route_client
    task_id = uuid4()
    db.fetch_one.return_value = updated_row

    response = client.patch(
        f"/api/v1/tasks/{task_id}/visibility",
        json={"is_public": is_public},
    )

    assert response.status_code == expected_status
    if expected_status == 200:
        assert response.json() == {"is_public": is_public}


@pytest.mark.parametrize(
    "service_error,expected_status",
    [
        (TaskNotFoundError("Task not found"), 404),
        (ForkNameConflictError("Choose another name"), 409),
    ],
)
def test_fork_route_maps_domain_errors(route_client, service_error, expected_status):
    client, _, _ = route_client

    with patch(
        "webwhen.api.routers.tasks.TaskService.fork",
        AsyncMock(side_effect=service_error),
    ):
        response = client.post(f"/api/v1/tasks/{uuid4()}/fork", json={})

    assert response.status_code == expected_status
    assert response.json() == {"detail": str(service_error)}


def test_public_viewer_execution_errors_are_scrubbed(route_client):
    client, db, current_user = route_client
    task_id = uuid4()
    now = datetime.now(UTC)
    db.fetch_one.return_value = {
        "id": task_id,
        "user_id": uuid4(),
        "is_public": True,
    }
    db.fetch_all.return_value = [
        {
            "id": uuid4(),
            "task_id": task_id,
            "status": "failed",
            "result": None,
            "error_message": "private stack trace",
            "notification": None,
            "grounding_sources": None,
            "started_at": now,
            "completed_at": now,
            "created_at": now,
        }
    ]

    response = client.get(f"/api/v1/tasks/{task_id}/executions")

    assert response.status_code == 200
    assert response.json()[0]["error_message"] is None
    assert current_user.id != db.fetch_one.return_value["user_id"]
