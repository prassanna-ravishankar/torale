# Next-Gen Backend Plan

## Current Status (YYYY-MM-DD - Replace with actual date)

This document has been updated to reflect the initial implementation phase. Many foundational components, services, schemas, models, and API endpoints have been scaffolded or implemented as initial versions. Key areas like concrete AI client implementations, robust dependency injection for AI models, background task scheduling, and comprehensive testing are part of the next steps or subsequent iterations.

**Key achievements in this iteration:**
*   Core service skeletons and initial logic (`SourceDiscoveryService`, `ContentIngestionService`, `ChangeDetectionService`).
*   `AIModelInterface` definition.
*   Database models (SQLAlchemy) for all planned entities.
*   Pydantic schemas for API requests/responses and data validation.
*   API endpoints for source discovery, monitored source management, and alert management.
*   Basic database setup (`core/db.py`) and configuration (`core/config.py`) updates.
*   FastAPI application (`main.py`) updated with new routers and DB initialization.
*   Legacy services (`MonitorService`, `EmbeddingService`) removed.

## Overview

This document outlines the plan for the second generation of the backend system. The system is designed to monitor web content for changes based on user queries. It will consist of several microservices, each with a distinct responsibility, and will feature an abstraction layer for AI model interactions to allow for flexibility in choosing AI providers, all while adhering to principles of elegance and simplicity (KISS).

## Core Services

The backend will be composed of the following core services:

### 1. Source Discovery Service

*   **Status:** Implemented (Initial Version - `app/services/source_discovery_service.py`)
*   **Purpose:** Takes an initial, potentially broad user query, refines it into a focused search query, and then identifies one or more stable, central webpages (URLs) that are likely to be updated when new, relevant information pertaining to the query appears.
*   **Input:** Raw user query (e.g., "discounts in tkmaxx").
*   **Output:** A list of monitorable URLs (e.g., `["tkmaxx.com/uk/en/offers"]`).
*   **Initial AI Provider:** Perplexity API.
*   **Details:** This service combines two conceptual steps. Internally, it will first use the AI model (via `AIModelInterface.refine_query()`) to transform the raw query into a refined query string. Then, it will use the AI model again (via `AIModelInterface.identify_sources()`) with this refined query to find canonical URLs, prioritizing official pages or reputable hubs.

### 2. Content Ingestion Service

*   **Status:** Implemented (Initial Version - `app/services/content_ingestion_service.py`)
*   **Purpose:**
    *   Scrapes the content from the URLs identified by the Source Discovery Service.
    *   Generates embeddings for the scraped content.
    *   Stores the scraped content and its embeddings for later comparison.
