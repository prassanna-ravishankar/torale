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
- Perplexity API key (for discovery service)

### Option 1: Microservices Mode (Recommended)

Start all services including the new Discovery microservice:

```bash
# Set up discovery service
cd discovery-service
cp .env.example .env  # Add your PERPLEXITY_API_KEY
uv sync

# Start all microservices
cd ..
./start-microservices.sh
```

This starts:
- Discovery Service (port 8001) - Natural language → URL discovery
- Backend API (port 8000) - Main application logic
- Frontend (port 3000) - User interface

### Option 2: Legacy Monolith Mode

```bash
# Backend setup
cd backend
cp .env.example .env  # Configure your environment variables
uv sync
uv run python -m uvicorn app.main:app --reload --port 8000

# Frontend setup  
cd frontend
cp .env.example .env.local  # Configure Supabase URL and anon key
npm install
npm run dev

# Or use the original start script
./start.sh  # Starts both frontend and backend (no microservices)
```

## Environment Variables

### Discovery Service (.env)
```bash
PERPLEXITY_API_KEY=your_perplexity_key
AI_PROVIDER=perplexity
SERVICE_PORT=8001
LOG_LEVEL=INFO
```

### Backend (.env)
```bash
SENDGRID_API_KEY=your_sendgrid_key
DATABASE_URL=your_supabase_db_url
OPENAI_API_KEY=your_openai_key
PERPLEXITY_API_KEY=your_perplexity_key
# Set to use microservice, leave empty for legacy mode
DISCOVERY_SERVICE_URL=http://localhost:8001
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

## Architecture

Torale is transitioning from a monolithic to a microservices architecture:

### Current Microservices (✅ Live)

**Discovery Service** (Port 8001)
- Natural language query processing
- AI-powered URL discovery using Perplexity
- Stateless, horizontally scalable
- RESTful API: `POST /api/v1/discover`

### Legacy Monolith (Port 8000)
- **API Layer**: Route handlers and request/response logic
- **Services Layer**: Business logic (content monitoring, change detection)
- **Repository Layer**: Database operations using Supabase
- **AI Integration**: OpenAI for embeddings, fallback discovery logic

### Frontend (Port 3000)
- **Next.js App Router**: Server components by default
- **Real-time**: Supabase Realtime subscriptions
- **State Management**: TanStack Query for server state

### Benefits Achieved
- ✅ **Independent Scaling**: Discovery service scales separately
- ✅ **Technology Flexibility**: Different tech stacks per service
- ✅ **Fault Isolation**: Service failures don't cascade
- ✅ **Development Velocity**: Teams can work independently

For detailed migration plan and future milestones, see [architecture-plan.md](./architecture-plan.md).

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
- **🎉 Discovery Microservice**: Natural language → URL discovery via Perplexity API
- Monitored source CRUD operations
- Change alert system with acknowledgment
- Semantic change detection using OpenAI embeddings
- Email notifications via SendGrid
- Comprehensive test coverage
- Modern, responsive UI
- **Microservices Foundation**: Service extraction, HTTP communication, fallback logic

### 🚀 Current Milestone Progress

**✅ Milestone 1: Discovery Service** - COMPLETE
- Standalone discovery microservice (port 8001)
- Perplexity API integration for source discovery
- RESTful API with proper error handling
- Backend integration with fallback support

**🔄 Next: Milestone 2: Notification Service**
- Extract notification logic to dedicated service
- Multi-channel support (email, webhooks, future SMS/Slack)
- Template management and delivery tracking

See [MILESTONE-1-SUCCESS.md](./MILESTONE-1-SUCCESS.md) for detailed completion report and [architecture-plan.md](./architecture-plan.md) for the full migration roadmap.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see LICENSE file for details