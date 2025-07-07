# Torale Backend

The backend service for Torale, a natural language-powered alerting service that monitors websites and content sources for meaningful changes.

## Features

- Natural language query parsing
- Website content monitoring
- Semantic change detection using embeddings
- Email notifications
- RESTful API
- Async operations
- SQLite database (can be extended to PostgreSQL)

## Prerequisites

- Python 3.9+
- uv (installed system-wide)
- SendGrid API key for email notifications

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/torale.git
cd torale/backend
```

2. Create virtual environment:

```bash
uv venv
```

3. Install dependencies:

```bash
uv sync --all-extras --dev
```

4. Copy the environment file and update with your settings:

```bash
cp .env.example .env
```

## Configuration

Update the `.env` file with your settings:

- `SENDGRID_API_KEY`: Your SendGrid API key for email notifications
- `DATABASE_URL`: Database connection URL (default: SQLite)
- Other settings as needed

## Development

1. Run the development server:

```bash
uv run uvicorn app.main:app --reload
```

2. Run tests:

```bash
uv run pytest
```

3. Run linting:

```bash
uv run ruff check .
```

4. Format code:

```bash
uv run ruff format .
```

## API Documentation

Once the server is running, you can access interactive API documentation via:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

The source of truth for the API contract is the "Service Contract" section below.

## Project Structure

```
backend/
├── app/
│   ├── api/            # API routes
│   ├── core/           # Core functionality
│   ├── models/         # Database models
│   ├── services/       # Business logic
│   └── utils/          # Utility functions
├── tests/              # Test files
├── .env.example        # Example environment file
├── pyproject.toml      # Project configuration
└── README.md          # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see LICENSE file for details

## Service Contract

The Backend service is the central API gateway for the Torale application. It orchestrates interactions between the user, the database, and other microservices (Discovery, Content Monitoring, Notification). It is responsible for managing user queries, monitored sources, alerts, and user notification preferences.

All API endpoints are prefixed with `/api/v1`. Authentication is handled via Supabase (JWTs in Authorization header).

### User Queries

Manages users' natural language queries.

*   **POST `/user-queries/`**
    *   **Function:** Creates a new user query.
    *   **Request Body:**
        ```json
        {
          "raw_query": "Latest news about renewable energy in Germany",
          "config_hints_json": { "priority": "high" }
        }
        ```
    *   **Response Body (201 Created):**
        ```json
        {
          "id": "generated-uuid-query-123",
          "user_id": "user-uuid-456",
          "raw_query": "Latest news about renewable energy in Germany",
          "config_hints_json": { "priority": "high" },
          "status": "active",
          "created_at": "2023-10-27T10:00:00Z",
          "updated_at": "2023-10-27T10:00:00Z"
        }
        ```
*   **GET `/user-queries/`**
    *   **Function:** Lists all queries for the authenticated user.
    *   **Query Parameters:** `skip` (int, default 0), `limit` (int, default 100).
    *   **Response Body (200 OK):**
        ```json
        [
          {
            "id": "generated-uuid-query-123",
            "user_id": "user-uuid-456",
            "raw_query": "Latest news about renewable energy in Germany",
            "config_hints_json": { "priority": "high" },
            "status": "active",
            "created_at": "2023-10-27T10:00:00Z",
            "updated_at": "2023-10-27T10:00:00Z"
          }
        ]
        ```
*   **GET `/user-queries/{query_id}`**
    *   **Function:** Retrieves a specific user query by its ID.
    *   **Response Body (200 OK):** (Similar to the POST response for a single query)
*   **DELETE `/user-queries/{query_id}`**
    *   **Function:** Deletes a specific user query.
    *   **Response Body (204 No Content):** (Empty response)

### Source Discovery

Handles discovery of monitorable URLs from user queries. This section describes endpoints that primarily orchestrate calls to the **Discovery Service**.

*   **POST `/discover-sources/`**
    *   **Function:** Takes a raw query and returns a list of suggested monitorable URLs. (Orchestrates a call to the Discovery Service).
    *   **Request Body:**
        ```json
        {
          "raw_query": "Updates from OpenAI blog"
        }
        ```
    *   **Response Body (200 OK):**
        ```json
        {
          "monitorable_urls": [
            "https://openai.com/blog",
            "https://openai.com/news"
          ]
        }
        ```

