import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio

from app.agents.code_review_agent import CodeReviewAgent
from app.agents.tools import GitHubPRTool, CodeAnalysisTool
from app.services.github_service import GitHubService


class TestGitHubService:
    """Test GitHub service functionality."""
    
    def test_parse_repo_url(self):
        """Test parsing GitHub repository URLs."""
        service = GitHubService()
        
        # Test various URL formats
        owner, repo = service.parse_repo_url("https://github.com/octocat/Hello-World")
        assert owner == "octocat"
        assert repo == "Hello-World"
        
        owner, repo = service.parse_repo_url("https://github.com/user/repo.git")
        assert owner == "user"
        assert repo == "repo"
    
    def test_parse_repo_url_invalid(self):
        """Test parsing invalid repository URLs."""
        service = GitHubService()
        
        with pytest.raises(ValueError):
            service.parse_repo_url("https://github.com/invalid")
        
        with pytest.raises(ValueError):
            service.parse_repo_url("not-a-url")
    
    def test_parse_diff_for_changed_lines(self):
        """Test parsing diff to extract changed lines."""
        service = GitHubService()
        
        sample_diff = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,4 @@
 def hello():
+    print("Hello")
     return "world"
 
@@ -10,2 +11,3 @@ def another_function():
     x = 1
+    y = 2
     return x"""
        
        changed_lines = service.parse_diff_for_changed_lines(sample_diff)
        
        assert "test.py" in changed_lines
        assert 1 in changed_lines["test.py"]  # Line with print added
        assert 11 in changed_lines["test.py"]  # Line with y = 2 added


class TestCodeAnalysisTool:
    """Test code analysis tool functionality."""
    
    def test_analyze_python_file(self):
        """Test analyzing Python code for issues."""
        tool = CodeAnalysisTool()
        
        sample_code = """def test_function():
    x = 1
    print("Debug message")  # Should trigger best practice issue
    if x == None:  # Should trigger bug issue
        return x
    very_long_line_that_exceeds_the_recommended_length_limit_and_should_trigger_a_style_issue_for_being_too_long = True
    return x"""
        
        result = tool._run(
            file_content=sample_code,
            file_name="test.py",
            changed_lines=[1, 2, 3, 4, 5, 6, 7]
        )
        
        assert result["file_name"] == "test.py"
        assert len(result["issues"]) > 0
        
        # Check for specific issue types
        issue_types = [issue["type"] for issue in result["issues"]]
        assert "best_practice" in issue_types  # print statement
        assert "bug" in issue_types  # == None instead of is None
        assert "style" in issue_types  # long line
    
    def test_should_skip_file(self):
        """Test file skipping logic."""
        agent = CodeReviewAgent()
        
        # Should skip binary files
        assert agent._should_skip_file("image.png") == True
        assert agent._should_skip_file("document.pdf") == True
        
        # Should skip certain directories
        assert agent._should_skip_file("node_modules/package.json") == True
        assert agent._should_skip_file("venv/lib/python.py") == True
        
        # Should not skip code files
        assert agent._should_skip_file("main.py") == False
        assert agent._should_skip_file("src/utils.js") == False


class TestGitHubPRTool:
    """Test GitHub PR tool functionality."""
    
    @pytest.mark.asyncio
    async def test_fetch_pr_data(self):
        """Test fetching PR data from GitHub."""
        with patch('app.services.github_service.GitHubService') as mock_service:
            # Mock the service methods
            mock_instance = mock_service.return_value
            mock_instance.get_pr_info = AsyncMock(return_value={
                "title": "Test PR",
                "body": "Test description",
                "user": {"login": "testuser"},
                "base": {"ref": "main"},
                "head": {"ref": "feature", "sha": "abc123"}
            })
            mock_instance.get_pr_files = AsyncMock(return_value=[
                {"filename": "test.py", "status": "modified"}
            ])
            mock_instance.get_pr_diff = AsyncMock(return_value="diff content")
            mock_instance.parse_diff_for_changed_lines = MagicMock(return_value={
                "test.py": [1, 2, 3]
            })
            mock_instance.get_file_content = AsyncMock(return_value="def test(): pass")
            
            tool = GitHubPRTool()
            tool.github_service = mock_instance
            
            result = await tool._fetch_pr_data("https://github.com/test/repo", 1)
            
            assert "pr_info" in result
            assert "files" in result
            assert "diff" in result
            assert "changed_lines" in result
            assert "files_content" in result
            
            assert result["pr_info"]["title"] == "Test PR"
            assert result["files_content"]["test.py"] == "def test(): pass"


class TestCodeReviewAgent:
    """Test the main code review agent."""
    
    @pytest.mark.asyncio
    async def test_analyze_pr_integration(self):
        """Test the complete PR analysis workflow."""
        with patch('app.agents.code_review_agent.GitHubPRTool') as mock_github_tool, \
             patch('app.agents.code_review_agent.CodeAnalysisTool') as mock_analysis_tool:
            
            # Mock GitHub tool
            mock_github_instance = mock_github_tool.return_value
            mock_github_instance._fetch_pr_data = AsyncMock(return_value={
                "pr_info": {
                    "title": "Test PR",
                    "description": "Test description",
                    "author": "testuser",
                    "base_branch": "main",
                    "head_branch": "feature"
                },
                "files": [
                    {"filename": "test.py", "status": "modified"}
                ],
                "diff": "diff content",
                "changed_lines": {"test.py": [1, 2, 3]},
                "files_content": {"test.py": "def test(): pass"}
            })
            
            # Mock analysis tool
            mock_analysis_instance = mock_analysis_tool.return_value
            mock_analysis_instance._run = MagicMock(return_value={
                "file_name": "test.py",
                "issues": [
                    {
                        "type": "style",
                        "line": 1,
                        "description": "Test issue",
                        "suggestion": "Fix it",
                        "severity": "low"
                    }
                ],
                "total_lines": 1,
                "analyzed_lines": 1
            })
            
            agent = CodeReviewAgent()
            agent.github_tool = mock_github_instance
            agent.analysis_tool = mock_analysis_instance
            
            result = await agent.analyze_pr("https://github.com/test/repo", 1)
            
            assert result.summary.total_files == 1
            assert result.summary.total_issues == 1
            assert result.summary.low_issues == 1
            assert len(result.files) == 1
            assert result.files[0].name == "test.py"
            assert len(result.files[0].issues) == 1
