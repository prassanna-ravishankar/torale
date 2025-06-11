import logging
import os  # Keep os import

import pytest

# --- Set Environment Variables for Tests BEFORE any app imports ---
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{os.path.abspath('./test.db')}"
os.environ["SENDGRID_API_KEY"] = "TEST_SENDGRID_KEY"
os.environ["PERPLEXITY_API_KEY"] = "TEST_PPLX_KEY"
os.environ["OPENAI_API_KEY"] = "TEST_OPENAI_KEY"
os.environ["LOG_LEVEL"] = "INFO"
os.environ["PROJECT_NAME"] = "Test Project"
os.environ["API_V1_STR"] = "/api/v1"
os.environ["CORS_ORIGINS"] = '["http://localhost:3000"]'  # No comma here!
os.environ["SELECTED_AI_PROVIDER"] = "openai"

# --- Now import application modules ---
import asyncio

from fastapi.testclient import TestClient
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.db import Base, get_db  # Import app engine directly
from app.core.db import engine as app_engine
from app.main import app as main_app

# Explicitly import all models

# --- Use a file-based SQLite DB for tests --- #
TEST_DB_FILE = "./test.db"  # Keep definition if needed for cleanup


@pytest.fixture(scope="session")
def event_loop():
    # Override default pytest-asyncio event loop scope if needed
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# --- Engine fixture uses app_engine now, which uses env var ---
@pytest.fixture(scope="session")
def test_async_engine():
    """Returns the application's async engine instance configured via env vars."""
    # The engine is created in db.py using the env var set above
    yield app_engine
    # Dispose logic might need adjustment if we rely on app_engine's lifecycle
    # Let's assume pytest or the OS handles file cleanup for now


# New fixture to handle async table creation and cleanup
@pytest.fixture(scope="session", autouse=True)
async def setup_database_async(test_async_engine):
    """Deletes old DB, creates tables, inspects, yields, then deletes."""
    logger = logging.getLogger(__name__)
    # Use the DB file path derived from the env var if possible
    # settings = get_settings() # Get settings instance
    # db_file_path = settings.DATABASE_URL.split("///")[-1]
    # Or just use the TEST_DB_FILE constant
    db_file_path = TEST_DB_FILE

    if os.path.exists(db_file_path):
        logger.info(f"Deleting existing test database: {db_file_path}")
        try:
            os.remove(db_file_path)
        except OSError as e:
            logger.warning(
                f"Could not delete existing db file {db_file_path}: {e}"
            )  # Log error if deletion fails

    logger.info(f"Running setup_database_async with engine: {test_async_engine.url}")
    async with test_async_engine.begin() as conn:
        logger.info("Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Tables created. Inspecting schema...")

        def inspect_sync(sync_conn):
            inspector = inspect(sync_conn)
            tables = inspector.get_table_names()
            logger.info(f"Inspector found tables: {tables}")
            for table_name in tables:
                columns = inspector.get_columns(table_name)
                logger.info(f"Columns in {table_name}: {columns}")
                if table_name == "monitored_sources":
                    has_name_col = any(col["name"] == "name" for col in columns)
                    logger.info(
                        f"Does 'monitored_sources' have 'name' column? {has_name_col}"
                    )

        await conn.run_sync(inspect_sync)
        logger.info("Schema inspection complete.")

    yield  # Run tests

    # Cleanup
    if os.path.exists(db_file_path):
        logger.info(f"Deleting test database after tests: {db_file_path}")
        try:
            # Ensure engine is disposed before deleting?
            # Maybe not necessary for SQLite file.
            # await test_async_engine.dispose() # Might fail if using shared app_engine
            os.remove(db_file_path)
            logger.info("Test database deleted.")
        except Exception as e:
            logger.error(f"Could not delete test database {db_file_path}: {e}")


# ...
# rest of the fixtures
# (TestingSessionLocal, db_session, override_get_db_for_testing, client)
# ...


# Make sure testing_session_local uses the test_async_engine
@pytest.fixture(scope="session")
def testing_session_local(test_async_engine):
    """Creates an async session factory bound to the async test engine."""
    return sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_async_engine,  # Bind to the engine from test_async_engine fixture
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest.fixture(scope="function")
async def db_session(testing_session_local: sessionmaker):
    """Clean async DB session. Test manages transactions, fixture ensures rollback."""
    async with testing_session_local() as session:
        try:
            yield session  # Provide the session, test must manage begin/commit/rollback
        finally:
            # Ensure rollback happens even if test fails or forgets
            try:
                await session.rollback()
            except Exception as e:
                # Log if rollback fails (e.g., session already closed)
                logger = logging.getLogger(__name__)
                logger.warning(f"Rollback failed in db_session fixture: {e}")
            # Session context manager handles closing


@pytest.fixture(scope="function")
def override_get_db_for_testing(testing_session_local: sessionmaker):
    """Overrides get_db. Session in savepoint, endpoint manages commit/rollback."""

    async def _override_get_db():
        async with testing_session_local() as session:
            # Start savepoint, yield session, let endpoint manage actions.
            # Outer test fixture (db_session) will roll back main transaction.
            async with session.begin_nested():
                yield session
            # No explicit commit/rollback; savepoint context manager handles it.
            # (based on exceptions or endpoint actions like session.commit()).

    return _override_get_db


@pytest.fixture(scope="function")
def client(override_get_db_for_testing) -> TestClient:
    """Creates TestClient w/ transactional DB override for each function."""
    main_app.dependency_overrides[get_db] = override_get_db_for_testing
    # Use context manager for TestClient
    with TestClient(main_app) as c:
        yield c
    # Clear overrides after the client is done
    main_app.dependency_overrides.clear()


# Remove old fixture definitions
# def test_engine(): ...
# TestingSessionLocal = sessionmaker(...)
# Base.metadata.create_all(bind=engine)
# def override_get_db(): ...
# app.dependency_overrides[get_db] = override_get_db
