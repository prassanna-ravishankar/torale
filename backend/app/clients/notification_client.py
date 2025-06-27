import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class NotificationClient:
    """Client for interacting with the Notification Service."""
    
    def __init__(self, base_url: str, timeout: float = 30.0):
        """
        Initialize the notification client.
        
        Args:
            base_url: Base URL of the notification service
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        
    async def send_alert(
        self,
        user_email: str,
        query: str,
        target_url: str,
        content: str,
    ) -> bool:
        """
        Send a change alert notification via the notification service.
        
        Args:
            user_email: User's email address
            query: The original monitoring query
            target_url: The URL being monitored
            content: The updated content
            
        Returns:
            bool: True if alert was sent successfully, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/notify/alert",
                    json={
                        "user_email": user_email,
                        "query": query,
                        "target_url": target_url,
                        "content": content,
                    },
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("success", False)
                else:
                    logger.error(
                        f"Failed to send alert via notification service. "
                        f"Status: {response.status_code}, Response: {response.text}"
                    )
                    return False
                    
        except httpx.ConnectError:
            logger.error(
                f"Could not connect to notification service at {self.base_url}"
            )
            return False
        except Exception as e:
            logger.error(
                f"Error sending alert via notification service: {e}", 
                exc_info=True
            )
            return False
            
    async def health_check(self) -> bool:
        """
        Check if the notification service is healthy.
        
        Returns:
            bool: True if service is healthy, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            return False