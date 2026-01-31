FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

# System deps: curl for health checks, nodejs+npm for perplexity MCP (npx)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    nodejs \
    npm \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (cache layer)
COPY torale-agent/pyproject.toml torale-agent/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy agent source and install project
COPY torale-agent/ .
RUN uv sync --frozen --no-dev

CMD [".venv/bin/uvicorn", "agent:app", "--host", "0.0.0.0", "--port", "8000"]
