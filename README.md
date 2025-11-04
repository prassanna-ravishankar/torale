# Torale

**Grounded search monitoring platform** for AI-powered conditional automation.

Monitor the web for specific conditions using Google Search + LLM analysis, then get notified when they're met.

## Use Cases

- **Product Launches**: "Tell me when the next iPhone release date is announced"
- **Availability Monitoring**: "Notify me when swimming pool memberships open for summer"
- **Stock Alerts**: "Alert me when PS5 is back in stock at Best Buy"
- **Event Tracking**: "Let me know when GPT-5 launch date is confirmed"
- **Price Monitoring**: "Tell me when iPhone 15 price drops below $500"

## How It Works

1. **Create a monitoring task** with a search query and condition
2. **Torale runs scheduled searches** via Google Search (grounded via Gemini)
3. **LLM evaluates** if your condition is met based on search results
4. **You get notified** when condition triggers (once, always, or on state change)

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
- **Google AI**: Get key from https://aistudio.google.com/app/apikey (required)
- **Database**: PostgreSQL connection string (local default works)
- **Secret Key**: Generate with `openssl rand -hex 32`

### 3. Start Services
```bash
# Start all services (PostgreSQL + Temporal + API + Workers)
docker compose up -d

# Check status
docker compose ps
```

### 4. Create Your First Monitoring Task
```bash
# Register an account
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"yourpassword"}'

# Login
curl -X POST http://localhost:8000/auth/jwt/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=you@example.com&password=yourpassword"

# Copy the access_token from response

# Create monitoring task
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "iPhone Release Monitor",
    "schedule": "0 9 * * *",
    "executor_type": "llm_grounded_search",
    "search_query": "When is the next iPhone being released?",
    "condition_description": "A specific release date has been announced",
    "notify_behavior": "once",
    "config": {
      "model": "gemini-2.0-flash-exp"
    }
  }'
```

### 5. Check Notifications
```bash
# View notifications (executions where condition was met)
curl http://localhost:8000/api/v1/tasks/TASK_ID/notifications \
  -H "Authorization: Bearer YOUR_TOKEN"

# View full execution history
curl http://localhost:8000/api/v1/tasks/TASK_ID/executions \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Frontend

The Torale frontend is a React + TypeScript application built with Vite.

### Setup
```bash
# Install frontend dependencies
cd frontend && npm install

# Start development server
npm run dev

# Or use justfile
just dev-frontend
```

### Features
- **Authentication**: JWT-based login and registration
- **Dashboard**: View and manage all monitoring tasks
- **Task Creation**: Create new monitoring tasks with search queries and conditions
- **Task Details**: View execution history, notifications, and state changes
- **Real-time Updates**: Auto-refresh execution status
- **Toast Notifications**: User feedback for all actions

### Tech Stack
- React 18 + TypeScript
- Vite (build tool)
- React Router (routing)
- Tailwind CSS (styling)
- shadcn/ui (component library)
- Sonner (toast notifications)

Access the frontend at http://localhost:3000 after starting the dev server.

## Architecture

- **API**: FastAPI with JWT authentication (FastAPI-Users)
- **Database**: PostgreSQL 16 with state tracking
- **Workers**: Temporal workflows for scheduled execution
- **Executor**: Grounded search + LLM condition evaluation
- **Scheduler**: Temporal cron schedules
- **Search**: Google Search via Gemini grounding

## Features

### ✅ Implemented
- Grounded search monitoring via Google Search
- Intelligent condition evaluation (LLM-based)
- Automatic scheduled execution (cron)
- State tracking (no duplicate alerts)
- User-configurable notify behavior:
  - `once`: Notify once, then auto-disable
  - `always`: Notify every time condition is met
  - `track_state`: Notify only when state changes
- In-app notifications endpoint
- JWT authentication
- Temporal schedule management

### 🚧 In Progress
- CLI enhancements for monitoring tasks
- Enhanced grounding source display
- Historical state comparison UI

### 📋 Future Roadmap
- External notifications (email/SMS via NotificationAPI)
- Browser automation for dynamic sites
- Price tracking with charts
- Multi-step conditional workflows
- Template marketplace
- Team/organization support

## Known Issues

### Frontend
- **Alert Component Layout**: The info panel in the task creation dialog has alignment issues with the icon and text. The shadcn/ui Alert component's grid layout may need adjustment for proper spacing.

## Testing

```bash
# Run manual execution test
./test_temporal_e2e.sh

# Run automatic schedule test (waits ~60s for scheduled execution)
./test_schedule.sh

# Run grounded search test
./test_grounded_search.sh
```

## Deployment

### Local Development
```bash
docker compose up -d
```

### Google Cloud Run
```bash
./deploy.sh
```

## How Grounded Search Works

1. **Task Created**: User defines search query + condition to monitor
2. **Scheduled Execution**: Temporal triggers task based on cron schedule
3. **Grounded Search**: Gemini performs Google Search with grounding
4. **LLM Evaluation**: LLM analyzes search results and evaluates condition
5. **State Comparison**: Compares with `last_known_state` to detect changes
6. **Notification**: If condition met (and not already notified), creates in-app notification
7. **Auto-disable** (optional): If `notify_behavior = "once"`, task deactivates after first alert

## Configuration

### Notify Behaviors

- **`once`**: Alert once when condition is first met, then auto-disable task
- **`always`**: Alert every time condition is met (use with caution)
- **`track_state`**: Alert only when underlying state changes (smart deduplication)

### Schedule Formats

Use standard cron expressions:
- `* * * * *`: Every minute (testing only)
- `0 * * * *`: Every hour
- `0 9 * * *`: Every day at 9 AM
- `0 9 * * 1`: Every Monday at 9 AM
- `0 9 1 * *`: First day of every month at 9 AM

## API Endpoints

```
POST   /auth/register                      # Create account
POST   /auth/jwt/login                     # Get JWT token

POST   /api/v1/tasks                       # Create monitoring task
GET    /api/v1/tasks                       # List tasks
GET    /api/v1/tasks/{id}                  # Get task details
PUT    /api/v1/tasks/{id}                  # Update task
DELETE /api/v1/tasks/{id}                  # Delete task + schedule
POST   /api/v1/tasks/{id}/execute          # Manual execution (testing)
GET    /api/v1/tasks/{id}/executions       # Full execution history
GET    /api/v1/tasks/{id}/notifications    # Filtered: condition_met = true
```

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql://torale:torale@localhost:5432/torale

# Authentication
SECRET_KEY=your-secret-key-for-jwt

# Temporal
TEMPORAL_HOST=localhost:7233
TEMPORAL_NAMESPACE=default

# AI (Gemini required for grounded search)
GOOGLE_API_KEY=your-gemini-api-key
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT
