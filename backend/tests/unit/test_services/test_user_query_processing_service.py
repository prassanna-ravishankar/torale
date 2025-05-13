import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user_query_processing_service import UserQueryProcessingService
from app.services.source_discovery_service import SourceDiscoveryService
from app.models.user_query_model import UserQuery
from app.models.monitored_source_model import MonitoredSource


@pytest.fixture
def processing_service():
    return UserQueryProcessingService()


@pytest.fixture
def mock_db_session():
    session = AsyncMock(spec=AsyncSession)

    mock_result = AsyncMock()
    session.execute = AsyncMock(return_value=mock_result)

    mock_result.scalar_one_or_none = MagicMock()

    async def async_context_manager(*args, **kwargs):
        pass

    mock_transaction = AsyncMock()
    mock_transaction.__aenter__ = AsyncMock(return_value=None)
    mock_transaction.__aexit__ = AsyncMock(return_value=False)
    session.begin = MagicMock(return_value=mock_transaction)
    session.begin_nested = MagicMock(return_value=mock_transaction)

    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def mock_discovery_service():
    return AsyncMock(spec=SourceDiscoveryService)


@pytest.mark.asyncio
async def test_process_query_success(
    mock_db_session: AsyncMock, mock_discovery_service: AsyncMock
):
    query_id = 1
    raw_query_text = "test query"
    discovered_urls = ["http://example.com/1", "http://example.com/2"]

    mock_user_query_instance = UserQuery(
        id=query_id, raw_query=raw_query_text, status="pending_discovery"
    )

    mock_result_user_query = AsyncMock()
    mock_result_user_query.scalar_one_or_none = MagicMock(
        return_value=mock_user_query_instance
    )

    mock_result_existing_source = AsyncMock()
    mock_result_existing_source.scalar_one_or_none = MagicMock(return_value=None)

    async def execute_side_effect(statement, *args, **kwargs):
        compiled_stmt = str(
            statement.compile(compile_kwargs={"literal_binds": True})
        ).lower()
        if (
            "user_queries" in compiled_stmt
            and f"user_queries.id = {query_id}" in compiled_stmt
        ):
            return mock_result_user_query
        elif (
            "monitored_sources" in compiled_stmt
            and f"monitored_sources.user_query_id = {query_id}" in compiled_stmt
        ):
            return mock_result_existing_source
        mock_default_result = AsyncMock()
        mock_default_result.scalar_one_or_none = MagicMock(return_value=None)
        return mock_default_result

    mock_db_session.execute = AsyncMock(side_effect=execute_side_effect)
    mock_discovery_service.discover_sources = AsyncMock(return_value=discovered_urls)

    processing_service = UserQueryProcessingService()
    await processing_service.process_query(
        query_id, mock_db_session, mock_discovery_service
    )

    assert mock_user_query_instance.status == "processed"
    mock_discovery_service.discover_sources.assert_awaited_once_with(raw_query_text)
    assert mock_db_session.add.call_count == 1 + len(discovered_urls)
    added_objects = [call.args[0] for call in mock_db_session.add.call_args_list]
    assert any(
        isinstance(obj, UserQuery) and obj.status == "processed"
        for obj in added_objects
    )
    assert sum(1 for obj in added_objects if isinstance(obj, MonitoredSource)) == len(
        discovered_urls
    )


@pytest.mark.asyncio
async def test_process_query_no_query_found(
    mock_db_session: AsyncMock,
    mock_discovery_service: AsyncMock,
    processing_service: UserQueryProcessingService,
):
    query_id = 99
    mock_result_user_query = AsyncMock()
    mock_result_user_query.scalar_one_or_none = MagicMock(return_value=None)
    mock_db_session.execute = AsyncMock(return_value=mock_result_user_query)

    await processing_service.process_query(
        query_id, mock_db_session, mock_discovery_service
    )

    mock_discovery_service.discover_sources.assert_not_awaited()
    mock_db_session.add.assert_not_called()


@pytest.mark.asyncio
async def test_process_query_already_processed(
    mock_db_session: AsyncMock,
    mock_discovery_service: AsyncMock,
    processing_service: UserQueryProcessingService,
):
    query_id = 2
    raw_query_text = "already processed query"
    mock_user_query_instance = UserQuery(
        id=query_id, raw_query=raw_query_text, status="processed"
    )

    mock_result_user_query = AsyncMock()
    mock_result_user_query.scalar_one_or_none = MagicMock(
        return_value=mock_user_query_instance
    )
    mock_db_session.execute = AsyncMock(return_value=mock_result_user_query)

    await processing_service.process_query(
        query_id, mock_db_session, mock_discovery_service
    )

    mock_discovery_service.discover_sources.assert_not_awaited()


@pytest.mark.asyncio
async def test_process_query_discovery_fails(
    mock_db_session: AsyncMock,
    mock_discovery_service: AsyncMock,
    processing_service: UserQueryProcessingService,
):
    query_id = 3
    raw_query_text = "failing query"
    mock_user_query_instance = UserQuery(
        id=query_id, raw_query=raw_query_text, status="pending_discovery"
    )

    mock_result_user_query = AsyncMock()
    mock_result_user_query.scalar_one_or_none = MagicMock(
        return_value=mock_user_query_instance
    )

    mock_result_error_fetch = AsyncMock()
    mock_result_error_fetch.scalar_one_or_none = MagicMock(
        return_value=mock_user_query_instance
    )

    async def execute_side_effect_fail(statement, *args, **kwargs):
        compiled_stmt = str(
            statement.compile(compile_kwargs={"literal_binds": True})
        ).lower()
        if (
            "user_queries" in compiled_stmt
            and f"user_queries.id = {query_id}" in compiled_stmt
            and mock_discovery_service.discover_sources.call_count == 0
        ):
            return mock_result_user_query
        elif (
            "user_queries" in compiled_stmt
            and f"user_queries.id = {query_id}" in compiled_stmt
            and mock_discovery_service.discover_sources.call_count > 0
        ):
            return mock_result_error_fetch
        mock_default_result = AsyncMock()
        mock_default_result.scalar_one_or_none = MagicMock(return_value=None)
        return mock_default_result

    mock_db_session.execute = AsyncMock(side_effect=execute_side_effect_fail)
    mock_discovery_service.discover_sources = AsyncMock(
        side_effect=Exception("Discovery API down")
    )

    await processing_service.process_query(
        query_id, mock_db_session, mock_discovery_service
    )

    assert mock_user_query_instance.status == "error"
    mock_db_session.add.assert_called_with(mock_user_query_instance)


# Remove the erroneous tag below
# </rewritten_file>
