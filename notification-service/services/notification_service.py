import logging
from typing import Optional

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# HTTP Status Codes
HTTP_ACCEPTED = 202

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for handling notifications across different channels."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the notification service with SendGrid API key."""
        self.sendgrid_client = SendGridAPIClient(api_key) if api_key else None
        
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        from_email: str = "noreply@torale.com",
    ) -> bool:
        """
        Send an email notification.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content for the email body
            from_email: Sender email address
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        if not self.sendgrid_client:
            logger.error("SendGrid client not initialized. Missing API key.")
            return False
            
        try:
            message = Mail(
                from_email=from_email,
                to_emails=to_email,
                subject=subject,
                html_content=html_content,
            )
            response = self.sendgrid_client.send(message)
            success = response.status_code == HTTP_ACCEPTED
            
            if success:
                logger.info(f"Email sent successfully to {to_email}")
            else:
                logger.error(
                    f"Failed to send email to {to_email}. "
                    f"Status code: {response.status_code}"
                )
                
            return success
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}", exc_info=True)
            return False
            
    async def send_alert(
        self,
        user_email: str,
        query: str,
        target_url: str,
        content: str,
        from_email: str = "noreply@torale.com",
    ) -> bool:
        """
        Send a change alert email to the user.
        
        This method maintains backward compatibility with the monolith implementation.
        
        Args:
            user_email: User's email address
            query: The original monitoring query
            target_url: The URL being monitored
            content: The updated content (will be truncated to 1000 chars)
            from_email: Sender email address
            
        Returns:
            bool: True if alert was sent successfully, False otherwise
        """
        subject = f"Alert: Changes detected for '{query}'"
        html_content = f"""
        <h2>Changes Detected</h2>
        <p>We've detected changes in the content you're monitoring:</p>
        <p><strong>Query:</strong> {query}</p>
        <p><strong>URL:</strong> <a href="{target_url}">{target_url}</a></p>
        <hr>
        <h3>Updated Content:</h3>
        <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; max-width: 100%; overflow-wrap: break-word;">
            {content[:1000]}...
        </div>
        """
        
        return await self.send_email(
            to_email=user_email,
            subject=subject,
            html_content=html_content,
            from_email=from_email,
        )