### Monitored Sources

Manages the specific sources (URLs) a user is monitoring.

*   **POST `/monitored-sources/`**
    *   **Function:** Creates a new monitored source for the authenticated user.
    *   **Request Body:**
        ```json
        {
          "url": "https://example.com/news",
          "name": "Example News",
          "check_interval_seconds": 3600,
          "source_type": "website",
          "keywords": ["update", "release"],
          "config": {"css_selector": ".article-content"},
          "user_query_id": "generated-uuid-query-123"
        }
        ```
    *   **Response Body (201 Created):**
        ```json
        {
          "id": "generated-uuid-source-789",
          "user_id": "user-uuid-456",
          "url": "https://example.com/news",
          "name": "Example News",
          "source_type": "website",
          "check_interval_seconds": 3600,
          "keywords_json": "[\"update\", \"release\"]",
          "config_json": "{\"css_selector\": \".article-content\"}",
          "status": "active",
          "user_query_id": "generated-uuid-query-123",
          "created_at": "2023-10-27T10:05:00Z",
          "updated_at": "2023-10-27T10:05:00Z",
          "is_deleted": false
        }
        ```
*   **GET `/monitored-sources/`**
    *   **Function:** Lists all monitored sources for the authenticated user.
    *   **Query Parameters:** `skip` (int, default 0), `limit` (int, default 100).
    *   **Response Body (200 OK):** (Array of monitored source objects, similar to the POST response)
*   **GET `/monitored-sources/{source_id}`**
    *   **Function:** Retrieves a specific monitored source by its ID.
    *   **Response Body (200 OK):** (Single monitored source object)
*   **PUT `/monitored-sources/{source_id}`**
    *   **Function:** Updates an existing monitored source.
    *   **Request Body:** (Similar to POST, but fields are optional)
        ```json
        {
          "name": "Updated Example News",
          "check_interval_seconds": 7200
        }
        ```
    *   **Response Body (200 OK):** (Updated monitored source object)
*   **DELETE `/monitored-sources/{source_id}`**
    *   **Function:** Soft-deletes a monitored source.
    *   **Response Body (204 No Content):** (Empty response)

### Alerts (Change Alerts)

Manages alerts generated when changes are detected in monitored sources.

*   **GET `/alerts/`** (Note: Path defined in `monitoring.router`)
    *   **Function:** Lists change alerts for the authenticated user.
    *   **Query Parameters:** `skip` (int, default 0), `limit` (int, default 100), `monitored_source_id` (string, optional), `is_acknowledged` (boolean, optional).
    *   **Response Body (200 OK):**
        ```json
        [
          {
            "id": "generated-uuid-alert-abc",
            "user_id": "user-uuid-456",
            "monitored_source_id": "generated-uuid-source-789",
            "detected_at": "2023-10-27T11:00:00Z",
            "change_summary": "New article posted: 'Important Update'",
            "change_details_json": {"title": "Important Update", "link": "https://example.com/news/important-update"},
            "is_acknowledged": false,
            "acknowledged_at": null
          }
        ]
        ```
*   **GET `/alerts/{alert_id}`**
    *   **Function:** Retrieves a specific change alert by its ID.
    *   **Response Body (200 OK):** (Single alert object)
*   **POST `/alerts/{alert_id}/acknowledge`**
    *   **Function:** Marks a change alert as acknowledged.
    *   **Response Body (200 OK):** (Updated alert object with `is_acknowledged: true`)

### Content Processing (Orchestration)

Endpoints to trigger processing of monitored sources. These endpoints orchestrate calls to the **Content Monitoring Service**.

*   **POST `/process-source/{source_id}`** (Note: Path defined in `monitoring.router`)
    *   **Function:** Triggers immediate content processing for a single monitored source. (Orchestrates a call to the Content Monitoring Service).
    *   **Response Body (200 OK):**
        ```json
        {
          "status": "processing_started", // Or similar status from Content Monitoring Service
          "source_id": "generated-uuid-source-789",
          "message": "Content processing initiated for source."
        }
        ```
