#!/bin/bash
# run_tests.sh - Test runner for api-server

set -e

# Change to the script's directory to ensure consistent paths
cd "$(dirname "$0")"

# Ensure all dependencies are installed before running tests
echo "Installing dependencies..."
python3 scripts/install_deps.py --dev
echo "Dependencies installed."

# Set test environment variables
export DTR_API_SERVER_VERSION="1.0.0-test"
export DTR_VERSION="2.0.0-test"
export DTR_API_SERVER="http://test-api"
export DTR_LOG_LEVEL="DEBUG"
export DTR_ENCRYPTION_KEY="test-key-that-is-32-bytes-long"
export DTR_DB_HOST="test-db"
export DTR_DB_PORT="5432"
export DTR_DB_USER="test"
export DTR_DB_PASSWORD="test"
export DTR_DB_NAME="test"
export FLASK_TESTING="True"
# Add other required test variables here
export FLASK_ENV="testing"

# Add the parent directory (main) to Python path to allow imports from `common`
# And the current directory for imports within api-server
export PYTHONPATH="$(pwd)/..:$(pwd):$PYTHONPATH"

# Run tests with coverage
python3 -m pytest tests/ \
    --cov=. \
    --cov-report=html \
    --cov-report=term-missing \
    --cov-fail-under=85 \
    -v \
    "$@"

echo "✅ All tests passed with required coverage!" 