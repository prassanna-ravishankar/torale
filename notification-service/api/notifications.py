import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from schemas.notification_schemas import (
    NotificationPreferencesRequest,
    SendNotificationRequest,
    SendNotificationResponse,
)
from services.notification_service import NotificationApiService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["notifications"])

# Global instance - will be set in main.py
notification_service: Optional[NotificationApiService] = None

def set_service(service: NotificationApiService) -> None:
    """Set the global service instance."""
    global notification_service
    notification_service = service

@router.post("/notify", response_model=SendNotificationResponse)
async def send_notification(request: SendNotificationRequest) -> SendNotificationResponse:
    """
    Triggers a change alert notification via NotificationAPI.
    This endpoint should be called by another service (e.g., content monitoring)
    when a change is detected and a notification needs to be sent.
    """
    if not notification_service:
        raise HTTPException(status_code=503, detail="Notification service not available")
    
    try:
        if not request.user_id:
            raise HTTPException(status_code=400, detail="user_id is required for NotificationAPI")

        success = await notification_service.send_change_alert(
            user_id=request.user_id,
            user_email=request.user_email,
            query=request.query,
            target_url=request.target_url,
            content=request.content,
            alert_id=request.alert_id
        )
        
        return SendNotificationResponse(
            success=success,
            message="Notification triggered successfully" if success else "Failed to trigger notification",
            alert_id=request.alert_id
        )
        
    except Exception as e:
        logger.error(f"Error sending notification: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to send notification: {str(e)}")

@router.get("/preferences/{user_id}", deprecated=True)
async def get_notification_preferences(user_id: str) -> Dict[str, Any]:
    """(Deprecated) Get user's notification preferences."""
    return JSONResponse(
        status_code=410,
        content={
            "message": "Notification preferences are now managed via NotificationAPI's UI components.",
            "user_id": user_id
        }
    )

@router.put("/preferences/{user_id}", deprecated=True)
async def update_notification_preferences(
    user_id: str,
    request: NotificationPreferencesRequest
) -> Dict[str, Any]:
    """(Deprecated) Update user's notification preferences."""
    return JSONResponse(
        status_code=410,
        content={
            "message": "Notification preferences are now managed via NotificationAPI's UI components.",
            "user_id": user_id
        }
    )