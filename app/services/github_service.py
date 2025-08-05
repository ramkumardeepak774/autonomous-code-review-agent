import httpx
import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
from loguru import logger

from app.config import settings


class GitHubService:
    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.github_token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "CodeReviewAgent/1.0"
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
    
    def parse_repo_url(self, repo_url: str) -> Tuple[str, str]:
        """Parse GitHub repo URL to extract owner and repo name."""
        parsed = urlparse(str(repo_url))
        path_parts = parsed.path.strip('/').split('/')
        
        if len(path_parts) >= 2:
            owner = path_parts[0]
            repo = path_parts[1].replace('.git', '')
            return owner, repo
        else:
            raise ValueError(f"Invalid GitHub repository URL: {repo_url}")
    
    async def get_pr_info(self, repo_url: str, pr_number: int) -> Dict:
        """Get pull request information."""
        owner, repo = self.parse_repo_url(repo_url)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def get_pr_files(self, repo_url: str, pr_number: int) -> List[Dict]:
        """Get files changed in the pull request."""
        owner, repo = self.parse_repo_url(repo_url)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/files",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def get_file_content(self, repo_url: str, file_path: str, ref: str) -> str:
        """Get content of a specific file at a specific commit."""
        owner, repo = self.parse_repo_url(repo_url)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/repos/{owner}/{repo}/contents/{file_path}",
                headers=self.headers,
                params={"ref": ref}
            )
            response.raise_for_status()
            
            content_data = response.json()
            if content_data.get("encoding") == "base64":
                import base64
                return base64.b64decode(content_data["content"]).decode("utf-8")
            else:
                return content_data["content"]
    
    async def get_pr_diff(self, repo_url: str, pr_number: int) -> str:
        """Get the diff for the entire pull request."""
        owner, repo = self.parse_repo_url(repo_url)
        
        headers = {**self.headers, "Accept": "application/vnd.github.v3.diff"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}",
                headers=headers
            )
            response.raise_for_status()
            return response.text
    
    def parse_diff_for_changed_lines(self, diff_content: str) -> Dict[str, List[int]]:
        """Parse diff to extract changed line numbers for each file."""
        changed_lines = {}
        current_file = None
        
        for line in diff_content.split('\n'):
            # File header
            if line.startswith('diff --git'):
                # Extract filename from diff header
                match = re.search(r'b/(.+)$', line)
                if match:
                    current_file = match.group(1)
                    changed_lines[current_file] = []
            
            # Hunk header
            elif line.startswith('@@') and current_file:
                # Extract line numbers from hunk header
                match = re.search(r'\+(\d+),?(\d+)?', line)
                if match:
                    start_line = int(match.group(1))
                    line_count = int(match.group(2)) if match.group(2) else 1
                    
                    # Add all lines in this hunk
                    for i in range(start_line, start_line + line_count):
                        changed_lines[current_file].append(i)
        
        return changed_lines
