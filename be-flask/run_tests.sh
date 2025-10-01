#!/bin/bash

# Test runner script for local development

set -e

echo "🧪 Starting test suite..."

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis is not running. Starting Redis..."
    if command -v redis-server >/dev/null 2>&1; then
        echo "Starting Redis server..."
        redis-server --daemonize yes --port 6379
        sleep 2
        REDIS_STARTED=true
    else
        echo "❌ Redis not found. Please install Redis or use Docker:"
        echo "   docker run -d --name test-redis -p 6379:6379 redis:7.2-alpine"
        exit 1
    fi
else
    echo "✅ Redis is running"
    REDIS_STARTED=false
fi

# Set test environment variables
export CELERY_BROKER_URL="redis://localhost:6379/0"
export CELERY_RESULT_BACKEND="redis://localhost:6379/0"
export CELERY_ALWAYS_EAGER="True"
export API_KEY="${API_KEY:-dummy-api-key-for-tests}"

echo "🔧 Running unit tests..."
python test_unit.py

echo "🔧 Starting Celery worker for integration tests..."
celery -A app.celery worker --loglevel=info --detach

echo "🔧 Starting Flask app for integration tests..."
python app.py &
FLASK_PID=$!

# Wait for Flask to start
sleep 3

echo "🔧 Running integration tests..."
python test_integration.py

# Cleanup
echo "🧹 Cleaning up..."
kill $FLASK_PID 2>/dev/null || true
pkill -f "celery.*worker" 2>/dev/null || true

# Stop Redis if we started it
if [ "$REDIS_STARTED" = true ]; then
    echo "Stopping Redis..."
    redis-cli shutdown 2>/dev/null || true
fi

echo "✅ All tests completed successfully!"