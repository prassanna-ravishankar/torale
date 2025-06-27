from typing import Any, Dict, List, Optional
from pydantic import BaseModel, EmailStr, Field


class NotificationPreferencesRequest(BaseModel):
    """Request model for updating notification preferences."""
    email_enabled: Optional[bool] = None
    email_frequency: Optional[str] = Field(None, description="'immediate', 'hourly', 'daily', 'disabled'")
    browser_enabled: Optional[bool] = None


class NotificationPreferencesResponse(BaseModel):
    """Response model for notification preferences."""
    user_id: str
    user_email: str
    email_enabled: bool
    email_frequency: str
    browser_enabled: bool
    created_at: str
    updated_at: str


class SendNotificationRequest(BaseModel):
    """Request model for sending a notification."""
    user_email: EmailStr
    query: str
    target_url: str
    content: str
    alert_id: Optional[str] = None


class SendNotificationResponse(BaseModel):
    """Response model for sending a notification."""
    success: bool
    message: str
    alert_id: Optional[str] = None


class ManualNotificationRequest(BaseModel):
    """Request model for manually triggering a notification."""
    alert_id: str


class NotificationStatsResponse(BaseModel):
    """Response model for notification statistics."""
    pending_notifications: int
    failed_last_24h: int
    sent_last_24h: int
    processor_running: bool
    last_check: str


class NotificationLogResponse(BaseModel):
    """Response model for notification logs."""
    alert_id: Optional[str]
    user_email: str
    notification_type: str
    status: str
    provider: Optional[str]
    response_code: Optional[int]
    metadata: Dict[str, Any]
    error_message: Optional[str]
    sent_at: str


class NotificationLogsResponse(BaseModel):
    """Response model for notification logs list."""
    logs: List[NotificationLogResponse]
    total: int
    offset: int
    limit: int


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    service: str
    version: str
    timestamp: str