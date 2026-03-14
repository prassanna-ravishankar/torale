FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

# System deps: curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
  && rm -rf /var/lib/apt/lists/*

# Install Lightpanda headless browser for JS-rendered page fetching
RUN curl -L -o /usr/local/bin/lightpanda \
    https://github.com/lightpanda-io/browser/releases/download/nightly/lightpanda-x86_64-linux \
  && chmod a+x /usr/local/bin/lightpanda

WORKDIR /app

# Install Python deps first (cache layer)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy agent source and install project
COPY . .
RUN uv sync --frozen --no-dev

RUN useradd -m agent && chown -R agent:agent /app
USER agent

CMD [".venv/bin/uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
