#!/bin/sh
# scripts/docker-entrypoint.sh - Enhanced production-ready container entry point

set -e

echo "Starting DTR API Server..."
echo "Version: ${DTR_API_VERSION:-unknown}"
echo "System Version: ${DTR_VERSION:-unknown}"
echo "Log Level: ${DTR_LOG_LEVEL}"

# Validate required environment variables
if [ "$DTR_DB_USER" = "**" ] || [ -z "$DTR_DB_USER" ]; then
  echo "ERROR: DTR_DB_USER environment variable is required and must be set"
  exit 1
fi

if [ "$DTR_DB_PASSWORD" = "**" ] || [ -z "$DTR_DB_PASSWORD" ]; then
  echo "ERROR: DTR_DB_PASSWORD environment variable is required and must be set"
  exit 1
fi

# Log configuration
echo "Database Configuration:"
echo "  Host: $DTR_DB_HOST"
echo "  Port: $DTR_DB_PORT"
echo "  Database: $DTR_DB_NAME"
echo "  User: $DTR_DB_USER"
echo "  Create DB: $DTR_DB_CREATE"

echo "Starting gunicorn server..."
gunicorn \
  --bind=0.0.0.0:80 \
  'api:create_app()'
