# Torale 🛰️

<div align="center">
  <img src="frontend/public/torale-logo.svg" alt="Torale Logo" width="120" height="120"/>
  <p><em>Natural language-powered website monitoring with intelligent change detection</em></p>
</div>

## What is Torale?

Torale is an intelligent alerting service that monitors websites for meaningful changes using natural language queries. Simply describe what you want to monitor in plain English, and Torale will find the right sources and notify you when important changes occur.

**Example**: "Tell me when OpenAI updates their research page" → Torale discovers the OpenAI research page, monitors it using semantic embeddings, and emails you when new papers are published.

## ✨ Key Features

- 🔍 **Natural Language Queries**: "Tell me when Tesla updates their pricing page"
- 🎯 **Smart Source Discovery**: Uses Perplexity AI to find authoritative sources
- 🧠 **Semantic Change Detection**: Embedding-based detection of meaningful changes, not just HTML diffs
- 📧 **Intelligent Notifications**: Email alerts with AI-generated summaries of what changed
- 🔐 **Secure Authentication**: Powered by Supabase Auth with RLS
- ⚡ **Real-time Updates**: Live alerts using Supabase Realtime
- 🚀 **Microservices Architecture**: Scalable, fault-tolerant service design

## 🏗️ Architecture

Torale uses a **selective microservices architecture** with three main services:

```
┌─────────────────┐     ┌─────────────────────────────────┐
│   Next.js App   │────▶│        Main Backend             │
│  (Frontend)     │     │        (FastAPI)                │
└─────────────────┘     │  ┌─────────────────────────────┐│
                        │  │ • User Management           ││
                        │  │ • API Orchestration         ││
              ┌─────────┼──┤ • Notifications (Integrated)││
              │         │  │ • Service Coordination      ││
              │         │  └─────────────────────────────┘│
              │         └─────────────┬───────────────────┘
              │                       │
        ┌─────▼─────┐           ┌─────▼──────────┐
        │ Discovery │           │Content Monitor │
        │ Service   │           │    Service     │
        │ :8001     │           │    :8002       │
        │           │           │                │
        │• AI Query │           │• Web Scraping  │
        │  Processing│          │• Embeddings    │
        │• Source   │           │• Change        │
        │  Finding  │           │  Detection     │
        │• Perplexity│          │• Alert         │
        │  Integration│         │  Generation    │
        └─────┬─────┘           └─────┬──────────┘
              │                       │
              └───────────┬───────────┘
                          │
                   ┌──────▼──────┐
                   │  Supabase   │
                   │  - Auth     │
                   │  - Database │
                   │  - Realtime │
                   │  - Functions│
                   └─────────────┘
```

### Service Responsibilities

- **Main Backend** (`:8000`): User management, API gateway, service coordination
- **Discovery Service** (`:8001`): Natural language → URL discovery using Perplexity AI
- **Content Monitoring Service** (`:8002`): Web scraping, embedding generation, change detection
- **Notification Service** (`:8003`): Multi-channel notifications via NotificationAPI (email, SMS, push, webhooks)

## 🚀 Quick Start

### Using Docker Compose (Recommended)

```bash
# 1. Copy and configure environment variables
cp .env.example .env
# Edit .env with your API keys (see SETUP.md for details)

# 2. Start the entire stack
docker-compose up --build

# 3. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
```

### Using Just (Command Runner)

If you have [just](https://github.com/casey/just) installed:

```bash
# See all available commands
just

# Setup and start everything
just setup
just up

# Check service health
just health

# View logs
just logs
```

### Manual Development Setup

```bash
# Backend
cd backend && uv sync && uv run uvicorn app.main:app --reload --port 8000

# Frontend  
cd frontend && npm install && npm run dev

# Microservices
./start-microservices.sh

# Or individually:
cd discovery-service && uv run uvicorn main:app --reload --port 8001
cd content-monitoring-service && uv run uvicorn main:app --reload --port 8002
cd notification-service && uv run uvicorn main:app --reload --port 8003
```

See [SETUP.md](./SETUP.md) for detailed setup instructions including API key configuration.

## 🛠️ Tech Stack

**Frontend**
- Next.js 15 with App Router
- React 19, TypeScript, Tailwind CSS
- Supabase Auth & Realtime
- TanStack Query for state management

**Backend Services**
- FastAPI with Python 3.12+
- Pydantic for data validation
- uv for dependency management
- Comprehensive async/await usage

**AI & Data**
- OpenAI GPT-4 for embeddings & analysis
- Perplexity API for source discovery
- Supabase (PostgreSQL + pgvector)
- NotificationAPI for multi-channel notifications

**Development & Deployment**
- Docker & docker-compose
- Just for task automation
- Comprehensive test suites (pytest, vitest)
- GitHub Actions CI/CD ready

## 📋 Requirements

**API Keys Required:**
- Supabase project (free tier available)
- OpenAI API key (for embeddings)
- Perplexity API key (for source discovery)
- NotificationAPI account (for multi-channel notifications)

**Development Tools:**
- Python 3.12+ with [uv](https://github.com/astral-sh/uv)
- Node.js 18+ with npm
- Docker (optional, for containerized development)

## 🧪 Development

### Code Quality

```bash
# Backend linting and testing
cd backend
uv run ruff check . && uv run ruff format .
uv run mypy .
uv run pytest --cov=app --cov-report=term-missing

# Frontend linting and testing  
cd frontend
npm run lint && npm run type-check
npm run test && npm run coverage

# All services
just test  # Runs tests for all services
just lint  # Runs linting for all services
```

### Project Structure

```
torale/
├── backend/                 # Main FastAPI backend
├── frontend/                # Next.js application
├── discovery-service/       # Natural language processing service
├── content-monitoring-service/ # Web scraping & change detection
├── notification-service/    # Email & notification delivery
├── supabase/               # Database migrations & functions
├── docs/                   # Additional documentation
├── docker-compose.yml      # Full-stack deployment
├── justfile               # Task automation
└── .env                   # Environment configuration
```

## 📊 Project Status

### ✅ Completed Features
- Core user authentication with Supabase Auth
- Natural language query processing
- Intelligent source discovery via AI
- Semantic change detection using embeddings
- Email notification system with preferences
- Real-time alerts via Supabase Realtime
- Comprehensive microservices architecture
- Full Docker deployment support
- Modern, responsive UI with dark mode

### 🚧 Current Development
- Performance optimizations for large-scale monitoring
- Advanced notification channels (webhooks, Slack)
- Improved change detection algorithms
- Enhanced monitoring dashboard

### 🎯 Roadmap
- Mobile app development
- Enterprise features (team accounts, SSO)
- Advanced analytics and reporting
- Machine learning for personalized alerts
- Webhook integrations for third-party services

## 📖 Documentation

- [SETUP.md](./SETUP.md) - Detailed setup instructions
- [DEVELOPMENT.md](./DEVELOPMENT.md) - Developer workflow and guidelines
- [CLAUDE.md](./CLAUDE.md) - Claude AI assistant context
- [API Documentation](http://localhost:8000/docs) - Interactive API docs (when running)

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Ensure all tests pass (`just test`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to your branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

MIT License - see [LICENSE](./LICENSE) file for details.

## 🆘 Support

- 📧 Email: team@torale.com
- 🐛 Issues: [GitHub Issues](https://github.com/your-org/torale/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/your-org/torale/discussions)

---

<div align="center">
  <p>Built with ❤️ by the Torale team</p>
  <p>Turning natural language into intelligent monitoring</p>
</div>