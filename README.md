# AmbiAlert

A natural language-powered alerting service that monitors websites and content sources for meaningful changes.

## 🌟 Features

- Natural language query parsing
- Website content monitoring
- YouTube channel monitoring
- RSS feed monitoring
- Semantic change detection
- Email notifications
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
- SendGrid API key
- uv (installed system-wide)

### Development Setup

1. Backend Setup: See [backend/README.md](backend/README.md)
2. Frontend Setup: See [frontend/README.md](frontend/README.md)

## 📚 Documentation

- Backend API documentation: http://localhost:8000/docs
- Frontend application: http://localhost:3000

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 🚀 Coming Up

### Backend

- YouTube API integration for channel monitoring
- RSS feed support with feed parsing
- User authentication with JWT
- Rate limiting for API endpoints
- Monitoring dashboard with metrics
- Comprehensive test coverage
- Deployment configuration

### Frontend

- User authentication flow
- Real-time updates using WebSocket
- Alert history view
- Alert statistics and analytics
- Email verification system
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
