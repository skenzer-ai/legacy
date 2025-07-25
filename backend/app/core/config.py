import os
from pydantic_settings import BaseSettings

# Get the root directory of the project (the parent of 'backend')
# This resolves to the 'backend' directory, so we need to go up one more level
# `__file__` is .../backend/app/core/config.py
# `os.path.dirname(__file__)` is .../backend/app/core
# We need to go up 3 levels to get to the project root.
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class Settings(BaseSettings):
    # File Paths - constructed to be absolute
    USER_GUIDE_PATH: str = os.path.join(ROOT_DIR, "user_docs/infraon_user_guide.md")
    API_SPEC_PATH: str = os.path.join(ROOT_DIR, "user_docs/infraon-api.json")
    PROCESSED_DATA_DIR: str = os.path.join(ROOT_DIR, "processed_data")
    STATE_FILE: str = os.path.join(PROCESSED_DATA_DIR, "processing_state.json")
    
    # Models
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    CROSS_ENCODER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()