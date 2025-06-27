# Torale 🛰️

<div align="center">
  <img src="frontend/public/torale-logo.svg" alt="Torale Logo" width="120" height="120"/>
</div>

A natural language-powered alerting service that monitors websites for meaningful changes. Users define alerts in plain English, and the system watches for changes using LLM-based query parsing and embedding-based change detection.

## Features

- 🔍 **Natural Language Queries**: "Tell me when OpenAI updates their research page"
- 🎯 **Smart Source Discovery**: Uses Perplexity API to find authoritative sources
- 🧠 **Semantic Change Detection**: Embedding-based detection of meaningful changes
- 📧 **Multi-Channel Notifications**: Email alerts with more channels coming soon
- 🔐 **Secure Authentication**: Powered by Supabase Auth
- 📊 **Real-time Updates**: Live alerts using Supabase Realtime

## Tech Stack

- **Frontend**: Next.js 15, React 19, TypeScript, Tailwind CSS
- **Backend**: FastAPI, Python 3.12+, Pydantic
- **Database**: Supabase (PostgreSQL with pgvector)
- **AI/ML**: OpenAI embeddings, Perplexity for source discovery
- **Auth**: Supabase Auth
- **Development**: uv (Python), npm (Node.js)

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- [uv](https://github.com/astral-sh/uv) for Python package management
- Supabase account and project

### Backend Setup

```bash
cd backend
cp .env.example .env  # Configure your environment variables
uv sync
uv run python -m uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
cp .env.example .env.local  # Configure Supabase URL and anon key
npm install
npm run dev
```

### Full Stack Development

From the project root:

```bash
./start.sh  # Starts both frontend and backend services
```

## Environment Variables

### Backend (.env)
```bash
SENDGRID_API_KEY=your_sendgrid_key
DATABASE_URL=your_supabase_db_url
OPENAI_API_KEY=your_openai_key
PERPLEXITY_API_KEY=your_perplexity_key
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

## Architecture

The project follows a modular architecture with clear separation of concerns:

- **API Layer**: Thin route handlers that delegate to services
- **Services Layer**: Business logic including AI integrations and change detection
- **Repository Layer**: Database operations using Supabase
- **Frontend**: Next.js App Router with server components by default

For detailed architecture and microservices migration plan, see [architecture-plan.md](./architecture-plan.md).

## Development

### Code Quality

**Backend**:
```bash
cd backend
ruff check .
ruff format .
mypy .
pytest
```

**Frontend**:
```bash
cd frontend
npm run lint
npm run type-check
npm run test
```

### Testing

Both frontend and backend have comprehensive test suites:

```bash
# Backend
cd backend
pytest --cov=app --cov-report=term-missing

# Frontend
cd frontend
npm run test
npm run coverage
```

## Project Status

### ✅ Completed

- Core user authentication flow with Supabase
- Natural language source discovery using Perplexity API
- Monitored source CRUD operations
- Change alert system with acknowledgment
- Semantic change detection using OpenAI embeddings
- Email notifications via SendGrid
- Comprehensive test coverage
- Modern, responsive UI

### 🚀 Roadmap

See [architecture-plan.md](./architecture-plan.md) for the detailed microservices migration plan.

**Next Steps**:
1. Extract Discovery Service as first microservice
2. Implement background task processing
3. Add real-time updates
4. Support additional content sources (YouTube, RSS)
5. Enhanced monitoring and observability

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see LICENSE file for details