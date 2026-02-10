"""Tests for the A2A agent client (call_agent + _parse_agent_response)."""

import json
from unittest.mock import AsyncMock, patch

import pytest
from a2a.client.errors import A2AClientHTTPError
from a2a.types import (
    Artifact,
    DataPart,
    JSONRPCError,
    JSONRPCErrorResponse,
    Message,
    Part,
    Role,
    SendMessageResponse,
    TaskState,
    TextPart,
)
from pydantic import ValidationError

from tests.conftest import data_artifact, make_a2a_task, poll_success, send_success, text_artifact
from torale.scheduler.agent import (
    _extract_error_details,
    _handle_failed_task,
    _parse_agent_response,
    call_agent,
)
from torale.scheduler.models import MonitoringResponse


class TestParseAgentResponse:
    """Tests for _parse_agent_response (pure function, no mocking).

    _parse_agent_response now takes a Task object directly.
    """

    def test_single_artifact_valid_json(self):
        task = make_a2a_task(
            artifacts=[text_artifact('{"condition_met": true, "evidence": "found"}')]
        )
        parsed = _parse_agent_response(task)
        assert parsed == {"condition_met": True, "evidence": "found"}

    def test_data_part_structured_response(self):
        """DataPart with structured data is parsed directly."""
        task = make_a2a_task(
            artifacts=[
                data_artifact(
                    {"evidence": "found it", "sources": ["https://example.com"], "confidence": 95}
                )
            ]
        )
        parsed = _parse_agent_response(task)
        assert parsed == {
            "evidence": "found it",
            "sources": ["https://example.com"],
            "confidence": 95,
        }

    def test_multiple_text_parts_concatenated(self):
        """Legacy text parts are concatenated and parsed as JSON."""
        task = make_a2a_task(
            artifacts=[
                Artifact(
                    artifact_id="art-1",
                    parts=[
                        Part(root=TextPart(kind="text", text='{"key": ')),
                        Part(root=TextPart(kind="text", text='"value"}')),
                    ],
                )
            ]
        )
        parsed = _parse_agent_response(task)
        assert parsed == {"key": "value"}

    @pytest.mark.parametrize(
        "artifacts",
        [
            [],
            None,
        ],
        ids=["empty_artifacts_list", "no_artifacts"],
    )
    def test_no_artifacts_raises(self, artifacts):
        task = make_a2a_task(artifacts=artifacts)
        with pytest.raises(RuntimeError, match="empty response"):
            _parse_agent_response(task)

    def test_invalid_json_raises(self):
        """Legacy text response that isn't valid JSON raises error."""
        task = make_a2a_task(artifacts=[text_artifact("not json at all")])
        with pytest.raises(RuntimeError, match="non-JSON text response"):
            _parse_agent_response(task)

    def test_non_text_parts_skipped(self):
        from a2a.types import FilePart, FileWithBytes

        task = make_a2a_task(
            artifacts=[
                Artifact(
                    artifact_id="art-1",
                    parts=[
                        Part(
                            root=FilePart(
                                kind="file",
                                file=FileWithBytes(bytes="binary", mimeType="image/png"),
                            )
                        ),
                        Part(root=TextPart(kind="text", text='{"status": "ok"}')),
                    ],
                )
            ]
        )
        parsed = _parse_agent_response(task)
        assert parsed == {"status": "ok"}

    def test_error_message_includes_artifact_count_and_keys(self):
        from a2a.types import FilePart, FileWithBytes

        task = make_a2a_task(
            artifacts=[
                Artifact(
                    artifact_id="art-1",
                    parts=[
                        Part(
                            root=FilePart(
                                kind="file",
                                file=FileWithBytes(bytes="binary", mimeType="image/png"),
                            )
                        )
                    ],
                )
            ]
        )
        with pytest.raises(RuntimeError, match=r"artifacts=1.*task_keys="):
            _parse_agent_response(task)

    def test_data_part_takes_precedence_over_text_part(self):
        """When both DataPart and TextPart exist, DataPart is preferred."""
        task = make_a2a_task(
            artifacts=[
                Artifact(
                    artifact_id="art-1",
                    parts=[
                        Part(
                            root=DataPart(
                                kind="data",
                                data={
                                    "evidence": "from data",
                                    "sources": ["https://data.com"],
                                    "confidence": 90,
                                },
                            )
                        ),
                        Part(
                            root=TextPart(
                                kind="text",
                                text='{"evidence": "from text", "sources": ["https://text.com"], "confidence": 50}',
                            )
                        ),
                    ],
                )
            ]
        )
        parsed = _parse_agent_response(task)
        assert parsed["evidence"] == "from data"
        assert parsed["confidence"] == 90

    def test_python_dict_repr_parsed_via_literal_eval(self):
        """Agent returning Python dict repr (single quotes) is parsed via ast.literal_eval."""
        task = make_a2a_task(
            artifacts=[
                text_artifact(
                    "{'evidence': 'found', 'sources': ['https://x.com'], 'confidence': 85}"
                )
            ]
        )
        parsed = _parse_agent_response(task)
        assert parsed == {
            "evidence": "found",
            "sources": ["https://x.com"],
            "confidence": 85,
        }

    def test_malformed_python_literal_raises(self):
        """Malformed Python literal that isn't valid JSON or literal_eval raises."""
        task = make_a2a_task(artifacts=[text_artifact("{'unclosed': 'dict'")])
        with pytest.raises(RuntimeError, match="non-JSON text response"):
            _parse_agent_response(task)

    def test_empty_data_part_falls_through_to_text(self):
        """DataPart with empty data dict falls through to TextPart parsing."""
        task = make_a2a_task(
            artifacts=[
                Artifact(
                    artifact_id="art-1",
                    parts=[
                        Part(root=DataPart(kind="data", data={})),
                        Part(
                            root=TextPart(
                                kind="text",
                                text='{"evidence": "from text", "sources": [], "confidence": 80}',
                            )
                        ),
                    ],
                )
            ]
        )
        parsed = _parse_agent_response(task)
        assert parsed["evidence"] == "from text"

    def test_data_part_with_minimal_fields(self):
        """DataPart with only required fields passes validation."""
        task = make_a2a_task(
            artifacts=[
                data_artifact(
                    {
                        "evidence": "checked",
                        "sources": [],
                        "confidence": 50,
                        # notification, next_run, topic omitted (optional)
                    }
                )
            ]
        )
        parsed = _parse_agent_response(task)
        response = MonitoringResponse.model_validate(parsed)
        assert response.notification is None
        assert response.next_run is None
        assert response.topic is None


