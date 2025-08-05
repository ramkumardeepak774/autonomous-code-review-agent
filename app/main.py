from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uuid
import json
from loguru import logger

from app.config import settings
from app.database import get_db, create_tables, AnalysisTask
from app.models import (
    AnalyzePRRequest, TaskResponse, TaskStatusResponse, 
    TaskResultsResponse, TaskStatus, AnalysisResults
)
from app.tasks import analyze_pr_task
from app.celery_app import celery_app

# Create tables on startup (only if database is available)
try:
    create_tables()
    logger.info("Database tables created successfully")
except Exception as e:
    logger.warning(f"Could not create database tables: {e}")

app = FastAPI(
    title=settings.project_name,
    version="1.0.0",
    description="Autonomous Code Review Agent System",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logger.add("logs/app.log", rotation="500 MB", level=settings.log_level)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Code Review Agent API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "analyze_pr": "POST /analyze-pr",
            "task_status": "GET /status/{task_id}",
            "task_results": "GET /results/{task_id}"
        }
    }


@app.post("/analyze-pr", response_model=TaskResponse)
async def analyze_pr(
    request: AnalyzePRRequest,
    db: Session = Depends(get_db)
):
    """
    Submit a pull request for analysis.
    
    This endpoint accepts a GitHub repository URL and PR number,
    then queues the analysis task for asynchronous processing.
    """
    try:
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Create task record in database
        task_record = AnalysisTask(
            task_id=task_id,
            repo_url=str(request.repo_url),
            pr_number=request.pr_number,
            status=TaskStatus.PENDING
        )
        db.add(task_record)
        db.commit()
        
        # Queue the analysis task
        analyze_pr_task.apply_async(
            args=[str(request.repo_url), request.pr_number, request.github_token],
            task_id=task_id
        )
        
        logger.info(f"Queued PR analysis task {task_id} for {request.repo_url} PR #{request.pr_number}")
        
        return TaskResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            message="PR analysis task has been queued for processing"
        )
        
    except Exception as e:
        logger.error(f"Error submitting PR analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit analysis: {str(e)}")


@app.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str, db: Session = Depends(get_db)):
    """
    Get the status of an analysis task.
    
    Returns the current status of the task (pending, processing, completed, failed)
    along with timestamps and progress information if available.
    """
    try:
        # Get task from database
        task_record = db.query(AnalysisTask).filter(AnalysisTask.task_id == task_id).first()
        
        if not task_record:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Get additional info from Celery if task is in progress
        progress = None
        try:
            celery_result = celery_app.AsyncResult(task_id)

            if celery_result.state == 'PROGRESS':
                progress = celery_result.info.get('status', 'Processing...')
            elif celery_result.state == 'FAILURE':
                # Update database if Celery shows failure but DB doesn't
                if task_record.status != TaskStatus.FAILED:
                    task_record.status = TaskStatus.FAILED
                    task_record.error_message = str(celery_result.info)
                    db.commit()
        except Exception as e:
            logger.warning(f"Could not get Celery task status: {e}")
            # Continue without Celery status
        
        return TaskStatusResponse(
            task_id=task_id,
            status=task_record.status,
            created_at=task_record.created_at,
            updated_at=task_record.updated_at,
            progress=progress
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")


@app.get("/results/{task_id}", response_model=TaskResultsResponse)
async def get_task_results(task_id: str, db: Session = Depends(get_db)):
    """
    Get the results of a completed analysis task.
    
    Returns the full analysis results including issues found,
    file-by-file breakdown, and summary statistics.
    """
    try:
        # Get task from database
        task_record = db.query(AnalysisTask).filter(AnalysisTask.task_id == task_id).first()
        
        if not task_record:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Parse results if available
        results = None
        if task_record.results:
            try:
                results_dict = json.loads(task_record.results)
                results = AnalysisResults(**results_dict)
            except Exception as e:
                logger.error(f"Error parsing results for task {task_id}: {e}")
        
        return TaskResultsResponse(
            task_id=task_id,
            status=task_record.status,
            results=results,
            error_message=task_record.error_message,
            created_at=task_record.created_at,
            updated_at=task_record.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task results: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task results: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check database connection
        from sqlalchemy import text
        db = next(get_db())
        db.execute(text("SELECT 1"))
        db.close()
        
        # Check Celery connection
        try:
            celery_inspect = celery_app.control.inspect()
            active_workers = celery_inspect.active()
            worker_count = len(active_workers) if active_workers else 0
        except Exception:
            worker_count = 0
        
        return {
            "status": "healthy",
            "database": "connected",
            "celery_workers": worker_count,
            "timestamp": "2024-01-01T00:00:00Z"  # You might want to use actual timestamp
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
