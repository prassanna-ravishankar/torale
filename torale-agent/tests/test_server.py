"""Unit and protocol integration tests for the A2A 1.x agent server."""

import json
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from a2a.client import ClientConfig, create_client
from a2a.helpers import get_data_parts, get_message_text, new_text_message
from a2a.server.events import Event, EventQueue
from a2a.types import (
    Role,
    SendMessageRequest,
    StreamResponse,
    Task,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatusUpdateEvent,
)
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.test import TestModel
from pydantic_ai.toolsets import AbstractToolset, ToolsetTool

import server
from models import MonitoringResponse
from server import ToraleAgentExecutor, _build_mcp_toolsets


RESPONSE = MonitoringResponse(
    evidence="checked",
    sources=["https://example.com"],
    confidence=91,
    next_run="2026-08-09T12:00:00Z",
)


class RecordingQueue(EventQueue):
    def __init__(self):
        self.events = []

    async def enqueue_event(self, event: Event) -> None:
        self.events.append(event)


def make_context(metadata=None):
    message = new_text_message(
        "check the web",
        role=Role.ROLE_USER,
        task_id="a2a-task",
        context_id="context-1",
    )
    context = MagicMock()
    context.task_id = message.task_id
    context.context_id = message.context_id
    context.message = message
    context.metadata = (
        {"user_id": "user-1", "task_id": "watch-1"} if metadata is None else metadata
    )
    context.get_user_input.return_value = "check the web"
    return context


def successful_agent():
    result = SimpleNamespace(output=RESPONSE, all_messages=lambda: [])
    agent = MagicMock()
    agent.run = AsyncMock(return_value=result)
    return agent


@pytest.mark.asyncio
async def test_success_emits_initial_task_before_updates():
    queue = RecordingQueue()
    executor = ToraleAgentExecutor(successful_agent())

    await executor.execute(make_context(), queue)

    assert isinstance(queue.events[0], Task)
    assert queue.events[0].status.state == TaskState.TASK_STATE_SUBMITTED
    assert isinstance(queue.events[1], TaskStatusUpdateEvent)
    assert queue.events[1].status.state == TaskState.TASK_STATE_WORKING
    assert isinstance(queue.events[2], TaskArtifactUpdateEvent)
    assert get_data_parts(queue.events[2].artifact.parts) == [
        RESPONSE.model_dump(mode="json")
    ]
    assert queue.events[3].status.state == TaskState.TASK_STATE_COMPLETED


@pytest.mark.asyncio
async def test_missing_metadata_emits_final_failed_status():
    queue = RecordingQueue()
    executor = ToraleAgentExecutor(successful_agent())

    await executor.execute(make_context(metadata={}), queue)

    assert isinstance(queue.events[0], Task)
    failure = queue.events[-1]
    assert failure.status.state == TaskState.TASK_STATE_FAILED
    details = json.loads(get_message_text(failure.status.message))
    assert details["error_type"] == "ConfigurationError"
    assert "user_id" in details["message"]
    assert "task_id" in details["message"]


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code", [429, 503])
async def test_model_http_error_preserves_fallback_details(status_code):
    queue = RecordingQueue()
    agent = MagicMock()
    agent.run = AsyncMock(side_effect=ModelHTTPError(status_code, "gemini", "failed"))
    executor = ToraleAgentExecutor(agent)

    await executor.execute(make_context(), queue)

    failure = queue.events[-1]
    details = json.loads(get_message_text(failure.status.message))
    assert failure.status.state == TaskState.TASK_STATE_FAILED
    assert details["error_type"] == "ModelHTTPError"
    assert details["status_code"] == status_code
    assert details["model_name"] == "gemini"


@pytest.mark.asyncio
async def test_cancel_is_terminal():
    queue = RecordingQueue()
    await ToraleAgentExecutor(successful_agent()).cancel(make_context(), queue)
    assert queue.events == [queue.events[0]]
    assert queue.events[0].status.state == TaskState.TASK_STATE_CANCELED


def test_no_mcp_metadata_allocates_nothing():
    assert _build_mcp_toolsets(None) == []
    assert _build_mcp_toolsets([]) == []


def test_mcp_entries_are_validated_and_configured(monkeypatch):
    monkeypatch.setenv("COMPOSIO_API_KEY", "secret")
    with patch("server.MCPToolset") as toolset:
        result = _build_mcp_toolsets(
            cast(
                list[dict],
                [
                    {"toolkit": "gmail", "url": "https://mcp.example/gmail"},
                    {"toolkit": "missing-url"},
                    "malformed",
                ],
            )
        )
    toolset.assert_called_once_with(
        "https://mcp.example/gmail",
        headers={"x-api-key": "secret"},
        id="gmail",
    )
    assert result == [toolset.return_value]


class TrackingToolset(AbstractToolset[Any]):
    def __init__(self, *, fail=False):
        self.entered = False
        self.exited = False
        self.fail = fail

    @property
    def id(self):
        return "tracking"

    async def __aenter__(self):
        self.entered = True
        return self

    async def __aexit__(self, *args):
        self.exited = True

    async def get_tools(self, ctx: RunContext[Any]) -> dict[str, ToolsetTool[Any]]:
        del ctx
        if self.fail:
            raise RuntimeError("tool discovery failed")
        return {}

    async def call_tool(
        self,
        name: str,
        tool_args: dict[str, Any],
        ctx: RunContext[Any],
        tool: ToolsetTool[Any],
    ) -> Any:  # pragma: no cover
        raise AssertionError("no tools are registered")


@pytest.mark.asyncio
@pytest.mark.parametrize("fail", [False, True])
async def test_per_run_toolset_lifecycle_closes_on_success_and_failure(fail):
    toolset = TrackingToolset(fail=fail)
    agent = Agent(
        TestModel(custom_output_args=RESPONSE.model_dump(mode="json")),
        output_type=MonitoringResponse,
    )

    if fail:
        with pytest.raises(RuntimeError, match="tool discovery failed"):
            await agent.run("check", toolsets=[toolset])
    else:
        result = await agent.run("check", toolsets=[toolset])
        assert result.output == RESPONSE

    assert toolset.entered is True
    assert toolset.exited is True


@pytest.mark.asyncio
async def test_real_client_and_server_stream_structured_result():
    original_agent = server.executor.agent
    server.executor.agent = successful_agent()
    http_client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=server.app),
        base_url="http://agent.test",
    )
    try:
        client = await create_client(
            "http://agent.test",
            ClientConfig(streaming=True, httpx_client=http_client),
        )
        request = SendMessageRequest(
            message=new_text_message("check", role=Role.ROLE_USER),
            metadata={"user_id": "user-1", "task_id": "watch-1"},
        )
        events: list[StreamResponse] = []
        async for event in client.send_message(request):
            events.append(event)

        assert events[0].HasField("task")
        assert any(event.HasField("artifact_update") for event in events)
        assert events[-1].status_update.status.state == TaskState.TASK_STATE_COMPLETED
        artifact_event = next(
            event for event in events if event.HasField("artifact_update")
        )
        assert get_data_parts(artifact_event.artifact_update.artifact.parts) == [
            RESPONSE.model_dump(mode="json")
        ]
    finally:
        server.executor.agent = original_agent
        await http_client.aclose()
