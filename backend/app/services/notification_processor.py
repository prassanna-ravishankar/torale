import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from supabase import Client

from app.services.notification_service import SupabaseNotificationService

logger = logging.getLogger(__name__)


class NotificationProcessor:
    """Background processor for handling notification queues and retries."""
    
    def __init__(self, notification_service: SupabaseNotificationService):
        """Initialize the processor with a notification service."""
        self.notification_service = notification_service
        self.supabase = notification_service.supabase
        self.is_running = False
        
    async def start(self) -> None:
        """Start the background notification processor."""
        if self.is_running:
            logger.warning("Notification processor is already running")
            return
            
        self.is_running = True
        logger.info("Starting notification processor")
        
        # Start background tasks
        tasks = [
            asyncio.create_task(self._process_pending_notifications()),
            asyncio.create_task(self._retry_failed_notifications()),
            asyncio.create_task(self._cleanup_old_logs())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Error in notification processor: {e}", exc_info=True)
        finally:
            self.is_running = False
            
    async def stop(self) -> None:
        """Stop the background notification processor."""
        self.is_running = False
        logger.info("Notification processor stopped")
        
    async def process_alert_notification(self, alert_id: str) -> bool:
        """
        Process a single alert notification immediately.
        
        Args:
            alert_id: UUID of the change alert to process
            
        Returns:
            True if notification was sent successfully, False otherwise
        """
        try:
            # Get alert details with related data
            result = self.supabase.table("change_alerts").select("""
                *,
                monitored_sources (
                    url,
                    user_queries (query_text)
                ),
                users:user_id (email)
            """).eq("id", alert_id).single().execute()
            
            if not result.data:
                logger.error(f"Alert {alert_id} not found")
                return False
                
            alert = result.data
            user_email = alert.get("users", {}).get("email")
            
            if not user_email:
                logger.error(f"No user email found for alert {alert_id}")
                return False
                
            # Get monitoring details
            monitored_source = alert.get("monitored_sources", {})
            target_url = monitored_source.get("url", "Unknown source")
            query_text = monitored_source.get("user_queries", {}).get("query_text", "Content monitoring")
            
            # Get the latest content for this alert
            content_result = self.supabase.table("scraped_content").select("processed_text, raw_content").eq("monitored_source_id", alert["monitored_source_id"]).order("scraped_at", desc=True).limit(1).execute()
            
            content = ""
            if content_result.data:
                content_data = content_result.data[0]
                content = content_data.get("processed_text") or content_data.get("raw_content") or alert.get("change_summary", "")
            else:
                content = alert.get("change_summary", "")
                
            # Send the notification
            success = await self.notification_service.send_email_notification(
                user_email=user_email,
                query=query_text,
                target_url=target_url,
                content=content,
                alert_id=alert_id
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing alert notification {alert_id}: {e}", exc_info=True)
            return False
            
    async def _process_pending_notifications(self) -> None:
        """Background task to process pending notifications."""
        while self.is_running:
            try:
                # Find alerts that need notifications
                result = self.supabase.table("change_alerts").select("id").eq("notification_sent", False).eq("is_acknowledged", False).limit(10).execute()
                
                if result.data:
                    logger.info(f"Processing {len(result.data)} pending notifications")
                    
                    for alert in result.data:
                        if not self.is_running:
                            break
                            
                        await self.process_alert_notification(alert["id"])
                        
                        # Small delay to avoid overwhelming email service
                        await asyncio.sleep(1)
                        
                # Sleep before next check
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in pending notifications processor: {e}", exc_info=True)
                await asyncio.sleep(60)  # Wait longer on error
                
    async def _retry_failed_notifications(self) -> None:
        """Background task to retry failed notifications."""
        while self.is_running:
            try:
                # Find failed notifications from the last hour that haven't been retried too many times
                cutoff_time = (datetime.utcnow() - timedelta(hours=1)).isoformat()
                
                result = self.supabase.table("notification_logs").select("alert_id").eq("status", "failed").gte("sent_at", cutoff_time).execute()
                
                if result.data:
                    # Get unique alert IDs
                    alert_ids = list(set(log["alert_id"] for log in result.data if log["alert_id"]))
                    
                    # Check retry count for each alert
                    for alert_id in alert_ids:
                        if not self.is_running:
                            break
                            
                        retry_result = self.supabase.table("change_alerts").select("notification_retry_count").eq("id", alert_id).single().execute()
                        
                        if retry_result.data:
                            retry_count = retry_result.data.get("notification_retry_count", 0)
                            
                            # Retry up to 3 times
                            if retry_count < 3:
                                logger.info(f"Retrying notification for alert {alert_id} (attempt {retry_count + 1})")
                                
                                success = await self.process_alert_notification(alert_id)
                                
                                # Update retry count
                                self.supabase.table("change_alerts").update({
                                    "notification_retry_count": retry_count + 1
                                }).eq("id", alert_id).execute()
                                
                                if success:
                                    logger.info(f"Retry successful for alert {alert_id}")
                                else:
                                    logger.warning(f"Retry failed for alert {alert_id}")
                                    
                                await asyncio.sleep(5)  # Delay between retries
                                
                # Sleep before next retry check
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in retry notifications processor: {e}", exc_info=True)
                await asyncio.sleep(600)  # Wait longer on error
                
    async def _cleanup_old_logs(self) -> None:
        """Background task to cleanup old notification logs."""
        while self.is_running:
            try:
                # Delete logs older than 30 days
                cutoff_time = (datetime.utcnow() - timedelta(days=30)).isoformat()
                
                result = self.supabase.table("notification_logs").delete().lt("sent_at", cutoff_time).execute()
                
                if result.data:
                    logger.info(f"Cleaned up {len(result.data)} old notification logs")
                    
                # Sleep for 24 hours before next cleanup
                await asyncio.sleep(86400)
                
            except Exception as e:
                logger.error(f"Error in log cleanup: {e}", exc_info=True)
                await asyncio.sleep(86400)  # Try again tomorrow
                
    async def get_queue_status(self) -> Dict[str, Any]:
        """Get current status of the notification queue."""
        try:
            # Count pending notifications
            pending_result = self.supabase.table("change_alerts").select("id", count="exact").eq("notification_sent", False).eq("is_acknowledged", False).execute()
            
            # Count failed notifications from last 24 hours
            cutoff_time = (datetime.utcnow() - timedelta(hours=24)).isoformat()
            failed_result = self.supabase.table("notification_logs").select("id", count="exact").eq("status", "failed").gte("sent_at", cutoff_time).execute()
            
            # Count successful notifications from last 24 hours
            success_result = self.supabase.table("notification_logs").select("id", count="exact").eq("status", "sent").gte("sent_at", cutoff_time).execute()
            
            return {
                "processor_running": self.is_running,
                "pending_notifications": pending_result.count or 0,
                "failed_last_24h": failed_result.count or 0,
                "sent_last_24h": success_result.count or 0,
                "last_check": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting queue status: {e}")
            return {
                "processor_running": self.is_running,
                "error": str(e)
            }