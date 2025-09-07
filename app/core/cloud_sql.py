"""
Google Cloud SQL connection management
"""
import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from app.core.config import settings

logger = logging.getLogger(__name__)


def create_cloud_sql_engine():
    """Create Cloud SQL engine with proper connection pooling"""
    
    # Check if running in Cloud Run (production)
    if os.getenv("K_SERVICE"):  # Cloud Run environment variable
        return create_cloud_sql_engine_production()
    else:
        return create_cloud_sql_engine_local()


def create_cloud_sql_engine_production():
    """Create Cloud SQL engine for production (Cloud Run)"""
    try:
        # Use Cloud SQL Proxy connection
        if settings.cloud_sql_connection_name:
            # Cloud SQL Proxy connection string
            db_url = f"postgresql+psycopg2://{settings.cloud_sql_user}:{settings.cloud_sql_password}@/{settings.cloud_sql_database}?host=/cloudsql/{settings.cloud_sql_connection_name}"
        else:
            # Direct connection (if using private IP)
            db_url = settings.database_url
        
        engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=3600,
            connect_args={
                "sslmode": "require",
                "options": "-c timezone=utc"
            }
        )
        
        logger.info("Cloud SQL engine created successfully")
        return engine
        
    except Exception as e:
        logger.error(f"Failed to create Cloud SQL engine: {e}")
        raise


def create_cloud_sql_engine_local():
    """Create Cloud SQL engine for local development"""
    try:
        # For local development, use Cloud SQL Proxy
        if settings.cloud_sql_connection_name:
            # Local Cloud SQL Proxy connection
            db_url = f"postgresql+psycopg2://{settings.cloud_sql_user}:{settings.cloud_sql_password}@127.0.0.1:5432/{settings.cloud_sql_database}"
        else:
            # Fallback to regular database URL
            db_url = settings.database_url
        
        engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=2,
            max_overflow=5,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        
        logger.info("Local Cloud SQL engine created successfully")
        return engine
        
    except Exception as e:
        logger.error(f"Failed to create local Cloud SQL engine: {e}")
        raise


def get_cloud_sql_engine():
    """Get Cloud SQL engine instance"""
    return create_cloud_sql_engine()
