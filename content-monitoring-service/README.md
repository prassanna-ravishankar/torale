# Content Monitoring Service

Microservice for Torale that handles content scraping, change detection, and alert generation.

## Features

- Content scraping from monitored URLs
- Embedding generation for semantic comparison
- Change detection using vector similarity
- Background processing with scheduling
- Alert generation for detected changes

## Development

```bash
# Install dependencies
uv sync

# Start development server
uv run python -m uvicorn main:app --reload --port 8002

# Run tests
uv run pytest

# Linting
uv run ruff check .
uv run ruff format .
```

## Service Contract

The Content Monitoring Service is responsible for the core tasks of fetching content from specified URLs, processing this content (e.g., generating embeddings), detecting meaningful changes compared to previously fetched versions, and creating alerts when such changes are identified. It interacts with a Supabase backend for storing source information, content data, and alerts.

All API endpoints are prefixed with `/api/v1`.

### Health Check

*   **GET `/api/v1/health`**
    *   **Function:** Returns the health status of the Content Monitoring service.
    *   **Response Body (200 OK):**
        ```json
        {
          "status": "healthy",
          "service": "content-monitoring-service",
          "version": "0.1.0" // Example version
        }
        ```

### Content Processing

*   **POST `/api/v1/process-source/{source_id}`**
    *   **Function:** Initiates the processing of a single monitored source. This involves scraping content from the source's URL, comparing it against the last known version, and generating an alert if significant changes are detected. The `source_id` corresponds to an ID in the `monitored_sources` table in Supabase.
    *   **Path Parameters:**
        *   `source_id` (string, required): The unique identifier of the monitored source to process.
    *   **Request Body:** None.
    *   **Response Body (200 OK - Example: Changes Detected):**
        ```json
        {
          "source_id": "some-uuid-string",
          "status": "changes_detected",
          "alert_id": "alert-uuid-string", // ID of the newly created alert
          "summary": "Content changed: new headlines found.",
          "similarity": 0.85 // Example similarity score
        }
        ```
    *   **Response Body (200 OK - Example: No Changes):**
        ```json
        {
          "source_id": "some-uuid-string",
          "status": "no_changes",
          "message": "Content processed successfully, no significant changes detected"
        }
        ```
    *   **Response Body (200 OK - Example: Ingestion Failed):**
        ```json
        {
          "source_id": "some-uuid-string",
          "status": "ingestion_failed",
          "message": "Failed to scrape or process content"
        }
        ```
    *   **Error Responses:**
        *   `404 Not Found`: If the `source_id` does not correspond to an active monitored source.
        *   `500 Internal Server Error`: For unexpected errors during processing.

*   **POST `/api/v1/process-batch`**
    *   **Function:** Initiates processing for a list of monitored source IDs. This is a convenience endpoint to trigger multiple source checks.
    *   **Request Body:** A JSON array of source ID strings.
        ```json
        [
          "source-uuid-1",
          "source-uuid-2",
          "source-uuid-3"
        ]
        ```
    *   **Response Body (200 OK):**
        ```json
        {
          "summary": {
            "total_processed": 3,
            "changes_detected": 1,
            "no_changes": 1,
            "errors": 1,
            "ingestion_failed": 0
          },
          "results": [
            {
              "source_id": "source-uuid-1",
              "status": "changes_detected",
              "alert_id": "alert-uuid-abc",
              "summary": "New content found",
              "similarity": 0.7
            },
            {
              "source_id": "source-uuid-2",
              "status": "no_changes",
              "message": "Content processed successfully, no significant changes detected"
            },
            {
              "source_id": "source-uuid-3",
              "status": "error",
              "error": "Source URL returned 404"
            }
          ]
        }
        ```
    *   **Error Responses:**
        *   `400 Bad Request`: If the batch size exceeds the configured maximum.
        *   `500 Internal Server Error`: For unexpected errors during batch processing.

### Source Status

*   **GET `/api/v1/sources/{source_id}/status`**
    *   **Function:** Retrieves the current status and recent activity for a specific monitored source.
    *   **Path Parameters:**
        *   `source_id` (string, required): The unique identifier of the monitored source.
    *   **Response Body (200 OK):**
        ```json
        {
          "source": {
            "id": "some-uuid-string",
            "url": "https://example.com/news",
            "name": "Example News",
            "status": "active",
            // ... other fields from monitored_sources table
          },
          "recent_content": [
            {
              "id": "content-uuid-1",
              "scraped_at": "2023-10-27T10:00:00Z",
              "raw_content": "Snippet of content..." // Potentially truncated
            }
          ],
          "recent_alerts": [
            {
              "id": "alert-uuid-1",
              "detected_at": "2023-10-27T09:00:00Z",
              "change_summary": "Significant update detected.",
              "is_acknowledged": false
            }
          ],
          "last_processed": "2023-10-27T10:00:00Z",
          "alert_count": 1
        }
        ```
    *   **Error Responses:**
        *   `404 Not Found`: If the `source_id` does not exist.
        *   `500 Internal Server Error`: For unexpected errors.

### Queue Status

*   **GET `/api/v1/queue/status`**
    *   **Function:** Provides an overview of the monitoring system's status, including counts of active sources and recent processing activity.
    *   **Response Body (200 OK):**
        ```json
        {
          "active_sources": 150,
          "content_processed_24h": 3000,
          "alerts_generated_24h": 45,
          "pending_alerts": 10,
          "service_status": "operational"
        }
        ```
    *   **Error Responses:**
        *   `500 Internal Server Error`: For unexpected errors.
```