class TestMonitoringResponseValidation:
    """Test Pydantic validation of agent responses."""

    @pytest.mark.parametrize(
        "invalid_data,expected_error_field",
        [
            (
                {"evidence": "found", "sources": [], "confidence": 150},
                "confidence",
            ),  # confidence > 100
            (
                {"evidence": "found", "sources": [], "confidence": "high"},
                "confidence",
            ),  # confidence wrong type
            ({"sources": [], "confidence": 80}, "evidence"),  # missing required field
            (
                {"evidence": "found", "sources": "https://example.com", "confidence": 80},
                "sources",
            ),  # sources wrong type
        ],
        ids=[
            "confidence_out_of_range",
            "confidence_wrong_type",
            "missing_required_field",
            "sources_wrong_type",
        ],
    )
    def test_validation_errors(self, invalid_data, expected_error_field):
        """Test that invalid data raises ValidationError with expected field."""
        task = make_a2a_task(artifacts=[data_artifact(invalid_data)])
        parsed = _parse_agent_response(task)
        with pytest.raises(ValidationError, match=expected_error_field):
            MonitoringResponse.model_validate(parsed)


class TestErrorHandling:
    """Tests for error extraction and handling functions."""

    def test_extract_error_details_valid_json(self):
        """Valid JSON error details are extracted correctly."""
        error_data = {
            "error_type": "ModelHTTPError",
            "status_code": 429,
            "model_name": "gemini-3-flash",
            "message": "Rate limit exceeded",
        }

        task = make_a2a_task(status_state=TaskState.failed)
        task.status.message = Message(
            message_id="msg-1",
            role=Role.agent,
            parts=[Part(root=TextPart(text=json.dumps(error_data)))],
        )

        details = _extract_error_details(task)

        assert details == error_data
        assert details["error_type"] == "ModelHTTPError"
        assert details["status_code"] == 429

    def test_extract_error_details_no_message(self):
        """Missing message returns None."""
        task = make_a2a_task(status_state=TaskState.failed)
        task.status.message = None

        assert _extract_error_details(task) is None

    def test_extract_error_details_empty_parts(self):
        """Empty parts list returns None."""
        task = make_a2a_task(status_state=TaskState.failed)
        task.status.message = Message(message_id="msg-1", role=Role.agent, parts=[])

        assert _extract_error_details(task) is None

    def test_extract_error_details_non_text_part(self):
        """Non-TextPart returns None."""
        task = make_a2a_task(status_state=TaskState.failed)
        task.status.message = Message(
            message_id="msg-1",
            role=Role.agent,
            parts=[Part(root=DataPart(data={"error": "wrong type"}))],
        )

        assert _extract_error_details(task) is None

    def test_extract_error_details_malformed_json(self):
        """Malformed JSON returns structured fallback error."""
        task = make_a2a_task(status_state=TaskState.failed)
        task.status.message = Message(
            message_id="msg-1",
            role=Role.agent,
            parts=[Part(root=TextPart(text="{'invalid': json"))],
        )

        details = _extract_error_details(task)

        assert details is not None
        assert details["error_type"] == "JSONParseError"
        assert "malformed error data" in details["message"]
        assert "parse_error" in details

    def test_extract_error_details_truncates_long_errors(self):
        """Very long error messages are truncated in fallback."""
        long_text = "x" * 1000
        task = make_a2a_task(status_state=TaskState.failed)
        task.status.message = Message(
            message_id="msg-1", role=Role.agent, parts=[Part(root=TextPart(text=long_text))]
        )

        details = _extract_error_details(task)

        assert details["error_type"] == "JSONParseError"
        assert len(details["message"]) < len(long_text)

    def test_handle_failed_task_no_error_details(self):
        """No error details raises RuntimeError with status."""
        task = make_a2a_task(status_state=TaskState.failed, task_id="task-123")
        task.status.message = None

        with pytest.raises(RuntimeError, match="failed without error details"):
            _handle_failed_task(task)

    def test_handle_failed_task_model_http_429(self):
        """ModelHTTPError with 429 raises A2AClientHTTPError(429)."""
        error_data = {
            "error_type": "ModelHTTPError",
            "status_code": 429,
            "model_name": "gemini-3-flash",
            "message": "Rate limit exceeded",
        }

        task = make_a2a_task(status_state=TaskState.failed, task_id="task-123")
        task.status.message = Message(
            message_id="msg-1",
            role=Role.agent,
            parts=[Part(root=TextPart(text=json.dumps(error_data)))],
        )

        with pytest.raises(A2AClientHTTPError) as exc_info:
            _handle_failed_task(task)

        assert exc_info.value.status_code == 429
        assert "Rate limit" in str(exc_info.value)

    def test_handle_failed_task_model_http_500(self):
        """ModelHTTPError with non-429 raises RuntimeError."""
        error_data = {
            "error_type": "ModelHTTPError",
            "status_code": 500,
            "model_name": "gemini-3-flash",
            "message": "Internal server error",
        }

        task = make_a2a_task(status_state=TaskState.failed, task_id="task-123")
        task.status.message = Message(
            message_id="msg-1",
            role=Role.agent,
            parts=[Part(root=TextPart(text=json.dumps(error_data)))],
        )

        with pytest.raises(RuntimeError, match="HTTP error 500"):
            _handle_failed_task(task)

    def test_handle_failed_task_non_http_error(self):
        """Non-HTTP errors raise RuntimeError with error type."""
        error_data = {"error_type": "ValidationError", "message": "Invalid response format"}

        task = make_a2a_task(status_state=TaskState.failed, task_id="task-123")
        task.status.message = Message(
            message_id="msg-1",
            role=Role.agent,
            parts=[Part(root=TextPart(text=json.dumps(error_data)))],
        )

        with pytest.raises(RuntimeError, match="ValidationError"):
            _handle_failed_task(task)


