# Torale Setup Guide

## Quick Setup with Docker Compose (Recommended)

### 1. Configure Environment Variables

The `.env` file in the root directory contains all environment variables needed for all services. You need to replace the placeholder values with your actual credentials:

#### Required Credentials:

**Supabase (Free tier available)**
1. Go to [supabase.com](https://supabase.com) and create a new project
2. In your project dashboard, go to Settings > API
3. Copy the following values to your `.env`:
   - `SUPABASE_URL` - Your project URL
   - `SUPABASE_SERVICE_KEY` - Service role key (keep secret!)
   - `SUPABASE_KEY` - Same as service role key
   - `SUPABASE_JWT_SECRET` - JWT secret
   - `NEXT_PUBLIC_SUPABASE_URL` - Same as SUPABASE_URL
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Anonymous public key
4. In Settings > Database, copy the connection string to `DATABASE_URL`

**OpenAI API (Required for embeddings)**
1. Go to [platform.openai.com](https://platform.openai.com/api-keys)
2. Create a new API key
3. Set `OPENAI_API_KEY` in your `.env`

**Perplexity API (Required for source discovery)**
1. Go to [perplexity.ai/settings/api](https://www.perplexity.ai/settings/api)
2. Create a new API key
3. Set `PERPLEXITY_API_KEY` in your `.env`

**SendGrid (Required for email notifications)**
1. Go to [app.sendgrid.com](https://app.sendgrid.com/settings/api_keys)
2. Create a new API key with "Full Access" permissions
3. Set `SENDGRID_API_KEY` in your `.env`
4. Optionally update `ALERT_FROM_EMAIL` with your sender email

### 2. Set Up Database Schema

1. In your Supabase project, go to the SQL Editor
2. Run the migration files in order:
   ```sql
   -- Run each file in the supabase/migrations/ folder in order
   -- 001_initial_schema.sql
   -- 20240414_create_profiles.sql
   -- etc.
   ```

### 3. Start All Services

```bash
# Build and start the entire stack
docker-compose up --build

# Or run in background
docker-compose up --build -d
```

This will start:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Discovery Service**: http://localhost:8001
- **Content Monitoring**: http://localhost:8002
- **Notification Service**: http://localhost:8003

### 4. Verify Setup

1. **Health Checks**:
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8001/health
   curl http://localhost:8002/api/v1/health
   curl http://localhost:8003/health
   ```

2. **Frontend Access**:
   - Go to http://localhost:3000
   - Sign up for a new account
   - Try creating a monitoring query

3. **Test Notifications**:
   - Go to Settings page
   - Configure notification preferences
   - Create a monitor and verify notifications work

### 5. Troubleshooting

**Services won't start:**
- Check that all required environment variables are set in `.env`
- Verify your API keys are valid
- Check Docker logs: `docker-compose logs service-name`

**Database connection issues:**
- Verify your Supabase connection string is correct
- Ensure your Supabase project is active
- Check that you've run the database migrations

**API key issues:**
- Verify each API key is valid and has the correct permissions
- Check service logs for specific error messages
- Make sure you're using the correct environment variable names

## Development Setup (Individual Services)

If you prefer to run services individually for development:

### Backend
```bash
cd backend
cp .env.example .env  # Configure variables
uv sync
uv run python -m uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
cp .env.example .env.local  # Configure variables
npm install
npm run dev
```

### Microservices
```bash
# Terminal 1 - Discovery Service
cd discovery-service
cp .env.example .env
uv sync
uv run uvicorn main:app --reload --port 8001

# Terminal 2 - Content Monitoring
cd content-monitoring-service
cp .env.example .env
uv sync
uv run uvicorn main:app --reload --port 8002

# Terminal 3 - Notification Service
cd notification-service
cp .env.example .env
uv sync
uv run uvicorn main:app --reload --port 8003
```

Or use the convenience script:
```bash
./start-microservices.sh
```

## Environment Variables Reference

See the `.env` file for a complete list of all environment variables with descriptions. The key categories are:

- **Supabase**: Database and authentication
- **AI Providers**: OpenAI and Perplexity API keys
- **Email**: SendGrid for notifications
- **Service Config**: Logging, timeouts, thresholds
- **Microservice URLs**: Service-to-service communication

## API Documentation

Once services are running, view the API documentation:
- **Backend**: http://localhost:8000/docs
- **Discovery**: http://localhost:8001/docs
- **Content Monitoring**: http://localhost:8002/docs
- **Notifications**: http://localhost:8003/docs