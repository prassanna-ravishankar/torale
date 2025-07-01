import logging
from typing import Any, Dict, Optional

from clients.notificationapi_client import NotificationApiHttpClient

logger = logging.getLogger(__name__)

class NotificationApiService:
    """Service for handling notifications via NotificationAPI."""

    def __init__(self, notificationapi_client: NotificationApiHttpClient):
        """Initialize the service with the NotificationAPI client."""
        self.notificationapi = notificationapi_client

    async def send_change_alert(
        self,
        user_id: str,
        user_email: str,
        query: str,
        target_url: str,
        content: str,
        alert_id: str
    ) -> bool:
        """
        Sends a change alert notification using NotificationAPI.
        
        The calling service is responsible for updating the alert's status after
        this action is complete.
        """
        # Send the notification using the new API format
        success = await self.notificationapi.send_notification(
            user_email=user_email,
            notification_type='torale_alert',  # Match your example type
            parameters={
                "query": query,
                "target_url": target_url,
                "content": content,
                "alert_id": alert_id,
                "dashboardLink": "https://app.torale.com/dashboard"
            }
        )
        
        if success:
            logger.info(f"Successfully triggered 'change-alert' for user {user_id} and alert {alert_id}")
        else:
            logger.error(f"Failed to trigger 'change-alert' for user {user_id} and alert {alert_id}")
            
        return success

    async def update_notification_preferences(
        self,
        user_id: str,
        # TODO: These will need to map to NotificationAPI's user preferences concept
        email_enabled: Optional[bool] = None,
        browser_enabled: Optional[bool] = None
    ) -> bool:
        """
        Updates user's notification preferences via NotificationAPI.
        
        NOTE: This is a placeholder. The actual implementation depends on how
        preferences are configured in NotificationAPI (e.g., using their hosted pages
        or specific API calls if available). For now, we assume frontend handles it.
        """
        logger.warning(f"NOTE: User preference updates for {user_id} should be handled by the NotificationAPI UI components on the frontend.")
        # In a real scenario, you might have an API call here if NotificationAPI provides one
        # for server-side preference management.
        return True

    # The methods below are kept for internal data consistency within Torale's database
    # but are decoupled from the notification sending logic.

    async def _get_user_id_by_email(self, email: str) -> Optional[str]:
        """Get user ID from email address using Supabase."""
        try:
            result = self.supabase.table("users").select("id").eq("email", email).single().execute()
            return result.data.get("id") if result.data else None
        except Exception as e:
            logger.error(f"Error fetching user ID for email {email}: {e}")
            return None

    async def _mark_alert_notified(self, alert_id: str) -> None:
        """Marks an alert as 'notified' in the Supabase database."""
        try:
            self.supabase.table("change_alerts").update({
                "status": "notified",
                "notified_at": "now()"
            }).eq("id", alert_id).execute()
            logger.info(f"Marked alert {alert_id} as notified in database.")
        except Exception as e:
            logger.error(f"Failed to mark alert {alert_id} as notified: {e}", exc_info=True)

    # The following methods from the old service are now deprecated as NotificationAPI
    # provides its own logging, stats, and preference management UI.
    # They can be removed or adapted if there's a need to pull data from NotificationAPI via API.

    async def get_notification_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        logger.warning("Deprecated: Notification preferences are now managed by NotificationAPI.")
        return {"message": "Preferences are managed by NotificationAPI."}

    async def get_notification_stats(self, user_id: str) -> Dict[str, Any]:
        logger.warning("Deprecated: Notification stats are now available in the NotificationAPI dashboard.")
        return {"message": "Stats are available in the NotificationAPI dashboard."}

    async def get_notification_logs(self, user_email: str, **kwargs) -> list:
        logger.warning("Deprecated: Notification logs are now available in the NotificationAPI dashboard.")
        return [{"message": "Logs are available in the NotificationAPI dashboard."}]

    async def mark_alert_as_notified(self, alert_id: str) -> bool:
        """Public method to mark an alert as notified."""
        await self._mark_alert_notified(alert_id)
        return True