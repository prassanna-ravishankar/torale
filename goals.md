# 🛰️ Project: Ambient Alert System (Codename: AmbiAlert)

## 🌟 Overview

**AmbiAlert** is a natural language-powered alerting service that monitors websites and content sources for meaningful changes. Users define alerts in plain English, and the system watches for changes using LLM-based query parsing and embedding-based change detection.

---

## 🎯 Core Features

- Accept user queries like “Tell me when OpenAI updates their research page”
- Parse intent into structured metadata using an LLM
- Monitor the target (webpage, RSS feed, YouTube) for updates
- Use **semantic embeddings** to detect meaningful changes
- Notify users via email when relevant updates are detected

---

## 🧩 System Components

### 1. Frontend (v0.dev or React)

- User input for alert text and email
- Dashboard to view/manage active alerts

### 2. Backend (FastAPI or Flask on Replit)

- POST /alert — Create a new alert
- GET /alerts — Retrieve active alerts
- DELETE /alert/{id} — Remove an alert
- POST /check-updates — Trigger all alert checks

### 3. NLP Parsing

- Powered by OpenAI or open-source LLMs
- Converts natural language into structured JSON, e.g.:

  {
  "type": "website_monitor",
  "target": "https://openai.com/research/",
  "keywords": ["GPT", "model"],
  "check_frequency_minutes": 30,
  "user_email": "user@example.com"
  }

### 4. Monitoring Engine

- Supports:
  - ✅ Static webpages (Playwright or BeautifulSoup)
  - ✅ YouTube channels (YouTube API)
  - ✅ RSS feeds
- Extracts readable text content
- Embeds using OpenAI or sentence-transformers
- Compares new embedding with previous using cosine similarity

### 5. Change Detection

- Uses vector-based semantic diffing
- Alerts user if similarity drops below threshold (e.g., 0.9)
- Optionally include keyword filter to improve precision

### 6. Notification Service

- Sends email alerts with detected changes
- Future: Slack, Discord, Webhooks, mobile push

---

## 💾 Data Storage

### Tables

- `alerts`: stores alert metadata
- `state`: stores last embedding and timestamp

### Embedding Storage Options

- pgvector (PostgreSQL extension)
- Pinecone, Weaviate, or Qdrant for scalable vector search

---

## 🛠️ Stack Summary

| Component     | Tool                                 |
| ------------- | ------------------------------------ |
| Frontend      | v0.dev, Next.js                      |
| Backend       | FastAPI, Replit                      |
| NLP Parsing   | OpenAI GPT, LangChain                |
| Web Scraping  | Playwright, requests + BeautifulSoup |
| Embedding     | OpenAI, sentence-transformers        |
| Vector DB     | pgvector, Pinecone, Qdrant           |
| Notifications | SendGrid, Mailgun, SMTP              |
| Scheduler     | cron, Celery, Modal.com              |

---

## ✅ MVP Goals

- [ ] Basic UI for entering alerts
- [ ] Store alert metadata
- [ ] Periodic website polling
- [ ] Embedding-based change detection
- [ ] Email notification on update

---

## 🧪 Future Ideas

- GPT-based diff summarization
- User authentication with magic link
- Change severity scoring
- Multi-source aggregation (track topics across sites)
- OpenAPI spec for third-party devs

---

## 📜 License

MIT or equivalent — TBD
