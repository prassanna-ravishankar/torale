"""Validation and storage projection for task notification configuration."""

import secrets
from dataclasses import dataclass
from typing import Any

from webwhen.notifications import NotificationValidationError, validate_notification


class TaskNotificationError(ValueError):
    """Raised when a task's notification configuration is invalid."""


@dataclass(frozen=True)
class NotificationStorage:
    notification_channels: list[str]
    notification_email: str | None
    webhook_url: str | None
    webhook_secret: str | None


async def prepare_notifications(
    notifications: list[Any], old_webhook_url: str | None = None
) -> tuple[list[dict[str, Any]], NotificationStorage]:
    """Validate API notification values and project their database columns."""
    validated: list[dict[str, Any]] = []
    for notification in notifications:
        value = notification.model_dump() if hasattr(notification, "model_dump") else notification
        try:
            validated.append(await validate_notification(value))
        except NotificationValidationError as exc:
            raise TaskNotificationError(f"Invalid notification: {exc}") from exc

    types = [notification.get("type") for notification in validated]
    if len(types) != len(set(types)):
        raise TaskNotificationError(
            "Multiple notifications of the same type are not supported. "
            "Please provide at most one email and one webhook notification."
        )

    channels: list[str] = []
    email = None
    webhook_url = None
    webhook_secret = None
    for notification in validated:
        if notification.get("type") == "email":
            channels.append("email")
            email = notification.get("address")
        elif notification.get("type") == "webhook":
            channels.append("webhook")
            webhook_url = notification.get("url")
            if old_webhook_url is None or old_webhook_url != webhook_url:
                webhook_secret = secrets.token_urlsafe(32)

    return validated, NotificationStorage(
        notification_channels=channels or ["email"],
        notification_email=email,
        webhook_url=webhook_url,
        webhook_secret=webhook_secret,
    )
