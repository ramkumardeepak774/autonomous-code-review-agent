# Deployment Guide

## Quick Start

### 1. Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd code-review-agent

# Copy environment file
cp .env.example .env

# Edit .env with your configuration (optional for basic testing)
# Add your GitHub token and OpenAI API key if available

# Start all services
docker-compose up -d

# Check if services are running
docker-compose ps

# View logs
docker-compose logs -f api
```

The API will be available at:
- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- Flower (Celery monitoring): http://localhost:5555

### 2. Local Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start supporting services
docker run -d --name redis -p 6379:6379 redis:7-alpine
docker run -d --name postgres -p 5432:5432 \
    -e POSTGRES_DB=code_review_db \
    -e POSTGRES_USER=user \
    -e POSTGRES_PASSWORD=password \
    postgres:15

# Start the application
./start_local.sh
```

## Testing the API

### 1. Health Check

```bash
curl http://localhost:8000/health
```

### 2. Submit PR for Analysis

```bash
curl -X POST "http://localhost:8000/analyze-pr" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/octocat/Hello-World",
    "pr_number": 1
  }'
```

### 3. Check Task Status

```bash
# Replace TASK_ID with the ID returned from the previous request
curl "http://localhost:8000/status/TASK_ID"
```

### 4. Get Results

```bash
curl "http://localhost:8000/results/TASK_ID"
```

### 5. Using the Example Script

```bash
python example_usage.py
```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Database Configuration
DATABASE_URL=sqlite:///./code_review.db
REDIS_URL=redis://localhost:6379/0

# GitHub Configuration (optional)
GITHUB_TOKEN=your_github_token_here

# AI Configuration (choose one)
OPENAI_API_KEY=your_openai_api_key_here
# OR
OLLAMA_BASE_URL=http://localhost:11434

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Application Configuration
SECRET_KEY=your_secret_key_here
DEBUG=True
LOG_LEVEL=INFO
```

### AI Model Configuration

The system supports two AI backends:

1. **OpenAI GPT-4** (Recommended)
   - Set `OPENAI_API_KEY` in your environment
   - Provides the best code analysis quality

2. **Ollama (Local)**
   - Install Ollama: https://ollama.com/download
   - Pull a model: `ollama pull llama2`
   - Set `OLLAMA_BASE_URL=http://localhost:11434`

## Production Deployment

### 1. Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

### 2. Render

1. Connect your GitHub repository to Render
2. Create a new Web Service
3. Set environment variables in Render dashboard
4. Deploy

### 3. Docker

```bash
# Build image
docker build -t code-review-agent:latest .

# Run with environment variables
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL=your_db_url \
  -e REDIS_URL=your_redis_url \
  -e OPENAI_API_KEY=your_key \
  code-review-agent:latest
```

## Monitoring

### Logs

```bash
# Docker Compose
docker-compose logs -f api

# Local development
tail -f logs/app.log
```

### Celery Monitoring

Access Flower at http://localhost:5555 to monitor:
- Active workers
- Task queue status
- Task execution history
- Worker performance metrics

### Health Checks

The `/health` endpoint provides system status:

```json
{
  "status": "healthy",
  "database": "connected",
  "celery_workers": 1,
  "timestamp": "2024-01-01T10:00:00Z"
}
```

## Troubleshooting

### Common Issues

1. Database Connection Error
   - Ensure PostgreSQL is running
   - Check DATABASE_URL configuration
   - For development, SQLite is used by default

2. Celery Worker Not Starting
   - Ensure Redis is running
   - Check CELERY_BROKER_URL configuration
   - Verify worker logs: `docker-compose logs celery-worker`

3. GitHub API Rate Limiting
   - Add GITHUB_TOKEN to increase rate limits
   - Use authenticated requests for private repositories

4. AI Model Not Responding
   - For OpenAI: Check API key and billing status
   - For Ollama: Ensure service is running and model is pulled

### Debug Mode

Enable debug logging:

```env
DEBUG=True
LOG_LEVEL=DEBUG
```

### Testing

Run the test suite:

```bash
# All tests
python -m pytest

# Specific test file
python -m pytest tests/test_api.py -v

# With coverage
python -m pytest --cov=app
```

## Performance Tuning

### Celery Workers

Scale workers based on load:

```bash
# Docker Compose
docker-compose up --scale celery-worker=3

# Manual
celery -A app.celery_app worker --concurrency=4
```

### Database Optimization

For production, use PostgreSQL with connection pooling:

```env
DATABASE_URL=postgresql://user:pass@host:5432/db?pool_size=20&max_overflow=0
```

### Caching

Redis is used for:
- Celery message broker
- Task result storage
- Session caching (future feature)

## Security Considerations

1. Environment Variables: Never commit secrets to version control
2. API Authentication: Add authentication for production use
3. Rate Limiting: Implement rate limiting for public APIs
4. CORS: Configure CORS appropriately for your domain
5. HTTPS: Use HTTPS in production
6. Database: Use strong passwords and connection encryption
