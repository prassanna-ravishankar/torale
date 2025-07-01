import logging
from typing import Any, Dict

from notificationapi_python_server_sdk import notificationapi
from config import settings

logger = logging.getLogger(__name__)


class NotificationApiHttpClient:
    """A client for interacting with the NotificationAPI service."""

    def __init__(self):
        """Initializes the NotificationAPI client."""
        if not settings.NOTIFICATIONAPI_CLIENT_ID or not settings.NOTIFICATIONAPI_CLIENT_SECRET:
            raise ValueError("NOTIFICATIONAPI_CLIENT_ID and NOTIFICATIONAPI_CLIENT_SECRET must be set.")
        
        notificationapi.init(
            settings.NOTIFICATIONAPI_CLIENT_ID,
            settings.NOTIFICATIONAPI_CLIENT_SECRET,
            'https://api.eu.notificationapi.com'  # EU endpoint
        )
        logger.info("NotificationAPI client initialized with EU endpoint.")

    async def send_notification(self, user_email: str, notification_type: str, parameters: Dict[str, Any]) -> bool:
        """
        Sends a notification via NotificationAPI.

        Args:
            user_email: The email address of the user to notify.
            notification_type: The type of notification template in NotificationAPI.
            parameters: A dictionary of parameters to personalize the notification.

        Returns:
            True if the notification was sent successfully, False otherwise.
        """
        try:
            response = await notificationapi.send({
                "type": notification_type,
                "to": {
                    "email": user_email
                },
                "parameters": parameters
            })
            logger.info(f"Successfully sent notification '{notification_type}' to user '{user_email}'.")
            return True
        except Exception as e:
            logger.error(f"Failed to send notification '{notification_type}' to user '{user_email}': {e}", exc_info=True)
            return False

    async def identify_user(self, user_id: str, user_data: Dict[str, Any]):
        """
        Identifies a user to NotificationAPI, creating or updating them.

        Args:
            user_id: The unique identifier for the user.
            user_data: A dictionary containing user properties (e.g., email, number).
        """
        try:
            notificationapi.user.identify(
                user_id=user_id,
                data=user_data
            )
            logger.info(f"Identified user '{user_id}' to NotificationAPI.")
        except Exception as e:
            logger.error(f"Failed to identify user '{user_id}' to NotificationAPI: {e}", exc_info=True) 