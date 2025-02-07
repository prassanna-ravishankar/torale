"""Test configuration and fixtures."""

import tempfile

import pytest
import pytest_asyncio
from aiohttp import web

from ambi_alert.alerting import MockAlertBackend
from ambi_alert.database import DatabaseManager
from ambi_alert.monitor import WebsiteMonitor


@pytest_asyncio.fixture
async def db_manager():
    """Create a temporary database for testing."""
    # Use temporary file for database
    with tempfile.NamedTemporaryFile(suffix=".db") as temp_db:
        db = DatabaseManager(temp_db.name)
        await db._init_db()
        yield db
        await db.close()
        # File is automatically deleted when context exits


@pytest_asyncio.fixture
async def mock_web_server():
    """Create a mock web server for testing."""

    async def hello(request):
        return web.Response(text="<html><body><div>Hello World</div></body></html>")

    app = web.Application()
    app.router.add_get("/", hello)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "localhost", 8080)
    await site.start()
    yield "http://localhost:8080"
    await runner.cleanup()


@pytest.fixture
def mock_alert_backend():
    """Create a mock alert backend for testing."""
    return MockAlertBackend()


@pytest.fixture
def website_monitor():
    """Create a WebsiteMonitor instance for testing."""
    monitor = WebsiteMonitor()
    yield monitor
    # Ensure cleanup in case test doesn't close the session
    if monitor._session and not monitor._session.closed:
        import asyncio

        asyncio.run(monitor.close())
