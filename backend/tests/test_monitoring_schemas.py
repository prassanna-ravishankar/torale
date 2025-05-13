from datetime import datetime

import pytest
from pydantic import ValidationError

from app.core.constants import (
    DEFAULT_CHECK_INTERVAL_SECONDS,
    DEFAULT_FREQUENT_INTERVAL_SECONDS,
    DEFAULT_INFREQUENT_INTERVAL_SECONDS,
    DEFAULT_QUICK_CHECK_INTERVAL_SECONDS,
    DEFAULT_VERY_FREQUENT_INTERVAL_SECONDS,
    TEST_ID_1,
    TEST_ID_2,
    TEST_ID_5,
)
from app.schemas.monitoring_schemas import (
    MonitoredSourceBase,
    MonitoredSourceCreate,
    MonitoredSourceInDB,
    MonitoredSourceUpdate,
)

# --- Tests for MonitoredSourceBase ---


def test_monitored_source_base_schema():
    """Test MonitoredSourceBase schema validation."""
    # Test with minimal required fields
    data = {"url": "https://example.com/"}
    schema = MonitoredSourceBase(**data)
    assert str(schema.url) == "https://example.com/"
    assert schema.check_interval_seconds == DEFAULT_CHECK_INTERVAL_SECONDS


def test_monitored_source_base_schema_with_interval():
    """Test MonitoredSourceBase schema with custom interval."""
    data = {
        "url": "https://example.com/",
        "check_interval_seconds": DEFAULT_VERY_FREQUENT_INTERVAL_SECONDS,
    }
    schema = MonitoredSourceBase(**data)
    assert str(schema.url) == "https://example.com/"
    assert schema.check_interval_seconds == DEFAULT_VERY_FREQUENT_INTERVAL_SECONDS


def test_monitored_source_base_schema_invalid_url():
    """Test MonitoredSourceBase schema with invalid URL."""
    data = {"url": "not-a-url"}
    with pytest.raises(ValidationError):
        MonitoredSourceBase(**data)


def test_monitored_source_base_missing_url():
    data = {"check_interval_seconds": 60}
    with pytest.raises(ValidationError):
        MonitoredSourceBase(**data)


# --- Tests for MonitoredSourceCreate ---


def test_monitored_source_create_schema():
    """Test MonitoredSourceCreate schema."""
    # Test with minimal required fields for create
    data = {"url": "https://create.example.com/"}
    schema = MonitoredSourceCreate(**data)
    assert str(schema.url) == "https://create.example.com/"
    assert schema.check_interval_seconds == DEFAULT_CHECK_INTERVAL_SECONDS


# --- Tests for MonitoredSourceUpdate ---


def test_monitored_source_update_schema_partial():
    """Test MonitoredSourceUpdate schema with partial data."""
    # Only updating interval, not URL
    data = {"check_interval_seconds": DEFAULT_QUICK_CHECK_INTERVAL_SECONDS}
    schema = MonitoredSourceUpdate(**data)
    assert schema.url is None
    assert schema.check_interval_seconds == DEFAULT_QUICK_CHECK_INTERVAL_SECONDS
    assert schema.status is None


def test_monitored_source_update_schema_full():
    """Test MonitoredSourceUpdate schema with full data."""
    data = {
        "url": "https://new.example.com/",
        "check_interval_seconds": DEFAULT_INFREQUENT_INTERVAL_SECONDS,
        "status": "paused",
    }
    schema = MonitoredSourceUpdate(**data)
    assert str(schema.url) == "https://new.example.com/"
    assert schema.check_interval_seconds == DEFAULT_INFREQUENT_INTERVAL_SECONDS
    assert schema.status == "paused"


def test_monitored_source_update_invalid_url():
    data = {"url": "still-invalid"}
    with pytest.raises(ValidationError):
        MonitoredSourceUpdate(**data)


# --- Tests for MonitoredSourceInDB ---


def test_monitored_source_indb_schema():
    """Test MonitoredSourceInDB schema."""
    now = datetime.utcnow()
    # Test with all fields including those added by ORM
    data = {
        "id": TEST_ID_1,
        "url": "https://db.example.com/",
        "check_interval_seconds": DEFAULT_FREQUENT_INTERVAL_SECONDS,
        "status": "active",
        "last_checked_at": now,
        "last_changed_at": now,
        "created_at": now,
        "updated_at": now,
        "user_query_id": TEST_ID_5,
    }
    schema = MonitoredSourceInDB(**data)
    assert schema.id == TEST_ID_1
    assert str(schema.url) == "https://db.example.com/"
    assert schema.check_interval_seconds == DEFAULT_FREQUENT_INTERVAL_SECONDS
    assert schema.status == "active"
    assert schema.last_checked_at == now
    assert schema.created_at == now
    assert schema.updated_at == now
    assert schema.user_query_id == TEST_ID_5


def test_monitored_source_indb_from_orm():
    """Test MonitoredSourceInDB.from_orm method."""

    # Mock an ORM object with required attributes
    class MockMonitoredSource:
        pass  # Simple namespace object for testing

    mock_orm_obj = MockMonitoredSource()
    mock_orm_obj.id = TEST_ID_2
    mock_orm_obj.url = "https://orm.example.com/"
    mock_orm_obj.check_interval_seconds = DEFAULT_CHECK_INTERVAL_SECONDS
    mock_orm_obj.status = "error"
    mock_orm_obj.last_checked_at = None
    mock_orm_obj.last_changed_at = None
    mock_orm_obj.created_at = datetime.utcnow()
    mock_orm_obj.updated_at = datetime.utcnow()
    mock_orm_obj.user_query_id = None

    schema = MonitoredSourceInDB.model_validate(mock_orm_obj)
    assert schema.id == TEST_ID_2
    assert str(schema.url) == "https://orm.example.com/"
    assert schema.status == "error"
    assert schema.last_checked_at is None
