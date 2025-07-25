from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import os

class ProcessingSettings(BaseSettings):
    """
    Configuration settings for the document processing pipeline.
    """
    model_config = SettingsConfigDict(env_file=os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'), env_file_encoding='utf-8', extra='ignore')

    # --- Directory Paths ---
    # Using Field with default_factory to construct path relative to this file's location
    base_dir: str = Field(default_factory=lambda: os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    
    @property
    def user_docs_path(self) -> str:
        return os.path.join(self.base_dir, "user_docs")

    @property
    def faiss_db_path(self) -> str:
        return os.path.join(self.base_dir, "data", "faiss_db")

    @property
    def tfidf_path(self) -> str:
        return os.path.join(self.base_dir, "data", "tfidf")

    # --- Embedding Settings ---
    doc_embedding_model_name: str = Field(default="BAAI/bge-m3", env="DOC_EMBEDDING_MODEL_NAME")
    api_embedding_model_name: str = Field(default="microsoft/codebert-base", env="API_EMBEDDING_MODEL_NAME")
    cross_encoder_model_name: str = Field(default="cross-encoder/ms-marco-MiniLM-L-12-v2", env="CROSS_ENCODER_MODEL_NAME")
    device: str = Field(default="cuda", env="DEVICE")

    # --- Text Splitting Settings ---
    chunk_size: int = Field(default=1000, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, env="CHUNK_OVERLAP")


# Instantiate the settings
settings = ProcessingSettings()