class TestCallAgent:
    """Tests for call_agent (mock a2a.client.A2AClient)."""

    @pytest.mark.asyncio
    @patch("torale.scheduler.agent.settings")
    async def test_happy_path(self, mock_settings):
        mock_settings.agent_url = "http://agent:8000"

        submitted_task = make_a2a_task(status_state=TaskState.submitted)
        working_task = make_a2a_task(status_state=TaskState.working)
        completed_task = make_a2a_task(
            artifacts=[
                data_artifact(
                    {
                        "evidence": "found it",
                        "sources": ["https://example.com"],
                        "confidence": 95,
                        "next_run": "2026-02-08T12:00:00Z",
                        "notification": None,
                        "topic": None,
                    }
                )
            ]
        )

        mock_client = AsyncMock()
        mock_client.send_message = AsyncMock(return_value=send_success(submitted_task))
        mock_client.get_task = AsyncMock(
            side_effect=[poll_success(working_task), poll_success(completed_task)]
        )

        with patch("torale.scheduler.agent.A2AClient", return_value=mock_client):
            with patch("torale.scheduler.agent.asyncio.sleep", new_callable=AsyncMock):
                result = await call_agent("test prompt")

        assert isinstance(result, MonitoringResponse)
        assert result.evidence == "found it"
        assert result.sources == ["https://example.com"]
        assert result.confidence == 95

    @pytest.mark.asyncio
    @patch("torale.scheduler.agent.settings")
    async def test_agent_failed_state_raises(self, mock_settings):
        mock_settings.agent_url = "http://agent:8000"

        submitted_task = make_a2a_task(status_state=TaskState.submitted)
        failed_task = make_a2a_task(status_state=TaskState.failed)

        mock_client = AsyncMock()
        mock_client.send_message = AsyncMock(return_value=send_success(submitted_task))
        mock_client.get_task = AsyncMock(return_value=poll_success(failed_task))

        with patch("torale.scheduler.agent.A2AClient", return_value=mock_client):
            with patch("torale.scheduler.agent.asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(
                    RuntimeError, match="Agent task task-abc failed without error details"
                ):
                    await call_agent("test prompt")

    @pytest.mark.asyncio
    @patch("torale.scheduler.agent.settings")
    async def test_timeout_raises(self, mock_settings):
        mock_settings.agent_url = "http://agent:8000"

        submitted_task = make_a2a_task(status_state=TaskState.submitted)
        working_task = make_a2a_task(status_state=TaskState.working)

        mock_client = AsyncMock()
        mock_client.send_message = AsyncMock(return_value=send_success(submitted_task))
        mock_client.get_task = AsyncMock(return_value=poll_success(working_task))

        # Simulate time passing beyond deadline
        times = iter([0, 0, 999])

        with patch("torale.scheduler.agent.A2AClient", return_value=mock_client):
            with patch("torale.scheduler.agent.asyncio.sleep", new_callable=AsyncMock):
                with patch("torale.scheduler.agent.time.monotonic", side_effect=times):
                    with pytest.raises(TimeoutError, match="did not complete"):
                        await call_agent("test prompt")

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "exception",
        [
            A2AClientHTTPError(503, "Service Unavailable"),
            ConnectionError("Connection refused"),
        ],
        ids=["http_error", "connection_error"],
    )
    @patch("torale.scheduler.agent.settings")
    async def test_send_error_raises_runtime(self, mock_settings, exception):
        mock_settings.agent_url = "http://agent:8000"

        mock_client = AsyncMock()
        mock_client.send_message = AsyncMock(side_effect=exception)

        with patch("torale.scheduler.agent.A2AClient", return_value=mock_client):
            with pytest.raises(RuntimeError, match="Failed to send task to agent"):
                await call_agent("test prompt")

    @pytest.mark.asyncio
    @patch("torale.scheduler.agent.settings")
    async def test_transient_poll_failure_then_recovery(self, mock_settings):
        mock_settings.agent_url = "http://agent:8000"

        submitted_task = make_a2a_task(status_state=TaskState.submitted)
        completed_task = make_a2a_task(
            artifacts=[
                data_artifact(
                    {
                        "evidence": "all good",
                        "sources": [],
                        "confidence": 100,
                        "next_run": None,
                        "notification": None,
                        "topic": None,
                    }
                )
            ]
        )

        mock_client = AsyncMock()
        mock_client.send_message = AsyncMock(return_value=send_success(submitted_task))
        mock_client.get_task = AsyncMock(
            side_effect=[
                A2AClientHTTPError(503, "Service Unavailable"),
                poll_success(completed_task),
            ]
        )

        with patch("torale.scheduler.agent.A2AClient", return_value=mock_client):
            with patch("torale.scheduler.agent.asyncio.sleep", new_callable=AsyncMock):
                result = await call_agent("test prompt")

        assert isinstance(result, MonitoringResponse)
        assert result.confidence == 100

    @pytest.mark.asyncio
    @patch("torale.scheduler.agent.settings")
    async def test_consecutive_poll_failures_raises(self, mock_settings):
        mock_settings.agent_url = "http://agent:8000"

        submitted_task = make_a2a_task(status_state=TaskState.submitted)

        mock_client = AsyncMock()
        mock_client.send_message = AsyncMock(return_value=send_success(submitted_task))
        mock_client.get_task = AsyncMock(
            side_effect=[
                A2AClientHTTPError(503, "err"),
                A2AClientHTTPError(503, "err"),
                A2AClientHTTPError(503, "err"),
            ]
        )

        with patch("torale.scheduler.agent.A2AClient", return_value=mock_client):
            with patch("torale.scheduler.agent.asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(RuntimeError, match="poll failed 3 consecutive"):
                    await call_agent("test prompt")

    @pytest.mark.asyncio
    @patch("torale.scheduler.agent.settings")
    async def test_send_jsonrpc_error_raises(self, mock_settings):
        mock_settings.agent_url = "http://agent:8000"

        error_response = SendMessageResponse(
            root=JSONRPCErrorResponse(
                id="req-1",
                error=JSONRPCError(code=-32600, message="Invalid request"),
            )
        )

        mock_client = AsyncMock()
        mock_client.send_message = AsyncMock(return_value=error_response)

        with patch("torale.scheduler.agent.A2AClient", return_value=mock_client):
            with pytest.raises(RuntimeError, match="Agent returned error"):
                await call_agent("test prompt")
