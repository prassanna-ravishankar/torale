import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine # Keep for potential sync examples, or remove if not used
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker # Keep for potential sync examples, or remove if not used
from sqlalchemy.pool import StaticPool

from app.main import app as fastapi_app # Import the instance, renamed to avoid conflict
from app.core.db import Base, get_db # Corrected import
from app.models.monitored_source_model import MonitoredSource # Corrected import
import app.models # Import the models package to ensure __init__.py runs

# --- Test Database Setup ---
# Use an in-memory SQLite database for testing with an ASYNC driver
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:" # Use async driver

# engine = create_engine(  # Old sync engine
#     SQLALCHEMY_DATABASE_URL,
#     connect_args={"check_same_thread": False}, # Required for SQLite (sync)
#     poolclass=StaticPool,
# )
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    # connect_args={"check_same_thread": False} is not needed for aiosqlite,
    # and StaticPool is also not typically used with async engines in the same way.
    # aiosqlite handles connections per task.
)
# TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) # Old sync sessionmaker
TestingSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Create tables in the in-memory database before tests run
# This needs to be done carefully in an async context.
# It's better to do this in an async fixture or at the beginning of relevant test functions.
# For module scope, we can use pytest-asyncio's event_loop fixture.

@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# --- Dependency Override ---
# async def override_get_db(): # Old sync override
#     try:
#         db = TestingSessionLocal()
#         yield db
#     finally:
#         db.close()
async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

# Apply override to the imported FastAPI app instance
fastapi_app.dependency_overrides[get_db] = override_get_db

# --- Test Client Fixture ---
@pytest.fixture(scope="module")
def client():
    # No async setup needed directly for TestClient if endpoints are sync,
    # but db interactions within endpoints will use the async override.
    with TestClient(fastapi_app) as c:
        yield c
    # Cleanup dependency override after tests if necessary (might be better in session scope fixture)
    # fastapi_app.dependency_overrides.clear() # Clearing might interfere if other tests need it.

# --- API Endpoint Tests ---

# Test POST /monitored-sources/
@pytest.mark.asyncio # Mark test as async
async def test_create_monitored_source_success(client): # Make test async
    """Test successfully creating a new monitored source."""
    test_url = "https://example-monitor.com/page"
    response = client.post( # client.post is synchronous
        "/api/v1/monitored-sources/",
        json={"url": test_url, "check_interval_seconds": 600}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["url"] == test_url
    assert data["check_interval_seconds"] == 600
    assert data["status"] == "active"
    assert "id" in data

    # Verify in DB (optional, but good practice)
    async with TestingSessionLocal() as db: # Get an async session
        db_item = await db.get(MonitoredSource, data["id"]) # Use await and db.get for primary key lookup
        assert db_item is not None
        assert str(db_item.url) == test_url # Check URL stored in DB
        assert db_item.check_interval_seconds == 600
    # db.close() # Not needed with async context manager

@pytest.mark.asyncio
async def test_create_monitored_source_duplicate_url(client):
    """Test creating a source with a URL that already exists."""
    test_url = "https://duplicate.com/path"
    # Create the first one
    client.post("/api/v1/monitored-sources/", json={"url": test_url, "check_interval_seconds": 300}) # Ensure required fields
    
    # Attempt to create the second one
    response = client.post("/api/v1/monitored-sources/", json={"url": test_url, "check_interval_seconds": 300}) # Ensure required fields
    
    assert response.status_code == 400
    assert "already being monitored" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_monitored_source_invalid_url(client):
    """Test creating a source with an invalid URL."""
    response = client.post(
        "/api/v1/monitored-sources/",
        json={"url": "not-a-valid-url"}
    )
    assert response.status_code == 422 # Unprocessable Entity from Pydantic validation

# Add more tests for GET, PUT, DELETE /monitored-sources/ and /alerts/ endpoints 