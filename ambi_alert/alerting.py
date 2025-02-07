"""Alerting system module."""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, Protocol


class AlertBackend(Protocol):
    """Protocol for alert backends."""

    def send_alert(self, subject: str, message: str) -> bool:
        """Send an alert with the given subject and message."""
        ...


class EmailAlertBackend:
    """Email-based alert backend."""

    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str, from_email: str, to_email: str):
        """Initialize the email alert backend.

        Args:
            smtp_server: SMTP server hostname
            smtp_port: SMTP server port
            username: SMTP authentication username
            password: SMTP authentication password
            from_email: Sender email address
            to_email: Recipient email address
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.to_email = to_email

    def send_alert(self, subject: str, message: str) -> bool:
        """Send an email alert.

        Args:
            subject: Email subject
            message: Email body

        Returns:
            True if the email was sent successfully
        """
        try:
            msg = MIMEMultipart()
            msg["From"] = self.from_email
            msg["To"] = self.to_email
            msg["Subject"] = subject

            msg.attach(MIMEText(message, "plain"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
        except Exception as e:
            print(f"Failed to send email alert: {e}")
            return False
        else:
            return True


class MockAlertBackend:
    """Mock alert backend for testing."""

    def send_alert(self, subject: str, message: str) -> bool:
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

    def send_change_alert(self, url: str, query: str, summary: str) -> bool:
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

        return self.backend.send_alert(subject, message.strip())
