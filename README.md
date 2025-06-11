# Torale

<div align="center">
  <img src="frontend/public/torale-logo.svg" alt="Torale Logo" width="120" height="120"/>
</div>

A natural language-powered alerting service that monitors websites and content sources for meaningful changes.

## 🌟 Features

- Natural language query parsing
- Website content monitoring
- YouTube channel monitoring (Planned)
- RSS feed monitoring (Planned)
- Semantic change detection
- Email notifications
- User Authentication (Supabase)
- Modern web interface
- RESTful API

## 🏗️ Project Structure

```
torale/
├── backend/           # FastAPI backend service
│   ├── app/          # Application code
│   ├── tests/        # Backend tests
│   └── README.md     # Backend documentation
├── frontend/         # Next.js frontend application
│   ├── src/         # Source code
│   ├── public/      # Static files
│   └── README.md    # Frontend documentation
└── README.md        # This file
```

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+
- SendGrid API key (for backend email alerts, if used)
- Supabase Project URL & Anon Key (for frontend auth)
- uv (installed system-wide)

### Development Setup

1.  **Backend Setup:** See [backend/README.md](backend/README.md)
2.  **Frontend Setup:** See [frontend/README.md](frontend/README.md) (Ensure Supabase environment variables are set)

### 🚀 Launch Instructions

The easiest way to launch Torale for development is by using the provided `start.sh` script from the root of the project. This script handles starting both the backend and frontend services.

1.  **Ensure Prerequisites are Met:**
    *   Complete the **Backend Setup** and **Frontend Setup** as detailed in their respective `README.md` files ([backend/README.md](backend/README.md) and [frontend/README.md](frontend/README.md)). This includes installing dependencies and setting up environment variables.

2.  **Make the script executable (one-time setup):**
    ```bash
    chmod +x start.sh
    ```
3.  **Run the script from the project root:**
    ```bash
    ./start.sh
    ```
    *   The backend API will start in the background (typically at `http://localhost:8000`).
    *   The frontend application will start in the foreground (typically at `http://localhost:3000`).
    *   Open your web browser and navigate to `http://localhost:3000` to use Torale.
    *   To stop the frontend server (and the script), press `Ctrl+C` in the terminal where `start.sh` is running. 
    *   The script will remind you to manually stop the backgrounded backend server (its PID will be displayed when it starts).

For more detailed information on running each service independently, or for troubleshooting, please refer to:
- [Backend README](backend/README.md)
- [Frontend README](frontend/README.md)

## 📚 Documentation

- Backend API documentation: http://localhost:8000/docs (when backend is running)
- Frontend application: http://localhost:3000 (when frontend is running)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## ✅ Implemented

### Core Functionality
- Natural language query parsing for source discovery.
- Website content monitoring (initial version).
- Semantic change detection (initial version based on embeddings).
- Email notifications (basic setup).
- User Authentication (Supabase with `@supabase/ssr`).
- RESTful API for core operations.

### Backend (Iteration 1 Completed)
- `UserQuery` model, schemas, and API endpoint (`POST /user-queries/`).
- Integration of `UserQuery` flow with `SourceDiscoveryService` via background tasks.
- `SourceDiscoveryService` for identifying monitorable URLs from raw queries.
- `ContentIngestionService` for scraping content and generating embeddings.
- `ChangeDetectionService` for comparing embeddings and flagging changes.
- AI Model Abstraction Layer (`AIModelInterface`) with Perplexity and OpenAI client implementations.
- Dependency Injection for AI models.
- Core database models (`UserQuery`, `MonitoredSource`, `ScrapedContent`, `ContentEmbedding`, `ChangeAlert`).
- Pydantic schemas for all models and API interactions.
- FastAPI application structure with routers for user queries, source discovery, monitored sources, and alerts.
- Comprehensive testing for Iteration 1 components.

### Frontend (Iteration 1 Completed)
- User authentication flow (Sign In, Sign Up, Profile) using Supabase Auth, Next.js Middleware, and `@supabase/ssr`.
- Dedicated Axios instance (`src/lib/axiosInstance.ts`) with Supabase JWT interceptor for API calls.
- TanStack Query (`QueryClientProvider`, `useQuery`, `useMutation`) for server state management.
- Source Discovery UI (`/discover`):
    - Form to submit raw queries (`POST /api/v1/discover-sources/`).
    - Display of `monitorable_urls`.
    - Navigation to `/sources/new` with pre-filled URL.
- Monitored Source Management UI (`/sources`):
    - List view (`/sources/page.tsx`) displaying sources via TanStack Query.
    - Create form (`/sources/new/page.tsx`) with `react-hook-form`, `zod`, and TanStack Query `useMutation`.
    - Edit form (`/sources/[id]/edit/page.tsx`) for URL, interval, and status updates.
    - Delete functionality with confirmation and `useMutation`.
- Change Alert Display UI (`/alerts`):
    - List view (`/alerts/page.tsx`) displaying `ChangeAlertSchema` records with basic filtering.
    - Detail view (`/alerts/[id]/page.tsx`) for comprehensive alert details.
    - Acknowledge functionality on list and detail views using `useMutation`.
- Toast notifications for user feedback (`react-hot-toast`).
- Basic responsive design and type-safe components.

## 🚀 Coming Up

### Backend (Iteration 2 & Beyond)
- **Background Task Management:** Implement a robust system (e.g., Celery) for periodic tasks (triggering discovery, content ingestion, change detection).
- **Scalability & Error Handling:** Design for scalability and implement advanced error handling/retries for services.
- **Monitoring & Observability:** Integrate comprehensive application monitoring and logging dashboards.
- **Storage Evolution:** Evaluate and potentially migrate to a dedicated vector database for embeddings and scraped content.
- **Robust Scraping Enhancements:** Continue to improve scraping capabilities in `ContentIngestionService` (e.g., handling dynamic content, different content types).
- **Refine Preprocessing Logic:** Enhance text cleaning and preprocessing in `ContentIngestionService`.
- YouTube API integration for channel monitoring.
- RSS feed support with feed parsing.
- Secure API endpoints further (e.g., advanced permissions beyond basic auth).
- Rate limiting for API endpoints.
- Deployment configuration and CI/CD maturation.

### Frontend
- User profile management (displaying/editing more detailed profile data beyond basic auth info).
- Real-time updates using WebSocket (potentially via Supabase Realtime) for alerts.
- Advanced filtering and sorting options for alerts and monitored sources.
- Alert statistics and analytics dashboard.
- Enhanced mobile responsiveness and accessibility improvements.
- Comprehensive loading states and error boundaries across the application.
- Dark mode support.
- UI for managing `UserQuery` configurations directly (if needed beyond initial discovery).

### General
- Slack and Discord notification support (extending the alert notification system).
- Advanced content filtering options for monitoring.
- Custom alert templates.

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- OpenAI for GPT models
- Sentence Transformers for embeddings
- FastAPI for the backend framework
- Next.js for the frontend framework
- Tailwind CSS for styling
- Supabase for Authentication and potentially database/realtime features