*   **Input:** A list of monitorable URLs (from Source Discovery Service).
*   **Output:** Stored data including raw scraped content, processed text, and content embeddings. (Specific storage mechanism TBD - e.g., vector database, simple file/DB storage initially, leaning on simplicity first).
*   **Initial AI Provider (for Embeddings):** OpenAI API.
*   **Details:**
    *   **Scraping:** Basic scraping implemented; robust capabilities to be enhanced.
    *   **Preprocessing:** Text cleaning and preprocessing before embedding generation.
    *   **Embedding:** Use an embedding model (e.g., OpenAI's text-embedding models via `AIModelInterface.generate_embeddings()`) to convert content into vector representations.
    *   **Storage:** Decide on a storage solution for raw content, processed text, embeddings, and timestamps of scrapes. Prioritize the simplest viable solution initially.
    *   Consider idempotency for storage and retry mechanisms.

### 3. Change Detection Service

*   **Status:** Implemented (Initial Version - `app/services/change_detection_service.py`)
*   **Purpose:** Compares the embeddings of content scraped at different intervals to detect significant and relevant changes on the monitored websites.
*   **Input:**
    *   Current content embeddings (from a recent scrape by Content Ingestion Service).
    *   Previous content embeddings (from a past scrape by Content Ingestion Service for the same URL).
*   **Output:** A notification or flag indicating a significant change, potentially with a summary of the detected change.
*   **Initial AI Provider (for Diff Analysis/Summarization, if needed):** OpenAI API.
*   **Details:**
    *   **Comparison:** Implement a method to compare embedding vectors (e.g., cosine similarity, Euclidean distance).
    *   **Thresholding:** Define thresholds to determine what constitutes a "significant" change.
    *   **Change Interpretation (Optional):** Potentially use an LLM (e.g., from OpenAI via `AIModelInterface.analyze_diff()`) to summarize or interpret the nature of the detected changes if simple embedding diff is not sufficient.

## AI Model Abstraction Layer

*   **Status:** Interface Defined; Concrete Clients Skeletonized.
*   **Goal:** To decouple the core service logic from specific AI model implementations (Perplexity, OpenAI, etc.), allowing for easier swapping of AI providers. This approach will use a single, comprehensive interface for all AI-related tasks, focusing on clarity and maintainability.
*   **Approach:**
    *   Define a single Python Abstract Base Class (ABC) named `AIModelInterface(ABC)` in `app/services/ai_integrations/interface.py`. **[Implemented]**
    *   The `AIModelInterface` will declare abstract methods for all identified AI tasks. These methods should preferably be asynchronous (`async def`) due to the I/O-bound nature of AI API calls: **[Implemented]**
        *   `async def refine_query(self, raw_query: str, **kwargs) -> str:`
        *   `async def identify_sources(self, refined_query: str, **kwargs) -> List[str]:`
        *   `async def generate_embeddings(self, texts: List[str], **kwargs) -> List[List[float]]:`
        *   `async def analyze_diff(self, old_representation: Any, new_representation: Any, **kwargs) -> Dict:` (e.g., returning a structured diff or summary).
    *   Concrete AI client classes (e.g., `PerplexityClient`, `OpenAIClient` located in `app/services/ai_integrations/`) will inherit from and implement this single `AIModelInterface`. **[Skeletons Created]**
        *   These client implementations are responsible for handling provider-specific API errors (e.g., network issues, rate limits) gracefully, potentially translating them into a limited set of application-specific exceptions.
    *   **Handling Unsupported Features:** For any method in `AIModelInterface` that a specific concrete client does not support, the implementation of that method within the client must raise a `NotImplementedError`.
    *   Services will use dependency injection to receive an instance of `AIModelInterface`.
    *   **Service Responsibility & DI Configuration:** **[Initial setup in API endpoints with placeholders; full DI configuration pending full client implementation]**
        *   The Dependency Injection (DI) mechanism should be configured to provide each service with an `AIModelInterface` instance (i.e., a *specific* concrete AI client) that *is known* to support the methods that particular service critically depends on for its core functionality. This minimizes the need for extensive runtime capability checks or broad `NotImplementedError` handling within the service's primary logic.
        *   Services should only call methods confirmed to be supported by the configured provider for their task or be prepared to catch and handle `NotImplementedError` for auxiliary/optional functionalities.
    *   The `**kwargs` in interface methods allow for passing provider-specific parameters. Consider explicitly naming common, high-level parameters if they exist across providers for a given method, reserving `**kwargs` for truly optional, provider-specific tuning.
    *   This approach centralizes all AI operations into one interface. When an external AI provider's API changes, modifications are primarily contained within the specific client class for that provider.

## Data Flow (Conceptual - Requires New Query Handling)

*   **Status:** Components for URL-based flow exist. Query-based flow needs new components.
1.  **User submits a monitoring query** via the new `/alerts/new` page.
2.  **New API Endpoint** (`POST /user-queries/`) receives the query and configuration hints, saving a `UserQuery` record (status: `pending_discovery`).
3.  **Background Task/Trigger (Iteration 2):** Detects new `UserQuery` records.
4.  For each new `UserQuery`, invoke **Source Discovery Service**:
    *   Takes the user query text.
    *   Refines it and identifies monitorable URLs.
5.  For each discovered URL:
    *   Create a `MonitoredSource` record, linking it to the original `UserQuery` and applying configuration hints.
6.  **Content Ingestion Service** (triggered by background task scheduler):
    *   Finds `MonitoredSource` records needing checks.
    *   Scrapes content from the associated URL.
    *   Generates embeddings.
    *   Stores content and embeddings with timestamps.
7.  **Change Detection Service** (triggered at intervals or after new scrapes):
    *   Retrieves current and previous embeddings for a `MonitoredSource` URL.
    *   Compares embeddings to detect changes.
    *   If a significant change is detected, creates a `ChangeAlert` record linked to the `MonitoredSource`.

## Integration with Existing `backend/app` Structure

*   **Status:** Largely Implemented, requires additions for User Query flow.
*   **`app/api/`**:
    *   New API endpoint modules will be created/updated:
        *   `app/api/endpoints/user_queries.py`: **[NEW]** Endpoints for submitting and managing monitoring tasks/queries (e.g., `POST /user-queries/`).
        *   `app/api/endpoints/source_discovery.py`: Endpoints for *direct* source discovery (if needed), potentially refactored to be primarily used internally by the User Query flow. **[Exists - Review Use Case]**
        *   `app/api/endpoints/monitoring.py`: Endpoints for managing individual `MonitoredSource` records and retrieving `ChangeAlert` records. **[Exists - Primarily for internal/admin use or viewing results]**
*   **`app/services/`**:
    *   Existing services remain crucial:
        *   `app/services/source_discovery_service.py` **[Exists - Used by User Query Flow]**
        *   `app/services/content_ingestion_service.py` **[Exists - Monitors sources created by User Query Flow]**
        *   `app/services/change_detection_service.py` **[Exists - Detects changes for sources created by User Query Flow]**
    *   AI Model Abstraction Layer: **[Exists - Used by Services]**
        *   `app/services/ai_integrations/interface.py`
        *   `app/services/ai_integrations/perplexity_client.py`
        *   `app/services/ai_integrations/openai_client.py`
*   **`app/schemas/`**:
    *   New/Updated Pydantic schemas:
        *   `app/schemas/user_query_schemas.py`: **[NEW]** Schemas for the user query/task itself (`UserQueryCreate`, `UserQueryInDB`).
        *   `source_discovery_schemas.py`. **[Exists]**
        *   `content_schemas.py`. **[Exists]**
        *   `alert_schemas.py`. **[Exists]**
        *   `monitoring_schemas.py`. **[Exists - Primarily for `MonitoredSource`]**
*   **`app/models/`**:
    *   New/Updated models:
        *   `app/models/user_query_model.py`: **[NEW]** SQLAlchemy model for `UserQuery`.
        *   `MonitoredSource`, `ScrapedContent`, `ContentEmbedding`, `ChangeAlert`. **[Exist]**
*   **`app/core/`**: **[Exists - Updates likely minimal]**
    *   `app/core/config.py`
    *   `app/core/db.py`
*   **`app/main.py`**: **[Exists - Needs new router]**
    *   Update to include the new `user_queries` API router.

## Consolidated Iteration 1: Query-Based Monitoring & Core Service Refinement

*   **Define User Query Model (`app/models/user_query_model.py`):** ✅
    *   Status: **Completed**. All fields added and model tested.
    *   *Task: Complete the SQLAlchemy model `UserQuery` with all necessary fields.*
*   **Define User Query Schemas (`app/schemas/user_query_schemas.py`):** ✅
    *   Status: **Completed**. Schemas created and tested.
    *   *Task: Create Pydantic schemas (`UserQueryCreate`, `UserQueryInDB`, etc.) for `UserQuery` data.*
*   **Implement User Query API Endpoint (`app/api/endpoints/user_queries.py`):** ✅
    *   Status: **Completed**. Endpoint implemented, tested, and router added to `main.py`.
    *   *Task: Create a `POST /user-queries/` endpoint to save a new `UserQuery` (status: `pending_discovery`). Add router to `main.py`.*
*   **Update Frontend API Call:** ✅
    *   Status: **Done**. Frontend prepares payload for the new endpoint (call is placeholder).
*   **Database Migration/Creation for `user_queries` table:** ✅
    *   Status: **Done**. Model complete; schema managed via test setup/SQLAlchemy create_all.
    *   *Task: Ensure DB schema matches the complete `UserQuery` model.*
*   **Connect User Query to Discovery:** ✅
    *   Status: **Completed**. Implemented via `UserQueryProcessingService` and background task in API; tested.
    *   *Task: Implement logic to trigger `SourceDiscoveryService` for new `UserQuery` records and create corresponding `MonitoredSource` records.*
*   **Full AI Client Implementation (`perplexity_client.py`, `openai_client.py`):** ✅
    *   Status: **Completed**. Reviewed, tested, and appear functional for the current scope.
    *   *Task: Review and complete AI client implementations.*
*   **Refine Dependency Injection for AI Models:** ✅
    *   Status: **Completed**. Reviewed and tested via endpoint dependencies.
    *   *Task: Ensure correct AI client injection via DI based on config.*
*   **Robust Scraping Enhancements (`ContentIngestionService`):** 🟡
    *   Status: **Ongoing/Planned**.
    *   *Task: Iteratively improve scraping capabilities.*
*   **Refine Preprocessing Logic (`ContentIngestionService`):** 🟡
    *   Status: **Ongoing/Planned**.
    *   *Task: Implement/enhance text cleaning and preprocessing.*
*   **Comprehensive Testing (Phase 1):** ✅
    *   Status: **Completed**. Tests written and debugged for Iteration 1 components.
    *   *Task: Write/expand unit and integration tests for new/modified components.*
*   **Logging Implementation:** ✅
    *   Status: **Largely Done**.
    *   *Task: Ensure consistent logging and remove any remaining `print` statements.*


## Iteration 2: Production Readiness & Scaling (Formerly Iteration 3)

*   **Background Task Management:**
    *   Implement a robust mechanism (e.g., Celery) for:
        *   Triggering the "Connect User Query to Discovery" logic periodically.
        *   Periodic content ingestion by `ContentIngestionService`.
        *   Triggering `ChangeDetectionService` after ingestion.
*   **Scalability Enhancements:** Design services to be scalable independently.
*   **Advanced Error Handling & Resilience:** Implement robust error handling, retries, dead-letter queues.
*   **Monitoring & Observability:** Integrate comprehensive application monitoring and logging dashboards.
*   **Storage Solutions Evolution:**
    *   Evaluate and potentially migrate to a dedicated vector database.
*   **Configuration Management Refinement:** Centralize and manage configurations robustly.
*   **User Interface/API for Notifications:** Develop or integrate a system for user notifications.
*   **Comprehensive Testing (Phase 2):**
    *   End-to-end tests.
    *   Performance and load tests.
*   **Security Hardening:** Conduct security reviews.
*   **Deployment & CI/CD:** Mature deployment scripts and CI/CD pipelines.


## Original Future Considerations (Review and merge into Iterations above)
*   **Scalability:** [Merged into Iteration 2]
*   **Error Handling & Resilience:** [Merged into Iteration 2]
*   **Monitoring & Logging:** [Merged into Iteration 1 & 2]
*   **Storage Solutions:** [Merged into Iteration 2]
*   **Configuration Management:** [Merged into Iteration 2]
*   **User Interface/API:** [Merged into Iteration 2]

**Key:**
*   ✅ Done
*   ⚠️ Partially Done / Needs Review / Incomplete
*   ❌ Not Started
*   🟡 Ongoing/Planned (iterative task)
