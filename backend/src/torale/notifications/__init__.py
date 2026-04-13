"""
Notification system for Torale.

This module provides validation and sending of notifications when task conditions are met.
Full implementation will be added in a separate PR.
"""

from typing import Any

from pydantic import EmailStr, TypeAdapter
from pydantic import ValidationError as PydanticValidationError

from .email import EmailVerificationService
from .novu_service import novu_service
from .webhook import WebhookDeliveryService, WebhookPayload, WebhookSignature, build_webhook_payload

__all__ = [
    "NotificationValidationError",
    "NotificationSendError",
    "validate_notification",
    "send_notifications",
    "EmailVerificationService",
    "WebhookDeliveryService",
    "build_webhook_payload",
    "WebhookPayload",
    "WebhookSignature",
    "novu_service",
]


class NotificationValidationError(Exception):
    """Raised when notification configuration is invalid."""

    pass


class NotificationSendError(Exception):
    """Raised when notification fails to send."""

    pass


async def validate_notification(notification: dict[str, Any]) -> dict[str, Any]:
    """
    Validate notification configuration before saving to database.

    TODO (Notification PR): Implement full validation
    - For email: validate address format, check against user's connected/validated emails
    - For webhook: validate URL format, check against blocklist, ensure HTTPS

    Args:
        notification: Notification config dict with 'type' and type-specific fields

    Returns:
        Validated notification dict (may be modified/normalized)

    Raises:
        NotificationValidationError: If notification config is invalid

    Example:
        >>> await validate_notification({"type": "email", "address": "user@example.com"})
        {'type': 'email', 'address': 'user@example.com'}
    """
    notif_type = notification.get("type")

    if notif_type == "email":
        address = notification.get("address")
        if not address:
            raise NotificationValidationError("Email address required")

        # Validate email format using Pydantic's public API
        try:
            TypeAdapter(EmailStr).validate_python(address)
        except PydanticValidationError as e:
            raise NotificationValidationError(f"Invalid email format: {str(e)}") from e

    elif notif_type == "webhook":
        url = notification.get("url")
        if not url:
            raise NotificationValidationError("Webhook URL required")

        # Require HTTPS for security
        if not url.startswith("https://"):
            raise NotificationValidationError("Webhook URL must use HTTPS")

    else:
        raise NotificationValidationError(f"Unknown notification type: {notif_type}")

    return notification


async def send_notifications(
    notifications: list[dict[str, Any]], event_data: dict[str, Any]
) -> list[dict[str, Any]]:
    """
    Send notifications when task condition is met.

    TODO (Notification PR): Implement actual notification sending
    - Send emails via email provider (SendGrid, SES, etc.)
    - Call webhooks with retry logic and exponential backoff
    - Track delivery status and failures
    - Store notification logs

    Args:
        notifications: List of notification configs from task
        event_data: Event data to include in notifications

    Returns:
        List of results for each notification
    """
    results = []

    for notification in notifications:
        notif_type = notification["type"]

        if notif_type == "email":
            results.append(
                {
                    "success": True,
                    "type": "email",
                    "address": notification["address"],
                    "message": "MOCK: Email would be sent here",
                    "event_data": event_data,
                }
            )

        elif notif_type == "webhook":
            results.append(
                {
                    "success": True,
                    "type": "webhook",
                    "url": notification["url"],
                    "message": "MOCK: Webhook would be called here",
                    "event_data": event_data,
                }
            )

    return results