*   **POST `/process-batch`** (Note: Path defined in `monitoring.router`)
    *   **Function:** Triggers batch processing for multiple monitored sources. (Orchestrates a call to the Content Monitoring Service).
    *   **Request Body:**
        ```json
        [
            "generated-uuid-source-789",
            "generated-uuid-source-xyz"
        ]
        ```
    *   **Response Body (200 OK):**
        ```json
        {
          "summary": "Batch processing initiated for 2 sources.", // Or similar from Content Monitoring Service
          "processed_ids": ["generated-uuid-source-789", "generated-uuid-source-xyz"],
          "errors": []
        }
        ```

### Notifications (Orchestration)

Manages user notification preferences and sending notifications. These endpoints primarily orchestrate calls to the **Notification Service**. The base path for these is `/notifications`.

*   **GET `/notifications/preferences`**
    *   **Function:** Gets the current user's notification preferences. (Orchestrates a call to the Notification Service).
    *   **Response Body (200 OK):**
        ```json
        {
          "user_id": "user-uuid-456",
          "user_email": "user@example.com",
          "email_enabled": true,
          "email_frequency": "immediate",
          "browser_enabled": true,
          "created_at": "2023-10-26T09:00:00Z",
          "updated_at": "2023-10-26T09:00:00Z"
        }
        ```
*   **PUT `/notifications/preferences`**
    *   **Function:** Updates the user's notification preferences. (Orchestrates a call to the Notification Service).
    *   **Request Body:**
        ```json
        {
          "email_enabled": false,
          "browser_enabled": true
        }
        ```
    *   **Response Body (200 OK):**
        ```json
        {
          "success": true,
          "message": "Notification preferences updated successfully"
        }
        ```
*   **GET `/notifications/stats`**
    *   **Function:** Gets notification statistics for the current user. (Orchestrates a call to the Notification Service).
    *   **Response Body (200 OK):** (Structure depends on Notification Service, e.g.)
        ```json
        {
          "total_sent": 10,
          "total_delivered": 9,
          "total_failed": 1
        }
        ```
*   **GET `/notifications/logs`**
    *   **Function:** Gets notification logs for the current user. (Orchestrates a call to the Notification Service).
    *   **Query Parameters:** `limit` (int, default 50), `offset` (int, default 0), `status_filter` (string, optional).
    *   **Response Body (200 OK):** (Array of log objects from Notification Service)
*   **POST `/notifications/send`**
    *   **Function:** Manually triggers sending/resending a notification for a specific alert. (Orchestrates a call to the Notification Service).
    *   **Request Body:**
        ```json
        {
          "alert_id": "generated-uuid-alert-abc",
          "force_resend": false
        }
        ```
    *   **Response Body (200 OK):**
        ```json
        {
          "success": true,
          "message": "Notification sent/queued successfully"
        }
        ```
*   **GET `/notifications/queue/status`** (Admin/Debug)
    *   **Function:** Gets the status of the notification queue. (Orchestrates a call to the Notification Service).
    *   **Response Body (200 OK):** (Status object from Notification Service)
*   **POST `/notifications/queue/process`** (Admin/Debug)
    *   **Function:** Manually triggers processing of the notification queue. (Orchestrates a call to the Notification Service).
    *   **Response Body (200 OK):** (Response from Notification Service)

### Health Check

*   **GET `/health`**
    *   **Function:** Returns the health status of the Backend service.
    *   **Response Body (200 OK):**
        ```json
        {
          "status": "healthy",
          "service": "torale-api"
        }
        ```
*   **GET `/supabase-test`**
    *   **Function:** Tests the connection to Supabase.
    *   **Response Body (200 OK if successful):**
        ```json
        {
            "status": "supabase_connected",
            "test_result": "success",
            "data_count": 123
        }
        ```
    *   **Response Body (Error if unsuccessful):**
        ```json
        {
            "status": "supabase_error",
            "test_result": "failed",
            "error": "Error message details"
        }
        ```