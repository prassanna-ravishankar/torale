import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from config import Settings, get_settings
from schemas.notification_schemas import (
    AlertNotificationRequest,
    EmailNotificationRequest,
    NotificationResponse,
)
from services.notification_service import NotificationService

router = APIRouter()
logger = logging.getLogger(__name__)


async def get_notification_service(
    settings: Annotated[Settings, Depends(get_settings)]
) -> NotificationService:
    """Dependency to provide NotificationService instance."""
    if not settings.SENDGRID_API_KEY:
        logger.error("SENDGRID_API_KEY not configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Notification service not properly configured",
        )
    return NotificationService(api_key=settings.SENDGRID_API_KEY)


@router.post("/email", response_model=NotificationResponse)
async def send_email_notification(
    request: EmailNotificationRequest,
    service: Annotated[NotificationService, Depends(get_notification_service)],
) -> NotificationResponse:
    """
    Send an email notification.
    
    Args:
        request: Email notification details
        service: Notification service instance
        
    Returns:
        NotificationResponse: Success status and optional message
    """
    logger.info(f"Sending email notification to {request.to_email}")
    
    success = await service.send_email(
        to_email=request.to_email,
        subject=request.subject,
        html_content=request.html_content,
        from_email=request.from_email or "noreply@torale.com",
    )
    
    if success:
        return NotificationResponse(
            success=True,
            message="Email sent successfully"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send email notification"
        )


@router.post("/alert", response_model=NotificationResponse)
async def send_alert_notification(
    request: AlertNotificationRequest,
    service: Annotated[NotificationService, Depends(get_notification_service)],
) -> NotificationResponse:
    """
    Send a change alert notification (backward compatible endpoint).
    
    Args:
        request: Alert notification details
        service: Notification service instance
        
    Returns:
        NotificationResponse: Success status and optional message
    """
    logger.info(
        f"Sending alert notification to {request.user_email} for query: {request.query}"
    )
    
    success = await service.send_alert(
        user_email=request.user_email,
        query=request.query,
        target_url=request.target_url,
        content=request.content,
        from_email=request.from_email or "noreply@torale.com",
    )
    
    if success:
        return NotificationResponse(
            success=True,
            message="Alert sent successfully"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send alert notification"
        )