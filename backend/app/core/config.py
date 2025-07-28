import os
from pydantic_settings import BaseSettings
from typing import Optional

# Get the root directory of the project (the parent of 'backend')
# This resolves to the 'backend' directory, so we need to go up one more level
# `__file__` is .../backend/app/core/config.py
# `os.path.dirname(__file__)` is .../backend/app/core
# We need to go up 3 levels to get to the project root.
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class Settings(BaseSettings):
    # Environment
    environment: str = "development"
    debug: bool = True
    
    # Database Configuration (SSH Remote Environment)
    database_url: str = "sqlite+aiosqlite:///./augment_dev.db"  # SQLite for development simplicity
    database_echo: bool = False
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379"
    redis_password: Optional[str] = None
    
    # Authentication
    secret_key: str = "your-secret-key-change-in-production"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    algorithm: str = "HS256"
    
    # Celery Configuration
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # File Paths - constructed to be absolute
    USER_GUIDE_PATH: str = os.path.join(ROOT_DIR, "user_docs/infraon_user_guide.md")
    API_SPEC_PATH: str = os.path.join(ROOT_DIR, "user_docs/infraon-api.json")
    PROCESSED_DATA_DIR: str = os.path.join(ROOT_DIR, "processed_data")
    STATE_FILE: str = os.path.join(PROCESSED_DATA_DIR, "processing_state.json")
    
    # AI Models
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    CROSS_ENCODER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    MODEL_CACHE_DIR: str = os.path.expanduser("~/.cache/huggingface")
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # CORS Configuration
    cors_origins: list = [
        "http://localhost:3000",
        "http://127.0.0.1:3000", 
        "http://ssh.skenzer.com:3000"
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Allow extra fields in .env without validation errors

settings = Settings()