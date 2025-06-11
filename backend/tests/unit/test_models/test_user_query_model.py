import asyncio  # Import asyncio for sleep

import pytest
from sqlalchemy import (
    select,  # Removed func
)  # Keep for engine definition if needed locally, but maybe not
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_query_model import UserQuery

# Remove engine and session setup if fully handled by conftest.py
# TEST_DATABASE_URL = "sqlite:///:memory:"
# engine = create_engine(TEST_DATABASE_URL)
# TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Remove the local fixture definition - provided by conftest.py
# @pytest.fixture(scope="function")
# def db_session():
#     """Creates a new database session for a test."""
#     Base.metadata.create_all(bind=engine) # Create tables
#     session = TestingSessionLocal()
#     try:
#         yield session
#     finally:
#         session.close()
#         Base.metadata.drop_all(bind=engine) # Drop tables


@pytest.mark.asyncio
async def test_user_query_creation(
    db_session: AsyncSession,
):  # Mark async, use async db_session
    """Test creating a UserQuery instance with default and provided values."""
    raw_query = "Test query for tkmaxx discounts"
    hints = {"priority": "high", "check_interval": 3600}

    # Manage transaction within the test
    async with db_session.begin():
        # Pass dict directly, SQLAlchemy handles JSON conversion
        query = UserQuery(
            raw_query=raw_query,
            config_hints_json=hints,
        )
        db_session.add(query)
        # Commit is handled by the context manager
        # `db_session.begin()` on successful exit

    # Refresh needs to happen after commit, potentially outside the transaction block
    # or within a new one, depending on session state.
    # Let's refresh after the transaction commits.
    # No, refresh should happen before commit or within the same tx if needed.
    # Let's commit explicitly and refresh within the block.

    async with db_session.begin():  # Start transaction
        query = UserQuery(raw_query=raw_query, config_hints_json=hints)
        db_session.add(query)
        await db_session.flush()  # Flush to assign ID etc.
        await db_session.refresh(query)  # Refresh within the transaction

        assert query.id is not None
        assert query.raw_query == raw_query
        assert query.config_hints_json == hints
        assert query.status == "pending_discovery"  # Default value
        assert query.created_at is not None
        assert query.updated_at is not None
        assert query.created_at == query.updated_at  # Should be same on creation

        # Commit handled by context manager


@pytest.mark.asyncio
async def test_user_query_update_timestamp(db_session: AsyncSession):  # Mark async
    """Test that updated_at timestamp is updated when the record changes."""
    initial_query = "Initial query"
    updated_query_text = "Updated query text"

    # Create initial record
    async with db_session.begin():
        query = UserQuery(raw_query=initial_query)
        db_session.add(query)
        await db_session.flush()  # Assign ID and timestamps
        await db_session.refresh(query)  # Load timestamps
        initial_created_at = query.created_at
        initial_updated_at = query.updated_at
        query_id = query.id
        # Commit handled by context manager

    assert initial_created_at is not None
    assert initial_updated_at is not None
    assert initial_created_at == initial_updated_at  # Should be same initially

    # Add a small delay to ensure timestamp difference (best effort)
    await asyncio.sleep(0.015)  # Slightly longer sleep, just in case

    # Update the record - Use a separate transaction block
    async with db_session.begin():
        # Fetch the object within the new transaction
        stmt = select(UserQuery).where(UserQuery.id == query_id)
        result = await db_session.execute(stmt)
        query_to_update = result.scalar_one()

        # Modify
        query_to_update.raw_query = updated_query_text
        db_session.add(query_to_update)  # Add to session to trigger onupdate
        # Commit handled by context manager

    # Verify update outside the transaction block
    # Use a new session or ensure the previous one is in a valid state
    async with db_session.begin():  # New transaction or re-use with begin for fetching
        stmt_verify = select(UserQuery).where(UserQuery.id == query_id)
        result_verify = await db_session.execute(stmt_verify)
        updated_query = result_verify.scalar_one()

        assert updated_query.raw_query == updated_query_text
        assert (
            updated_query.created_at == initial_created_at
        )  # Created_at should not change
        assert updated_query.updated_at is not None
        # Check that updated_at is at least the same as created_at
        # (covers initial creation and update)
        assert updated_query.updated_at >= initial_created_at
