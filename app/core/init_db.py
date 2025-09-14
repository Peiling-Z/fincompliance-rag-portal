"""
Database initialization script
"""
import logging
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.user import User
from app.models.document import Document, DocumentChunk, QueryLog

logger = logging.getLogger(__name__)


def init_database():
    """Initialize database with tables and default data"""
    try:
        # Get database session
        db = next(get_db())
        
        # Create tables
        logger.info("Creating database tables...")
        User.metadata.create_all(bind=db.bind)
        Document.metadata.create_all(bind=db.bind)
        DocumentChunk.metadata.create_all(bind=db.bind)
        QueryLog.metadata.create_all(bind=db.bind)
        logger.info("Database tables created successfully")
        
        # Create default superuser
        create_default_superuser(db)
        
        # Create sample data
        create_sample_data(db)
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    finally:
        db.close()


def create_default_superuser(db: Session):
    """Create default superuser if not exists"""
    try:
        # Check if superuser already exists
        existing_user = db.query(User).filter(User.username == "admin").first()
        if existing_user:
            logger.info("Default superuser already exists")
            return
        
        # Create default superuser
        superuser = User(
            username="admin",
            email="admin@fincompliance.com",
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            is_superuser=True
        )
        
        db.add(superuser)
        db.commit()
        
        logger.info("Default superuser created: admin/admin123")
        
    except Exception as e:
        logger.error(f"Failed to create default superuser: {e}")
        db.rollback()
        raise


def create_sample_data(db: Session):
    """Create sample data for testing"""
    try:
        # Check if sample data already exists
        existing_docs = db.query(Document).count()
        if existing_docs > 0:
            logger.info("Sample data already exists")
            return
        
        # Create sample documents
        sample_documents = [
            {
                "title": "KYC Requirements Guide",
                "description": "Know Your Customer requirements and procedures",
                "file_name": "kyc_requirements.pdf",
                "file_size": 1024000,
                "mime_type": "application/pdf",
                "status": "processed",
                "metadata": {
                    "category": "compliance",
                    "version": "1.0",
                    "author": "Compliance Team"
                }
            },
            {
                "title": "AML Policy Document",
                "description": "Anti-Money Laundering policy and procedures",
                "file_name": "aml_policy.pdf",
                "file_size": 2048000,
                "mime_type": "application/pdf",
                "status": "processed",
                "metadata": {
                    "category": "compliance",
                    "version": "2.1",
                    "author": "Risk Management"
                }
            },
            {
                "title": "Data Privacy Regulations",
                "description": "Data protection and privacy compliance requirements",
                "file_name": "data_privacy.pdf",
                "file_size": 1536000,
                "mime_type": "application/pdf",
                "status": "processing",
                "metadata": {
                    "category": "privacy",
                    "version": "1.5",
                    "author": "Legal Team"
                }
            }
        ]
        
        for doc_data in sample_documents:
            document = Document(**doc_data)
            db.add(document)
        
        db.commit()
        
        # Create sample chunks for processed documents
        create_sample_chunks(db)
        
        logger.info("Sample data created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create sample data: {e}")
        db.rollback()
        raise


def create_sample_chunks(db: Session):
    """Create sample document chunks"""
    try:
        # Get processed documents
        processed_docs = db.query(Document).filter(Document.status == "processed").all()
        
        for doc in processed_docs:
            # Create sample chunks
            sample_chunks = [
                {
                    "document_id": doc.id,
                    "chunk_index": 0,
                    "content": f"Introduction to {doc.title}. This document outlines the key requirements and procedures.",
                    "metadata": {
                        "page": 1,
                        "section": "introduction"
                    },
                    "embedding": [0.1, 0.2, 0.3, 0.4, 0.5]  # Dummy embedding
                },
                {
                    "document_id": doc.id,
                    "chunk_index": 1,
                    "content": f"Main content of {doc.title}. Detailed procedures and requirements are described here.",
                    "metadata": {
                        "page": 2,
                        "section": "main_content"
                    },
                    "embedding": [0.2, 0.3, 0.4, 0.5, 0.6]  # Dummy embedding
                },
                {
                    "document_id": doc.id,
                    "chunk_index": 2,
                    "content": f"Conclusion of {doc.title}. Summary and next steps are provided.",
                    "metadata": {
                        "page": 3,
                        "section": "conclusion"
                    },
                    "embedding": [0.3, 0.4, 0.5, 0.6, 0.7]  # Dummy embedding
                }
            ]
            
            for chunk_data in sample_chunks:
                chunk = DocumentChunk(**chunk_data)
                db.add(chunk)
        
        db.commit()
        logger.info("Sample chunks created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create sample chunks: {e}")
        db.rollback()
        raise


def reset_database():
    """Reset database by dropping and recreating all tables"""
    try:
        db = next(get_db())
        
        logger.info("Dropping all database tables...")
        DocumentChunk.metadata.drop_all(bind=db.bind)
        QueryLog.metadata.drop_all(bind=db.bind)
        Document.metadata.drop_all(bind=db.bind)
        User.metadata.drop_all(bind=db.bind)
        
        logger.info("Recreating database tables...")
        User.metadata.create_all(bind=db.bind)
        Document.metadata.create_all(bind=db.bind)
        DocumentChunk.metadata.create_all(bind=db.bind)
        QueryLog.metadata.create_all(bind=db.bind)
        
        logger.info("Database reset completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to reset database: {e}")
        raise
    finally:
        db.close()


def check_database_health():
    """Check database health and connectivity"""
    try:
        db = next(get_db())
        
        # Test basic queries
        user_count = db.query(User).count()
        doc_count = db.query(Document).count()
        chunk_count = db.query(DocumentChunk).count()
        query_count = db.query(QueryLog).count()
        
        logger.info(f"Database health check passed:")
        logger.info(f"  - Users: {user_count}")
        logger.info(f"  - Documents: {doc_count}")
        logger.info(f"  - Chunks: {chunk_count}")
        logger.info(f"  - Queries: {query_count}")
        
        return True
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "init":
            init_database()
        elif command == "reset":
            reset_database()
        elif command == "health":
            check_database_health()
        else:
            print("Usage: python init_db.py [init|reset|health]")
    else:
        init_database()
