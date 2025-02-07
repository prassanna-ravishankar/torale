"""Alerting system module."""

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, Protocol

import aiosmtplib

from .rate_limiter import RateLimiter


class AlertBackend(Protocol):
    """Protocol for alert backends."""

    async def send_alert(self, subject: str, message: str) -> bool:
        """Send an alert with the given subject and message.

        Args:
            subject: Alert subject
            message: Alert message

        Returns:
            True if the alert was sent successfully
        """
        ...


class EmailAlertBackend:
    """Email-based alert backend."""

    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        username: str,
        password: str,
        from_email: str,
        to_email: str,
        emails_per_minute: int = 30,
    ):
        """Initialize the email alert backend.

        Args:
            smtp_server: SMTP server hostname
            smtp_port: SMTP server port
            username: SMTP authentication username
            password: SMTP authentication password
            from_email: Sender email address
            to_email: Recipient email address
            emails_per_minute: Maximum number of emails per minute
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.to_email = to_email
        self._client: Optional[aiosmtplib.SMTP] = None
        self._rate_limiter = RateLimiter(rate=emails_per_minute)

    async def _get_client(self) -> aiosmtplib.SMTP:
        """Get or create an SMTP client.

        Returns:
            An SMTP client instance
        """
        if self._client is None or not self._client.is_connected:
            self._client = aiosmtplib.SMTP(
                hostname=self.smtp_server,
                port=self.smtp_port,
                use_tls=True,
            )
            await self._client.connect()
            await self._client.login(self.username, self.password)
        return self._client

    async def close(self) -> None:
        """Close the SMTP connection."""
        if self._client and self._client.is_connected:
            await self._client.quit()
            self._client = None

    async def send_alert(self, subject: str, message: str) -> bool:
        """Send an email alert.

        Args:
            subject: Email subject
            message: Email body

        Returns:
            True if the email was sent successfully
        """
        try:
            await self._rate_limiter.acquire()  # Rate limit emails
            msg = MIMEMultipart()
            msg["From"] = self.from_email
            msg["To"] = self.to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(message, "plain"))

            client = await self._get_client()
            await client.send_message(msg)
        except Exception as e:
            print(f"Failed to send email alert: {e}")
            return False
        else:
            return True

    async def __aenter__(self) -> "EmailAlertBackend":
        """Async context manager entry."""
        await self._get_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()


class MockAlertBackend:
    """Mock alert backend for testing."""

    async def send_alert(self, subject: str, message: str) -> bool:
        """Print the alert to console instead of sending it.

        Args:
            subject: Alert subject
            message: Alert message

        Returns:
            Always returns True
        """
        print("\n=== MOCK ALERT ===")
        print(f"Subject: {subject}")
        print("Message:")
        print(message)
        print("================\n")
        return True


class AlertManager:
    """Manages sending alerts through configured backends."""

    def __init__(self, backend: Optional[AlertBackend] = None):
        """Initialize the alert manager.

        Args:
            backend: Optional alert backend. Defaults to MockAlertBackend
        """
        self.backend = backend or MockAlertBackend()

    async def send_change_alert(self, url: str, query: str, summary: str) -> bool:
        """Send an alert about a relevant change.

        Args:
            url: The URL that changed
            query: The original search query
            summary: Summary of the changes

        Returns:
            True if the alert was sent successfully
        """
        subject = f"AmbiAlert Update: New information about '{query}'"
        message = f"""
        Hello!

        We've detected relevant changes related to your query: "{query}"

        URL: {url}

        What's New:
        {summary}

        Best regards,
        Your AmbiAlert System
        """

        return await self.backend.send_alert(subject, message.strip())
