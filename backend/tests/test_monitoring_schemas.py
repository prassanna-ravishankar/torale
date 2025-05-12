import pytest
from pydantic import ValidationError
from datetime import datetime
from unittest.mock import Mock

from app.schemas.monitoring_schemas import (
    MonitoredSourceBase,
    MonitoredSourceCreate,
    MonitoredSourceUpdate,
    MonitoredSourceInDB
)

# --- Tests for MonitoredSourceBase ---

def test_monitored_source_base_valid():
    data = {"url": "https://example.com"}
    schema = MonitoredSourceBase(**data)
    assert str(schema.url) == "https://example.com/"
    assert schema.check_interval_seconds == 3600 # Default value

def test_monitored_source_base_custom_interval():
    data = {"url": "https://example.com", "check_interval_seconds": 60}
    schema = MonitoredSourceBase(**data)
    assert str(schema.url) == "https://example.com/"
    assert schema.check_interval_seconds == 60

def test_monitored_source_base_invalid_url():
    data = {"url": "invalid-url"}
    with pytest.raises(ValidationError):
        MonitoredSourceBase(**data)

def test_monitored_source_base_missing_url():
    data = {"check_interval_seconds": 60}
    with pytest.raises(ValidationError):
        MonitoredSourceBase(**data)

# --- Tests for MonitoredSourceCreate ---

def test_monitored_source_create_valid():
    # Inherits validation from Base
    data = {"url": "https://create.example.com"}
    schema = MonitoredSourceCreate(**data)
    assert str(schema.url) == "https://create.example.com/"
    assert schema.check_interval_seconds == 3600

# --- Tests for MonitoredSourceUpdate ---

def test_monitored_source_update_valid_partial():
    # All fields are optional
    data = {"check_interval_seconds": 120}
    schema = MonitoredSourceUpdate(**data)
    assert schema.url is None
    assert schema.check_interval_seconds == 120
    assert schema.status is None

def test_monitored_source_update_valid_full():
    data = {
        "url": "https://new.example.com",
        "check_interval_seconds": 1800,
        "status": "paused"
    }
    schema = MonitoredSourceUpdate(**data)
    assert str(schema.url) == "https://new.example.com/"
    assert schema.check_interval_seconds == 1800
    assert schema.status == "paused"

def test_monitored_source_update_invalid_url():
    data = {"url": "still-invalid"}
    with pytest.raises(ValidationError):
        MonitoredSourceUpdate(**data)

# --- Tests for MonitoredSourceInDB ---

def test_monitored_source_in_db_valid():
    now = datetime.now()
    data = {
        "id": 1,
        "url": "https://db.example.com",
        "check_interval_seconds": 300,
        "status": "active",
        "last_checked_at": now,
        "created_at": now,
        "updated_at": now,
        "user_query_id": 5 # Optional
    }
    schema = MonitoredSourceInDB(**data)
    assert schema.id == 1
    assert str(schema.url) == "https://db.example.com/"
    assert schema.check_interval_seconds == 300
    assert schema.status == "active"
    assert schema.last_checked_at == now
    assert schema.created_at == now
    assert schema.updated_at == now
    assert schema.user_query_id == 5

def test_monitored_source_in_db_orm_mode(mocker): # Example for orm_mode if needed
    mock_orm_obj = Mock()
    mock_orm_obj.id = 2
    mock_orm_obj.url = "https://orm.example.com"
    mock_orm_obj.check_interval_seconds = 900
    mock_orm_obj.status = "error"
    mock_orm_obj.last_checked_at = None
    mock_orm_obj.created_at = datetime.now()
    mock_orm_obj.updated_at = datetime.now()
    mock_orm_obj.user_query_id = None
    mock_orm_obj.name = "Test ORM Source"
    mock_orm_obj.source_type = "website"
    mock_orm_obj.keywords = ["test", "orm"]
    mock_orm_obj.config = {"threshold": 0.95}

    schema = MonitoredSourceInDB.model_validate(mock_orm_obj)
    assert schema.id == 2
    assert str(schema.url) == "https://orm.example.com/"
    assert schema.status == "error"
    assert schema.name == "Test ORM Source"
    assert schema.source_type == "website"
    assert schema.keywords == ["test", "orm"]
    assert schema.config == {"threshold": 0.95} 