import os

import pytest
from httpx import AsyncClient

# We will run tests against the running service if E2E is specified,
# otherwise we might want to spin up a test app.
# For now, let's assume we are running against the local docker-compose environment as the original scripts did.


@pytest.fixture(scope="session")
def api_url():
    return os.getenv("API_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def auth_token():
    # Check if running in no-auth mode
    noauth_mode = os.getenv("TORALE_NOAUTH", "0") == "1"

    if noauth_mode:
        return None

    token = os.getenv("CLERK_TEST_TOKEN")
    if not token:
        pytest.skip("CLERK_TEST_TOKEN not set and not in NOAUTH mode")
    return token


@pytest.fixture
async def client(api_url, auth_token):
    headers = {}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    async with AsyncClient(base_url=api_url, headers=headers) as ac:
        yield ac
