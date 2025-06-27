# Notification Service Deployment

## Overview

The Notification Service is a microservice responsible for handling multi-channel notifications in the Torale system. Currently supports email notifications via SendGrid.

## Architecture

- **Framework**: FastAPI
- **Port**: 8002
- **Dependencies**: SendGrid for email delivery
- **Logging**: Structured JSON logging with structlog

## API Endpoints

### Health Check
- `GET /health` - Service health status

### Notifications
- `POST /api/v1/notify/email` - Send email notification
- `POST /api/v1/notify/alert` - Send change alert (backward compatible)

## Environment Variables

- `SENDGRID_API_KEY` - SendGrid API key (required)
- `LOG_LEVEL` - Logging level (default: INFO)
- `CORS_ORIGINS` - Allowed CORS origins (default: *)

## Running Locally

```bash
# Install dependencies
uv sync

# Run the service
uv run python -m uvicorn main:app --reload --port 8002

# Test the service
uv run python test_service.py
```

## Docker Deployment

```bash
# Build the image
docker build -t notification-service .

# Run with docker-compose
docker-compose up notification-service
```

## Integration with Backend

The backend service can use the notification service in two ways:

1. **Microservice Mode**: When `NOTIFICATION_SERVICE_URL` is set, the backend will use the HTTP client to communicate with this service.

2. **Legacy Mode**: When `NOTIFICATION_SERVICE_URL` is not set, the backend falls back to the embedded notification service.

## Future Enhancements

- Webhook delivery support
- SMS notifications
- Push notifications
- Retry logic with exponential backoff
- Delivery status tracking
- Template management
- Bulk notification support