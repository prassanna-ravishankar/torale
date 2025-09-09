# Torale

Platform-agnostic background task manager for AI-powered automation.

Create scheduled tasks like "Write me a blog post every morning at 6 AM about climate tech" or "Check the weather and send me a summary every day at 7 AM."

## Quick Start

### 1. Install Dependencies
```bash
pip install uv
uv sync
```

### 2. Set up Environment
```bash
cp .env.example .env
```
Edit `.env` with your API keys:
- **Supabase**: Create project at https://supabase.com, get URL/keys from Settings > API
- **OpenAI**: Get key from https://platform.openai.com/api-keys
- **Anthropic**: Get key from https://console.anthropic.com/settings/keys
- **Google**: Get key from https://aistudio.google.com/app/apikey

### 3. Set up Database
Run the migration in `supabase/migrations/001_initial_schema.sql` in your Supabase SQL editor.

### 4. Start Local Services
```bash
# Start Temporal
docker compose up -d

# Start API
uv run python run_api.py

# Start worker (in another terminal)
uv run python run_worker.py
```

### 5. Use CLI
```bash
# Login
uv run torale auth login

# Create a task
uv run torale task create "Daily summary" \
  --schedule "0 9 * * *" \
  --prompt "Summarize today's tech news" \
  --model "gemini-2.0-flash-exp"

# List tasks
uv run torale task list

# Execute manually
uv run torale task execute <task-id>
```

## Deploy to GCP

1. Set up gcloud CLI and authenticate
2. Enable required APIs:
   ```bash
   gcloud services enable cloudbuild.googleapis.com run.googleapis.com
   ```
3. Deploy:
   ```bash
   ./deploy.sh
   ```

## Architecture

- **API**: FastAPI with Supabase auth
- **Workers**: Temporal workflows for task execution  
- **Executors**: Pluggable task runners (LLM text generation for MVP)
- **CLI**: Typer-based command interface
- **Database**: Supabase (PostgreSQL)

## MVP Features

- ✅ Natural language task creation
- ✅ Cron-based scheduling
- ✅ LLM text generation (OpenAI/Anthropic/Google Gemini)
- ✅ Task management via CLI
- ✅ User authentication
- ✅ Cloud deployment

## Post-MVP Roadmap

- Web search + LLM analysis
- Browser automation
- Webhook integrations
- Conditional execution
- Web UI