from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class EmailNotificationRequest(BaseModel):
    """Request model for sending email notifications."""
    
    to_email: EmailStr = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject")
    html_content: str = Field(..., description="HTML content for email body")
    from_email: Optional[EmailStr] = Field(
        default="noreply@torale.com",
        description="Sender email address"
    )


class AlertNotificationRequest(BaseModel):
    """Request model for sending alert notifications (backward compatible)."""
    
    user_email: EmailStr = Field(..., description="User's email address")
    query: str = Field(..., description="The original monitoring query")
    target_url: str = Field(..., description="The URL being monitored")
    content: str = Field(..., description="The updated content")
    from_email: Optional[EmailStr] = Field(
        default="noreply@torale.com",
        description="Sender email address"
    )


class NotificationResponse(BaseModel):
    """Response model for notification operations."""
    
    success: bool = Field(..., description="Whether the notification was sent successfully")
    message: Optional[str] = Field(default=None, description="Additional information or error message")