"""Deterministic HTTP contract tests for the public Python SDK."""

import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

import httpx
import pytest

from webwhen.sdk import Webwhen, WebwhenAsync
from webwhen.sdk.exceptions import APIError, AuthenticationError, NotFoundError, ValidationError

API_URL = "https://sdk.test"
API_KEY = "test-api-key"


def task_payload(task_id: UUID | None = None, **overrides) -> dict:
    now = datetime.now(UTC).isoformat()
    payload = {
        "id": str(task_id or uuid4()),
        "user_id": str(uuid4()),
        "name": "Release watch",
        "state": "active",
        "search_query": "When is it released?",
        "condition_description": "A date is announced",
        "notifications": [],
        "attached_connector_slugs": [],
        "created_at": now,
        "state_changed_at": now,
    }
    payload.update(overrides)
    return payload


def json_body(request: httpx.Request) -> dict:
    return json.loads(request.content)


def sync_client(handler) -> Webwhen:
    client = Webwhen(api_key=API_KEY, api_url=API_URL)
    client.http_client.close()
    client.http_client = httpx.Client(
        base_url=API_URL,
        headers={"Authorization": f"Bearer {API_KEY}"},
        transport=httpx.MockTransport(handler),
    )
    return client


async def async_client(handler) -> WebwhenAsync:
    client = WebwhenAsync(api_key=API_KEY, api_url=API_URL)
    await client.http_client.aclose()
    client.http_client = httpx.AsyncClient(
        base_url=API_URL,
        headers={"Authorization": f"Bearer {API_KEY}"},
        transport=httpx.MockTransport(handler),
    )
    return client


def test_sync_task_crud_request_contract():
    task_id = uuid4()
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.method == "POST":
            return httpx.Response(200, json=task_payload(task_id), request=request)
        if request.method == "GET":
            return httpx.Response(200, json=[task_payload(task_id)], request=request)
        if request.method == "PUT":
            return httpx.Response(
                200, json=task_payload(task_id, name="Renamed", state="paused"), request=request
            )
        return httpx.Response(204, request=request)

    with sync_client(handler) as client:
        created = client.tasks.create(
            name="Release watch",
            search_query="When is it released?",
            condition_description="A date is announced",
            notifications=[{"type": "email", "address": "person@example.com"}],
        )
        listed = client.tasks.list(active=True)
        updated = client.tasks.update(task_id, name="Renamed", state="paused")
        client.tasks.delete(task_id)

    assert created.id == task_id
    assert listed[0].id == task_id
    assert updated.name == "Renamed"
    assert [(request.method, request.url.path) for request in requests] == [
        ("POST", "/api/v1/tasks/"),
        ("GET", "/api/v1/tasks/"),
        ("PUT", f"/api/v1/tasks/{task_id}"),
        ("DELETE", f"/api/v1/tasks/{task_id}"),
    ]
    assert json_body(requests[0]) == {
        "name": "Release watch",
        "search_query": "When is it released?",
        "condition_description": "A date is announced",
        "notifications": [{"type": "email", "address": "person@example.com"}],
        "state": "active",
    }
    assert dict(requests[1].url.params) == {"state": "active"}
    assert json_body(requests[2]) == {"name": "Renamed", "state": "paused"}
    assert all(request.headers["authorization"] == f"Bearer {API_KEY}" for request in requests)


@pytest.mark.asyncio
async def test_async_task_crud_request_contract():
    task_id = uuid4()
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.method == "POST":
            return httpx.Response(200, json=task_payload(task_id), request=request)
        if request.method == "PUT":
            return httpx.Response(200, json=task_payload(task_id, state="paused"), request=request)
        return httpx.Response(204, request=request)

    client = await async_client(handler)
    async with client:
        created = await client.tasks.create(
            "Release watch", "When is it released?", "A date is announced"
        )
        updated = await client.tasks.update(task_id, state="paused")
        await client.tasks.delete(task_id)

    assert created.id == task_id
    assert updated.state == "paused"
    assert [(request.method, request.url.path) for request in requests] == [
        ("POST", "/api/v1/tasks/"),
        ("PUT", f"/api/v1/tasks/{task_id}"),
        ("DELETE", f"/api/v1/tasks/{task_id}"),
    ]
    assert json_body(requests[0])["notifications"] == []
    assert json_body(requests[1]) == {"state": "paused"}


@pytest.mark.parametrize(
    ("status", "exception_type"),
    [
        (401, AuthenticationError),
        (404, NotFoundError),
        (422, ValidationError),
        (500, APIError),
    ],
)
def test_sync_error_mapping(status: int, exception_type: type[Exception]):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, json={"detail": "request failed"}, request=request)

    with (
        sync_client(handler) as client,
        pytest.raises(exception_type, match="request failed") as exc,
    ):
        client.tasks.get(uuid4())

    if isinstance(exc.value, APIError):
        assert exc.value.status_code == status
        assert exc.value.response == {"detail": "request failed"}


@pytest.mark.asyncio
async def test_async_not_found_mapping():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"detail": "watch missing"}, request=request)

    client = await async_client(handler)
    async with client:
        with pytest.raises(NotFoundError, match="watch missing"):
            await client.tasks.get(uuid4())
