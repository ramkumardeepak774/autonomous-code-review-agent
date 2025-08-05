# Autonomous Code Review Agent System

An AI-powered system that automatically analyzes GitHub pull requests and provides comprehensive code reviews using advanced language models and agent frameworks.

## Features

- **Asynchronous Processing**: Uses Celery for scalable, non-blocking PR analysis
- **AI-Powered Reviews**: Leverages CrewAI framework with LLM integration
- **Comprehensive Analysis**: Detects style issues, bugs, performance problems, and best practices
- **RESTful API**: Clean FastAPI endpoints for easy integration
- **Real-time Status**: Track analysis progress and retrieve results
- **Multi-language Support**: Extensible architecture for different programming languages
- **Docker Ready**: Complete containerization with docker-compose
- **Production Ready**: Includes logging, error handling, and health checks

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │  Celery Worker  │    │   PostgreSQL    │
│                 │    │                 │    │                 │
│ • API Endpoints │◄──►│ • PR Analysis   │◄──►│ • Task Storage  │
│ • Task Queue    │    │ • AI Agents     │    │ • Results Cache │
│ • Status Track  │    │ • GitHub API    │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │      Redis      │
                    │                 │
                    │ • Message Queue │
                    │ • Result Store  │
                    │ • Session Cache │
                    └─────────────────┘
```

## API Endpoints

### POST `/analyze-pr`
Submit a pull request for analysis.

**Request:**
```json
{
  "repo_url": "https://github.com/user/repo",
  "pr_number": 123,
  "github_token": "optional_github_token"
}
```

**Response:**
```json
{
  "task_id": "abc123-def456-ghi789",
  "status": "pending",
  "message": "PR analysis task has been queued for processing"
}
```

### GET `/status/{task_id}`
Check the status of an analysis task.

**Response:**
```json
{
  "task_id": "abc123-def456-ghi789",
  "status": "processing",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:05:00Z",
  "progress": "Analyzing file 2 of 5..."
}
```

### GET `/results/{task_id}`
Retrieve analysis results.

**Response:**
```json
{
  "task_id": "abc123-def456-ghi789",
  "status": "completed",
  "results": {
    "files": [
      {
        "name": "main.py",
        "issues": [
          {
            "type": "style",
            "line": 15,
            "description": "Line too long (125 characters)",
            "suggestion": "Break line into multiple lines",
            "severity": "low"
          }
        ]
      }
    ],
    "summary": {
      "total_files": 1,
      "total_issues": 1,
      "critical_issues": 0,
      "high_issues": 0,
      "medium_issues": 0,
      "low_issues": 1
    }
  },
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:10:00Z"
}
```

## Installation & Setup

### Prerequisites
- Python 3.8+
- Docker & Docker Compose
- PostgreSQL (if running locally)
- Redis (if running locally)

### Quick Start with Docker

1. **Clone the repository:**
```bash
git clone <repository-url>
cd code-review-agent
```

2. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start all services:**
```bash
docker-compose up -d
```

4. **Verify the setup:**
```bash
curl http://localhost:8000/health
```

The API will be available at `http://localhost:8000` and the documentation at `http://localhost:8000/docs`.

### Local Development Setup

1. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up databases:**
```bash
# Start PostgreSQL and Redis
docker run -d --name postgres -p 5432:5432 -e POSTGRES_DB=code_review_db -e POSTGRES_USER=user -e POSTGRES_PASSWORD=password postgres:15
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

4. **Run the application:**
```bash
# Terminal 1: Start FastAPI
uvicorn app.main:app --reload

# Terminal 2: Start Celery worker
celery -A app.celery_app worker --loglevel=info

# Terminal 3: Start Celery beat (optional)
celery -A app.celery_app beat --loglevel=info
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_api.py -v
```

## Configuration

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:password@localhost:5432/code_review_db` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `GITHUB_TOKEN` | GitHub API token (optional) | None |
| `OPENAI_API_KEY` | OpenAI API key | None |
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` |

## AI Agent Configuration

The system uses CrewAI framework with configurable LLM backends:

- **OpenAI GPT-4**: Set `OPENAI_API_KEY` for cloud-based inference
- **Ollama**: Use local models by setting `OLLAMA_BASE_URL`

### Supported Analysis Types

1. **Style Issues**: Line length, formatting, conventions
2. **Bug Detection**: Null checks, exception handling, logic errors
3. **Performance**: Inefficient patterns, optimization opportunities
4. **Security**: Vulnerability detection, best practices
5. **Best Practices**: Language-specific conventions, code quality

## Monitoring

- **API Documentation**: `http://localhost:8000/docs`
- **Celery Monitoring**: `http://localhost:5555` (Flower)
- **Health Check**: `http://localhost:8000/health`
- **Logs**: Available in `./logs/` directory

## Deployment

### Production Considerations

1. **Environment Variables**: Use secure secret management
2. **Database**: Use managed PostgreSQL service
3. **Redis**: Use managed Redis service
4. **Scaling**: Increase Celery workers based on load
5. **Monitoring**: Implement proper logging and metrics
6. **Security**: Add authentication and rate limiting

### Example Production Deployment

```bash
# Build and push Docker image
docker build -t code-review-agent:latest .
docker push your-registry/code-review-agent:latest

# Deploy with production docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Future Improvements

- GitHub webhook integration
- Support for more programming languages
- Advanced security vulnerability detection
- Integration with code quality tools (SonarQube, CodeClimate)
- Custom rule configuration
- Slack/Teams notifications
- Performance metrics and analytics
- Multi-repository batch processing
