import logging
from datetime import datetime
from typing import Any, Dict, Optional

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from supabase import Client

logger = logging.getLogger(__name__)


class SupabaseNotificationService:
    """Service for handling notifications via Supabase database and Python backend."""
    
    def __init__(self, supabase_client: Client, sendgrid_api_key: Optional[str] = None):
        """Initialize the service with a Supabase client and optional SendGrid API key."""
        self.supabase = supabase_client
        self.sendgrid_client = SendGridAPIClient(sendgrid_api_key) if sendgrid_api_key else None
        
    async def get_notification_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user's notification preferences.
        
        Args:
            user_id: User's UUID
            
        Returns:
            Dict with user preferences or None if not found
        """
        try:
            result = self.supabase.table("notification_preferences").select("*").eq("user_id", user_id).single().execute()
            return result.data if result.data else None
        except Exception as e:
            logger.error(f"Error fetching notification preferences for user {user_id}: {e}")
            return None
            
    async def update_notification_preferences(
        self, 
        user_id: str, 
        email_enabled: Optional[bool] = None,
        email_frequency: Optional[str] = None,
        browser_enabled: Optional[bool] = None
    ) -> bool:
        """
        Update user's notification preferences.
        
        Args:
            user_id: User's UUID
            email_enabled: Whether email notifications are enabled
            email_frequency: Email frequency ('immediate', 'hourly', 'daily', 'disabled')
            browser_enabled: Whether browser notifications are enabled
            
        Returns:
            True if successful, False otherwise
        """
        try:
            update_data = {"updated_at": "now()"}
            
            if email_enabled is not None:
                update_data["email_enabled"] = email_enabled
            if email_frequency is not None:
                update_data["email_frequency"] = email_frequency
            if browser_enabled is not None:
                update_data["browser_enabled"] = browser_enabled
                
            result = self.supabase.table("notification_preferences").update(update_data).eq("user_id", user_id).execute()
            
            if not result.data:
                # Try to insert if update failed (preferences don't exist)
                user_result = self.supabase.auth.get_user()
                if user_result.user:
                    insert_data = {
                        "user_id": user_id,
                        "user_email": user_result.user.email,
                        **update_data
                    }
                    result = self.supabase.table("notification_preferences").insert(insert_data).execute()
                    
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error updating notification preferences for user {user_id}: {e}")
            return False
            
    async def send_notification_manual(self, alert_id: str) -> Dict[str, Any]:
        """
        Manually trigger a notification for a specific alert.
        
        Args:
            alert_id: UUID of the change alert
            
        Returns:
            Dict with success status and message
        """
        try:
            result = self.supabase.rpc("send_notification_manual", {"p_alert_id": alert_id}).execute()
            return result.data if result.data else {"success": False, "error": "No response from function"}
        except Exception as e:
            logger.error(f"Error sending manual notification for alert {alert_id}: {e}")
            return {"success": False, "error": str(e)}
            
    async def send_email_notification(
        self,
        user_email: str,
        query: str,
        target_url: str,
        content: str,
        alert_id: Optional[str] = None
    ) -> bool:
        """
        Send an email notification for a change alert.
        
        Args:
            user_email: User's email address
            query: The monitoring query that triggered the alert
            target_url: URL that was monitored
            content: The content that changed
            alert_id: Optional alert ID for tracking
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        if not self.sendgrid_client:
            logger.error("SendGrid client not initialized. Missing API key.")
            await self._log_notification(
                alert_id=alert_id,
                user_email=user_email,
                notification_type="email",
                status="failed",
                error_message="SendGrid client not initialized"
            )
            return False
            
        try:
            # Check user's notification preferences
            user_id = await self._get_user_id_by_email(user_email)
            if user_id:
                prefs = await self.get_notification_preferences(user_id)
                if prefs and not prefs.get("email_enabled", True):
                    logger.info(f"Email notifications disabled for user: {user_email}")
                    return True  # Not an error, just disabled
            
            # Create beautiful HTML email
            html_content = self._create_email_html(query, target_url, content)
            
            message = Mail(
                from_email="Torale Alerts <noreply@torale.com>",
                to_emails=user_email,
                subject=f"🔔 Changes detected for \"{query}\"",
                html_content=html_content
            )
            
            response = self.sendgrid_client.send(message)
            success = response.status_code == 202
            
            # Log the notification attempt
            await self._log_notification(
                alert_id=alert_id,
                user_email=user_email,
                notification_type="email",
                status="sent" if success else "failed",
                provider="sendgrid",
                response_code=response.status_code,
                metadata={
                    "query": query,
                    "target_url": target_url,
                    "content_length": len(content)
                }
            )
            
            # Update alert as notified if successful
            if success and alert_id:
                await self._mark_alert_notified(alert_id)
                
            if success:
                logger.info(f"Email notification sent successfully to {user_email}")
            else:
                logger.error(f"Failed to send email to {user_email}. Status: {response.status_code}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error sending email notification to {user_email}: {e}", exc_info=True)
            
            await self._log_notification(
                alert_id=alert_id,
                user_email=user_email,
                notification_type="email",
                status="failed",
                error_message=str(e)
            )
            
            return False
            
    def _create_email_html(self, query: str, target_url: str, content: str) -> str:
        """Create beautiful HTML email content."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Torale Alert</title>
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 30px;">
                <h1 style="color: white; margin: 0; font-size: 28px;">🔔 Content Change Detected</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 16px;">Your monitored content has been updated</p>
            </div>
            
            <div style="background: #f8f9fa; padding: 25px; border-radius: 8px; margin-bottom: 20px;">
                <h2 style="color: #2c3e50; margin-top: 0; font-size: 20px;">📋 Monitoring Details</h2>
                <p style="margin: 8px 0;"><strong>Query:</strong> <span style="color: #5865f2;">{query}</span></p>
                <p style="margin: 8px 0;"><strong>Source:</strong> <a href="{target_url}" style="color: #5865f2; text-decoration: none;">{target_url}</a></p>
            </div>
            
            <div style="background: white; border: 1px solid #e1e8ed; padding: 25px; border-radius: 8px; margin-bottom: 20px;">
                <h3 style="color: #2c3e50; margin-top: 0; font-size: 18px;">📄 Updated Content</h3>
                <div style="background-color: #f5f5f5; padding: 20px; border-radius: 6px; border-left: 4px solid #5865f2; font-family: 'SF Mono', Monaco, monospace; font-size: 14px; line-height: 1.5; overflow-wrap: break-word; max-height: 300px; overflow-y: auto;">
                    {content[:1500]}{'...' if len(content) > 1500 else ''}
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e1e8ed;">
                <p style="color: #6c757d; font-size: 14px; margin: 0;">
                    This alert was sent by <strong>Torale</strong> - your content monitoring assistant
                </p>
                <p style="color: #6c757d; font-size: 12px; margin: 10px 0 0 0;">
                    You can manage your notification preferences in your dashboard
                </p>
            </div>
        </body>
        </html>
        """
        
    async def _get_user_id_by_email(self, email: str) -> Optional[str]:
        """Get user ID from email address."""
        try:
            # Note: This requires service role access to auth.users
            result = self.supabase.table("auth.users").select("id").eq("email", email).single().execute()
            return result.data.get("id") if result.data else None
        except Exception:
            # Fallback: try to get from notification_preferences
            try:
                result = self.supabase.table("notification_preferences").select("user_id").eq("user_email", email).single().execute()
                return result.data.get("user_id") if result.data else None
            except Exception:
                return None
                
    async def _log_notification(
        self,
        alert_id: Optional[str],
        user_email: str,
        notification_type: str,
        status: str,
        provider: Optional[str] = None,
        response_code: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Log notification attempt to database."""
        try:
            log_entry = {
                "alert_id": alert_id,
                "user_email": user_email,
                "notification_type": notification_type,
                "status": status,
                "provider": provider,
                "response_code": response_code,
                "metadata": metadata or {},
                "error_message": error_message,
                "sent_at": datetime.utcnow().isoformat()
            }
            
            self.supabase.table("notification_logs").insert(log_entry).execute()
        except Exception as e:
            logger.error(f"Failed to log notification: {e}")
            
    async def _mark_alert_notified(self, alert_id: str) -> None:
        """Mark an alert as having been notified."""
        try:
            self.supabase.table("change_alerts").update({
                "notification_sent": True,
                "notification_sent_at": datetime.utcnow().isoformat()
            }).eq("id", alert_id).execute()
        except Exception as e:
            logger.error(f"Failed to mark alert {alert_id} as notified: {e}")
            
    async def get_notification_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get notification statistics for a user.
        
        Args:
            user_id: User's UUID
            
        Returns:
            Dict with notification statistics
        """
        try:
            result = self.supabase.rpc("get_notification_stats", {"p_user_id": user_id}).execute()
            return result.data if result.data else {}
        except Exception as e:
            logger.error(f"Error fetching notification stats for user {user_id}: {e}")
            return {}
            
    async def get_notification_logs(
        self, 
        user_email: str, 
        limit: int = 50, 
        offset: int = 0,
        status_filter: Optional[str] = None
    ) -> list[Dict[str, Any]]:
        """
        Get notification logs for a user.
        
        Args:
            user_email: User's email address
            limit: Maximum number of logs to return
            offset: Number of logs to skip
            status_filter: Filter by notification status
            
        Returns:
            List of notification log entries
        """
        try:
            query = self.supabase.table("notification_logs").select("*").eq("user_email", user_email)
            
            if status_filter:
                query = query.eq("status", status_filter)
                
            result = query.order("sent_at", desc=True).range(offset, offset + limit - 1).execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error fetching notification logs for user {user_email}: {e}")
            return []
            
    async def mark_alert_as_notified(self, alert_id: str) -> bool:
        """
        Mark an alert as having been notified (used by external notification systems).
        
        Args:
            alert_id: UUID of the change alert
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.supabase.table("change_alerts").update({
                "notification_sent": True,
                "notification_sent_at": "now()"
            }).eq("id", alert_id).execute()
            
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error marking alert {alert_id} as notified: {e}")
            return False