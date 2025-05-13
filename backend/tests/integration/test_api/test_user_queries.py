import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import (
    Session,
)  # Keep Session for type hint if needed, but we use AsyncSession
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select  # Import select
from unittest.mock import patch, AsyncMock, MagicMock  # Import patch and AsyncMock
from fastapi import BackgroundTasks  # Import BackgroundTasks

from app.main import app  # Import your FastAPI app instance
from app.core.config import get_settings
from app.schemas.user_query_schemas import UserQueryCreate
from app.models.user_query_model import UserQuery

# Import services and AI interface
from app.services.user_query_processing_service import UserQueryProcessingService
from app.services.source_discovery_service import SourceDiscoveryService
from app.services.ai_integrations.interface import AIModelInterface

# Remove the client fixture - provided by conftest.py
# @pytest.fixture(scope="module")
# def client() -> TestClient:
#     return TestClient(app)

# Assuming you have a fixture for test DB session, similar to model tests
# If not, you might need to set up test DB overrides for dependencies
# For now, let's assume a db_session fixture exists like in model tests


@pytest.mark.asyncio
@patch("app.api.endpoints.user_queries.BackgroundTasks.add_task")  # Patch add_task
@patch(
    "app.services.source_discovery_service.SourceDiscoveryService.discover_sources",
    new_callable=AsyncMock,
)  # Mock discovery
async def test_create_user_query_success(
    mock_discover_sources: AsyncMock,
    mock_add_task: MagicMock,
    client: TestClient,
    db_session: AsyncSession,
):
    """Test successful creation and background processing trigger."""
    # Mock the discovery service to return some URLs
    mock_discover_sources.return_value = [
        "http://discovered.com/1",
        "http://discovered.com/2",
    ]

    settings = get_settings()
    endpoint_url = f"{settings.API_V1_STR}/user-queries/"
    query_data = {
        "raw_query": "Test query for background task",
        "config_hints_json": {"test_bg": True},
    }

    # --- Act --- Phase 1: Call the API endpoint
    response = client.post(endpoint_url, json=query_data)

    # --- Assert --- Phase 1: Check API response and initial DB state
    assert response.status_code == 201
    data = response.json()
    assert data["raw_query"] == query_data["raw_query"]
    assert data["status"] == "pending_discovery"  # Status should be pending initially
    assert "id" in data
    query_id = data["id"]

    # Verify the mock add_task was called (endpoint schedules the task)
    mock_add_task.assert_called_once()
    # Extract arguments passed to add_task to simulate its execution
    args, kwargs = mock_add_task.call_args
    task_func = args[0]
    task_query_id = kwargs.get("query_id")
    task_db = kwargs.get("db")  # This db session is from the endpoint's scope
    task_discovery_service = kwargs.get("discovery_service")

    # assert task_func == UserQueryProcessingService().process_query # Check correct function was scheduled - This can fail due to instance comparison
    # Instead, check the function's name or qualified name
    assert task_func.__name__ == "process_query"
    assert task_func.__qualname__.startswith(
        "UserQueryProcessingService."
    )  # More specific check

    assert task_query_id == query_id
    assert isinstance(task_discovery_service, SourceDiscoveryService)

    # --- Act --- Phase 2: Manually run the background task logic using the test session
    # Re-create the processing service instance (it's stateless)
    processing_service = UserQueryProcessingService()
    # Use the discovery service instance that *would* have been passed to the task
    # Its discover_sources method is already mocked
    await processing_service.process_query(
        query_id=query_id,
        db=db_session,  # Use the main test session for verification
        discovery_service=task_discovery_service,
    )

    # --- Assert --- Phase 2: Verify final state after simulated task completion
    # Fetch the updated query from the DB using the test session
    stmt = select(UserQuery).where(UserQuery.id == query_id)
    result = await db_session.execute(stmt)
    db_obj_after_processing = result.scalar_one_or_none()

    assert db_obj_after_processing is not None
    assert db_obj_after_processing.raw_query == query_data["raw_query"]
    assert (
        db_obj_after_processing.status == "processed"
    )  # Status should be processed now

    # Optional: Check if MonitoredSource entries were created (if that's part of process_query)
    # from app.models.monitored_source_model import MonitoredSource
    # source_stmt = select(MonitoredSource).where(MonitoredSource.user_query_id == query_id)
    # source_result = await db_session.execute(source_stmt)
    # created_sources = source_result.scalars().all()
    # assert len(created_sources) == 2
    # assert {src.url for src in created_sources} == set(mock_discover_sources.return_value)


def test_create_user_query_missing_query(client: TestClient):
    """Test creating a query with missing raw_query field."""
    settings = get_settings()
    endpoint_url = f"{settings.API_V1_STR}/user-queries/"
    query_data = {"config_hints_json": {}}  # Missing raw_query

    response = client.post(endpoint_url, json=query_data)

    assert response.status_code == 422  # Unprocessable Entity


def test_create_user_query_empty_query(client: TestClient):
    """Test creating a query with an empty raw_query string."""
    settings = get_settings()
    endpoint_url = f"{settings.API_V1_STR}/user-queries/"
    query_data = {"raw_query": "", "config_hints_json": {}}

    response = client.post(endpoint_url, json=query_data)

    # Expecting 422 because UserQueryBase has min_length=1 for raw_query
    assert response.status_code == 422
