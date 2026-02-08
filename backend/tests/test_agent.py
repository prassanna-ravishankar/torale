"""Tests for the A2A agent client (call_agent + _parse_agent_response)."""

from unittest.mock import AsyncMock, patch

import pytest
from fasta2a.client import UnexpectedResponseError
from pydantic import ValidationError

from torale.scheduler.agent import _parse_agent_response, call_agent
from torale.scheduler.models import MonitoringResponse


class TestParseAgentResponse:
    """Tests for _parse_agent_response (pure function, no mocking).

    _parse_agent_response now takes a Task dict directly (no JSON-RPC wrapper).
    """

    def test_single_artifact_valid_json(self):
        task = {
            "artifacts": [
                {
                    "parts": [
                        {"kind": "text", "text": '{"condition_met": true, "evidence": "found"}'}
                    ]
                }
            ]
        }
        parsed = _parse_agent_response(task)
        assert parsed == {"condition_met": True, "evidence": "found"}

    def test_data_part_structured_response(self):
        """DataPart with structured data is parsed directly."""
        task = {
            "artifacts": [
                {
                    "parts": [
                        {
                            "kind": "data",
                            "data": {
                                "evidence": "found it",
                                "sources": ["https://example.com"],
                                "confidence": 95,
                            },
                        }
                    ]
                }
            ]
        }
        parsed = _parse_agent_response(task)
        assert parsed == {
            "evidence": "found it",
            "sources": ["https://example.com"],
            "confidence": 95,
        }

    def test_multiple_text_parts_concatenated(self):
        """Legacy text parts are concatenated and parsed as JSON."""
        task = {
            "artifacts": [
                {
                    "parts": [
                        {"kind": "text", "text": '{"key": '},
                        {"kind": "text", "text": '"value"}'},
                    ]
                }
            ]
        }
        parsed = _parse_agent_response(task)
        assert parsed == {"key": "value"}

    @pytest.mark.parametrize(
        "task",
        [
            {"artifacts": [], "id": "task-123"},
            {"id": "task-123", "status": "completed"},
        ],
        ids=["empty_artifacts_list", "missing_artifacts_key"],
    )
    def test_no_artifacts_raises(self, task):
        with pytest.raises(RuntimeError, match="empty response"):
            _parse_agent_response(task)

    def test_invalid_json_raises(self):
        """Legacy text response that isn't valid JSON raises error."""
        task = {"artifacts": [{"parts": [{"kind": "text", "text": "not json at all"}]}]}
        with pytest.raises(RuntimeError, match="non-JSON text response"):
            _parse_agent_response(task)

    def test_non_text_parts_skipped(self):
        task = {
            "artifacts": [
                {
                    "parts": [
                        {"kind": "image", "data": "binary"},
                        {"kind": "text", "text": '{"status": "ok"}'},
                    ]
                }
            ]
        }
        parsed = _parse_agent_response(task)
        assert parsed == {"status": "ok"}

    def test_error_message_includes_artifact_count_and_keys(self):
        task = {
            "artifacts": [{"parts": [{"kind": "image", "data": "binary"}]}],
            "id": "task-123",
            "status": {"state": "completed"},
        }
        with pytest.raises(RuntimeError, match=r"artifacts=1.*task_keys="):
            _parse_agent_response(task)

    def test_data_part_takes_precedence_over_text_part(self):
        """When both DataPart and TextPart exist, DataPart is preferred."""
        task = {
            "artifacts": [
                {
                    "parts": [
                        {
                            "kind": "data",
                            "data": {
                                "evidence": "from data",
                                "sources": ["https://data.com"],
                                "confidence": 90,
                            },
                        },
                        {
                            "kind": "text",
                            "text": '{"evidence": "from text", "sources": ["https://text.com"], "confidence": 50}',
                        },
                    ]
                }
            ]
        }
        parsed = _parse_agent_response(task)
        assert parsed["evidence"] == "from data"
        assert parsed["confidence"] == 90

    def test_python_dict_repr_parsed_via_literal_eval(self):
        """Agent returning Python dict repr (single quotes) is parsed via ast.literal_eval."""
        task = {
            "artifacts": [
                {
                    "parts": [
                        {
                            "kind": "text",
                            "text": "{'evidence': 'found', 'sources': ['https://x.com'], 'confidence': 85}",
                        }
                    ]
                }
            ]
        }
        parsed = _parse_agent_response(task)
        assert parsed == {
            "evidence": "found",
            "sources": ["https://x.com"],
            "confidence": 85,
        }

    def test_malformed_python_literal_raises(self):
        """Malformed Python literal that isn't valid JSON or literal_eval raises."""
        task = {"artifacts": [{"parts": [{"kind": "text", "text": "{'unclosed': 'dict'"}]}]}
        with pytest.raises(RuntimeError, match="non-JSON text response"):
            _parse_agent_response(task)

    def test_empty_data_part_falls_through_to_text(self):
        """DataPart with empty data dict falls through to TextPart parsing."""
        task = {
            "artifacts": [
                {
                    "parts": [
                        {"kind": "data", "data": {}},
                        {
                            "kind": "text",
                            "text": '{"evidence": "from text", "sources": [], "confidence": 80}',
                        },
                    ]
                }
            ]
        }
        parsed = _parse_agent_response(task)
        assert parsed["evidence"] == "from text"

    def test_data_part_with_minimal_fields(self):
        """DataPart with only required fields passes validation."""
        task = {
            "artifacts": [
                {
                    "parts": [
                        {
                            "kind": "data",
                            "data": {
                                "evidence": "checked",
                                "sources": [],
                                "confidence": 50,
                                # notification, next_run, topic omitted (optional)
                            },
                        }
                    ]
                }
            ]
        }
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
        task = {"artifacts": [{"parts": [{"kind": "data", "data": invalid_data}]}]}
        parsed = _parse_agent_response(task)
        with pytest.raises(ValidationError, match=expected_error_field):
            MonitoringResponse.model_validate(parsed)


