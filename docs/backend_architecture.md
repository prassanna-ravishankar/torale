# Backend Architecture

<div align="center">
  <img src="../frontend/public/torale-logo.svg" alt="Torale Logo" width="120" height="120"/>
</div>

## 1. Overview

The Torale backend is built with FastAPI and designed to monitor web content for meaningful changes based on user queries. It features a service-oriented architecture with a clear separation of concerns, an abstraction layer for AI model interactions to allow flexibility in choosing AI providers (e.g., Perplexity, OpenAI), and a PostgreSQL database managed via SQLAlchemy.

The system processes user queries to discover relevant web sources, periodically ingests content from these sources, detects significant changes using embedding comparisons, and generates alerts.

## 2. Core Components and Services

The backend is composed of several key services, models, schemas, and API endpoints.

### 2.1. Main Application (`app/main.py`)

*   Initializes the FastAPI application.
*   Sets up database connections and creates tables on startup (for development).
*   Includes API routers for different functionalities.
*   Configures CORS and other middleware.

### 2.2. Configuration (`app/core/config.py`)

*   Manages application settings and environment variables using Pydantic's `BaseSettings`.
*   Provides centralized access to configuration values like database URLs, API keys, etc.

### 2.3. Database (`app/core/db.py`)

*   Defines the SQLAlchemy engine and session management.
*   Provides utility functions for database interactions (e.g., `get_db` dependency for FastAPI).
*   Initializes database tables based on defined models.

### 2.4. Models (`app/models/`)

SQLAlchemy ORM models define the database schema:

*   **`UserQuery` (`user_query_model.py`):** Stores the initial query submitted by the user, its status (e.g., `pending_discovery`, `active`), and any configuration hints.
*   **`MonitoredSource` (`monitoring_models.py`):** Represents a specific URL that is being monitored for changes. It links to a `UserQuery` and includes details like the URL, check interval, and status (e.g., `active`, `paused`).
*   **`ScrapedContent` (`monitoring_models.py`):** Stores the raw and processed content scraped from a `MonitoredSource` at a specific time.
*   **`ContentEmbedding` (`monitoring_models.py`):** Stores the vector embeddings generated from the `ScrapedContent`.
*   **`ChangeAlert` (`alert_models.py`):** Records a detected significant change for a `MonitoredSource`, including a summary, details of the change, and its acknowledgment status.

### 2.5. Schemas (`app/schemas/`)

Pydantic schemas define the data structures for API requests and responses, ensuring data validation:

*   **`UserQuerySchema` (`user_query_schemas.py`):** Schemas for creating and representing `UserQuery` data (e.g., `UserQueryCreate`, `UserQueryInDB`).
*   **`MonitoredSourceSchema` (`monitoring_schemas.py`):** Schemas for `MonitoredSource` (e.g., `MonitoredSourceCreate`, `MonitoredSourceInDB`, `MonitoredSourceUpdate`).
*   **`AlertSchema` (`alert_schemas.py`):** Schemas for `ChangeAlert` (e.g., `ChangeAlertSchema`, `ChangeAlertCreate`).
*   **`SourceDiscoverySchema` (`source_discovery_schemas.py`):** Schemas for the source discovery process (e.g., `RawQueryInput`, `MonitoredURLOutput`).
*   **`ContentSchema` (`content_schemas.py`):** Schemas related to scraped content and embeddings.

### 2.6. Services (`app/services/`)

Contain the core business logic:

*   **`SourceDiscoveryService` (`source_discovery_service.py`):**
    *   **Purpose:** Takes a raw user query, refines it (using an AI model), and identifies stable, central webpages (URLs) relevant to the query.
    *   **Input:** Raw user query string.
    *   **Output:** A list of monitorable URLs.
    *   **Interaction:** Uses the `AIModelInterface` for query refinement and source identification.

*   **`ContentIngestionService` (`content_ingestion_service.py`):**
    *   **Purpose:** Scrapes content from monitored URLs, preprocesses it, generates embeddings, and stores the content and embeddings.
    *   **Input:** A list of monitorable URLs.
    *   **Output:** Stores `ScrapedContent` and `ContentEmbedding` records.
    *   **Interaction:** Uses web scraping libraries (e.g., BeautifulSoup, httpx) and the `AIModelInterface` for generating embeddings.

*   **`ChangeDetectionService` (`change_detection_service.py`):**
    *   **Purpose:** Compares embeddings of content scraped at different intervals to detect significant and relevant changes.
    *   **Input:** Current and previous content embeddings for a URL.
    *   **Output:** A `ChangeAlert` record if a significant change is detected.
    *   **Interaction:** Uses embedding comparison techniques (e.g., cosine similarity) and potentially the `AIModelInterface` for summarizing changes.

*   **`UserQueryProcessingService` (implicitly, logic within `user_queries.py` endpoint or a dedicated service):**
    *   **Purpose:** Orchestrates the flow after a new `UserQuery` is submitted. It triggers the `SourceDiscoveryService` and then creates `MonitoredSource` records based on the discovered URLs.
    *   **Interaction:** Called when a new `UserQuery` is created.

### 2.7. AI Model Abstraction Layer (`app/services/ai_integrations/`)

*   **Goal:** Decouples core service logic from specific AI model implementations, allowing for flexibility.
*   **`AIModelInterface` (`interface.py`):** An Abstract Base Class (ABC) defining methods for AI tasks like `refine_query`, `identify_sources`, `generate_embeddings`, and `analyze_diff`.
*   **Concrete Clients (e.g., `perplexity_client.py`, `openai_client.py`):** Implement the `AIModelInterface` for specific AI providers. They handle API calls, error handling, and provider-specific logic.
*   **Dependency Injection:** Services receive an instance of a configured `AIModelInterface` implementation.

