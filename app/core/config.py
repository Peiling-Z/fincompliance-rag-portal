"""
Application configuration management
"""
from pydantic_settings import BaseSettings
from typing import Optional, List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "FinCompliance RAG Portal"
    app_version: str = "2.0.0"
    debug: bool = False
    
    # API
    api_v1_prefix: str = "/api/v1"
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Database
    database_url: str
    redis_url: str = "redis://localhost:6379"
    
    # Cloud SQL Configuration
    cloud_sql_connection_name: Optional[str] = None
    cloud_sql_user: Optional[str] = None
    cloud_sql_password: Optional[str] = None
    cloud_sql_database: Optional[str] = None
    cloud_sql_region: Optional[str] = None
    
    # Vector Database
    vector_db_type: str = "vertex_ai"
    weaviate_url: Optional[str] = None
    weaviate_api_key: Optional[str] = None
    pinecone_api_key: Optional[str] = None
    pinecone_environment: Optional[str] = None

    # Google Cloud Configuration
    gcp_project_id: Optional[str] = None
    gcp_region: str = "us-central1"
    gcp_zone: str = "us-central1-a"
    
    # AI/LLM
    openai_api_key: str
    openai_model: str = "gpt-4-turbo-preview"
    embedding_model: str = "text-embedding-3-large"
    max_tokens: int = 4000
    temperature: float = 0.1
    
    # Document Processing
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_file_size_mb: int = 50
    supported_formats: List[str] = ["pdf", "docx", "txt", "md"]
    
    # Storage
    upload_dir: str = "data/uploads"
    processed_dir: str = "data/processed"
    
    # Cloud Storage
    cloud_storage_bucket: Optional[str] = None
    
    # Monitoring
    sentry_dsn: Optional[str] = None
    log_level: str = "INFO"
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8501"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()