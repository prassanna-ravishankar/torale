"""Tests for the streaming A2A 1.x agent client."""

import json
from unittest.mock import AsyncMock, patch

import pytest
from a2a.client.errors import A2AClientError
from a2a.helpers import (
    new_data_artifact_update_event,
    new_data_message,
    new_text_message,
    new_text_status_update_event,
)
from a2a.types import Role, StreamResponse, TaskState
from google.protobuf.json_format import MessageToDict
from pydantic import ValidationError

from tests.conftest import data_artifact, make_a2a_task, task_stream_event, text_artifact
from webwhen.scheduler.agent import (
    AgentUpstreamHTTPError,
    _apply_stream_event,
    _extract_error_details,
    _handle_failed_task,
    _parse_agent_response,
    call_agent,
)
from webwhen.scheduler.models import MonitoringResponse

VALID_RESPONSE = {
    "evidence": "found it",
    "sources": ["https://example.com"],
    "confidence": 95,
    "next_run": "2026-02-08T12:00:00Z",
    "notification": None,
    "topic": None,
}


class FakeClient:
    def __init__(self, events=(), error: Exception | None = None, wait_forever=False):
        self.events = list(events)
        self.error = error
        self.wait_forever = wait_forever
        self.request = None

    def send_message(self, request):
        self.request = request

        async def stream():
            if self.wait_forever:
                await __import__("asyncio").Event().wait()
            for event in self.events:
                yield event
            if self.error:
                raise self.error

        return stream()


def success_events(data=VALID_RESPONSE):
    submitted = make_a2a_task(status_state=TaskState.TASK_STATE_SUBMITTED)
    artifact = new_data_artifact_update_event(
        task_id=submitted.id,
        context_id=submitted.context_id,
        name="monitoring-response",
        data=data,
        last_chunk=True,
        artifact_id="result-1",
    )
    completed = new_text_status_update_event(
        submitted.id,
        submitted.context_id,
        TaskState.TASK_STATE_COMPLETED,
        "complete",
    )
    return [
        task_stream_event(submitted),
        StreamResponse(artifact_update=artifact),
        StreamResponse(status_update=completed),
    ]


def failure_events(status_code=429, error_type="ModelHTTPError"):
    submitted = make_a2a_task(status_state=TaskState.TASK_STATE_SUBMITTED)
    details = {
        "error_type": error_type,
        "status_code": status_code,
        "model_name": "gemini",
        "message": "provider failed",
    }
    failed = new_text_status_update_event(
        submitted.id,
        submitted.context_id,
        TaskState.TASK_STATE_FAILED,
        json.dumps(details),
    )
    return [task_stream_event(submitted), StreamResponse(status_update=failed)]


class TestParseAgentResponse:
    def test_structured_data(self):
        task = make_a2a_task(artifacts=[data_artifact(VALID_RESPONSE)])
        assert _parse_agent_response(task) == VALID_RESPONSE

    def test_result_wrapper_is_unwrapped(self):
        task = make_a2a_task(artifacts=[data_artifact({"result": VALID_RESPONSE})])
        assert _parse_agent_response(task) == VALID_RESPONSE

    def test_json_text_compatibility(self):
        task = make_a2a_task(artifacts=[text_artifact(json.dumps(VALID_RESPONSE))])
        assert _parse_agent_response(task) == VALID_RESPONSE

    @pytest.mark.parametrize("artifacts", [[], None])
    def test_empty_response_raises(self, artifacts):
        with pytest.raises(RuntimeError, match="empty response"):
            _parse_agent_response(make_a2a_task(artifacts=artifacts))

    def test_python_repr_is_no_longer_accepted(self):
        task = make_a2a_task(artifacts=[text_artifact("{'evidence': 'legacy'}")])
        with pytest.raises(RuntimeError, match="non-JSON"):
            _parse_agent_response(task)

    def test_invalid_application_shape_fails_validation(self):
        task = make_a2a_task(artifacts=[data_artifact({"confidence": 150})])
        with pytest.raises(ValidationError):
            MonitoringResponse.model_validate(_parse_agent_response(task))


class TestStreamAggregation:
    def test_folds_artifact_and_terminal_status(self):
        task = None
        for event in success_events():
            task = _apply_stream_event(task, event)
        assert task is not None
        assert task.status.state == TaskState.TASK_STATE_COMPLETED
        assert _parse_agent_response(task) == VALID_RESPONSE

    def test_event_before_initial_task_is_ignored(self):
        event = StreamResponse(
            status_update=new_text_status_update_event(
                "task", "ctx", TaskState.TASK_STATE_WORKING, "working"
            )
        )
        assert _apply_stream_event(None, event) is None


