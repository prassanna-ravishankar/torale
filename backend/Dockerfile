FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

# ---- SYSTEM DEPENDENCIES ----
# Installed first as they rarely change
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    procps \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ---- UV CONFIGURATION ----
# Enable bytecode compilation for faster startup
ENV UV_COMPILE_BYTECODE=1
# Copy from cache instead of linking (required for mounted volumes)
ENV UV_LINK_MODE=copy

# ---- DEPENDENCY CACHE LAYER ----
# Only copy lockfiles - this layer is cached until dependencies change
# Code changes won't invalidate this layer, making rebuilds much faster
COPY pyproject.toml uv.lock ./

# Install dependencies without installing the project itself
# This creates .venv with all dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# ---- APPLICATION CODE ----
# Copy source code - this layer invalidates on any code change
# But since dependencies are already installed above, this is fast
COPY . /app

# Install the project itself (links to already-installed dependencies)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# ---- RUNTIME CONFIGURATION ----
# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Disable Python output buffering for better logging
ENV PYTHONUNBUFFERED=1

# Default command (can be overridden)
CMD ["uvicorn", "torale.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
