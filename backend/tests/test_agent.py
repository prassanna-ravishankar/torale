"""Tests for the A2A agent client (call_agent + _parse_agent_response)."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from torale.scheduler.agent import _parse_agent_response, call_agent


class TestParseAgentResponse:
    """Tests for _parse_agent_response (pure function, no mocking)."""

    def test_single_artifact_valid_json(self):
        poll_result = {
            "result": {
                "artifacts": [
                    {
                        "parts": [
                            {"kind": "text", "text": '{"condition_met": true, "evidence": "found"}'}
                        ]
                    }
                ]
            }
        }
        parsed = _parse_agent_response(poll_result)
        assert parsed == {"condition_met": True, "evidence": "found"}

    def test_multiple_text_parts_concatenated(self):
        poll_result = {
            "result": {
                "artifacts": [
                    {
                        "parts": [
                            {"kind": "text", "text": '{"key": '},
                            {"kind": "text", "text": '"value"}'},
                        ]
                    }
                ]
            }
        }
        parsed = _parse_agent_response(poll_result)
        assert parsed == {"key": "value"}

    def test_no_artifacts_raises(self):
        poll_result = {"result": {"artifacts": [], "id": "task-123"}}
        with pytest.raises(RuntimeError, match="empty text content"):
            _parse_agent_response(poll_result)

    def test_no_artifacts_key_raises(self):
        poll_result = {"result": {"id": "task-123", "status": "completed"}}
        with pytest.raises(RuntimeError, match="empty text content"):
            _parse_agent_response(poll_result)

    def test_invalid_json_raises(self):
        poll_result = {
            "result": {"artifacts": [{"parts": [{"kind": "text", "text": "not json at all"}]}]}
        }
        with pytest.raises(RuntimeError, match="non-JSON response"):
            _parse_agent_response(poll_result)

    def test_non_text_parts_skipped(self):
        poll_result = {
            "result": {
                "artifacts": [
                    {
                        "parts": [
                            {"kind": "image", "data": "binary"},
                            {"kind": "text", "text": '{"status": "ok"}'},
                        ]
                    }
                ]
            }
        }
        parsed = _parse_agent_response(poll_result)
        assert parsed == {"status": "ok"}

    def test_error_message_includes_artifact_count_and_keys(self):
        poll_result = {
            "result": {
                "artifacts": [{"parts": [{"kind": "image", "data": "binary"}]}],
                "id": "task-123",
                "status": {"state": "completed"},
            }
        }
        with pytest.raises(RuntimeError, match=r"artifacts=1.*result_keys="):
            _parse_agent_response(poll_result)


class TestCallAgent:
    """Tests for call_agent (mock httpx)."""

    @pytest.mark.asyncio
    @patch("torale.scheduler.agent.settings")
    async def test_happy_path(self, mock_settings):
        mock_settings.agent_url = "http://agent:8000"

        send_response = MagicMock()
        send_response.json.return_value = {"result": {"id": "task-abc"}}
        send_response.raise_for_status = MagicMock()

        poll_working = MagicMock()
        poll_working.json.return_value = {"result": {"status": {"state": "working"}}}
        poll_working.raise_for_status = MagicMock()

        poll_completed = MagicMock()
        poll_completed.json.return_value = {
            "result": {
                "status": {"state": "completed"},
                "artifacts": [{"parts": [{"kind": "text", "text": '{"evidence": "found it"}'}]}],
            }
        }
        poll_completed.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=[send_response, poll_working, poll_completed])
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("torale.scheduler.agent.httpx.AsyncClient", return_value=mock_client):
            with patch("torale.scheduler.agent.asyncio.sleep", new_callable=AsyncMock):
                result = await call_agent("test prompt")

        assert result == {"evidence": "found it"}

    @pytest.mark.asyncio
    @patch("torale.scheduler.agent.settings")
    async def test_agent_failed_state_raises(self, mock_settings):
        mock_settings.agent_url = "http://agent:8000"

        send_response = MagicMock()
        send_response.json.return_value = {"result": {"id": "task-abc"}}
        send_response.raise_for_status = MagicMock()

        poll_failed = MagicMock()
        poll_failed.json.return_value = {
            "result": {"status": {"state": "failed"}, "error": "agent crashed"}
        }
        poll_failed.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=[send_response, poll_failed])
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("torale.scheduler.agent.httpx.AsyncClient", return_value=mock_client):
            with patch("torale.scheduler.agent.asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(RuntimeError, match="Agent task failed"):
                    await call_agent("test prompt")

    @pytest.mark.asyncio
    @patch("torale.scheduler.agent.settings")
    async def test_timeout_raises(self, mock_settings):
        mock_settings.agent_url = "http://agent:8000"

        send_response = MagicMock()
        send_response.json.return_value = {"result": {"id": "task-abc"}}
        send_response.raise_for_status = MagicMock()

        poll_working = MagicMock()
        poll_working.json.return_value = {"result": {"status": {"state": "working"}}}
        poll_working.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=[send_response, poll_working])
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        # Simulate time passing beyond deadline
        times = iter([0, 0, 999])  # first call sets deadline, second enters loop, third exits

        with patch("torale.scheduler.agent.httpx.AsyncClient", return_value=mock_client):
            with patch("torale.scheduler.agent.asyncio.sleep", new_callable=AsyncMock):
                with patch("torale.scheduler.agent.time.monotonic", side_effect=times):
                    with pytest.raises(TimeoutError, match="did not complete"):
                        await call_agent("test prompt")

    @pytest.mark.asyncio
    @patch("torale.scheduler.agent.settings")
    async def test_missing_task_id_raises(self, mock_settings):
        mock_settings.agent_url = "http://agent:8000"

        send_response = MagicMock()
        send_response.json.return_value = {"result": {}}
        send_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=send_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("torale.scheduler.agent.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(RuntimeError, match="did not return task_id"):
                await call_agent("test prompt")

    @pytest.mark.asyncio
    @patch("torale.scheduler.agent.settings")
    async def test_transient_poll_failure_then_recovery(self, mock_settings):
        mock_settings.agent_url = "http://agent:8000"

        send_response = MagicMock()
        send_response.json.return_value = {"result": {"id": "task-abc"}}
        send_response.raise_for_status = MagicMock()

        poll_completed = MagicMock()
        poll_completed.json.return_value = {
            "result": {
                "status": {"state": "completed"},
                "artifacts": [{"parts": [{"kind": "text", "text": '{"ok": true}'}]}],
            }
        }
        poll_completed.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            side_effect=[
                send_response,
                httpx.HTTPError("503 Service Unavailable"),
                poll_completed,
            ]
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("torale.scheduler.agent.httpx.AsyncClient", return_value=mock_client):
            with patch("torale.scheduler.agent.asyncio.sleep", new_callable=AsyncMock):
                result = await call_agent("test prompt")

        assert result == {"ok": True}

    @pytest.mark.asyncio
    @patch("torale.scheduler.agent.settings")
    async def test_send_http_error_raises_runtime(self, mock_settings):
        mock_settings.agent_url = "http://agent:8000"

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.HTTPError("Connection refused"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("torale.scheduler.agent.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(RuntimeError, match="Failed to send task to agent"):
                await call_agent("test prompt")

    @pytest.mark.asyncio
    @patch("torale.scheduler.agent.settings")
    async def test_consecutive_poll_failures_raises(self, mock_settings):
        mock_settings.agent_url = "http://agent:8000"

        send_response = MagicMock()
        send_response.json.return_value = {"result": {"id": "task-abc"}}
        send_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            side_effect=[
                send_response,
                httpx.HTTPError("503"),
                httpx.HTTPError("503"),
                httpx.HTTPError("503"),
            ]
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("torale.scheduler.agent.httpx.AsyncClient", return_value=mock_client):
            with patch("torale.scheduler.agent.asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(RuntimeError, match="poll failed 3 consecutive"):
                    await call_agent("test prompt")
