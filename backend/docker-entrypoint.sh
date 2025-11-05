#!/bin/bash
set -e

# Wait for Cloud SQL proxy to be ready (in Kubernetes)
if [ -n "$KUBERNETES_SERVICE_HOST" ]; then
  echo "Waiting for Cloud SQL proxy..."
  until nc -z localhost 5432 2>/dev/null; do
    echo "Cloud SQL proxy not ready yet..."
    sleep 2
  done
  echo "Cloud SQL proxy is ready!"

  # Give proxy a bit more time to fully initialize
  sleep 2
else
  # Local development - wait for postgres directly
  echo "Waiting for postgres..."
  while ! pg_isready -h postgres -p 5432 -U torale; do
    sleep 1
  done
fi

echo "Running database migrations..."
alembic upgrade head

echo "Starting application..."
exec "$@"
