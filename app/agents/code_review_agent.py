from typing import Dict, List, Any
from loguru import logger

from app.agents.tools import GitHubPRTool, CodeAnalysisTool
from app.agents.prompts import CODE_REVIEW_AGENT_PROMPT, ANALYSIS_TASK_PROMPT
from app.models import FileAnalysis, CodeIssue, AnalysisSummary, AnalysisResults
from app.config import settings


class CodeReviewAgent:
    """
    Simplified code review agent that analyzes GitHub pull requests.
    This version doesn't use CrewAI to avoid dependency issues.
    """

    def __init__(self, github_token: str = None):
        self.github_token = github_token
        self.github_tool = GitHubPRTool(github_token=github_token)
        self.analysis_tool = CodeAnalysisTool()
    
    async def analyze_pr(self, repo_url: str, pr_number: int) -> AnalysisResults:
        """Main method to analyze a pull request."""
        try:
            logger.info(f"Starting analysis of PR #{pr_number} from {repo_url}")
            
            # Fetch PR data
            pr_data = await self.github_tool._fetch_pr_data(repo_url, pr_number)
            
            # Analyze each file
            file_analyses = []
            
            for file_info in pr_data['files']:
                if file_info['status'] == 'removed':
                    continue
                
                file_name = file_info['filename']
                
                # Skip binary files and certain file types
                if self._should_skip_file(file_name):
                    continue
                
                logger.info(f"Analyzing file: {file_name}")
                
                # Get file content
                file_content = pr_data['files_content'].get(file_name, "")
                if not file_content:
                    continue
                
                # Get changed lines for this file
                changed_lines = pr_data['changed_lines'].get(file_name, [])
                
                # Analyze the file
                analysis_result = self.analysis_tool._run(
                    file_content=file_content,
                    file_name=file_name,
                    changed_lines=changed_lines
                )
                
                # Convert to our model format
                issues = []
                for issue in analysis_result['issues']:
                    issues.append(CodeIssue(
                        type=issue['type'],
                        line=issue['line'],
                        description=issue['description'],
                        suggestion=issue['suggestion'],
                        severity=issue['severity']
                    ))
                
                if issues:  # Only include files with issues
                    file_analyses.append(FileAnalysis(
                        name=file_name,
                        issues=issues
                    ))
            
            # Create summary
            total_issues = sum(len(fa.issues) for fa in file_analyses)
            critical_issues = sum(1 for fa in file_analyses for issue in fa.issues if issue.severity == 'critical')
            high_issues = sum(1 for fa in file_analyses for issue in fa.issues if issue.severity == 'high')
            medium_issues = sum(1 for fa in file_analyses for issue in fa.issues if issue.severity == 'medium')
            low_issues = sum(1 for fa in file_analyses for issue in fa.issues if issue.severity == 'low')
            
            summary = AnalysisSummary(
                total_files=len(file_analyses),
                total_issues=total_issues,
                critical_issues=critical_issues,
                high_issues=high_issues,
                medium_issues=medium_issues,
                low_issues=low_issues
            )
            
            results = AnalysisResults(
                files=file_analyses,
                summary=summary
            )
            
            logger.info(f"Analysis completed. Found {total_issues} issues across {len(file_analyses)} files")
            return results
            
        except Exception as e:
            logger.error(f"Error analyzing PR: {e}")
            raise
    
    def _should_skip_file(self, file_name: str) -> bool:
        """Determine if a file should be skipped during analysis."""
        skip_extensions = {
            '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx',
            '.zip', '.tar', '.gz', '.rar',
            '.mp4', '.avi', '.mov', '.mp3', '.wav',
            '.lock', '.log'
        }
        
        skip_patterns = {
            'node_modules/', 'venv/', '__pycache__/', '.git/',
            'dist/', 'build/', 'target/', '.idea/', '.vscode/'
        }
        
        # Check file extension
        for ext in skip_extensions:
            if file_name.lower().endswith(ext):
                return True
        
        # Check path patterns
        for pattern in skip_patterns:
            if pattern in file_name:
                return True
        
        return False
