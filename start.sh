#!/bin/bash

# This script starts both the backend and frontend development servers for Torale.

# Exit immediately if a command exits with a non-zero status.
set -e

echo "🚀 Starting Torale services..."

# --- Start Backend Server ---
echo "🔄 Starting Backend (FastAPI)..."
cd backend
# Ensure uv is available and pyproject.toml is configured for a run command, or use direct uvicorn invocation.
# Example: uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
# Using a placeholder run command. Replace with your actual command if different.
(uv run python -m uvicorn app.main:app --reload --port 8000) & # Run in background
BACKEND_PID=$!
echo "✅ Backend server started in background (PID: $BACKEND_PID). Output will be in this terminal if not redirected."
cd ..

# Give the backend a moment to start up
sleep 3

# --- Start Frontend Server ---
echo "🔄 Starting Frontend (Next.js)..."
cd frontend
if [ ! -d "node_modules" ]; then
  echo "📦 Node modules not found. Running npm install..."
  npm install
fi
echo "🔥 Launching Next.js development server... (This will occupy this terminal)"
# npm run dev will typically occupy the terminal.
# If you want to run it in the background, you could use: (npm run dev) & FRONTEND_PID=$!
npm run dev

# --- Cleanup (Optional - if frontend is also backgrounded) ---
# If you run frontend in background as well, you might want to wait for Ctrl+C
# and then clean up background processes.
# echo "🛑 To stop all services, press Ctrl+C here, then you might need to manually kill PIDs: Backend ($BACKEND_PID), Frontend ($FRONTEND_PID)"
# wait $BACKEND_PID
# wait $FRONTEND_PID

# If frontend is in foreground, Ctrl+C in the terminal will stop it.
# The backend, started with &, will need to be stopped manually (e.g., kill $BACKEND_PID) or when the terminal session ends.

echo "👋 Frontend server (npm run dev) has been stopped (or Ctrl+C was pressed)."
echo "👉 Remember to stop the backend server (PID: $BACKEND_PID) if it's still running. (e.g., 'kill $BACKEND_PID')"