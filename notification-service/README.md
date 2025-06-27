# Notification Service

A microservice for handling multi-channel notifications in the Torale system.

## Features

- Email notifications via SendGrid
- RESTful API for sending notifications
- Structured logging
- Health check endpoint

## Development

```bash
# Install dependencies
uv sync

# Run the service
uv run python -m uvicorn app.main:app --reload --port 8002

# Run tests
uv run pytest
```

## API Endpoints

- `POST /api/v1/notify/email` - Send email notification
- `GET /health` - Health check endpoint

## Environment Variables

- `SENDGRID_API_KEY` - SendGrid API key for email delivery
- `LOG_LEVEL` - Logging level (default: INFO)