#!/bin/bash

# Script to start the application locally

echo "Starting Code Review Agent locally..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Start Redis and PostgreSQL with Docker
echo "Starting Redis and PostgreSQL..."
docker run -d --name code-review-redis -p 6379:6379 redis:7-alpine 2>/dev/null || echo "Redis container already running"
docker run -d --name code-review-postgres -p 5432:5432 \
    -e POSTGRES_DB=code_review_db \
    -e POSTGRES_USER=user \
    -e POSTGRES_PASSWORD=password \
    postgres:15 2>/dev/null || echo "PostgreSQL container already running"

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 5

# Create logs directory
mkdir -p logs

echo "Starting services..."

# Start Celery worker in background
celery -A app.celery_app worker --loglevel=info &
CELERY_PID=$!

# Start FastAPI application
echo "FastAPI server starting at http://localhost:8000"
echo "API documentation available at http://localhost:8000/docs"
echo "Press Ctrl+C to stop all services"

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Cleanup on exit
echo "Stopping services..."
kill $CELERY_PID 2>/dev/null
echo "Done!"
