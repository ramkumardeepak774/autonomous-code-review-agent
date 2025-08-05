import pytest
from unittest.mock import patch, MagicMock
import json

from app.models import TaskStatus


class TestAnalyzePREndpoint:
    """Test the /analyze-pr endpoint."""
    
    def test_analyze_pr_success(self, client, sample_pr_request):
        """Test successful PR analysis submission."""
        with patch('app.main.analyze_pr_task.apply_async') as mock_task:
            mock_task.return_value = MagicMock()
            
            response = client.post("/analyze-pr", json=sample_pr_request)
            
            assert response.status_code == 200
            data = response.json()
            assert "task_id" in data
            assert data["status"] == TaskStatus.PENDING
            assert "queued for processing" in data["message"]
    
    def test_analyze_pr_invalid_url(self, client):
        """Test PR analysis with invalid URL."""
        invalid_request = {
            "repo_url": "not-a-valid-url",
            "pr_number": 1
        }
        
        response = client.post("/analyze-pr", json=invalid_request)
        assert response.status_code == 422  # Validation error
    
    def test_analyze_pr_missing_fields(self, client):
        """Test PR analysis with missing required fields."""
        incomplete_request = {
            "repo_url": "https://github.com/octocat/Hello-World"
            # Missing pr_number
        }
        
        response = client.post("/analyze-pr", json=incomplete_request)
        assert response.status_code == 422


class TestTaskStatusEndpoint:
    """Test the /status/{task_id} endpoint."""
    
    def test_get_task_status_success(self, client, db_session):
        """Test getting status of existing task."""
        from app.database import AnalysisTask
        
        # Create a test task
        task = AnalysisTask(
            task_id="test-task-123",
            repo_url="https://github.com/test/repo",
            pr_number=1,
            status=TaskStatus.PROCESSING
        )
        db_session.add(task)
        db_session.commit()
        
        response = client.get("/status/test-task-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-task-123"
        assert data["status"] == TaskStatus.PROCESSING
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_get_task_status_not_found(self, client):
        """Test getting status of non-existent task."""
        response = client.get("/status/non-existent-task")
        
        assert response.status_code == 404
        assert "Task not found" in response.json()["detail"]


class TestTaskResultsEndpoint:
    """Test the /results/{task_id} endpoint."""
    
    def test_get_task_results_success(self, client, db_session):
        """Test getting results of completed task."""
        from app.database import AnalysisTask
        
        # Sample results
        sample_results = {
            "files": [
                {
                    "name": "test.py",
                    "issues": [
                        {
                            "type": "style",
                            "line": 1,
                            "description": "Line too long",
                            "suggestion": "Break line",
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
        }
        
        # Create a completed task
        task = AnalysisTask(
            task_id="completed-task-123",
            repo_url="https://github.com/test/repo",
            pr_number=1,
            status=TaskStatus.COMPLETED,
            results=json.dumps(sample_results)
        )
        db_session.add(task)
        db_session.commit()
        
        response = client.get("/results/completed-task-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "completed-task-123"
        assert data["status"] == TaskStatus.COMPLETED
        assert data["results"] is not None
        assert data["results"]["summary"]["total_issues"] == 1
    
    def test_get_task_results_not_found(self, client):
        """Test getting results of non-existent task."""
        response = client.get("/results/non-existent-task")
        
        assert response.status_code == 404
        assert "Task not found" in response.json()["detail"]


class TestHealthEndpoint:
    """Test the /health endpoint."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        with patch('app.main.celery_app.control.inspect') as mock_inspect:
            mock_inspect.return_value.active.return_value = {"worker1": []}
            
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "database" in data
            assert "celery_workers" in data


class TestRootEndpoint:
    """Test the root endpoint."""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns API information."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data
        assert "analyze_pr" in data["endpoints"]
