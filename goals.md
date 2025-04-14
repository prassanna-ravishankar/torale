# 🛰️ Project: Ambient Alert System (Codename: AmbiAlert)

## 🌟 Overview

**AmbiAlert** is a natural language-powered alerting service that monitors websites and content sources for meaningful changes. Users define alerts in plain English, and the system watches for changes using LLM-based query parsing and embedding-based change detection.

---

## 🎯 Core Features

- Accept user queries like "Tell me when OpenAI updates their research page"
- Use Perplexity API to identify authoritative sources to monitor
- Parse intent into structured metadata using an LLM
- Monitor the target (webpage, RSS feed, YouTube) for updates
- Use **semantic embeddings** to detect meaningful changes
- Notify users via email when relevant updates are detected

---

## 🧩 System Components

### 1. Frontend (Next.js)

- User input for alert text and email
- Source discovery interface with Perplexity integration
- Source selection and management dashboard
- Change visualization and history
- Source reliability metrics display

### 2. Backend (FastAPI)

- POST /alert — Create a new alert with source discovery
- GET /alerts — Retrieve active alerts
- DELETE /alert/{id} — Remove an alert
- POST /check-updates — Trigger all alert checks
- POST /sources/discover — Discover new sources
- POST /sources/re-evaluate — Re-evaluate existing sources
- Auth endpoints (handled by Supabase):
  - POST /auth/signup
  - POST /auth/login
  - POST /auth/logout
  - GET /auth/user

### 3. Source Discovery Service

- Powered by Perplexity API
- Identifies authoritative sources
- Provides source metadata:
  - Reliability score
  - Update frequency
  - Content relevance
  - Source type (website, RSS, YouTube)
- Supports periodic re-evaluation

### 4. Monitoring Engine

- Supports:
  - ✅ Static webpages (Playwright or BeautifulSoup)
  - ✅ YouTube channels (YouTube API)
  - ✅ RSS feeds
- Extracts readable text content
- Embeds using OpenAI's text-embedding-3-small model
- Compares new embedding with previous using cosine similarity
- Tracks changes relative to original query

### 5. Change Detection

- Uses vector-based semantic diffing
- Alerts user if similarity drops below threshold (e.g., 0.9)
- Optionally include keyword filter to improve precision
- Provides change context and relevance
- Maintains change history

### 6. Notification Service

- Sends email alerts with detected changes
- Includes source reliability context
- Future: Slack, Discord, Webhooks, mobile push

---

## 💾 Data Storage

### Supabase Integration

- PostgreSQL database with pgvector extension
- Tables:
  - `alerts`: stores alert metadata
  - `sources`: stores discovered sources and metadata
  - `changes`: stores content change history
  - `embeddings`: stores content embeddings using pgvector
  - `profiles`: stores user profile data
- Authentication:
  - Email/password authentication
  - Magic link authentication
  - OAuth providers (GitHub, Google)
- Real-time subscriptions for updates
- Row Level Security for data protection
- Built-in authentication and authorization

### Features

- Vector similarity search using pgvector
- Real-time updates via Supabase Realtime
- Automatic backups and point-in-time recovery
- Database migrations and versioning
- Connection pooling and query optimization

---

## 🛠️ Stack Summary

| Component        | Tool                                 |
| ---------------- | ------------------------------------ |
| Frontend         | Next.js, Tailwind CSS                |
| Backend          | FastAPI, Docker                      |
| Authentication   | Supabase Auth                        |
| Source Discovery | Perplexity API                       |
| Web Scraping     | Playwright, requests + BeautifulSoup |
| Embedding        | OpenAI text-embedding-3-small        |
| Database         | Supabase (PostgreSQL + pgvector)     |
| Notifications    | SendGrid, Mailgun, SMTP              |
| Infrastructure   | Docker, Docker Compose               |
| Monitoring       | Prometheus, Grafana                  |

---

## ✅ MVP Goals

- [x] User Authentication

  - [x] Set up Supabase Auth
  - [x] Implement email/password authentication
  - [x] Add magic link authentication
  - [ ] Configure Row Level Security
  - [ ] Add user profile management

- [ ] Source Discovery Integration

  - [ ] Implement Perplexity API integration
  - [ ] Create source discovery service
  - [ ] Add source metadata storage in Supabase
  - [ ] Implement source re-evaluation

- [ ] Monitoring System

  - [ ] Set up Supabase with pgvector
  - [ ] Implement embedding storage and similarity search
  - [ ] Add source reliability metrics
  - [ ] Support multiple content types

- [ ] Frontend Updates

  - [ ] Add source discovery interface
  - [ ] Create source management dashboard
  - [ ] Implement change visualization
  - [ ] Add reliability metrics display

- [ ] Docker Infrastructure
  - [ ] Create Dockerfiles for services
  - [ ] Set up docker-compose
  - [ ] Add monitoring containers
  - [ ] Configure production settings

---

## 🧪 Future Ideas

- Additional OAuth providers (GitHub, Google)
- User preferences and settings
- Team collaboration features
- API key management
- Usage quotas and billing
- GPT-based diff summarization
- Change severity scoring
- Multi-source aggregation (track topics across sites)
- OpenAPI spec for third-party devs
- Advanced source reliability scoring
- Automated source pruning
- Custom alert templates
- Real-time updates via WebSocket

---

## 📜 License

MIT or equivalent — TBD
