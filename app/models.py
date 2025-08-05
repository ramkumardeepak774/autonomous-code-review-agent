from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class IssueType(str, Enum):
    STYLE = "style"
    BUG = "bug"
    PERFORMANCE = "performance"
    BEST_PRACTICE = "best_practice"
    SECURITY = "security"


class AnalyzePRRequest(BaseModel):
    repo_url: HttpUrl
    pr_number: int
    github_token: Optional[str] = None


class CodeIssue(BaseModel):
    type: IssueType
    line: int
    description: str
    suggestion: str
    severity: str = "medium"  # low, medium, high, critical


class FileAnalysis(BaseModel):
    name: str
    issues: List[CodeIssue]


class AnalysisSummary(BaseModel):
    total_files: int
    total_issues: int
    critical_issues: int
    high_issues: int = 0
    medium_issues: int = 0
    low_issues: int = 0


class AnalysisResults(BaseModel):
    files: List[FileAnalysis]
    summary: AnalysisSummary


class TaskResponse(BaseModel):
    task_id: str
    status: TaskStatus
    message: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    progress: Optional[str] = None


class TaskResultsResponse(BaseModel):
    task_id: str
    status: TaskStatus
    results: Optional[AnalysisResults] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
