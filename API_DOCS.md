# Code Review Agent API Documentation

## Overview

The Code Review Agent API provides endpoints to analyze GitHub pull requests using AI-powered code review agents. The system processes requests asynchronously and provides real-time status updates.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API doesn't require authentication for basic usage. GitHub tokens can be provided in requests for accessing private repositories.

## Endpoints

### 1. Root Endpoint

**GET** `/`

Returns basic API information and available endpoints.

**Response:**
```json
{
  "message": "Code Review Agent API",
  "version": "1.0.0",
  "docs": "/docs",
  "endpoints": {
    "analyze_pr": "POST /analyze-pr",
    "task_status": "GET /status/{task_id}",
    "task_results": "GET /results/{task_id}"
  }
}
```

### 2. Analyze Pull Request

**POST** `/analyze-pr`

Submits a GitHub pull request for analysis.

**Request Body:**
```json
{
  "repo_url": "https://github.com/owner/repository",
  "pr_number": 123,
  "github_token": "ghp_xxxxxxxxxxxx"  // Optional
}
```

**Parameters:**
- `repo_url` (required): Full GitHub repository URL
- `pr_number` (required): Pull request number
- `github_token` (optional): GitHub personal access token for private repos

**Response:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "PR analysis task has been queued for processing"
}
```

**Status Codes:**
- `200`: Task successfully queued
- `422`: Invalid request data
- `500`: Internal server error

### 3. Get Task Status

**GET** `/status/{task_id}`

Retrieves the current status of an analysis task.

**Parameters:**
- `task_id` (path): UUID of the analysis task

**Response:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "created_at": "2024-01-01T10:00:00.000Z",
  "updated_at": "2024-01-01T10:05:30.000Z",
  "progress": "Analyzing file 3 of 7..."
}
```

**Task Status Values:**
- `pending`: Task is queued but not yet started
- `processing`: Task is currently being processed
- `completed`: Task completed successfully
- `failed`: Task failed with an error

**Status Codes:**
- `200`: Status retrieved successfully
- `404`: Task not found
- `500`: Internal server error

### 4. Get Task Results

**GET** `/results/{task_id}`

Retrieves the analysis results for a completed task.

**Parameters:**
- `task_id` (path): UUID of the analysis task

**Response:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "results": {
    "files": [
      {
        "name": "src/main.py",
        "issues": [
          {
            "type": "style",
            "line": 15,
            "description": "Line too long (125 characters)",
            "suggestion": "Break line into multiple lines or refactor",
            "severity": "low"
          },
          {
            "type": "bug",
            "line": 23,
            "description": "Use 'is None' instead of '== None'",
            "suggestion": "Replace '== None' with 'is None'",
            "severity": "medium"
          }
        ]
      }
    ],
    "summary": {
      "total_files": 1,
      "total_issues": 2,
      "critical_issues": 0,
      "high_issues": 0,
      "medium_issues": 1,
      "low_issues": 1
    }
  },
  "error_message": null,
  "created_at": "2024-01-01T10:00:00.000Z",
  "updated_at": "2024-01-01T10:10:45.000Z"
}
```

**Issue Types:**
- `style`: Code formatting and style issues
- `bug`: Potential bugs or logical errors
- `performance`: Performance optimization opportunities
- `security`: Security vulnerabilities or concerns
- `best_practice`: Best practice violations

**Severity Levels:**
- `low`: Minor issues that don't affect functionality
- `medium`: Issues that should be addressed
- `high`: Important issues that may cause problems
- `critical`: Severe issues that must be fixed

**Status Codes:**
- `200`: Results retrieved successfully
- `404`: Task not found
- `500`: Internal server error

### 5. Health Check

**GET** `/health`

Checks the health status of the API and its dependencies.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "celery_workers": 2,
  "timestamp": "2024-01-01T10:00:00.000Z"
}
```

**Status Codes:**
- `200`: Service is healthy
- `503`: Service is unhealthy

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "detail": "Error description"
}
```

Common error scenarios:
- Invalid GitHub repository URL
- Pull request not found
- GitHub API rate limit exceeded
- Task processing timeout
- Database connection issues

## Rate Limiting

Currently, no rate limiting is implemented. In production, consider implementing rate limiting based on IP address or API key.

## Example Usage

### Using cURL

```bash
# Submit PR for analysis
curl -X POST "http://localhost:8000/analyze-pr" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/octocat/Hello-World",
    "pr_number": 1
  }'

# Check task status
curl "http://localhost:8000/status/550e8400-e29b-41d4-a716-446655440000"

# Get results
curl "http://localhost:8000/results/550e8400-e29b-41d4-a716-446655440000"
```

### Using Python

```python
import requests
import time

# Submit analysis request
response = requests.post("http://localhost:8000/analyze-pr", json={
    "repo_url": "https://github.com/octocat/Hello-World",
    "pr_number": 1
})
task_id = response.json()["task_id"]

# Poll for completion
while True:
    status_response = requests.get(f"http://localhost:8000/status/{task_id}")
    status = status_response.json()["status"]
    
    if status == "completed":
        # Get results
        results_response = requests.get(f"http://localhost:8000/results/{task_id}")
        results = results_response.json()
        print(f"Analysis found {results['results']['summary']['total_issues']} issues")
        break
    elif status == "failed":
        print("Analysis failed")
        break
    
    time.sleep(5)  # Wait 5 seconds before checking again
```

## Interactive Documentation

Visit `http://localhost:8000/docs` for interactive API documentation powered by Swagger UI, where you can test endpoints directly from your browser.
