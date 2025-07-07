# Notification Service

Microservice for handling all notification functionality in Torale using NotificationAPI for multi-channel delivery.

## Overview

The Notification Service is responsible for:
- Sending multi-channel notifications via NotificationAPI (email, SMS, push, webhooks)
- User identification and preference management through NotificationAPI
- Integration with Torale's monitoring system to send change alerts
- Template-based notification delivery with merge tags

## Key Features

- **Multi-Channel Support**: Email, SMS, push notifications, webhooks via NotificationAPI
- **Template Management**: Uses NotificationAPI's template system for consistent messaging
- **User Management**: Automatic user identification and preference synchronization
- **Scalable Delivery**: Leverages NotificationAPI's infrastructure for reliable delivery
- **Analytics**: Built-in delivery tracking and analytics through NotificationAPI dashboard

## Service Contract (API)

The Notification Service centralizes the sending of notifications for the Torale application. It leverages NotificationAPI for multi-channel delivery (email, SMS, push, etc.) and template management. Its primary role is to receive requests to notify users about detected changes or other important events.

All API endpoints are prefixed with `/api/v1`, unless specified otherwise.

### Send Change Alert Notification

*   **POST `/api/v1/notify`** (Note: The `api/notifications.py` defines this as the primary send endpoint, the README's mention of `/api/v1/change-alert` might be an alias or older concept not present in the current router.)
    *   **Function:** Triggers a notification (typically a change alert) to a user via NotificationAPI. This endpoint is usually called by other backend services (e.g., the main Backend or Content Monitoring Service) when an event requiring user notification occurs.
    *   **Request Body (`SendNotificationRequest` schema):**
        *   Content-Type: `application/json`
        ```json
        {
          "user_id": "user-uuid-123", // Crucial for NotificationAPI user identification
          "user_email": "user@example.com",
          "query": "Updates on Project X",
          "target_url": "https://example.com/project-x-updates",
          "content": "A new entry titled 'Milestone Reached' was posted.",
          "alert_id": "alert-uuid-abc" // Optional, for tracking
        }
        ```
    *   **Response Body (`SendNotificationResponse` schema, 200 OK):**
        ```json
        {
          "success": true,
          "message": "Notification triggered successfully",
          "alert_id": "alert-uuid-abc"
        }
        ```
    *   **Error Responses:**
        *   `400 Bad Request`: If `user_id` is missing or other required fields are invalid.
            ```json
            {
              "detail": "user_id is required for NotificationAPI"
            }
            ```
        *   `500 Internal Server Error`: If there's an issue communicating with NotificationAPI or an unexpected internal error.
            ```json
            {
              "detail": "Failed to send notification: <error_message>"
            }
            ```
        *   `503 Service Unavailable`: If the `notification_service` instance is not initialized.

### Notification Preferences (Deprecated)

The following endpoints related to managing notification preferences directly through this service are **deprecated**. User preferences are now expected to be managed via NotificationAPI's own UI components or SDK, which the main frontend application would integrate.

*   **GET `/api/v1/preferences/{user_id}`** (Deprecated)
    *   **Response (410 Gone):**
        ```json
        {
            "message": "Notification preferences are now managed via NotificationAPI's UI components.",
            "user_id": "user-uuid-123"
        }
        ```
*   **PUT `/api/v1/preferences/{user_id}`** (Deprecated)
    *   **Response (410 Gone):** (Similar to the GET deprecated response)

### Health Check & Service Information

*   **GET `/health`** (Path defined in `main.py`)
    *   **Function:** Standard health check endpoint.
    *   **Request Body:** None.
    *   **Response Body (200 OK):**
        ```json
        {
          "status": "healthy",
          "service": "notification-service",
          "version": "0.2.0", // Example version
          "timestamp": "2023-10-27T12:00:00.000Z"
        }
        ```
*   **GET `/`** (Path defined in `main.py`, provides basic service info - not part of the formal contract but useful for discovery)
    *   **Function:** Returns basic information about the service.
    *   **Response Body (200 OK):** (Details may vary, typically info like service name, version)


## API Endpoints

_This section is maintained for historical context but the **Service Contract (API)** section above provides the canonical details._

### Send Notification
- `POST /api/v1/notify` - Send a notification using NotificationAPI. (Primary endpoint)
- `POST /api/v1/change-alert` - (Likely deprecated or an internal concept not directly exposed as a unique route in current code)

### Health & Info
- `GET /health` - Health check endpoint.
- `GET /` - Service information.

## NotificationAPI Integration

### Templates Required

Set up these notification templates in your NotificationAPI dashboard:

1. **torale_alert** - For content change notifications
   - **Parameters**: 
     - `{{query}}` - User's monitoring query
     - `{{target_url}}` - URL being monitored
     - `{{content}}` - Summary of changes detected
     - `{{alert_id}}` - Unique alert identifier
     - `{{dashboardLink}}` - Link to user dashboard

### User Identification

The service automatically identifies users to NotificationAPI with their email addresses, enabling:
- Email delivery to the correct address
- User preference management through NotificationAPI's UI
- Delivery tracking and analytics per user

## Running Locally

1. Create a `.env` file:
```env
NOTIFICATIONAPI_CLIENT_ID=your_client_id
NOTIFICATIONAPI_CLIENT_SECRET=your_client_secret
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8003
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
- **NotificationApiService**: Core notification logic using NotificationAPI
- **NotificationApiHttpClient**: HTTP client for NotificationAPI integration
- **FastAPI Application**: REST API endpoints
- **Template System**: Uses NotificationAPI's template management

## Migration from SendGrid

This service has been migrated from a custom SendGrid implementation to NotificationAPI:

### Benefits of NotificationAPI
- **Multi-Channel**: Support for email, SMS, push notifications, webhooks
- **Template Management**: Visual template editor with version control
- **Analytics**: Built-in delivery tracking and engagement metrics
- **User Preferences**: Hosted preference center for users
- **Scalability**: Enterprise-grade delivery infrastructure
- **Compliance**: Built-in unsubscribe and compliance features

### Legacy Methods
Some methods are deprecated and now handled by NotificationAPI:
- User preference management (use NotificationAPI's preference center)
- Notification logs (available in NotificationAPI dashboard)
- Delivery statistics (available in NotificationAPI analytics)

## Integration

The notification service integrates with:
- **NotificationAPI**: Multi-channel notification delivery
- **Main Backend**: Receives notification requests via HTTP
- **Content Monitoring Service**: Sends change alerts when content changes detected

## Environment Variables

- `NOTIFICATIONAPI_CLIENT_ID`: NotificationAPI client ID
- `NOTIFICATIONAPI_CLIENT_SECRET`: NotificationAPI client secret
- `LOG_LEVEL`: Logging level (default: INFO)
- `HOST`: Service host (default: 0.0.0.0)
- `PORT`: Service port (default: 8003)

## Setting Up NotificationAPI

1. **Create Account**: Sign up at [notificationapi.com](https://www.notificationapi.com)
2. **Get Credentials**: Navigate to Settings to get your client ID and secret
3. **Create Templates**: Set up notification templates with the required merge tags
4. **Configure Channels**: Enable and configure your preferred notification channels
5. **Customize Branding**: Update templates with your brand colors and messaging

## Testing

```bash
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=. --cov-report=term-missing

# Linting
uv run ruff check .
uv run ruff format .
```

## API Documentation

When the service is running, visit:
- http://localhost:8003/docs - Interactive API documentation
- http://localhost:8003/health - Health check endpoint