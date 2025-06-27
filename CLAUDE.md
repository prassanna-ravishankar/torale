# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Backend (Python/FastAPI)
```bash
# Development
cd backend
uv run python -m uvicorn app.main:app --reload --port 8000

# Testing
uv run pytest
uv run pytest --cov=app --cov-report=term-missing

# Linting and Formatting
uv run ruff check .
uv run ruff format .
uv run black .
uv run mypy .
```

### Frontend (TypeScript/Next.js)
```bash
# Development
cd frontend
npm run dev

# Build and Production
npm run build
npm run start

# Quality Checks
npm run lint
npm run type-check
npm run test
npm run coverage
```

### Full Stack Development
```bash
# From project root - starts main backend + discovery service
./start.sh
```

### Discovery Service (Microservice)
```bash
# Development
cd discovery-service
uv run python -m uvicorn main:app --reload --port 8001

# Testing
uv run pytest
uv run pytest --cov=. --cov-report=term-missing

# Linting and Formatting
uv run ruff check .
uv run ruff format .

# Docker build
docker build -t discovery-service .
```

### Content Monitoring Service (Microservice)
```bash
# Development
cd content-monitoring-service
uv run python -m uvicorn main:app --reload --port 8002

# Testing
uv run pytest
uv run pytest --cov=. --cov-report=term-missing

# Linting and Formatting
uv run ruff check .
uv run ruff format .

# Docker build
docker build -t content-monitoring-service .

# Run all microservices
docker-compose up
# or
./start-microservices.sh
```

## Architecture Overview

### Selective Microservices Architecture
Torale uses a selective microservice approach, extracting services where it provides clear benefits:

**Microservices:**
- **Discovery Service** (`:8001`): Stateless query processing and source identification
- **Content Monitoring Service** (`:8002`): Heavy computational work for content processing

**Main Backend (`:8000`):**
- **API Layer** (`/api/endpoints/`): Orchestrates microservices and handles CRUD operations
- **Services Layer** (`/services/`): Integrated notification system and user management
- **Repository Layer**: Database operations using Supabase
- **Schemas** (`/schemas/`): Pydantic models for validation and serialization

**Architecture Benefits:**
- **Service Isolation**: Heavy processing doesn't affect main application
- **Independent Scaling**: Scale content processing and discovery independently  
- **Technology Flexibility**: Each service can use optimal technology stack
- **Deployment Simplicity**: Critical services (auth, notifications) remain integrated

Key design patterns:
- Async/await throughout for I/O operations
- Service-to-service communication via HTTP APIs
- Shared database with service-specific table ownership
- Integrated notification processing for better performance

### Frontend Architecture
The frontend uses Next.js 15 with App Router and follows modern React patterns:

- **App Router** (`/app/`): File-based routing with layouts
- **Server Components**: Default for pages, with client components where needed
- **State Management**: 
  - TanStack Query for server state
  - React Hook Form + Zod for forms
  - Context for auth state
- **API Integration**: Axios instance with Supabase JWT interceptor
- **UI Components**: Tailwind CSS with responsive design

Key flows:
1. **Authentication**: Supabase Auth with middleware protection
2. **Source Discovery**: Natural language → API → Monitorable URLs
3. **Monitoring**: Create/edit sources → Background monitoring → Change alerts
4. **Alerts**: List/detail views with acknowledgment functionality

### Database Schema
Uses Supabase (PostgreSQL) with these core tables:
- `user_queries`: Natural language queries from users
- `monitored_sources`: URLs being monitored with intervals
- `scraped_content`: Raw content from sources
- `content_embeddings`: Vector embeddings for semantic comparison
- `change_alerts`: Detected changes requiring user attention

### Development Principles (from .cursorrules)
- **KISS (Keep It Simple, Stupid)**: Prefer simple, clear solutions
- **Type Safety**: TypeScript strict mode, Python type hints everywhere
- **Small Functions**: Single responsibility principle
- **Error Handling**: Meaningful errors, proper HTTP status codes
- **Testing**: High coverage on critical paths
- **Security**: Input validation, sanitization, proper auth

### Key Dependencies
- **Backend**: FastAPI, Pydantic, Supabase, OpenAI, Perplexity, BeautifulSoup4, SendGrid
- **Frontend**: Next.js 15, React 19, Supabase Auth, TanStack Query, Tailwind CSS
- **Development**: uv (Python), pytest, ruff, black, ESLint, Vitest

### Environment Variables
Backend `.env`:
- `SENDGRID_API_KEY`
- `DATABASE_URL`
- AI model API keys

Frontend `.env.local`:
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`