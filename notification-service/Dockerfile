FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml README.md ./

# Create necessary directories and files for package
RUN mkdir -p api schemas services && \
    touch __init__.py api/__init__.py schemas/__init__.py services/__init__.py

# Install dependencies
RUN uv venv && uv sync --no-dev

# Copy application code
COPY . .

# Expose port
EXPOSE 8002

# Run the application
CMD ["uv", "run", "python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]