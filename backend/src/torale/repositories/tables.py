from pypika_tortoise import Table

# Define all database tables for PyPika queries
# These map to the actual PostgreSQL tables in the schema


class Tables:
    """Container for all database table definitions."""

    # User & Authentication
    users = Table("users")
    api_keys = Table("api_keys")
    email_verifications = Table("email_verifications")

    # Tasks & Executions
    tasks = Table("tasks")
    task_executions = Table("task_executions")
    task_templates = Table("task_templates")

    # Webhooks & Notifications
    webhooks = Table("webhooks")
    webhook_deliveries = Table("webhook_deliveries")
    notification_sends = Table("notification_sends")

    # Other
    waitlist = Table("waitlist")


# Singleton instance for easy imports
tables = Tables()
