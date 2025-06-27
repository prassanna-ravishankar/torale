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

## 📡 API

### `POST /api/v1/discover`
**Input:**
```json
{"raw_query": "Python programming news"}
```

**Output:**
```json
{
  "monitorable_urls": [
    "https://www.python.org/blogs/",
    "https://pythonweekly.com/",
    "https://realpython.com/",
    "https://planet.python.org/",
    "https://pypi.org/project/pycodersweekly/"
  ]
}
```

### `GET /health`
Service health check for load balancers.

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