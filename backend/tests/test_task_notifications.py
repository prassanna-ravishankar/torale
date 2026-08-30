from unittest.mock import AsyncMock, patch

import pytest

from webwhen.tasks.notifications import TaskNotificationError, prepare_notifications


@pytest.mark.asyncio
async def test_prepare_notifications_projects_email_and_webhook_storage():
    async def validate(value):
        return value

    with patch("webwhen.tasks.notifications.validate_notification", side_effect=validate):
        validated, storage = await prepare_notifications(
            [
                {"type": "email", "address": "person@example.com"},
                {"type": "webhook", "url": "https://example.com/hook"},
            ]
        )

    assert len(validated) == 2
    assert storage.notification_channels == ["email", "webhook"]
    assert storage.notification_email == "person@example.com"
    assert storage.webhook_url == "https://example.com/hook"
    assert storage.webhook_secret


@pytest.mark.asyncio
async def test_prepare_notifications_preserves_secret_when_webhook_url_is_unchanged():
    notification = {"type": "webhook", "url": "https://example.com/hook"}
    with patch(
        "webwhen.tasks.notifications.validate_notification", AsyncMock(return_value=notification)
    ):
        _, storage = await prepare_notifications(
            [notification], old_webhook_url="https://example.com/hook"
        )

    assert storage.webhook_secret is None


@pytest.mark.asyncio
async def test_prepare_notifications_rejects_duplicate_channels():
    notifications = [
        {"type": "email", "address": "one@example.com"},
        {"type": "email", "address": "two@example.com"},
    ]
    with patch(
        "webwhen.tasks.notifications.validate_notification", AsyncMock(side_effect=notifications)
    ):
        with pytest.raises(TaskNotificationError, match="same type"):
            await prepare_notifications(notifications)