class TestCallAgent:
    """Tests for call_agent (mock fasta2a.client.A2AClient)."""

    @pytest.mark.asyncio
    @patch("torale.scheduler.agent.settings")
    async def test_happy_path(self, mock_settings):
        mock_settings.agent_url = "http://agent:8000"

        send_result = {"result": {"id": "task-abc", "status": {"state": "submitted"}}}
        poll_working = {"result": {"id": "task-abc", "status": {"state": "working"}}}
        poll_completed = {
            "result": {
                "id": "task-abc",
                "status": {"state": "completed"},
                "artifacts": [
                    {
                        "parts": [
                            {
                                "kind": "data",
                                "data": {
                                    "evidence": "found it",
                                    "sources": ["https://example.com"],
                                    "confidence": 95,
                                    "next_run": "2026-02-08T12:00:00Z",
                                    "notification": None,
                                    "topic": None,
                                },
                            }
                        ]
                    }
                ],
            }
        }

        mock_client = AsyncMock()
        mock_client.send_message = AsyncMock(return_value=send_result)
        mock_client.get_task = AsyncMock(side_effect=[poll_working, poll_completed])

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

        send_result = {"result": {"id": "task-abc", "status": {"state": "submitted"}}}
        poll_failed = {"result": {"id": "task-abc", "status": {"state": "failed"}}}

        mock_client = AsyncMock()
        mock_client.send_message = AsyncMock(return_value=send_result)
        mock_client.get_task = AsyncMock(return_value=poll_failed)

        with patch("torale.scheduler.agent.A2AClient", return_value=mock_client):
            with patch("torale.scheduler.agent.asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(RuntimeError, match="Agent task failed"):
                    await call_agent("test prompt")

    @pytest.mark.asyncio
    @patch("torale.scheduler.agent.settings")
    async def test_timeout_raises(self, mock_settings):
        mock_settings.agent_url = "http://agent:8000"

        send_result = {"result": {"id": "task-abc", "status": {"state": "submitted"}}}
        poll_working = {"result": {"id": "task-abc", "status": {"state": "working"}}}

        mock_client = AsyncMock()
        mock_client.send_message = AsyncMock(return_value=send_result)
        mock_client.get_task = AsyncMock(return_value=poll_working)

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
            UnexpectedResponseError(503, "Service Unavailable"),
            ConnectionError("Connection refused"),
        ],
        ids=["unexpected_response_error", "connection_error"],
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

        send_result = {"result": {"id": "task-abc", "status": {"state": "submitted"}}}
        poll_completed = {
            "result": {
                "id": "task-abc",
                "status": {"state": "completed"},
                "artifacts": [
                    {
                        "parts": [
                            {
                                "kind": "data",
                                "data": {
                                    "evidence": "all good",
                                    "sources": [],
                                    "confidence": 100,
                                    "next_run": None,
                                    "notification": None,
                                    "topic": None,
                                },
                            }
                        ]
                    }
                ],
            }
        }

        mock_client = AsyncMock()
        mock_client.send_message = AsyncMock(return_value=send_result)
        mock_client.get_task = AsyncMock(
            side_effect=[
                UnexpectedResponseError(503, "Service Unavailable"),
                poll_completed,
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

        send_result = {"result": {"id": "task-abc", "status": {"state": "submitted"}}}

        mock_client = AsyncMock()
        mock_client.send_message = AsyncMock(return_value=send_result)
        mock_client.get_task = AsyncMock(
            side_effect=[
                UnexpectedResponseError(503, "err"),
                UnexpectedResponseError(503, "err"),
                UnexpectedResponseError(503, "err"),
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

        send_result = {"error": {"code": -32600, "message": "Invalid request"}}

        mock_client = AsyncMock()
        mock_client.send_message = AsyncMock(return_value=send_result)

        with patch("torale.scheduler.agent.A2AClient", return_value=mock_client):
            with pytest.raises(RuntimeError, match="Agent returned error"):
                await call_agent("test prompt")
