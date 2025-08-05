from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./code_review.db"
    redis_url: str = "redis://localhost:6379/0"
    
    # GitHub
    github_token: Optional[str] = None
    
    # AI Configuration
    openai_api_key: Optional[str] = None
    ollama_base_url: str = "http://localhost:11434"
    
    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # Application
    secret_key: str = "your-secret-key-change-in-production"
    debug: bool = True
    log_level: str = "INFO"
    
    # API
    api_v1_str: str = "/api/v1"
    project_name: str = "Code Review Agent"
    
    class Config:
        env_file = ".env"


settings = Settings()
