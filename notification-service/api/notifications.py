import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from schemas.notification_schemas import (
    NotificationPreferencesRequest,
    NotificationPreferencesResponse,
    SendNotificationRequest,
    SendNotificationResponse,
    ManualNotificationRequest,
    NotificationStatsResponse,
    NotificationLogResponse,
    NotificationLogsResponse,
)
from services.notification_service import SupabaseNotificationService
from services.notification_processor import NotificationProcessor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["notifications"])

# Global instances - will be set in main.py
notification_service: Optional[SupabaseNotificationService] = None
notification_processor: Optional[NotificationProcessor] = None


def set_services(
    service: SupabaseNotificationService,
    processor: NotificationProcessor
) -> None:
    """Set the global service instances."""
    global notification_service, notification_processor
    notification_service = service
    notification_processor = processor


@router.post("/notify", response_model=SendNotificationResponse)
async def send_notification(request: SendNotificationRequest) -> SendNotificationResponse:
    """Send a notification for a change alert."""
    if not notification_service:
        raise HTTPException(status_code=500, detail="Notification service not initialized")
    
    try:
        success = await notification_service.send_email_notification(
            user_email=request.user_email,
            query=request.query,
            target_url=request.target_url,
            content=request.content,
            alert_id=request.alert_id
        )
        
        return SendNotificationResponse(
            success=success,
            message="Notification sent successfully" if success else "Failed to send notification",
            alert_id=request.alert_id
        )
        
    except Exception as e:
        logger.error(f"Error sending notification: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to send notification: {str(e)}")


@router.post("/notify/manual", response_model=Dict[str, Any])
async def send_manual_notification(request: ManualNotificationRequest) -> Dict[str, Any]:
    """Manually trigger a notification for a specific alert."""
    if not notification_service:
        raise HTTPException(status_code=500, detail="Notification service not initialized")
    
    try:
        result = await notification_service.send_notification_manual(request.alert_id)
        return result
        
    except Exception as e:
        logger.error(f"Error sending manual notification: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to send manual notification: {str(e)}")


@router.get("/preferences/{user_id}", response_model=NotificationPreferencesResponse)
async def get_notification_preferences(user_id: str) -> NotificationPreferencesResponse:
    """Get user's notification preferences."""
    if not notification_service:
        raise HTTPException(status_code=500, detail="Notification service not initialized")
    
    try:
        preferences = await notification_service.get_notification_preferences(user_id)
        
        if not preferences:
            raise HTTPException(status_code=404, detail="Notification preferences not found")
            
        return NotificationPreferencesResponse(**preferences)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching notification preferences: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch preferences: {str(e)}")


@router.put("/preferences/{user_id}")
async def update_notification_preferences(
    user_id: str,
    request: NotificationPreferencesRequest
) -> Dict[str, Any]:
    """Update user's notification preferences."""
    if not notification_service:
        raise HTTPException(status_code=500, detail="Notification service not initialized")
    
    try:
        success = await notification_service.update_notification_preferences(
            user_id=user_id,
            email_enabled=request.email_enabled,
            email_frequency=request.email_frequency,
            browser_enabled=request.browser_enabled
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update notification preferences")
            
        return {"success": True, "message": "Notification preferences updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating notification preferences: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update preferences: {str(e)}")


@router.get("/stats/{user_id}", response_model=Dict[str, Any])
async def get_notification_stats(user_id: str) -> Dict[str, Any]:
    """Get notification statistics for a user."""
    if not notification_service:
        raise HTTPException(status_code=500, detail="Notification service not initialized")
    
    try:
        stats = await notification_service.get_notification_stats(user_id)
        return stats
        
    except Exception as e:
        logger.error(f"Error fetching notification stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch stats: {str(e)}")


@router.get("/logs/{user_email}", response_model=NotificationLogsResponse)
async def get_notification_logs(
    user_email: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status_filter: Optional[str] = Query(None, description="Filter by status: sent, failed, pending")
) -> NotificationLogsResponse:
    """Get notification logs for a user."""
    if not notification_service:
        raise HTTPException(status_code=500, detail="Notification service not initialized")
    
    try:
        logs = await notification_service.get_notification_logs(
            user_email=user_email,
            limit=limit,
            offset=offset,
            status_filter=status_filter
        )
        
        log_responses = [NotificationLogResponse(**log) for log in logs]
        
        return NotificationLogsResponse(
            logs=log_responses,
            total=len(log_responses),
            offset=offset,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error fetching notification logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch logs: {str(e)}")


@router.get("/queue/status", response_model=NotificationStatsResponse)
async def get_queue_status() -> NotificationStatsResponse:
    """Get current status of the notification queue."""
    if not notification_processor:
        raise HTTPException(status_code=500, detail="Notification processor not initialized")
    
    try:
        status = await notification_processor.get_queue_status()
        
        return NotificationStatsResponse(
            pending_notifications=status.get("pending_notifications", 0),
            failed_last_24h=status.get("failed_last_24h", 0),
            sent_last_24h=status.get("sent_last_24h", 0),
            processor_running=status.get("processor_running", False),
            last_check=status.get("last_check", datetime.utcnow().isoformat())
        )
        
    except Exception as e:
        logger.error(f"Error fetching queue status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch queue status: {str(e)}")


@router.post("/alerts/{alert_id}/mark-notified")
async def mark_alert_notified(alert_id: str) -> Dict[str, Any]:
    """Mark an alert as having been notified."""
    if not notification_service:
        raise HTTPException(status_code=500, detail="Notification service not initialized")
    
    try:
        success = await notification_service.mark_alert_as_notified(alert_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to mark alert as notified")
            
        return {"success": True, "message": "Alert marked as notified"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking alert as notified: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to mark alert: {str(e)}")


@router.post("/process/{alert_id}")
async def process_alert_notification(alert_id: str) -> Dict[str, Any]:
    """Process a single alert notification immediately."""
    if not notification_processor:
        raise HTTPException(status_code=500, detail="Notification processor not initialized")
    
    try:
        success = await notification_processor.process_alert_notification(alert_id)
        
        return {
            "success": success,
            "message": "Alert notification processed successfully" if success else "Failed to process alert notification",
            "alert_id": alert_id
        }
        
    except Exception as e:
        logger.error(f"Error processing alert notification: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process alert: {str(e)}")