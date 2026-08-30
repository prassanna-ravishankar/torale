"""TaskService fork ownership and data-copy contracts."""

import json
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from webwhen.tasks.service import TaskNotFoundError, TaskService


@pytest.fixture
def database_and_connection():
    db = MagicMock()
    db.fetch_one = AsyncMock()

    connection = MagicMock()
    connection.execute = AsyncMock()
    connection.fetchrow = AsyncMock()

    transaction = MagicMock()
    transaction.__aenter__ = AsyncMock(return_value=transaction)
    transaction.__aexit__ = AsyncMock(return_value=None)
    connection.transaction.return_value = transaction

    acquired = MagicMock()
    acquired.__aenter__ = AsyncMock(return_value=connection)
    acquired.__aexit__ = AsyncMock(return_value=None)
    db.acquire.return_value = acquired
    return db, connection


def _source(*, owner_id, is_public=True, **overrides):
    row = {
        "id": uuid4(),
        "user_id": owner_id,
        "name": "Original watch",
        "is_public": is_public,
        "search_query": "test query",
        "condition_description": "test condition",
        "notifications": '[{"type":"email","address":"owner@example.com"}]',
        "notification_channels": ["email", "webhook"],
        "notification_email": "owner@example.com",
        "webhook_url": "https://example.com/hook",
        "webhook_secret": "private-secret",
    }
    row.update(overrides)
    return row


def _forked(source, user_id, name):
    return {
        "id": uuid4(),
        "user_id": user_id,
        "name": name,
        "forked_from_task_id": source["id"],
    }


@pytest.mark.asyncio
async def test_public_fork_increments_subscribers_and_scrubs_notifications(
    database_and_connection,
):
    db, connection = database_and_connection
    user_id = uuid4()
    source = _source(owner_id=uuid4())
    db.fetch_one.return_value = source
    connection.fetchrow.return_value = _forked(source, user_id, "My fork")

    result = await TaskService(db).fork(source["id"], user_id, "My fork")

    connection.execute.assert_awaited_once()
    (
        _,
        inserted_user_id,
        name,
        state,
        _,
        _,
        notifications,
        channels,
        email,
        webhook_url,
        webhook_secret,
        forked_from,
        is_public,
    ) = connection.fetchrow.await_args.args
    assert (inserted_user_id, name, state) == (user_id, "My fork", "paused")
    assert (notifications, channels, email, webhook_url, webhook_secret) == (
        json.dumps([]),
        [],
        None,
        None,
        None,
    )
    assert (forked_from, is_public) == (source["id"], False)
    assert result["name"] == "My fork"


@pytest.mark.asyncio
async def test_private_fork_rejects_non_owner(database_and_connection):
    db, _ = database_and_connection
    source = _source(owner_id=uuid4(), is_public=False)
    db.fetch_one.return_value = source

    with pytest.raises(TaskNotFoundError, match="Task not found"):
        await TaskService(db).fork(source["id"], uuid4(), None)


@pytest.mark.asyncio
async def test_owner_fork_preserves_notifications_without_subscriber_increment(
    database_and_connection,
):
    db, connection = database_and_connection
    owner_id = uuid4()
    source = _source(owner_id=owner_id)
    db.fetch_one.return_value = source
    connection.fetchrow.return_value = _forked(source, owner_id, "Duplicate")

    await TaskService(db).fork(source["id"], owner_id, "Duplicate")

    connection.execute.assert_not_awaited()
    insert_args = connection.fetchrow.await_args.args
    assert insert_args[6:11] == (
        source["notifications"],
        source["notification_channels"],
        source["notification_email"],
        source["webhook_url"],
        source["webhook_secret"],
    )


@pytest.mark.asyncio
async def test_fork_without_name_uses_copy_suffix(database_and_connection):
    db, connection = database_and_connection
    user_id = uuid4()
    source = _source(owner_id=uuid4())
    db.fetch_one.return_value = source
    connection.fetchrow.return_value = _forked(source, user_id, "Original watch (Copy)")

    result = await TaskService(db).fork(source["id"], user_id, None)

    assert connection.fetchrow.await_args.args[2] == "Original watch (Copy)"
    assert result["name"] == "Original watch (Copy)"