### 2.8. API Endpoints (`app/api/endpoints/`)

FastAPI routers that expose the backend functionality:

*Note on Authentication: Based on a review of individual endpoint files (`monitoring.py`, `source_discovery.py`, `user_queries.py`) and `main.py`/`dependencies.py` (as of the last review), explicit JWT-based authentication dependencies were not observed directly on many of these routes. While frontend authentication is in place and JWTs are sent, securing these backend endpoints would typically involve FastAPI dependencies that verify the JWT. This might be planned, handled by a mechanism not yet identified in the reviewed files, or indicates that some routes may currently be open. This should be a key consideration for security hardening.*

*   **`user_queries.py`:**
    *   `POST /user-queries/`: Submits a new user query to start the monitoring process.
    *   (Future GET, PUT, DELETE for managing queries)
*   **`source_discovery.py`:**
    *   `POST /discover-sources/`: (Can be used directly, but primarily supports the `UserQuery` flow) Takes a raw query and returns suggested monitorable URLs.
*   **`monitoring.py`:**
    *   `POST /monitored-sources/`: Creates a new `MonitoredSource`.
    *   `GET /monitored-sources/`: Lists `MonitoredSource` records for the user.
    *   `GET /monitored-sources/{source_id}`: Retrieves a specific `MonitoredSource`.
    *   `PUT /monitored-sources/{source_id}`: Updates a `MonitoredSource`.
    *   `DELETE /monitored-sources/{source_id}`: Deletes a `MonitoredSource`.
*   **`alerts.py`:**
    *   `GET /alerts/`: Lists `ChangeAlert` records, with filtering options.
    *   `GET /alerts/{alert_id}`: Retrieves a specific `ChangeAlert`.
    *   `POST /alerts/{alert_id}/acknowledge`: Marks an alert as acknowledged.

## 3. Data Flow (Conceptual - Iteration 1 Focus)

1.  **User Submits Query:** Frontend sends a raw query to `POST /user-queries/`. A `UserQuery` record is created.
2.  **Source Discovery (Triggered by New UserQuery):**
    *   The `UserQueryProcessingService` (or logic within the endpoint) picks up the new `UserQuery`.
    *   It calls the `SourceDiscoveryService` with the raw query.
    *   `SourceDiscoveryService` uses an AI model (via `AIModelInterface`) to refine the query and identify canonical URLs.
    *   For each discovered URL, a `MonitoredSource` record is created, linked to the `UserQuery`.
3.  **Content Ingestion (Periodic Background Task - Future Iteration 2):**
    *   The `ContentIngestionService` finds `MonitoredSource` records due for a check.
    *   It scrapes content from the URL, preprocesses it.
    *   It uses an AI model (via `AIModelInterface`) to generate embeddings for the content.
    *   `ScrapedContent` and `ContentEmbedding` records are stored.
4.  **Change Detection (Periodic Background Task - Future Iteration 2):**
    *   The `ChangeDetectionService` retrieves the latest and previous embeddings for a `MonitoredSource`.
    *   It compares the embeddings.
    *   If a significant change is detected, a `ChangeAlert` record is created and linked to the `MonitoredSource`.
5.  **Alert Retrieval:** Frontend fetches alerts via `GET /alerts/` for display.

## 4. Architecture Diagram (Textual Representation)

```
+---------------------+      +-------------------------+      +---------------------+
| User (via Frontend)|----->| FastAPI (app/main.py)   |<---->| Database (SQLAlchemy)|
+---------------------+      |  - API Routers          |      |  - UserQuery        |
                             |  - Dependency Injection |      |  - MonitoredSource  |
                             +-------------------------+      |  - ScrapedContent   |
                                    |         ^               |  - ContentEmbedding |
                                    |         |               |  - ChangeAlert      |
                                    v         |               +---------------------+
       +-----------------------------------------------------------------------------+
       |                                Services (app/services/)                     |
       |-----------------------------------------------------------------------------|
       | UserQueryProcess | SourceDiscovery | ContentIngestion | ChangeDetection     |
       | (in user_queries)| Service         | Service          | Service             |
       +------------------+-----------------+------------------+---------------------+
               |                    |                 |                  |
               |                    V                 V                  V
               |      +---------------------------------------------------+
               |      | AI Model Abstraction Layer (app/services/ai_integrations) |
               |      |  - AIModelInterface                               |
               |      |  - PerplexityClient, OpenAIClient                 |
               |      +---------------------------------------------------+
               |                            |
               V                            V
+--------------------------+    +----------------------+
| (Creates MonitoredSource)|    | External AI Services |
| in DB                    |    | (Perplexity, OpenAI) |
+--------------------------+    +----------------------+

Key Interactions:
- API Routers delegate to Services.
- Services use Models (via SQLAlchemy session from `get_db`) to interact with the Database.
- Services use Schemas for data validation.
- Services performing AI tasks use the AIModelInterface.
- Background tasks (Iteration 2) will trigger ContentIngestion and ChangeDetection services.
```

## 5. Future Iteration 2 Considerations (Key Points)

*   **Background Task Management (e.g., Celery):** Crucial for automating periodic tasks like content ingestion and change detection.
*   **Scalability and Error Handling:** Enhancements to make services independently scalable and more resilient.
*   **Vector Database:** Potential migration for efficient storage and querying of embeddings. 