class TestErrorHandling:
    def test_extracts_structured_error(self):
        task = make_a2a_task(status_state=TaskState.TASK_STATE_FAILED)
        details = {"error_type": "ModelHTTPError", "status_code": 429, "message": "rate"}
        task.status.message.CopyFrom(
            new_text_message(
                json.dumps(details),
                role=Role.ROLE_AGENT,
                task_id=task.id,
                context_id=task.context_id,
            )
        )
        assert _extract_error_details(task) == details

    def test_missing_error_message(self):
        task = make_a2a_task(status_state=TaskState.TASK_STATE_FAILED)
        task.status.ClearField("message")
        assert _extract_error_details(task) is None
        with pytest.raises(RuntimeError, match="without error details"):
            _handle_failed_task(task)

    def test_non_text_error_message(self):
        task = make_a2a_task(status_state=TaskState.TASK_STATE_FAILED)
        task.status.message.CopyFrom(new_data_message({"bad": True}, task_id=task.id))
        assert _extract_error_details(task) is None

    def test_malformed_error_json(self):
        task = make_a2a_task(status_state=TaskState.TASK_STATE_FAILED)
        task.status.message.CopyFrom(new_text_message("{'bad': json", task_id=task.id))
        assert _extract_error_details(task)["error_type"] == "JSONParseError"

    @pytest.mark.parametrize("status_code", [429, 503])
    def test_fallback_status_raises_typed_error(self, status_code):
        task = make_a2a_task(status_state=TaskState.TASK_STATE_FAILED)
        task.status.message.CopyFrom(
            new_text_message(
                json.dumps(
                    {
                        "error_type": "ModelHTTPError",
                        "status_code": status_code,
                        "message": "provider failed",
                    }
                ),
                task_id=task.id,
            )
        )
        with pytest.raises(AgentUpstreamHTTPError) as exc:
            _handle_failed_task(task)
        assert exc.value.status_code == status_code

    def test_non_fallback_status_is_runtime_error(self):
        task = make_a2a_task(status_state=TaskState.TASK_STATE_FAILED)
        task.status.message.CopyFrom(
            new_text_message(
                json.dumps(
                    {
                        "error_type": "ModelHTTPError",
                        "status_code": 500,
                        "message": "provider failed",
                    }
                ),
                task_id=task.id,
            )
        )
        with pytest.raises(RuntimeError, match="HTTP error 500"):
            _handle_failed_task(task)


class TestCallAgent:
    @pytest.mark.asyncio
    async def test_completed_stream(self):
        client = FakeClient(success_events())
        with patch("webwhen.scheduler.agent.create_client", AsyncMock(return_value=client)):
            result = await call_agent("test prompt")
        assert result.evidence == "found it"
        assert not hasattr(client, "get_task")

    @pytest.mark.asyncio
    async def test_metadata_survives_protobuf_conversion(self):
        client = FakeClient(success_events())
        mcp = [{"toolkit": "gmail", "url": "https://mcp.example.test"}]
        with patch("webwhen.scheduler.agent.create_client", AsyncMock(return_value=client)):
            await call_agent("test", user_id="user-1", task_id="watch-1", mcp_servers=mcp)
        assert MessageToDict(client.request.metadata) == {
            "user_id": "user-1",
            "task_id": "watch-1",
            "mcp_servers": mcp,
        }

    @pytest.mark.asyncio
    async def test_failed_stream(self):
        client = FakeClient(failure_events(status_code=500))
        with patch("webwhen.scheduler.agent.create_client", AsyncMock(return_value=client)):
            with pytest.raises(RuntimeError, match="HTTP error 500"):
                await call_agent("test")

    @pytest.mark.asyncio
    async def test_transport_failure(self):
        client = FakeClient(error=A2AClientError("connection lost"))
        with patch("webwhen.scheduler.agent.create_client", AsyncMock(return_value=client)):
            with pytest.raises(RuntimeError, match="Failed to stream"):
                await call_agent("test")

    @pytest.mark.asyncio
    async def test_timeout(self):
        client = FakeClient(wait_forever=True)
        with (
            patch("webwhen.scheduler.agent.create_client", AsyncMock(return_value=client)),
            patch("webwhen.scheduler.agent.AGENT_TIMEOUT", 0.01),
        ):
            with pytest.raises(TimeoutError, match="did not complete"):
                await call_agent("test")

    @pytest.mark.asyncio
    @pytest.mark.parametrize("status_code", [429, 503])
    async def test_free_tier_falls_back_to_paid(self, status_code):
        free = FakeClient(failure_events(status_code=status_code))
        paid = FakeClient(success_events())
        create = AsyncMock(side_effect=[free, paid])
        with (
            patch("webwhen.scheduler.agent.create_client", create),
            patch("webwhen.scheduler.agent.settings") as settings,
        ):
            settings.agent_url_free = "http://free"
            settings.agent_url_paid = "http://paid"
            result = await call_agent("test")
        assert result.confidence == 95
        assert [call.args[0] for call in create.await_args_list] == ["http://free", "http://paid"]

    @pytest.mark.asyncio
    async def test_non_fallback_error_does_not_switch_tiers(self):
        create = AsyncMock(return_value=FakeClient(failure_events(status_code=500)))
        with patch("webwhen.scheduler.agent.create_client", create):
            with pytest.raises(RuntimeError, match="HTTP error 500"):
                await call_agent("test")
        assert create.await_count == 1

    @pytest.mark.asyncio
    async def test_both_tiers_failing_propagates(self):
        create = AsyncMock(
            side_effect=[
                FakeClient(failure_events(status_code=429)),
                FakeClient(failure_events(status_code=503)),
            ]
        )
        with patch("webwhen.scheduler.agent.create_client", create):
            with pytest.raises(AgentUpstreamHTTPError) as exc:
                await call_agent("test")
        assert exc.value.status_code == 503
