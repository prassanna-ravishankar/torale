import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.api.deps import get_current_user, User
from app.clients.notification_client import NotificationServiceClient
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


class NotificationPreferencesUpdate(BaseModel):
    """Model for updating notification preferences."""
    email_enabled: bool | None = None
    email_frequency: str | None = None
    browser_enabled: bool | None = None


class SendNotificationRequest(BaseModel):
    """Model for manually sending a notification."""
    alert_id: str
    force_resend: bool = False


class NotificationResponse(BaseModel):
    """Generic response model for notification operations."""
    success: bool
    message: str
    data: Dict[str, Any] | None = None


@router.get("/preferences", response_model=Dict[str, Any])
async def get_notification_preferences(
    current_user: User = Depends(get_current_user),
):
    """Get current user's notification preferences."""
    client = NotificationServiceClient(settings.NOTIFICATION_SERVICE_URL)
    try:
        preferences = await client.get_notification_preferences(current_user.id)
        
        if not preferences:
            # Return default preferences if none exist
            return {
                "user_id": current_user.id,
                "user_email": current_user.email,
                "email_enabled": True,
                "email_frequency": "immediate",
                "browser_enabled": True,
                "created_at": None,
                "updated_at": None
            }
            
        return preferences
        
    except Exception as e:
        logger.error(f"Error fetching notification preferences for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch notification preferences"
        )
    finally:
        await client.close()


@router.put("/preferences", response_model=NotificationResponse)
async def update_notification_preferences(
    preferences_update: NotificationPreferencesUpdate,
    current_user: User = Depends(get_current_user),
):
    """Update user's notification preferences."""
    client = NotificationServiceClient(settings.NOTIFICATION_SERVICE_URL)
    try:
        success = await client.update_notification_preferences(
            user_id=current_user.id,
            email_enabled=preferences_update.email_enabled,
            email_frequency=preferences_update.email_frequency,
            browser_enabled=preferences_update.browser_enabled
        )
        
        if success:
            return NotificationResponse(
                success=True,
                message="Notification preferences updated successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update notification preferences"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating notification preferences for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notification preferences"
        )
    finally:
        await client.close()


@router.get("/stats", response_model=Dict[str, Any])
async def get_notification_stats(
    current_user: User = Depends(get_current_user),
):
    """Get notification statistics for the current user."""
    client = NotificationServiceClient(settings.NOTIFICATION_SERVICE_URL)
    try:
        stats = await client.get_notification_stats(current_user.id)
        return stats
        
    except Exception as e:
        logger.error(f"Error fetching notification stats for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch notification statistics"
        )
    finally:
        await client.close()


@router.get("/logs", response_model=List[Dict[str, Any]])
async def get_notification_logs(
    limit: int = 50,
    offset: int = 0,
    status_filter: str | None = None,
    current_user: User = Depends(get_current_user),
):
    """Get notification logs for the current user."""
    client = NotificationServiceClient(settings.NOTIFICATION_SERVICE_URL)
    try:
        logs = await client.get_notification_logs(
            user_email=current_user.email,
            limit=limit,
            offset=offset,
            status_filter=status_filter
        )
        return logs
        
    except Exception as e:
        logger.error(f"Error fetching notification logs for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch notification logs"
        )
    finally:
        await client.close()


@router.post("/send", response_model=NotificationResponse)
async def send_notification(
    request: SendNotificationRequest,
    current_user: User = Depends(get_current_user),
):
    """Manually send or resend a notification for a specific alert."""
    client = NotificationServiceClient(settings.NOTIFICATION_SERVICE_URL)
    try:
        # Process the notification via the notification service
        result = await client.process_alert_notification(request.alert_id)
        
        return NotificationResponse(
            success=result.get("success", False),
            message=result.get("message", "Failed to send notification")
        )
        
    except Exception as e:
        logger.error(f"Error sending notification for alert {request.alert_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send notification"
        )
    finally:
        await client.close()


@router.get("/queue/status", response_model=Dict[str, Any])
async def get_queue_status(
    current_user: User = Depends(get_current_user),
):
    """Get the current status of the notification queue (admin endpoint)."""
    client = NotificationServiceClient(settings.NOTIFICATION_SERVICE_URL)
    try:
        status = await client.get_queue_status()
        return status
            
    except Exception as e:
        logger.error(f"Error fetching queue status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch queue status"
        )
    finally:
        await client.close()


@router.post("/queue/process", response_model=NotificationResponse)
async def trigger_queue_processing(
    current_user: User = Depends(get_current_user),
):
    """Manually trigger processing of pending notifications (admin endpoint)."""
    # This endpoint is now primarily informational since the notification service
    # handles its own queue processing automatically
    client = NotificationServiceClient(settings.NOTIFICATION_SERVICE_URL)
    try:
        status = await client.get_queue_status()
        
        return NotificationResponse(
            success=True,
            message="Notification service is processing queue automatically",
            data=status
        )
        
    except Exception as e:
        logger.error(f"Error checking notification queue: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check notification queue"
        )
    finally:
        await client.close()