# ruff: noqa: E501
from typing import Optional

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# HTTP Status Codes
HTTP_ACCEPTED = 202


class NotificationService:
    def __init__(self, api_key: Optional[str] = None):
        self.sendgrid_client = SendGridAPIClient(api_key)

    async def send_alert(
        self,
        user_email: str,
        query: str,
        target_url: str,
        content: str,
    ) -> bool:
        """Send an email alert to the user."""
        try:
            message = Mail(
                from_email="noreply@ambialert.com",
                to_emails=user_email,
                subject=f"Alert: Changes detected for '{query}'",
                html_content=f"""
                <h2>Changes Detected</h2>
                <p>We've detected changes in the content you're monitoring:</p>
                <p><strong>Query:</strong> {query}</p>
                <p><strong>URL:</strong> <a href="{target_url}">{target_url}</a></p>
                <hr>
                <h3>Updated Content:</h3>
                <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; max-width: 100%; overflow-wrap: break-word;">
                    {content[:1000]}...
                </div>
                """,
            )
            response = self.sendgrid_client.send(message)
            return response.status_code == HTTP_ACCEPTED
        except Exception as e:
            print(f"Error sending email alert: {e}")
            return False

    def _generate_email_content(self, query: str, target_url: str, content: str) -> str:
        """Generate HTML content for the email."""
        return f"""
        <html>
            <body>
                <h2>Changes Detected!</h2>
                <p>We've detected changes for your alert:</p>
                <p><strong>Query:</strong> {query}</p>
                <p><strong>URL:</strong> <a href="{target_url}">{target_url}</a></p>
                <hr>
                <h3>Updated Content:</h3>
                <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px;">
                    {content[:1000]}...
                </div>
                <p>
                    <small>
                        This is an automated alert from AmbiAlert.
                        You can manage your alerts at <a href="https://ambialert.com/dashboard">ambialert.com/dashboard</a>
                    </small>
                </p>
            </body>
        </html>
        """
