#!/bin/bash

# Script to run tests with proper setup

echo "Setting up test environment..."

# Create test database if it doesn't exist
export DATABASE_URL="sqlite:///./test.db"
export REDIS_URL="redis://localhost:6379/1"  # Use different Redis DB for tests

echo "Running tests..."
pytest tests/ -v --cov=app --cov-report=html --cov-report=term

echo "Test coverage report generated in htmlcov/"
echo "Done!"
