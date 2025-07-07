# Discovery Service

A standalone microservice that converts natural language queries into monitorable URLs using AI providers.

## 🎯 What it does

Transform queries like "latest updates from OpenAI" into a curated list of monitorable URLs like:
- `https://openai.com/blog`
- `https://openai.com/news`
- `https://platform.openai.com/docs/changelog`

## ⚡ Quick Start

```bash
# Setup
cp .env.example .env  # Add your PERPLEXITY_API_KEY
uv sync

# Run
uv run uvicorn main:app --reload --port 8001

# Test
curl -X POST http://localhost:8001/api/v1/discover \
  -H "Content-Type: application/json" \
  -d '{"raw_query": "Tesla stock updates"}'
```

## 🏗️ Architecture

**Stateless Microservice Design**
- FastAPI web framework
- Perplexity/OpenAI AI integration
- Structured logging with `structlog`
- Clean dependency injection
- RESTful API design

**Perfect for:**
- Horizontal scaling
- Independent deployment
- Container orchestration
- Multi-environment deployment

## 📡 Service Contract (API)

The Discovery Service is a specialized microservice that translates raw natural language queries into a list of relevant, monitorable URLs. It utilizes AI providers (like Perplexity or OpenAI) to find stable web pages (blogs, news sections, changelogs, etc.) that are likely to be updated when new information related to the query appears.

All API endpoints are prefixed with `/api/v1`.

### Discover Sources

*   **POST `/api/v1/discover`**
    *   **Function:** Takes a natural language query and returns a list of suggested monitorable URLs.
    *   **Request Body:**
        *   Content-Type: `application/json`
        ```json
        {
          "raw_query": "Latest advancements in quantum computing by Google"
        }
        ```
        *   Constraints: `raw_query` must be between 1 and 500 characters.
    *   **Response Body (200 OK):**
        *   Content-Type: `application/json`
        ```json
        {
          "monitorable_urls": [
            "https://ai.googleblog.com/",
            "https://quantumai.google/research",
            "https://cloud.google.com/blog/products/ai-machine-learning"
          ]
        }
        ```
        *   If no relevant URLs are found, it returns an empty list: `{"monitorable_urls": []}`.
    *   **Error Responses:**
        *   `422 Unprocessable Entity`: If the request body is invalid (e.g., `raw_query` is missing or too long).
            ```json
            {
              "detail": [
                {
                  "loc": ["body", "raw_query"],
                  "msg": "ensure this value has at least 1 characters",
                  "type": "value_error.any_str.min_length",
                  "ctx": {"limit_value": 1}
                }
              ]
            }
            ```
        *   `500 Internal ServerError`: If an unexpected error occurs during the discovery process (e.g., issue with the AI provider).
            ```json
            {
              "detail": "An error occurred while discovering sources: <error_message>"
            }
            ```

### Health Check

*   **GET `/health`** (Note: path is `/health`, not `/api/v1/health` as per `main.py`)
    *   **Function:** Standard health check endpoint. Useful for load balancers and service monitoring.
    *   **Request Body:** None.
    *   **Response Body (200 OK):**
        *   Content-Type: `application/json`
        ```json
        {
          "status": "healthy",
          "service": "discovery-service"
        }
        ```

## 🚀 Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for comprehensive deployment guides covering:
- Local development
- Docker containers
- Cloud platforms (Railway, Google Cloud Run, AWS ECS)
- Monitoring and scaling

## 🔧 Configuration

Required:
- `PERPLEXITY_API_KEY` - Your Perplexity API key

Optional:
- `AI_PROVIDER` - "perplexity" (default) or "openai"
- `SERVICE_PORT` - Port number (default: 8001)
- `LOG_LEVEL` - INFO, DEBUG, etc.

## 🎁 Integration

**Backend Integration:**
```python
# Backend automatically detects and uses this service
DISCOVERY_SERVICE_URL=http://localhost:8001
```

**Fallback Support:**
If service is unavailable, backend automatically falls back to legacy AI model approach.

Part of the [Torale](../README.md) microservices architecture.