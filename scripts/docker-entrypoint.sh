#!/bin/sh
# scripts/docker-entrypoint.sh - Enhanced production-ready container entry point

set -e

echo "Starting DTR API Server..."
echo "Version: ${DTR_API_VERSION:-unknown}"
echo "System Version: ${DTR_VERSION:-unknown}"
echo "Log Level: ${DTR_LOG_LEVEL:-INFO}"

# Validate required environment variables
if [ "$DTR_DB_USER" = "**" ] || [ -z "$DTR_DB_USER" ]; then
  echo "ERROR: DTR_DB_USER environment variable is required and must be set"
  exit 1
fi

if [ "$DTR_DB_PASSWORD" = "**" ] || [ -z "$DTR_DB_PASSWORD" ]; then
  echo "ERROR: DTR_DB_PASSWORD environment variable is required and must be set"
  exit 1
fi

if [ -z "$DTR_DB_HOST" ]; then
  echo "ERROR: DTR_DB_HOST environment variable is required"
  exit 1
fi

if [ -z "$DTR_DB_NAME" ]; then
  echo "ERROR: DTR_DB_NAME environment variable is required"
  exit 1
fi

# Set defaults for optional variables
DTR_DB_PORT=${DTR_DB_PORT:-5432}
DTR_LOG_LEVEL=${DTR_LOG_LEVEL:-INFO}
DTR_DB_CREATE=${DTR_DB_CREATE:-false}

# Log configuration
echo "Database Configuration:"
echo "  Host: $DTR_DB_HOST"
echo "  Port: $DTR_DB_PORT"
echo "  Database: $DTR_DB_NAME"
echo "  User: $DTR_DB_USER"
echo "  Create DB: $DTR_DB_CREATE"

# Wait for database to be ready (simple check)
echo "Checking database connectivity..."
max_attempts=30
attempt=1
while [ $attempt -le $max_attempts ]; do
    if nc -z "$DTR_DB_HOST" "$DTR_DB_PORT" 2>/dev/null; then
        echo "Database is ready!"
        break
    fi
    echo "Database not ready, attempt $attempt/$max_attempts. Waiting..."
    sleep 2
    attempt=$((attempt + 1))
done

# Run database migrations if needed
if [ "$DTR_DB_CREATE" = "true" ]; then
    echo "Running database migrations..."
    alembic upgrade head || {
        echo "ERROR: Database migration failed"
        exit 1
    }
fi

echo "Starting gunicorn server..."
exec gunicorn \
  --bind=0.0.0.0:80 \
  'api:create_app()'
