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

## Data Flow

*   **Status:** Components for this flow have been scaffolded. Actual execution requires full AI client implementation and background task scheduling (deferred).
1.  User submits an initial query.
2.  **Source Discovery Service** processes the raw query, refines it internally, and identifies monitorable URLs.
3.  Monitorable URLs are passed to **Content Ingestion Service**:
    *   Scrapes content from URLs.
    *   Generates embeddings.
    *   Stores content and embeddings with timestamps.
    *   This step is repeated at scheduled intervals.
4.  **Change Detection Service** (triggered at intervals or after new scrapes):
    *   Retrieves current and previous embeddings for a URL.
    *   Compares embeddings to detect changes.
    *   If a significant change is detected, an alert/notification is generated (implemented as `ChangeAlert` DB record).

## Integration with Existing `backend/app` Structure

*   **Status:** Largely Implemented.
*   **`app/api/`**:
    *   New API endpoint modules will be created here:
        *   `app/api/endpoints/source_discovery.py`: Endpoints for submitting raw queries and getting monitorable sources (handled by the `SourceDiscoveryService`). **[Implemented - Initial Version]**
        *   `app/api/endpoints/monitoring.py`: Endpoints for managing monitored sources (if manual management is needed) and retrieving change notifications/alerts. **[Implemented - Initial Version]**
*   **`app/services/`**:
    *   This will be the primary location for the business logic of the new services:
        *   `app/services/source_discovery_service.py` **[Implemented - Initial Version]**
        *   `app/services/content_ingestion_service.py` **[Implemented - Initial Version]**
        *   `app/services/change_detection_service.py` **[Implemented - Initial Version]**
    *   The **AI Model Abstraction Layer** will also reside here:
        *   `app/services/ai_integrations/interface.py`: Defines the `AIModelInterface(ABC)`. **[Implemented]**
        *   `app/services/ai_integrations/perplexity_client.py`: Implements `AIModelInterface` using the Perplexity API. **[Skeleton Created]**
        *   `app/services/ai_integrations/openai_client.py`: Implements `AIModelInterface` using the OpenAI API. **[Skeleton Created]**
*   **`app/schemas/`**:
    *   New Pydantic schemas will be added for requests and responses: **[Implemented]**
        *   Schemas for raw queries and lists of URLs (`source_discovery_schemas.py`).
        *   Schemas for scraped content, embeddings, and associated metadata (`content_schemas.py`).
        *   Schemas for change detection results and alerts (`alert_schemas.py`).
        *   Schemas for monitored source CRUD (`monitoring_schemas.py`).
*   **`app/models/`**:
    *   If using a relational database, new models: `UserQuery`, `MonitoredSource`, `ScrapedContent`, `ContentEmbedding`, `ChangeAlert`. **[Implemented using SQLAlchemy]**
    *   Vector database interaction logic, if used, might be encapsulated or linked from here/services. **[Deferred - Current uses JSON in SQL]**
*   **`app/core/`**:
    *   `app/core/config.py`: Updated for AI API keys, model selection for different tasks (which concrete AI client to inject for services). **[Implemented - Initial Version with placeholders]**
    *   `app/core/db.py`: Implemented for SQLAlchemy `Base`, `engine`, `SessionLocal`, `get_db`. **[Implemented]**
    *   Client initialization for AI services or a shared HTTP client. **[Placeholder DI in API endpoints; full initialization pending]**
*   **`app/main.py`**:
    *   Updated to include new API routers from `app/api/endpoints/`. **[Implemented]**
    *   May include initialization for background tasks (e.g., `ContentIngestionService` scheduler). **[Deferred to Iteration 2]**

## Iteration 1: Next Steps (Immediate Focus)

*   **Full AI Client Implementation:**
    *   Implement `PerplexityClient` in `app/services/ai_integrations/perplexity_client.py` to interact with the Perplexity API using API key from settings.
    *   Implement `OpenAIClient` in `app/services/ai_integrations/openai_client.py` to interact with OpenAI APIs (embeddings, chat completion for diff analysis) using API key from settings.
*   **Refine Dependency Injection for AI Models:**
    *   Update API endpoint dependencies (e.g., in `source_discovery.py`, `monitoring.py` if ChangeDetectionService uses AI for diff) to correctly instantiate and provide the configured `AIModelInterface` (e.g., `OpenAIClient` or `PerplexityClient`) based on `settings` from `config.py`.
*   **Robust Scraping Enhancements:**
    *   Improve `ContentIngestionService` scraping capabilities (e.g., handling different content types, better error handling, respecting `robots.txt`).
*   **Refine Preprocessing Logic:**
    *   Implement text cleaning and preprocessing in `ContentIngestionService` before embedding generation.
*   **Comprehensive Testing (Phase 1):**
    *   Unit tests for individual services, AI client interaction points (with mocking), and utility functions.
    *   Integration tests for API endpoints.
*   **Logging Implementation:**
    *   Replace all `print()` statements with a structured logging framework (e.g., Python's `logging` module).

## Iteration 2: Enhancements & Production Readiness (Future Work)

*   **Background Task Management:**
    *   Implement a robust mechanism for scheduling and running background tasks, especially for:
        *   Periodic content ingestion by `ContentIngestionService` for all monitored sources.
        *   Triggering `ChangeDetectionService` after new content is ingested.
    *   Consider tools like Celery, FastAPI's `BackgroundTasks`, or a dedicated scheduler service.
*   **Scalability Enhancements:** Design services to be scalable independently.
*   **Advanced Error Handling & Resilience:** Implement robust error handling, retries for external API calls and DB operations, and consider dead-letter queues.
*   **Monitoring & Observability:** Integrate comprehensive application monitoring and logging dashboards.
*   **Storage Solutions Evolution:**
    *   Evaluate and potentially migrate to a dedicated vector database for embeddings if performance with JSON in SQL becomes a bottleneck.
*   **Configuration Management Refinement:** Centralize and manage configurations more robustly, potentially using a dedicated service for dynamic configurations if needed.
*   **User Interface/API for Notifications:** Develop or integrate with a system for how users interact with and receive notifications beyond basic alert storage.
*   **Comprehensive Testing (Phase 2):**
    *   End-to-end tests.
    *   Performance and load tests.
*   **Security Hardening:** Conduct security reviews and implement necessary hardening measures.
*   **Deployment & CI/CD:** Mature deployment scripts and CI/CD pipelines.


## Original Future Considerations (Review and merge into Iterations above)
*   **Scalability:** Design services to be scalable independently. **[Moved to Iteration 2]**
*   **Error Handling & Resilience:** Robust error handling, retries, and dead-letter queues (beyond AI client specifics). **[Moved to Iteration 2]**
*   **Monitoring & Logging:** Comprehensive logging and monitoring. **[Logging to Iteration 1, Monitoring to Iteration 2]**
*   **Storage Solutions:** Phased approach to storage, starting simple. **[Partially addressed, vector DB to Iteration 2]**
*   **Configuration Management:** Centralized configuration. **[Refinement to Iteration 2]**
*   **User Interface/API:** How users interact and receive notifications. **[Moved to Iteration 2]**
