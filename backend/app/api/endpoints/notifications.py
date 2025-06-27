import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.api.deps import get_current_user, User
from app.api.dependencies import get_notification_service
from app.services.notification_service import SupabaseNotificationService
from app.services.notification_processor import NotificationProcessor

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
    notification_service: SupabaseNotificationService = Depends(get_notification_service),
):
    """Get current user's notification preferences."""
    try:
        preferences = await notification_service.get_notification_preferences(current_user.id)
        
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


@router.put("/preferences", response_model=NotificationResponse)
async def update_notification_preferences(
    preferences_update: NotificationPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    notification_service: SupabaseNotificationService = Depends(get_notification_service),
):
    """Update user's notification preferences."""
    try:
        success = await notification_service.update_notification_preferences(
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


@router.get("/stats", response_model=Dict[str, Any])
async def get_notification_stats(
    current_user: User = Depends(get_current_user),
    notification_service: SupabaseNotificationService = Depends(get_notification_service),
):
    """Get notification statistics for the current user."""
    try:
        stats = await notification_service.get_notification_stats(current_user.id)
        return stats
        
    except Exception as e:
        logger.error(f"Error fetching notification stats for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch notification statistics"
        )


@router.get("/logs", response_model=List[Dict[str, Any]])
async def get_notification_logs(
    limit: int = 50,
    offset: int = 0,
    status_filter: str | None = None,
    current_user: User = Depends(get_current_user),
    notification_service: SupabaseNotificationService = Depends(get_notification_service),
):
    """Get notification logs for the current user."""
    try:
        logs = await notification_service.get_notification_logs(
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


@router.post("/send", response_model=NotificationResponse)
async def send_notification(
    request: SendNotificationRequest,
    current_user: User = Depends(get_current_user),
    notification_service: SupabaseNotificationService = Depends(get_notification_service),
):
    """Manually send or resend a notification for a specific alert."""
    try:
        # Create a notification processor instance
        processor = NotificationProcessor(notification_service)
        
        # Verify the alert belongs to the current user
        alert_result = notification_service.supabase.table("change_alerts").select("id, user_id, notification_sent").eq("id", request.alert_id).eq("user_id", current_user.id).single().execute()
        
        if not alert_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found or access denied"
            )
            
        alert = alert_result.data
        
        # Check if already sent and force_resend is False
        if alert.get("notification_sent") and not request.force_resend:
            return NotificationResponse(
                success=False,
                message="Notification already sent. Use force_resend=true to resend."
            )
            
        # Process the notification
        success = await processor.process_alert_notification(request.alert_id)
        
        return NotificationResponse(
            success=success,
            message="Notification sent successfully" if success else "Failed to send notification"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending notification for alert {request.alert_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send notification"
        )


@router.get("/queue/status", response_model=Dict[str, Any])
async def get_queue_status(
    current_user: User = Depends(get_current_user),
    notification_service: SupabaseNotificationService = Depends(get_notification_service),
):
    """Get the current status of the notification queue (admin endpoint)."""
    try:
        # For now, return basic queue info
        # In production, you might want to restrict this to admin users
        result = notification_service.supabase.rpc("get_notification_queue_status").execute()
        
        if result.data:
            return result.data
        else:
            return {"error": "Failed to get queue status"}
            
    except Exception as e:
        logger.error(f"Error fetching queue status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch queue status"
        )


@router.post("/queue/process", response_model=NotificationResponse)
async def trigger_queue_processing(
    current_user: User = Depends(get_current_user),
    notification_service: SupabaseNotificationService = Depends(get_notification_service),
):
    """Manually trigger processing of pending notifications (admin endpoint)."""
    try:
        # Get pending notifications for this user
        pending_result = notification_service.supabase.table("change_alerts").select("id").eq("user_id", current_user.id).eq("notification_sent", False).eq("is_acknowledged", False).limit(10).execute()
        
        if not pending_result.data:
            return NotificationResponse(
                success=True,
                message="No pending notifications to process"
            )
            
        # Process each pending notification
        processor = NotificationProcessor(notification_service)
        processed_count = 0
        
        for alert in pending_result.data:
            success = await processor.process_alert_notification(alert["id"])
            if success:
                processed_count += 1
                
        return NotificationResponse(
            success=True,
            message=f"Processed {processed_count} out of {len(pending_result.data)} pending notifications",
            data={"processed": processed_count, "total": len(pending_result.data)}
        )
        
    except Exception as e:
        logger.error(f"Error processing notification queue: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process notification queue"
        )