from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import pytest
from pydantic import ValidationError

from app.core.constants import TEST_ID_2
from app.schemas.user_query_schemas import UserQueryBase, UserQueryCreate, UserQueryInDB


def test_user_query_base_valid():
    data = {"raw_query": "Valid query"}
    schema = UserQueryBase(**data)
    assert schema.raw_query == "Valid query"
    assert schema.config_hints_json is None


def test_user_query_base_with_hints():
    data = {"raw_query": "Query with hints", "config_hints_json": {"key": "value"}}
    schema = UserQueryBase(**data)
    assert schema.raw_query == "Query with hints"
    assert schema.config_hints_json == {"key": "value"}


def test_user_query_base_invalid_empty_query():
    with pytest.raises(ValidationError):
        UserQueryBase(raw_query="")


def test_user_query_create():
    data = {"raw_query": "Create query", "config_hints_json": {"a": 1}}
    schema = UserQueryCreate(**data)
    assert schema.raw_query == "Create query"
    assert schema.config_hints_json == {"a": 1}


def test_user_query_in_db():
    now = datetime.now()
    data = {
        "id": 1,
        "raw_query": "DB query",
        "status": "pending_discovery",
        "config_hints_json": None,
        "created_at": now,
        "updated_at": now,
    }
    schema = UserQueryInDB(**data)
    assert schema.id == 1
    assert schema.raw_query == "DB query"
    assert schema.status == "pending_discovery"
    assert schema.config_hints_json is None
    assert schema.created_at == now
    assert schema.updated_at == now


# Example mock object that mimics a SQLAlchemy model for orm_mode test
@dataclass
class MockOrmQuery:
    """Data class for mimicking a SQLAlchemy model in tests."""

    id: int
    raw_query: str
    status: str
    created_at: datetime
    updated_at: datetime
    config_hints_json: Optional[dict[str, Any]] = None


def test_user_query_in_db_orm_mode():
    now = datetime.now()
    mock_orm_object = MockOrmQuery(
        id=TEST_ID_2,
        raw_query="ORM Query",
        status="processing",
        config_hints_json={"orm": True},
        created_at=now,
        updated_at=now,
    )
    schema = UserQueryInDB.model_validate(mock_orm_object)
    assert schema.id == TEST_ID_2
    assert schema.raw_query == "ORM Query"
    assert schema.status == "processing"
    assert schema.config_hints_json == {"orm": True}
    assert schema.created_at == now
    assert schema.updated_at == now
