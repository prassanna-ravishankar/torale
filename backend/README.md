# Torale Backend

The backend service for Torale, a natural language-powered alerting service that monitors websites and content sources for meaningful changes.

## Features

- Natural language query parsing
- Website content monitoring
- Semantic change detection using embeddings
- Email notifications
- RESTful API
- Async operations
- SQLite database (can be extended to PostgreSQL)

## Prerequisites

- Python 3.9+
- uv (installed system-wide)
- SendGrid API key for email notifications

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/torale.git
cd torale/backend
```

2. Create virtual environment:

```bash
uv venv
```

3. Install dependencies:

```bash
uv sync --all-extras --dev
```

4. Copy the environment file and update with your settings:

```bash
cp .env.example .env
```

## Configuration

Update the `.env` file with your settings:

- `SENDGRID_API_KEY`: Your SendGrid API key for email notifications
- `DATABASE_URL`: Database connection URL (default: SQLite)
- Other settings as needed

## Development

1. Run the development server:

```bash
uv run uvicorn app.main:app --reload
```

2. Run tests:

```bash
uv run pytest
```

3. Run linting:

```bash
uv run ruff check .
```

4. Format code:

```bash
uv run ruff format .
```

## API Documentation

Once the server is running, you can access:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Alerts

- `POST /api/v1/alerts`: Create a new alert
- `GET /api/v1/alerts`: Get all alerts for a user
- `DELETE /api/v1/alerts/{alert_id}`: Delete an alert
- `POST /api/v1/alerts/check`: Manually trigger alert checking

## Project Structure

```
backend/
├── app/
│   ├── api/            # API routes
│   ├── core/           # Core functionality
│   ├── models/         # Database models
│   ├── services/       # Business logic
│   └── utils/          # Utility functions
├── tests/              # Test files
├── .env.example        # Example environment file
├── pyproject.toml      # Project configuration
└── README.md          # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see LICENSE file for details