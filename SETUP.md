# Torale Setup Guide

This guide will help you get Torale running locally for development or production deployment.

## 🚀 Quick Start (Docker Compose)

The fastest way to get Torale running is with Docker Compose, which starts all services automatically.

### Prerequisites

- Docker and Docker Compose installed
- API keys from required services (see Configuration section)

### Steps

1. **Clone and configure**:
   ```bash
   git clone https://github.com/your-org/torale.git
   cd torale
   cp .env.example .env
   ```

2. **Configure environment variables** (see [Configuration](#-configuration) section below)

3. **Start all services**:
   ```bash
   docker-compose up --build
   ```

4. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/docs
   - Discovery Service: http://localhost:8001/docs
   - Content Monitoring: http://localhost:8002/docs
   - Notifications: http://localhost:8003/docs

## ⚙️ Configuration

### Required API Keys

You'll need accounts and API keys from these services:

#### 1. Supabase (Database & Auth)
- Go to [supabase.com](https://supabase.com) and create a project
- Navigate to Settings > API in your project dashboard
- Copy these values to your `.env`:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.your-service-role-key
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.your-service-role-key
SUPABASE_JWT_SECRET=your-jwt-secret-from-supabase

# Frontend Supabase Config
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.your-anon-key

# Database Connection (from Settings > Database)
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.your-project-id.supabase.co:5432/postgres
```

#### 2. OpenAI (Embeddings & AI Analysis)
- Visit [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- Create a new API key
- Add to `.env`:

```bash
OPENAI_API_KEY=sk-your-openai-api-key
```

#### 3. Perplexity (Source Discovery)
- Go to [perplexity.ai/settings/api](https://www.perplexity.ai/settings/api)
- Generate an API key
- Add to `.env`:

```bash
PERPLEXITY_API_KEY=pplx-your-perplexity-key
```

#### 4. SendGrid (Email Notifications)
- Sign up at [sendgrid.com](https://sendgrid.com)
- Create an API key with Full Access permissions
- Add to `.env`:

```bash
SENDGRID_API_KEY=SG.your-sendgrid-api-key
ALERT_FROM_EMAIL=noreply@yourdomain.com  # Your verified sender email
```

### Database Setup

1. **Run migrations** in your Supabase SQL Editor:
   ```sql
   -- Execute each file in supabase/migrations/ in order:
   -- 001_initial_schema.sql
   -- 20240414_create_profiles.sql  
   -- 20250414213107_restrict_profile_select.sql
   -- 20250627001_create_notification_tables.sql
   -- 20250627002_python_notification_system.sql
   -- 20250627003_create_notification_triggers.sql
   -- 20250627005_notification_functions.sql
   ```

2. **Enable required extensions** in Supabase:
   ```sql
   -- In SQL Editor, run:
   CREATE EXTENSION IF NOT EXISTS vector;
   CREATE EXTENSION IF NOT EXISTS pg_cron;
   ```

## 🐳 Deployment Options

### Option 1: Docker Compose (Recommended)

Best for: Full-stack deployment, production, or development with all services.

```bash
# Start all services
docker-compose up --build

# Run in background
docker-compose up --build -d

# Scale specific services
docker-compose up --scale content-monitoring-service=3

# View logs
docker-compose logs -f [service-name]

# Stop all services
docker-compose down
```

**Services started:**
- Frontend (React/Next.js)
- Backend API (FastAPI) 
- Discovery Service (AI processing)
- Content Monitoring Service (scraping & analysis)
- Notification Service (email delivery)

### Option 2: Individual Services (Development)

Best for: Development when you only need specific services or want to modify individual components.

#### Backend Development
```bash
cd backend
cp .env.example .env  # Configure your variables
uv sync
uv run python -m uvicorn app.main:app --reload --port 8000
```

#### Frontend Development
```bash
cd frontend
cp .env.example .env.local  # Configure Supabase keys
npm install
npm run dev
```

#### Microservices Development
```bash
# Terminal 1: Discovery Service
cd discovery-service
uv sync
uv run uvicorn main:app --reload --port 8001

# Terminal 2: Content Monitoring
cd content-monitoring-service  
uv sync
uv run uvicorn main:app --reload --port 8002

# Terminal 3: Notification Service
cd notification-service
uv sync
uv run uvicorn main:app --reload --port 8003
```

Or use the convenience script:
```bash
./start-microservices.sh
```

### Option 3: Just Commands (Task Runner)

If you have [just](https://github.com/casey/just) installed:

```bash
# See all available commands
just

# Setup environment and dependencies
just setup

# Start all services with Docker
just up

# Start individual services for development
just dev-backend
just dev-frontend  
just dev-discovery
just dev-monitoring
just dev-notifications

# Health checks
just health

# Run tests
just test
just test-backend
just test-frontend

# Linting
just lint
just format

# View logs
just logs [service-name]

# Clean up
just clean
```

### Option 4: Legacy Monolith Mode

For compatibility with older setups:

```bash
# Starts both backend and frontend (no microservices)
./start.sh
```

## 🏥 Health Checks & Verification

### Service Health
```bash
# Check all services are running
curl http://localhost:8000/health      # Backend
curl http://localhost:8001/health      # Discovery
curl http://localhost:8002/api/v1/health # Content Monitoring  
curl http://localhost:8003/health      # Notifications

# Or use just
just health
```

### End-to-End Testing
1. **Sign up**: Go to http://localhost:3000 and create an account
2. **Discover sources**: Try "Monitor OpenAI research updates"
3. **Create monitor**: Add a source to monitor
4. **Test notifications**: Configure email preferences in Settings
5. **Trigger alert**: Process a source and verify email delivery

## 🔧 Development Setup

### Prerequisites

**Required:**
- Python 3.12+ with [uv](https://github.com/astral-sh/uv) installed
- Node.js 18+ with npm
- Git

**Optional:**
- Docker & Docker Compose (for containerized development)
- [just](https://github.com/casey/just) command runner

### Development Workflow

1. **Setup environment**:
   ```bash
   # Using just
   just setup
   
   # Or manually
   cd backend && uv sync
   cd ../frontend && npm install
   cd ../discovery-service && uv sync
   cd ../content-monitoring-service && uv sync
   cd ../notification-service && uv sync
   ```

2. **Start development servers**:
   ```bash
   # All services with hot reload
   just dev
   
   # Or individually
   just dev-backend     # Backend on :8000
   just dev-frontend    # Frontend on :3000  
   just dev-discovery   # Discovery on :8001
   just dev-monitoring  # Monitoring on :8002
   just dev-notifications # Notifications on :8003
   ```

3. **Run tests**:
   ```bash
   just test           # All tests
   just test-backend   # Python tests
   just test-frontend  # JavaScript tests
   ```

## 🚨 Troubleshooting

### Common Issues

**Services won't start:**
```bash
# Check environment variables
just check-env

# View service logs
docker-compose logs [service-name]
just logs [service-name]

# Restart specific service
docker-compose restart [service-name]
```

**Database connection errors:**
- Verify Supabase project is active and connection string is correct
- Ensure database migrations have been run
- Check that Supabase service key has the correct permissions

**API key errors:**
- Verify all API keys are valid and have proper permissions
- Check service logs for specific error messages
- Ensure no extra spaces or characters in environment variables

**Port conflicts:**
- Default ports: Frontend (3000), Backend (8000), Discovery (8001), Monitoring (8002), Notifications (8003)
- Change ports in docker-compose.yml or individual service configs if needed

**Docker issues:**
```bash
# Clean up containers and rebuild
docker-compose down -v
docker system prune -f
docker-compose up --build
```

### Performance Tuning

**For high-load scenarios:**
```bash
# Scale content monitoring service
docker-compose up --scale content-monitoring-service=3

# Scale discovery service  
docker-compose up --scale discovery-service=2

# Monitor resource usage
docker stats
```

**Memory optimization:**
- Content monitoring service is memory-intensive (embeddings)
- Consider increasing Docker memory limits for production
- Monitor OpenAI API usage to control costs

### Getting Help

- **Logs**: Check service logs for detailed error messages
- **API Docs**: Visit http://localhost:8000/docs for API documentation
- **Issues**: Create a GitHub issue with logs and configuration details
- **Discussions**: Join GitHub Discussions for community help

## 🌐 Production Deployment

### Environment Variables for Production

```bash
# Production-specific settings
NODE_ENV=production
LOG_LEVEL=INFO
DEBUG=false

# Security
CORS_ORIGINS="https://yourdomain.com,https://app.yourdomain.com"
ALLOWED_HOSTS="yourdomain.com,app.yourdomain.com"

# Performance  
DEFAULT_SIMILARITY_THRESHOLD=0.85
DEFAULT_REQUEST_TIMEOUT_SECONDS=30
BATCH_SIZE=10
```

### Docker Compose for Production

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  backend:
    build: ./backend
    environment:
      - NODE_ENV=production
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Recommended Infrastructure

- **Compute**: 2+ CPU cores, 4GB+ RAM minimum
- **Database**: Supabase Pro tier or dedicated PostgreSQL with pgvector
- **Monitoring**: Consider Sentry for error tracking
- **Logs**: Centralized logging with services like LogDNA or DataDog
- **SSL**: Use a reverse proxy (nginx, Caddy) with SSL certificates

---

**Next Steps:** After setup, see [DEVELOPMENT.md](./DEVELOPMENT.md) for development workflows and [CLAUDE.md](./CLAUDE.md) for AI assistant context.