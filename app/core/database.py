"""
Database configuration and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool, QueuePool
import redis
import os
from app.core.config import settings
from app.core.cloud_sql import get_cloud_sql_engine

# SQLAlchemy setup
if settings.cloud_sql_connection_name:
    # Use Cloud SQL for production
    engine = get_cloud_sql_engine()
else:
    # Use local database for development
    engine = create_engine(
        settings.database_url,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis setup (use Cloud Memorystore in production)
if os.getenv("K_SERVICE"):  # Cloud Run environment
    # Use Cloud Memorystore Redis
    redis_url = f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', '6379')}"
else:
    # Use local Redis
    redis_url = settings.redis_url

redis_client = redis.from_url(redis_url, decode_responses=True)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_redis():
    """Get Redis client"""
    return redis_client