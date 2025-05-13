import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.constants import (
    DEFAULT_CHECK_INTERVAL_SECONDS,
    HTTP_STATUS_CREATED,
)
from app.core.db import get_db  # Corrected import
from app.main import (
    app as fastapi_app,
)  # Import the instance, renamed to avoid conflict

# F811: Removed import of TestingSessionLocal from conftest, as it's redefined locally
# from tests.conftest import (
#     TestingSessionLocal,
# )

# --- Test Constants ---
# Using constants to avoid hardcoding magic numbers in the test
TEST_MONITORED_URL = "https://example.com/test"

# --- Test Database Setup ---
# This has been moved to conftest.py and is now shared
# Various DB setup blocks removed to reduce duplication

# The above local TestDatabaseSetup is commented out because conftest.py
# now handles the test database lifecycle.

# Define constants for magic numbers
HTTP_STATUS_BAD_REQUEST = 400
HTTP_STATUS_UNPROCESSABLE_ENTITY = 422


@pytest.fixture(scope="session")
def engine():  # Changed to avoid conflict if run standalone
    # This fixture should now defer to conftest.py's shared fixtures
    # if this test is run as part of the full test suite.
    pass


@pytest.fixture(scope="session")
def testing_session_local(engine):
    # This fixture should defer to conftest.py if available
    pass


@pytest.fixture(scope="function")  # Changed from module to function for session
async def dbsession(engine):
    # N806: Renamed TestingSessionLocal to testing_session_local
    testing_session_local = async_sessionmaker(  # Use local var
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with testing_session_local() as session:
        yield session


# --- Dependency Override ---
async def override_get_db_for_this_module(dbsession: AsyncSession = Depends(dbsession)):
    yield dbsession


# Apply override to the imported FastAPI app instance
fastapi_app.dependency_overrides[get_db] = override_get_db_for_this_module


# --- Test Client Fixture ---
@pytest.fixture(scope="module")  # Keep module scope for client
def client():
    with TestClient(fastapi_app) as c:
        yield c
    # Cleanup dependency override after tests if necessary
    # fastapi_app.dependency_overrides.clear() # Better handled by conftest


# --- API Endpoint Tests ---


async def test_create_monitored_source(client: AsyncClient):
    """
    Test creating a monitored source via the API.

    This uses the shared client fixture from conftest.py
    which provides a properly configured AsyncClient instance
    that already has all the necessary application setup.
    """
    test_url = TEST_MONITORED_URL

    response = client.post(
        "/api/v1/monitored-sources/",
        json={
            "url": test_url,
            "check_interval_seconds": DEFAULT_CHECK_INTERVAL_SECONDS,
        },
    )
    assert response.status_code == HTTP_STATUS_CREATED, (
        f"Expected status code {HTTP_STATUS_CREATED}, got {response.status_code}. "
        f"Response: {response.text}"
    )
    data = response.json()
    assert data["url"] == test_url
    assert "id" in data
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_create_monitored_source_duplicate_url(client):
    """Test creating a source with a URL that already exists."""
    test_url = "https://duplicate.com/path"
    # Create the first one
    client.post(
        "/api/v1/monitored-sources/",
        json={"url": test_url, "check_interval_seconds": 300},
    )  # Ensure required fields

    # Attempt to create the second one
    response = client.post(
        "/api/v1/monitored-sources/",
        json={"url": test_url, "check_interval_seconds": 300},
    )  # Ensure required fields

    assert response.status_code == HTTP_STATUS_BAD_REQUEST  # Used constant
    assert "already being actively monitored" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_monitored_source_invalid_url(client):
    """Test creating a source with an invalid URL."""
    response = client.post(
        "/api/v1/monitored-sources/", json={"url": "not-a-valid-url"}
    )
    assert response.status_code == HTTP_STATUS_UNPROCESSABLE_ENTITY  # Used constant


# Add more tests for GET, PUT, DELETE /monitored-sources/ and /alerts/ endpoints
