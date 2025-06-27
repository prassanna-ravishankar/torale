# Notification Service

Microservice for handling all notification-related functionality in Torale, including email notifications, preference management, and background processing.

## Overview

The Notification Service is responsible for:
- Sending email notifications via SendGrid
- Managing user notification preferences
- Background processing of pending notifications with retry logic
- Maintaining notification logs and statistics
- Providing APIs for notification management

## API Endpoints

### Send Notification
- `POST /api/v1/notify` - Send an email notification
- `POST /api/v1/notify/manual` - Manually trigger notification for an alert
- `POST /api/v1/process/{alert_id}` - Process a specific alert notification

### Preferences Management
- `GET /api/v1/preferences/{user_id}` - Get user notification preferences
- `PUT /api/v1/preferences/{user_id}` - Update user notification preferences

### Monitoring & Logs
- `GET /api/v1/stats/{user_id}` - Get notification statistics for a user
- `GET /api/v1/logs/{user_email}` - Get notification logs
- `GET /api/v1/queue/status` - Get notification queue status

### Alert Management
- `POST /api/v1/alerts/{alert_id}/mark-notified` - Mark an alert as notified

### Health & Info
- `GET /health` - Health check endpoint
- `GET /` - Service information

## Running Locally

1. Create a `.env` file:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SENDGRID_API_KEY=your_sendgrid_api_key
LOG_LEVEL=INFO
```

2. Install dependencies:
```bash
uv sync
```

3. Run the service:
```bash
uv run python -m uvicorn main:app --reload --port 8003
```

## Docker

Build and run with Docker:
```bash
docker build -t notification-service .
docker run -p 8003:8003 --env-file .env notification-service
```

## Architecture

The service consists of:
- **SupabaseNotificationService**: Core notification logic
- **NotificationProcessor**: Background processor for queue management
- **FastAPI Application**: REST API endpoints
- **Supabase Integration**: Database operations and auth

## Background Processing

The service runs three background tasks:
1. **Pending Notifications**: Processes unnotified alerts every 30 seconds
2. **Retry Failed**: Retries failed notifications (up to 3 attempts) every 5 minutes
3. **Cleanup**: Removes logs older than 30 days once daily

## Integration

The notification service integrates with:
- **Supabase**: Database and authentication
- **SendGrid**: Email delivery
- **Main Backend**: Receives notification requests via HTTP

## Environment Variables

- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_KEY`: Supabase service role key
- `SENDGRID_API_KEY`: SendGrid API key for email sending
- `LOG_LEVEL`: Logging level (default: INFO)
- `HOST`: Service host (default: 0.0.0.0)
- `PORT`: Service port (default: 8003)