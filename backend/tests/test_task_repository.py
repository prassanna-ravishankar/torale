"""Authorization and serialization contracts for task repositories."""

import json
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from webwhen.tasks.repository import TaskExecutionRepository, TaskRepository


@pytest.fixture
def db():
    return AsyncMock()


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["set_owned_visibility", "delete_owned"])
async def test_owned_mutations_include_task_and_user_predicates(db, operation):
    task_id = uuid4()
    user_id = uuid4()
    db.fetch_one.return_value = {"id": task_id}
    repository = TaskRepository(db)

    if operation == "set_owned_visibility":
        result = await repository.set_owned_visibility(task_id, user_id, True)
        expected_params = (True, task_id, user_id)
    else:
        result = await repository.delete_owned(task_id, user_id)
        expected_params = (task_id, user_id)

    query, *params = db.fetch_one.await_args.args
    assert "user_id" in query
    assert "task" in query.lower()
    assert tuple(params) == expected_params
    assert result is True


@pytest.mark.asyncio
async def test_owned_update_serializes_notifications_and_keeps_owner_predicate(db):
    task_id = uuid4()
    user_id = uuid4()
    notifications = [{"type": "email", "address": "owner@example.com"}]
    db.fetch_one.return_value = {"id": task_id}

    await TaskRepository(db).update_owned_fields(
        task_id,
        user_id,
        {"name": "Updated", "notifications": notifications},
    )

    query, name, stored_notifications, stored_task_id, stored_user_id = db.fetch_one.await_args.args
    assert "user_id" in query
    assert name == "Updated"
    assert stored_notifications == json.dumps(notifications)
    assert (stored_task_id, stored_user_id) == (task_id, user_id)


@pytest.mark.asyncio
async def test_notification_history_query_excludes_non_notifications(db):
    task_id = uuid4()
    db.fetch_all.return_value = []

    await TaskExecutionRepository(db).find_recent(task_id, 25, notifications_only=True)

    query, stored_task_id, limit = db.fetch_all.await_args.args
    assert "notification IS NOT NULL" in query
    assert (stored_task_id, limit) == (task_id, 25)
