# AmbiAlert

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
ambi-alert/
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

The easiest way to launch AmbiAlert for development is by using the provided `start.sh` script from the root of the project. This script handles starting both the backend and frontend services.

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
    *   Open your web browser and navigate to `http://localhost:3000` to use AmbiAlert.
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

## ✅ Implemented (Formerly "Coming Up")

### Frontend

- User authentication flow (using Supabase Auth with `@supabase/ssr`)
- Email verification system (via Supabase Auth)

## 🚀 Coming Up

### Backend

- YouTube API integration for channel monitoring
- RSS feed support with feed parsing
- Secure API endpoints (e.g., requiring authentication)
- Rate limiting for API endpoints
- Monitoring dashboard with metrics
- Comprehensive test coverage
- Deployment configuration

### Frontend

- User profile management (display/edit)
- Real-time updates using WebSocket (potentially via Supabase Realtime)
- Alert history view
- Alert statistics and analytics
- Enhanced mobile responsiveness
- Loading states and error boundaries
- Dark mode support

### General

- Slack and Discord notification support
- Advanced content filtering
- Custom alert templates
- API key management
- Usage analytics
- Performance optimizations
- Documentation improvements

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- OpenAI for GPT models
- Sentence Transformers for embeddings
- FastAPI for the backend framework
- Next.js for the frontend framework
- Tailwind CSS for styling
- Supabase for Authentication and potentially database/realtime features
