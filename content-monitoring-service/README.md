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

## API Endpoints

- `GET /health` - Health check
- `POST /monitor` - Start monitoring a URL
- `GET /monitor/{source_id}/status` - Get monitoring status
- `POST /process` - Manually trigger content processing