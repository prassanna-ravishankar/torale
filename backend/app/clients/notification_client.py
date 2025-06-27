import logging
from typing import Any, Dict, List, Optional

import aiohttp
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class NotificationServiceClient:
    """Client for interacting with the notification microservice."""
    
    def __init__(self, base_url: str = "http://notification-service:8003"):
        """Initialize the notification service client."""
        self.base_url = base_url.rstrip("/")
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure we have an active session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
        
    async def close(self) -> None:
        """Close the HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            
    async def send_notification(
        self,
        user_email: str,
        query: str,
        target_url: str,
        content: str,
        alert_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a notification via the notification service."""
        try:
            session = await self._ensure_session()
            
            payload = {
                "user_email": user_email,
                "query": query,
                "target_url": target_url,
                "content": content,
                "alert_id": alert_id
            }
            
            async with session.post(
                f"{self.base_url}/api/v1/notify",
                json=payload
            ) as response:
                result = await response.json()
                
                if response.status == 200:
                    return result
                else:
                    logger.error(f"Notification service error: {response.status} - {result}")
                    return {
                        "success": False,
                        "message": result.get("detail", "Notification service error")
                    }
                    
        except aiohttp.ClientError as e:
            logger.error(f"Failed to connect to notification service: {e}")
            return {
                "success": False,
                "message": f"Notification service unavailable: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error sending notification: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Failed to send notification: {str(e)}"
            }
            
    async def process_alert_notification(self, alert_id: str) -> Dict[str, Any]:
        """Process a specific alert notification."""
        try:
            session = await self._ensure_session()
            
            async with session.post(
                f"{self.base_url}/api/v1/process/{alert_id}"
            ) as response:
                result = await response.json()
                
                if response.status == 200:
                    return result
                else:
                    logger.error(f"Notification service error: {response.status} - {result}")
                    return {
                        "success": False,
                        "message": result.get("detail", "Failed to process alert")
                    }
                    
        except Exception as e:
            logger.error(f"Error processing alert notification: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Failed to process alert: {str(e)}"
            }
            
    async def get_notification_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's notification preferences."""
        try:
            session = await self._ensure_session()
            
            async with session.get(
                f"{self.base_url}/api/v1/preferences/{user_id}"
            ) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    return None
                else:
                    logger.error(f"Failed to get preferences: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting notification preferences: {e}", exc_info=True)
            return None
            
    async def update_notification_preferences(
        self,
        user_id: str,
        email_enabled: Optional[bool] = None,
        email_frequency: Optional[str] = None,
        browser_enabled: Optional[bool] = None
    ) -> bool:
        """Update user's notification preferences."""
        try:
            session = await self._ensure_session()
            
            payload = {}
            if email_enabled is not None:
                payload["email_enabled"] = email_enabled
            if email_frequency is not None:
                payload["email_frequency"] = email_frequency
            if browser_enabled is not None:
                payload["browser_enabled"] = browser_enabled
                
            async with session.put(
                f"{self.base_url}/api/v1/preferences/{user_id}",
                json=payload
            ) as response:
                return response.status == 200
                
        except Exception as e:
            logger.error(f"Error updating notification preferences: {e}", exc_info=True)
            return False
            
    async def get_notification_stats(self, user_id: str) -> Dict[str, Any]:
        """Get notification statistics for a user."""
        try:
            session = await self._ensure_session()
            
            async with session.get(
                f"{self.base_url}/api/v1/stats/{user_id}"
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {}
                    
        except Exception as e:
            logger.error(f"Error getting notification stats: {e}", exc_info=True)
            return {}
            
    async def get_notification_logs(
        self,
        user_email: str,
        limit: int = 50,
        offset: int = 0,
        status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get notification logs for a user."""
        try:
            session = await self._ensure_session()
            
            params = {
                "limit": limit,
                "offset": offset
            }
            if status_filter:
                params["status_filter"] = status_filter
                
            async with session.get(
                f"{self.base_url}/api/v1/logs/{user_email}",
                params=params
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("logs", [])
                else:
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting notification logs: {e}", exc_info=True)
            return []
            
    async def get_queue_status(self) -> Dict[str, Any]:
        """Get notification queue status."""
        try:
            session = await self._ensure_session()
            
            async with session.get(
                f"{self.base_url}/api/v1/queue/status"
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": "Failed to get queue status"}
                    
        except Exception as e:
            logger.error(f"Error getting queue status: {e}", exc_info=True)
            return {"error": str(e)}
            
    async def mark_alert_notified(self, alert_id: str) -> bool:
        """Mark an alert as notified."""
        try:
            session = await self._ensure_session()
            
            async with session.post(
                f"{self.base_url}/api/v1/alerts/{alert_id}/mark-notified"
            ) as response:
                return response.status == 200
                
        except Exception as e:
            logger.error(f"Error marking alert as notified: {e}", exc_info=True)
            return False
            
    async def health_check(self) -> bool:
        """Check if the notification service is healthy."""
        try:
            session = await self._ensure_session()
            
            async with session.get(
                f"{self.base_url}/health",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                return response.status == 200
                
        except Exception:
            return False