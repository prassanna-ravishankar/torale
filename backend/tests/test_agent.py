"""Tests for the A2A agent client (call_agent + _parse_agent_response)."""

from unittest.mock import AsyncMock, patch

import pytest
from a2a.client.errors import A2AClientHTTPError
from a2a.types import (
    Artifact,
    DataPart,
    GetTaskResponse,
    GetTaskSuccessResponse,
    JSONRPCError,
    JSONRPCErrorResponse,
    Part,
    SendMessageResponse,
    SendMessageSuccessResponse,
    Task,
    TaskState,
    TaskStatus,
    TextPart,
)
from pydantic import ValidationError

from torale.scheduler.agent import _parse_agent_response, call_agent
from torale.scheduler.models import MonitoringResponse


def _make_task(*, artifacts=None, status_state=TaskState.completed, task_id="task-abc"):
    """Helper to build Task objects for tests."""
    return Task(
        id=task_id,
        context_id="ctx-test",
        status=TaskStatus(state=status_state),
        artifacts=artifacts,
    )


def _text_artifact(text):
    """Helper to create an artifact with a single TextPart."""
    return Artifact(
        artifact_id="art-1",
        parts=[Part(root=TextPart(kind="text", text=text))],
    )


def _data_artifact(data):
    """Helper to create an artifact with a single DataPart."""
    return Artifact(
        artifact_id="art-1",
        parts=[Part(root=DataPart(kind="data", data=data))],
    )


def _send_success(task):
    """Wrap a Task in a SendMessageResponse success."""
    return SendMessageResponse(root=SendMessageSuccessResponse(id="req-1", result=task))


def _poll_success(task):
    """Wrap a Task in a GetTaskResponse success."""
    return GetTaskResponse(root=GetTaskSuccessResponse(id="req-1", result=task))


class TestParseAgentResponse:
    """Tests for _parse_agent_response (pure function, no mocking).

    _parse_agent_response now takes a Task object directly.
    """

    def test_single_artifact_valid_json(self):
        task = _make_task(
            artifacts=[_text_artifact('{"condition_met": true, "evidence": "found"}')]
        )
        parsed = _parse_agent_response(task)
        assert parsed == {"condition_met": True, "evidence": "found"}

    def test_data_part_structured_response(self):
        """DataPart with structured data is parsed directly."""
        task = _make_task(
            artifacts=[
                _data_artifact(
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
        task = _make_task(
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
        task = _make_task(artifacts=artifacts)
        with pytest.raises(RuntimeError, match="empty response"):
            _parse_agent_response(task)

    def test_invalid_json_raises(self):
        """Legacy text response that isn't valid JSON raises error."""
        task = _make_task(artifacts=[_text_artifact("not json at all")])
        with pytest.raises(RuntimeError, match="non-JSON text response"):
            _parse_agent_response(task)

    def test_non_text_parts_skipped(self):
        from a2a.types import FilePart, FileWithBytes

        task = _make_task(
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

        task = _make_task(
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
        task = _make_task(
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
        task = _make_task(
            artifacts=[
                _text_artifact(
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
        task = _make_task(artifacts=[_text_artifact("{'unclosed': 'dict'")])
        with pytest.raises(RuntimeError, match="non-JSON text response"):
            _parse_agent_response(task)

    def test_empty_data_part_falls_through_to_text(self):
        """DataPart with empty data dict falls through to TextPart parsing."""
        task = _make_task(
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
        task = _make_task(
            artifacts=[
                _data_artifact(
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
        task = _make_task(artifacts=[_data_artifact(invalid_data)])
        parsed = _parse_agent_response(task)
        with pytest.raises(ValidationError, match=expected_error_field):
            MonitoringResponse.model_validate(parsed)


class TestCallAgent:
    """Tests for call_agent (mock a2a.client.A2AClient)."""

    @pytest.mark.asyncio
    @patch("torale.scheduler.agent.settings")
    async def test_happy_path(self, mock_settings):
        mock_settings.agent_url = "http://agent:8000"

        submitted_task = _make_task(status_state=TaskState.submitted)
        working_task = _make_task(status_state=TaskState.working)
        completed_task = _make_task(
            artifacts=[
                _data_artifact(
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
        mock_client.send_message = AsyncMock(return_value=_send_success(submitted_task))
        mock_client.get_task = AsyncMock(
            side_effect=[_poll_success(working_task), _poll_success(completed_task)]
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

        submitted_task = _make_task(status_state=TaskState.submitted)
        failed_task = _make_task(status_state=TaskState.failed)

        mock_client = AsyncMock()
        mock_client.send_message = AsyncMock(return_value=_send_success(submitted_task))
        mock_client.get_task = AsyncMock(return_value=_poll_success(failed_task))

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

        submitted_task = _make_task(status_state=TaskState.submitted)
        working_task = _make_task(status_state=TaskState.working)

        mock_client = AsyncMock()
        mock_client.send_message = AsyncMock(return_value=_send_success(submitted_task))
        mock_client.get_task = AsyncMock(return_value=_poll_success(working_task))

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

        submitted_task = _make_task(status_state=TaskState.submitted)
        completed_task = _make_task(
            artifacts=[
                _data_artifact(
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
        mock_client.send_message = AsyncMock(return_value=_send_success(submitted_task))
        mock_client.get_task = AsyncMock(
            side_effect=[
                A2AClientHTTPError(503, "Service Unavailable"),
                _poll_success(completed_task),
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

        submitted_task = _make_task(status_state=TaskState.submitted)

        mock_client = AsyncMock()
        mock_client.send_message = AsyncMock(return_value=_send_success(submitted_task))
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
