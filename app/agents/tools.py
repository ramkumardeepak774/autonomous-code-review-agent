from typing import Dict, List, Any
import re
from loguru import logger

from app.services.github_service import GitHubService


class GitHubPRTool:
    """Tool to fetch and analyze GitHub pull request data including files, diffs, and metadata."""

    def __init__(self, github_token: str = None):
        self.github_service = GitHubService(token=github_token)
    
    def _run(self, repo_url: str, pr_number: int) -> Dict[str, Any]:
        """Fetch PR data synchronously (wrapper for async method)."""
        import asyncio
        return asyncio.run(self._fetch_pr_data(repo_url, pr_number))
    
    async def _fetch_pr_data(self, repo_url: str, pr_number: int) -> Dict[str, Any]:
        """Fetch comprehensive PR data."""
        try:
            # Get PR info
            pr_info = await self.github_service.get_pr_info(repo_url, pr_number)
            
            # Get changed files
            pr_files = await self.github_service.get_pr_files(repo_url, pr_number)
            
            # Get diff
            pr_diff = await self.github_service.get_pr_diff(repo_url, pr_number)
            
            # Parse changed lines
            changed_lines = self.github_service.parse_diff_for_changed_lines(pr_diff)
            
            # Get file contents for analysis
            files_content = {}
            for file_info in pr_files:
                if file_info['status'] != 'removed':
                    try:
                        content = await self.github_service.get_file_content(
                            repo_url, 
                            file_info['filename'], 
                            pr_info['head']['sha']
                        )
                        files_content[file_info['filename']] = content
                    except Exception as e:
                        logger.warning(f"Could not fetch content for {file_info['filename']}: {e}")
            
            return {
                "pr_info": {
                    "title": pr_info.get("title"),
                    "description": pr_info.get("body"),
                    "author": pr_info.get("user", {}).get("login"),
                    "base_branch": pr_info.get("base", {}).get("ref"),
                    "head_branch": pr_info.get("head", {}).get("ref"),
                },
                "files": pr_files,
                "diff": pr_diff,
                "changed_lines": changed_lines,
                "files_content": files_content
            }
        except Exception as e:
            logger.error(f"Error fetching PR data: {e}")
            raise


class CodeAnalysisTool:
    """Tool to analyze code for various issues including style, bugs, performance, and best practices."""
    
    def _run(self, file_content: str, file_name: str, changed_lines: List[int] = None) -> Dict[str, Any]:
        """Analyze code content for issues."""
        issues = []
        
        lines = file_content.split('\n')
        file_extension = file_name.split('.')[-1].lower()
        
        # Focus on changed lines if provided
        lines_to_analyze = changed_lines if changed_lines else range(1, len(lines) + 1)
        
        for line_num in lines_to_analyze:
            if line_num <= len(lines):
                line = lines[line_num - 1]
                
                # Style checks
                issues.extend(self._check_style_issues(line, line_num, file_extension))
                
                # Bug checks
                issues.extend(self._check_potential_bugs(line, line_num, file_extension))
                
                # Performance checks
                issues.extend(self._check_performance_issues(line, line_num, file_extension))
                
                # Best practice checks
                issues.extend(self._check_best_practices(line, line_num, file_extension))
        
        return {
            "file_name": file_name,
            "issues": issues,
            "total_lines": len(lines),
            "analyzed_lines": len(lines_to_analyze)
        }
    
    def _check_style_issues(self, line: str, line_num: int, file_extension: str) -> List[Dict]:
        """Check for style-related issues."""
        issues = []
        
        # Long lines
        if len(line) > 120:
            issues.append({
                "type": "style",
                "line": line_num,
                "description": f"Line too long ({len(line)} characters)",
                "suggestion": "Break line into multiple lines or refactor",
                "severity": "low"
            })
        
        # Trailing whitespace
        if line.endswith(' ') or line.endswith('\t'):
            issues.append({
                "type": "style",
                "line": line_num,
                "description": "Trailing whitespace",
                "suggestion": "Remove trailing whitespace",
                "severity": "low"
            })
        
        # Python-specific style checks
        if file_extension == 'py':
            # Missing space after comma
            if re.search(r',[^\s\]]', line):
                issues.append({
                    "type": "style",
                    "line": line_num,
                    "description": "Missing space after comma",
                    "suggestion": "Add space after comma",
                    "severity": "low"
                })
        
        return issues
    
    def _check_potential_bugs(self, line: str, line_num: int, file_extension: str) -> List[Dict]:
        """Check for potential bugs."""
        issues = []
        
        # Python-specific bug checks
        if file_extension == 'py':
            # Potential None comparison
            if 'is None' not in line and ('== None' in line or '!= None' in line):
                issues.append({
                    "type": "bug",
                    "line": line_num,
                    "description": "Use 'is None' instead of '== None'",
                    "suggestion": "Replace '== None' with 'is None'",
                    "severity": "medium"
                })
            
            # Bare except clause
            if re.match(r'\s*except\s*:', line):
                issues.append({
                    "type": "bug",
                    "line": line_num,
                    "description": "Bare except clause",
                    "suggestion": "Specify exception type or use 'except Exception:'",
                    "severity": "high"
                })
        
        return issues
    
    def _check_performance_issues(self, line: str, line_num: int, file_extension: str) -> List[Dict]:
        """Check for performance-related issues."""
        issues = []
        
        # Python-specific performance checks
        if file_extension == 'py':
            # String concatenation in loop (simplified check)
            if '+=' in line and 'str' in line.lower():
                issues.append({
                    "type": "performance",
                    "line": line_num,
                    "description": "Potential inefficient string concatenation",
                    "suggestion": "Consider using join() or f-strings for better performance",
                    "severity": "medium"
                })
        
        return issues
    
    def _check_best_practices(self, line: str, line_num: int, file_extension: str) -> List[Dict]:
        """Check for best practice violations."""
        issues = []
        
        # Python-specific best practice checks
        if file_extension == 'py':
            # TODO comments
            if 'TODO' in line.upper():
                issues.append({
                    "type": "best_practice",
                    "line": line_num,
                    "description": "TODO comment found",
                    "suggestion": "Consider creating a ticket or implementing the TODO",
                    "severity": "low"
                })
            
            # Print statements (should use logging)
            if re.search(r'\bprint\s*\(', line):
                issues.append({
                    "type": "best_practice",
                    "line": line_num,
                    "description": "Print statement found",
                    "suggestion": "Consider using logging instead of print statements",
                    "severity": "low"
                })
        
        return issues
