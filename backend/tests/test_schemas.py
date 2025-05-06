import pytest
from pydantic import ValidationError

from app.schemas.alert import AlertBase


def test_alert_base_valid():
    """Test creating AlertBase with valid data."""
    data = {
        "user_email": "test@example.com",
        "query": "test query",
        "target_url": "https://example.com",
        "target_type": "website",
        "keywords": "test, keywords",
        "check_frequency_minutes": 60,
        "similarity_threshold": 0.85,
    }
    alert = AlertBase(**data)
    assert alert.user_email == data["user_email"]
    assert alert.query == data["query"]
    assert str(alert.target_url) == data["target_url"] + '/' # Added trailing slash for comparison
    assert alert.target_type == data["target_type"]
    assert alert.keywords == data["keywords"]
    assert alert.check_frequency_minutes == data["check_frequency_minutes"]
    assert alert.similarity_threshold == data["similarity_threshold"]


def test_alert_base_defaults():
    """Test default values for optional fields in AlertBase."""
    data = {
        "user_email": "test@example.com",
        "query": "test query",
        "target_url": "https://example.com",
        "target_type": "website",
    }
    alert = AlertBase(**data)
    assert alert.keywords is None
    assert alert.check_frequency_minutes == 30
    assert alert.similarity_threshold == 0.9


def test_alert_base_invalid_email():
    """Test AlertBase creation fails with invalid email."""
    data = {
        "user_email": "invalid-email",
        "query": "test query",
        "target_url": "https://example.com",
        "target_type": "website",
    }
    with pytest.raises(ValidationError):
        AlertBase(**data)


def test_alert_base_invalid_url():
    """Test AlertBase creation fails with invalid URL."""
    data = {
        "user_email": "test@example.com",
        "query": "test query",
        "target_url": "invalid-url",
        "target_type": "website",
    }
    with pytest.raises(ValidationError):
        AlertBase(**data)


def test_alert_base_missing_required_field():
    """Test AlertBase creation fails if required fields are missing."""
    data = {
        # Missing user_email
        "query": "test query",
        "target_url": "https://example.com",
        "target_type": "website",
    }
    with pytest.raises(ValidationError):
        AlertBase(**data)


# --- Tests for AlertCreate ---

from app.schemas.alert import AlertCreate # Import AlertCreate

def test_alert_create_valid():
    """Test creating AlertCreate with valid data."""
    data = {
        "user_email": "create@example.com",
        "query": "create query",
        "target_url": "https://create.example.com",
        "target_type": "youtube",
    }
    alert_create = AlertCreate(**data)
    assert alert_create.user_email == data["user_email"]
    assert alert_create.query == data["query"]
    assert str(alert_create.target_url) == data["target_url"] + '/'
    assert alert_create.target_type == data["target_type"]
    # Check defaults inherited from AlertBase
    assert alert_create.keywords is None
    assert alert_create.check_frequency_minutes == 30
    assert alert_create.similarity_threshold == 0.9


# --- Tests for AlertUpdate ---

from app.schemas.alert import AlertUpdate # Import AlertUpdate

def test_alert_update_with_is_active():
    """Test creating AlertUpdate with is_active set."""
    data = {
        "user_email": "update@example.com",
        "query": "update query",
        "target_url": "https://update.example.com",
        "target_type": "rss",
        "is_active": False
    }
    alert_update = AlertUpdate(**data)
    assert alert_update.user_email == data["user_email"]
    assert alert_update.is_active == False

def test_alert_update_without_is_active():
    """Test creating AlertUpdate without is_active (should default to None)."""
    data = {
        "user_email": "update@example.com",
        "query": "update query",
        "target_url": "https://update.example.com",
        "target_type": "rss",
    }
    alert_update = AlertUpdate(**data)
    assert alert_update.user_email == data["user_email"]
    assert alert_update.is_active is None # Check that it's None when not provided

def test_alert_update_invalid_type():
    """Test AlertUpdate fails if is_active has wrong type."""
    data = {
        "user_email": "update@example.com",
        "query": "update query",
        "target_url": "https://update.example.com",
        "target_type": "rss",
        "is_active": "not-a-boolean" 
    }
    with pytest.raises(ValidationError):
        AlertUpdate(**data) 