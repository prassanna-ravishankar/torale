FROM python:3.12-slim

WORKDIR /app

# Install system dependencies including build tools for cryptography
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Install minimal dependencies for testing
RUN uv pip install --system fastapi uvicorn[standard]

# Copy source code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run the simple application
CMD ["uvicorn", "app.main_simple:app", "--host", "0.0.0.0", "--port", "8000"]