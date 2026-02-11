---
description: Contributing to Torale development. Local setup, development environment, coding standards, and contribution workflow.
---

# Development Setup

## Prerequisites

- Python 3.9+
- Node.js 20+
- Docker & Docker Compose
- UV package manager

## Quick Start

```bash
git clone https://github.com/torale-ai/torale
cd torale

# Backend
cd backend && uv sync

# Frontend
cd frontend && npm install

# Start all services
just dev
```

## Running Services

```bash
# All services
just dev

# API only
cd backend && uv run uvicorn torale.api.main:app --reload

# Workers only
cd backend && uv run python -m torale.workers

# Frontend only
cd frontend && npm run dev
```

## Next Steps

- Read [Testing Guide](/contributing/testing)
- View [Code Conventions](/contributing/conventions)
