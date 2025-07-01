#!/bin/bash
# Script to start microservices in development mode

echo "Starting Torale Microservices..."
echo "================================"

# Check if .env files exist
if [ ! -f "discovery-service/.env" ]; then
    echo "⚠️  discovery-service/.env not found!"
    echo "   Please copy discovery-service/.env.example to discovery-service/.env"
    echo "   and configure your API keys."
    exit 1
fi

if [ ! -f "content-monitoring-service/.env" ]; then
    echo "⚠️  content-monitoring-service/.env not found!"
    echo "   Please copy content-monitoring-service/.env.example to content-monitoring-service/.env"
    echo "   and configure your settings."
    exit 1
fi

if [ ! -f "notification-service/.env" ]; then
    echo "⚠️  notification-service/.env not found!"
    echo "   Please copy notification-service/.env.example to notification-service/.env"
    echo "   and configure your settings."
    exit 1
fi

if [ ! -f "backend/.env" ]; then
    echo "⚠️  backend/.env not found!"
    echo "   Please copy backend/.env.example to backend/.env"
    echo "   and configure your settings."
    exit 1
fi

# Function to cleanup on exit
cleanup() {
    echo -e "\n\nStopping services..."
    kill $DISCOVERY_PID $CONTENT_PID $NOTIFICATION_PID $BACKEND_PID 2>/dev/null
    exit 0
}

trap cleanup EXIT INT TERM

# Start discovery service
echo -e "\n📡 Starting Discovery Service on port 8001..."
cd discovery-service
uv run uvicorn main:app --reload --port 8001 &
DISCOVERY_PID=$!
cd ..

# Wait a bit for discovery service to start
sleep 3

# Start content monitoring service
echo -e "\n🔍 Starting Content Monitoring Service on port 8002..."
cd content-monitoring-service
uv run uvicorn main:app --reload --port 8002 &
CONTENT_PID=$!
cd ..

# Wait a bit for content service to start
sleep 3

# Start notification service
echo -e "\n📧 Starting Notification Service on port 8003..."
cd notification-service
uv run uvicorn main:app --reload --port 8003 &
NOTIFICATION_PID=$!
cd ..

# Wait a bit for notification service to start
sleep 3

# Start backend with all service URLs
echo -e "\n🚀 Starting Backend Service on port 8000..."
cd backend
DISCOVERY_SERVICE_URL=http://localhost:8001 CONTENT_MONITORING_SERVICE_URL=http://localhost:8002 NOTIFICATION_SERVICE_URL=http://localhost:8003 uv run uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

echo -e "\n✅ Services started!"
echo "   - Discovery Service: http://localhost:8001"
echo "   - Content Monitoring Service: http://localhost:8002"
echo "   - Notification Service: http://localhost:8003"
echo "   - Backend API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo -e "\nPress Ctrl+C to stop all services.\n"

# Wait for services
wait