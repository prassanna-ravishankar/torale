"""Command-line interface for AmbiAlert."""

import argparse
from typing import Optional

from .alerting import EmailAlertBackend
from .main import AmbiAlert


def create_alert_backend(args: argparse.Namespace) -> Optional[EmailAlertBackend]:
    """Create an email alert backend if credentials are provided."""
    if all([args.smtp_server, args.smtp_port, args.smtp_username, args.smtp_password, args.from_email, args.to_email]):
        return EmailAlertBackend(
            smtp_server=args.smtp_server,
            smtp_port=args.smtp_port,
            username=args.smtp_username,
            password=args.smtp_password,
            from_email=args.from_email,
            to_email=args.to_email,
        )
    return None


def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="AmbiAlert - Monitor the web for changes")

    # Add query argument
    parser.add_argument("query", help="The search query to monitor")

    # Add optional arguments
    parser.add_argument("--check-interval", type=int, default=3600, help="How often to check for updates (in seconds)")

    parser.add_argument("--db-path", default="ambi_alert.db", help="Path to the SQLite database")

    # Email configuration
    parser.add_argument("--smtp-server", help="SMTP server hostname")
    parser.add_argument("--smtp-port", type=int, help="SMTP server port")
    parser.add_argument("--smtp-username", help="SMTP authentication username")
    parser.add_argument("--smtp-password", help="SMTP authentication password")
    parser.add_argument("--from-email", help="Sender email address")
    parser.add_argument("--to-email", help="Recipient email address")

    args = parser.parse_args()

    # Create the alert backend if email configuration is provided
    alert_backend = create_alert_backend(args)

    # Create and run AmbiAlert
    ambi = AmbiAlert(alert_backend=alert_backend, db_path=args.db_path, check_interval=args.check_interval)

    # Add the query
    ambi.add_monitoring_query(args.query)

    # Run the monitor
    ambi.run_monitor()


if __name__ == "__main__":
    main()
