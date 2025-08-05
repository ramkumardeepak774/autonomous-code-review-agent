import json
from celery import current_task
from sqlalchemy.orm import Session
from loguru import logger

from app.celery_app import celery_app
from app.database import SessionLocal, AnalysisTask
from app.agents.code_review_agent import CodeReviewAgent
from app.models import TaskStatus


@celery_app.task(bind=True)
def analyze_pr_task(self, repo_url: str, pr_number: int, github_token: str = None):
    """Celery task to analyze a pull request."""
    task_id = self.request.id
    db = SessionLocal()
    
    try:
        # Update task status to processing
        task_record = db.query(AnalysisTask).filter(AnalysisTask.task_id == task_id).first()
        if task_record:
            task_record.status = TaskStatus.PROCESSING
            db.commit()
        
        logger.info(f"Starting PR analysis task {task_id} for {repo_url} PR #{pr_number}")
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'current': 10, 'total': 100, 'status': 'Initializing agent...'}
        )
        
        # Initialize the code review agent
        agent = CodeReviewAgent(github_token=github_token)
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'current': 30, 'total': 100, 'status': 'Fetching PR data...'}
        )
        
        # Analyze the PR
        import asyncio
        results = asyncio.run(agent.analyze_pr(repo_url, pr_number))
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'current': 90, 'total': 100, 'status': 'Finalizing results...'}
        )
        
        # Convert results to JSON
        results_json = results.model_dump_json()
        
        # Update task record with results
        if task_record:
            task_record.status = TaskStatus.COMPLETED
            task_record.results = results_json
            db.commit()
        
        logger.info(f"PR analysis task {task_id} completed successfully")
        
        return {
            'task_id': task_id,
            'status': 'completed',
            'results': results.model_dump()
        }
        
    except Exception as e:
        logger.error(f"PR analysis task {task_id} failed: {str(e)}")
        
        # Update task record with error
        if task_record:
            task_record.status = TaskStatus.FAILED
            task_record.error_message = str(e)
            db.commit()
        
        # Update task state
        self.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )
        
        raise
    
    finally:
        db.close()


@celery_app.task
def cleanup_old_tasks():
    """Cleanup old completed tasks (run periodically)."""
    from datetime import datetime, timedelta
    
    db = SessionLocal()
    try:
        # Delete tasks older than 7 days
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        
        old_tasks = db.query(AnalysisTask).filter(
            AnalysisTask.created_at < cutoff_date,
            AnalysisTask.status.in_([TaskStatus.COMPLETED, TaskStatus.FAILED])
        ).all()
        
        for task in old_tasks:
            db.delete(task)
        
        db.commit()
        logger.info(f"Cleaned up {len(old_tasks)} old tasks")
        
    except Exception as e:
        logger.error(f"Error cleaning up old tasks: {e}")
        db.rollback()
    finally:
        db.close()
