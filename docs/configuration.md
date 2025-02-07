# Configuration

AmbiAlert offers various configuration options to customize its behavior. This guide covers all available configuration methods.

## Command Line Options

When using the `ambi-alert` command-line tool, you can configure:

### Basic Options

- `query`: The search query to monitor (required)
- `--check-interval`: How often to check for updates (in seconds, default: 3600)
- `--db-path`: Path to the SQLite database file (default: "ambi_alert.db")

### Email Configuration

- `--smtp-server`: SMTP server hostname
- `--smtp-port`: SMTP server port
- `--smtp-username`: SMTP authentication username
- `--smtp-password`: SMTP authentication password
- `--from-email`: Sender email address
- `--to-email`: Recipient email address

Example:

```bash
ambi-alert "my query" \
    --check-interval 1800 \
    --db-path "/path/to/db.sqlite" \
    --smtp-server "smtp.gmail.com" \
    --smtp-port 587 \
    --smtp-username "user@gmail.com" \
    --smtp-password "app-password" \
    --from-email "alerts@domain.com" \
    --to-email "me@domain.com"
```

## Python API Configuration

When using the Python API, you can configure AmbiAlert through constructor parameters:

### AmbiAlert Class

```python
from ambi_alert import AmbiAlert
from ambi_alert.alerting import EmailAlertBackend

# Configure email backend
email_backend = EmailAlertBackend(
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    username="user@gmail.com",
    password="app-password",
    from_email="alerts@domain.com",
    to_email="me@domain.com"
)

# Configure AmbiAlert
ambi = AmbiAlert(
    model=None,  # Optional custom LLM model
    alert_backend=email_backend,
    db_path="ambi_alert.db",
    check_interval=3600  # 1 hour
)
```

### Custom Models

You can provide your own language model implementation:

```python
from smolagents import HfApiModel

# Configure custom model
model = HfApiModel(
    api_key="your-api-key",
    model_name="your-model"
)

# Use custom model
ambi = AmbiAlert(model=model)
```

### Custom Alert Backends

Implement your own alert backend by subclassing `AlertBackend`:

```python
from ambi_alert.alerting import AlertBackend

class SlackAlertBackend(AlertBackend):
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def send_alert(self, subject: str, message: str) -> bool:
        # Implement Slack notification logic
        ...
        return True

# Use custom backend
slack_backend = SlackAlertBackend("https://hooks.slack.com/...")
ambi = AmbiAlert(alert_backend=slack_backend)
```

## Environment Variables

AmbiAlert also supports configuration through environment variables:

- `AMBI_ALERT_DB_PATH`: Default database path
- `AMBI_ALERT_CHECK_INTERVAL`: Default check interval in seconds
- `AMBI_ALERT_SMTP_SERVER`: Default SMTP server
- `AMBI_ALERT_SMTP_PORT`: Default SMTP port
- `AMBI_ALERT_SMTP_USERNAME`: Default SMTP username
- `AMBI_ALERT_SMTP_PASSWORD`: Default SMTP password
- `AMBI_ALERT_FROM_EMAIL`: Default sender email
- `AMBI_ALERT_TO_EMAIL`: Default recipient email

Example:

```bash
export AMBI_ALERT_DB_PATH="/path/to/db.sqlite"
export AMBI_ALERT_CHECK_INTERVAL="1800"
export AMBI_ALERT_SMTP_SERVER="smtp.gmail.com"
# ... etc ...
```
