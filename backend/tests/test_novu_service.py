"""Tests for Novu notification helpers."""

from unittest.mock import AsyncMock

import pytest

from webwhen.core.config import settings
from webwhen.notifications.novu_service import (
    NotificationPayload,
    NovuService,
    _build_task_url,
    _format_confidence,
)


class TestFormatConfidence:
    """Confidence arrives as int 0-100 (MonitoringResponse schema).

    Regression: a prior version multiplied by 100, producing "9500%"/"10000%"
    in notification emails.
    """

    @pytest.mark.parametrize(
        "value,expected",
        [
            (None, None),
            (0, "0%"),
            (50, "50%"),
            (95, "95%"),
            (100, "100%"),
        ],
    )
    def test_format(self, value, expected):
        assert _format_confidence(value) == expected


class TestTaskUrl:
    def test_builds_canonical_frontend_task_url(self, monkeypatch):
        monkeypatch.setattr(settings, "frontend_url", "https://webwhen.ai/")

        assert (
            _build_task_url("76243542-8019-44d3-b171-4fb334d6f822")
            == "https://webwhen.ai/dashboard/tasks/76243542-8019-44d3-b171-4fb334d6f822"
        )

    def test_url_encodes_task_id(self, monkeypatch):
        monkeypatch.setattr(settings, "frontend_url", "https://webwhen.ai")

        assert _build_task_url("task/../id") == "https://webwhen.ai/dashboard/tasks/task%2F..%2Fid"

    @pytest.mark.asyncio
    async def test_condition_met_payload_includes_task_url(self, monkeypatch):
        monkeypatch.setattr(settings, "frontend_url", "https://webwhen.ai")
        service = NovuService()
        service._trigger = AsyncMock()

        await service.send_condition_met_notification(
            payload=NotificationPayload(
                subscriber_id="user@example.com",
                task_name="iPhone release",
                search_query="iPhone release date",
                answer="Apple announced the release date.",
                grounding_sources=[],
                task_id="76243542-8019-44d3-b171-4fb334d6f822",
            ),
            execution_id="exec-123",
            confidence=95,
        )

        sent_payload = service._trigger.call_args.kwargs["payload"]
        assert sent_payload["task_id"] == "76243542-8019-44d3-b171-4fb334d6f822"
        assert (
            sent_payload["task_url"]
            == "https://webwhen.ai/dashboard/tasks/76243542-8019-44d3-b171-4fb334d6f822"
        )
