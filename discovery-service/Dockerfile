FROM python:3.12-slim

# Install uv
RUN pip install uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml .python-version uv.lock README.md ./

# Install dependencies
RUN uv sync --frozen

# Copy application code
COPY *.py ./
COPY api ./api
COPY clients ./clients
COPY services ./services

# Expose port
EXPOSE 8001

# Run the application
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]