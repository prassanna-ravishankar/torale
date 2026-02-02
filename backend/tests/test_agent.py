"""Tests for the A2A agent client (call_agent + _parse_agent_response)."""

from unittest.mock import AsyncMock, patch

import pytest
from fasta2a.client import UnexpectedResponseError

from torale.scheduler.agent import _parse_agent_response, call_agent


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

    def test_multiple_text_parts_concatenated(self):
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

    def test_no_artifacts_raises(self):
        task = {"artifacts": [], "id": "task-123"}
        with pytest.raises(RuntimeError, match="empty text content"):
            _parse_agent_response(task)

    def test_no_artifacts_key_raises(self):
        task = {"id": "task-123", "status": "completed"}
        with pytest.raises(RuntimeError, match="empty text content"):
            _parse_agent_response(task)

    def test_invalid_json_raises(self):
        task = {"artifacts": [{"parts": [{"kind": "text", "text": "not json at all"}]}]}
        with pytest.raises(RuntimeError, match="non-JSON response"):
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
                "artifacts": [{"parts": [{"kind": "text", "text": '{"evidence": "found it"}'}]}],
            }
        }

        mock_client = AsyncMock()
        mock_client.send_message = AsyncMock(return_value=send_result)
        mock_client.get_task = AsyncMock(side_effect=[poll_working, poll_completed])

        with patch("torale.scheduler.agent.A2AClient", return_value=mock_client):
            with patch("torale.scheduler.agent.asyncio.sleep", new_callable=AsyncMock):
                result = await call_agent("test prompt")

        assert result == {"evidence": "found it"}

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
    @patch("torale.scheduler.agent.settings")
    async def test_send_error_raises_runtime(self, mock_settings):
        mock_settings.agent_url = "http://agent:8000"

        mock_client = AsyncMock()
        mock_client.send_message = AsyncMock(
            side_effect=UnexpectedResponseError(503, "Service Unavailable")
        )

        with patch("torale.scheduler.agent.A2AClient", return_value=mock_client):
            with pytest.raises(RuntimeError, match="Failed to send task to agent"):
                await call_agent("test prompt")

    @pytest.mark.asyncio
    @patch("torale.scheduler.agent.settings")
    async def test_send_generic_error_raises_runtime(self, mock_settings):
        mock_settings.agent_url = "http://agent:8000"

        mock_client = AsyncMock()
        mock_client.send_message = AsyncMock(side_effect=ConnectionError("Connection refused"))

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
                "artifacts": [{"parts": [{"kind": "text", "text": '{"ok": true}'}]}],
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

        assert result == {"ok": True}

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
