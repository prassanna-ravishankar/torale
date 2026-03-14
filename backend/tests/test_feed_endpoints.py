import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, UTC
from fastapi import Request
from torale.api.routers.tasks import get_user_feed
from torale.api.routers.public_tasks import get_public_feed
from torale.tasks import TaskStatus

@pytest.mark.asyncio
async def test_get_user_feed_unit():
    mock_db = AsyncMock()
    mock_user = MagicMock()
    mock_user.id = uuid4()
    
    execution_id = uuid4()
    task_id = uuid4()
    
    # Mock row returned by database
    mock_row = {
        "id": execution_id,
        "task_id": task_id,
        "status": TaskStatus.SUCCESS.value,
        "started_at": datetime.now(UTC),
        "completed_at": datetime.now(UTC),
        "result": '{"metadata": {"changed": true}}',
        "notification": "Something found!",
        "grounding_sources": "[]",
        "error_message": None,
        "task_name": "Test Task",
        "task_search_query": "query",
        "task_is_public": False,
        "task_user_id": mock_user.id
    }
    
    mock_db.fetch_all.return_value = [mock_row]
    
    feed = await get_user_feed(user=mock_user, db=mock_db)
    
    assert len(feed) == 1
    assert feed[0].id == execution_id
    assert feed[0].task_name == "Test Task"
    assert feed[0].notification == "Something found!"
    mock_db.fetch_all.assert_called_once()

@pytest.mark.asyncio
async def test_get_public_feed_unit():
    mock_db = AsyncMock()
    # slowapi needs a Request object with a client host
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/public/feed",
        "headers": [],
        "client": ("127.0.0.1", 1234),
    }
    mock_request = Request(scope=scope)
    
    execution_id = uuid4()
    task_id = uuid4()
    user_id = uuid4()
    
    mock_row = {
        "id": execution_id,
        "task_id": task_id,
        "status": TaskStatus.SUCCESS.value,
        "started_at": datetime.now(UTC),
        "completed_at": datetime.now(UTC),
        "result": '{"metadata": {"changed": true}}',
        "notification": "Public finding!",
        "grounding_sources": "[]",
        "error_message": None,
        "task_name": "Public Task",
        "task_search_query": "query",
        "task_is_public": True,
        "task_user_id": user_id
    }
    
    mock_db.fetch_all.return_value = [mock_row]
    
    feed = await get_public_feed(request=mock_request, db=mock_db)
    
    assert len(feed) == 1
    assert feed[0].id == execution_id
    assert feed[0].task_name == "Public Task"
    assert feed[0].notification == "Public finding!"
    mock_db.fetch_all.assert_called_once()
