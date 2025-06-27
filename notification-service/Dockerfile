FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml ./
COPY uv.lock* ./

# Install dependencies
RUN uv sync --frozen

# Copy source code
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# Expose port
EXPOSE 8003

# Run the application
CMD ["uv", "run", "python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]