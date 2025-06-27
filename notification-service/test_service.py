#!/usr/bin/env python3
"""
Test script for the Notification Service.
Run with: uv run python test_service.py
"""

import asyncio
import logging

import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

NOTIFICATION_SERVICE_URL = "http://localhost:8002"


async def test_health_check():
    """Test the health check endpoint."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{NOTIFICATION_SERVICE_URL}/health")
            logger.info(f"Health check response: {response.json()}")
            assert response.status_code == 200
            logger.info("✅ Health check passed")
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")


async def test_send_email():
    """Test sending an email notification."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{NOTIFICATION_SERVICE_URL}/api/v1/notify/email",
                json={
                    "to_email": "test@example.com",
                    "subject": "Test Email from Notification Service",
                    "html_content": "<h1>Test Email</h1><p>This is a test email from the notification service.</p>",
                },
            )
            logger.info(f"Email notification response: {response.json()}")
            if response.status_code == 200:
                logger.info("✅ Email notification endpoint working (check logs for actual send status)")
            else:
                logger.error(f"❌ Email notification failed with status {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Email notification test failed: {e}")


async def test_send_alert():
    """Test sending an alert notification."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{NOTIFICATION_SERVICE_URL}/api/v1/notify/alert",
                json={
                    "user_email": "test@example.com",
                    "query": "test monitoring query",
                    "target_url": "https://example.com",
                    "content": "This is the updated content that triggered the alert.",
                },
            )
            logger.info(f"Alert notification response: {response.json()}")
            if response.status_code == 200:
                logger.info("✅ Alert notification endpoint working (check logs for actual send status)")
            else:
                logger.error(f"❌ Alert notification failed with status {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Alert notification test failed: {e}")


async def main():
    """Run all tests."""
    logger.info("Testing Notification Service...")
    logger.info(f"Service URL: {NOTIFICATION_SERVICE_URL}")
    
    await test_health_check()
    await test_send_email()
    await test_send_alert()
    
    logger.info("All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())