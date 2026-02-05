"""
Unit tests for statistics API endpoints
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.models.document import Document, QueryLog, DocumentStatus
from app.core.security import get_password_hash, create_access_token

# Create test database
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="function")
def test_db():
    """Create test database and tables"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(test_db):
    """Create a test user"""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("testpassword"),
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Get authentication headers"""
    access_token = create_access_token(data={"sub": test_user.email})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def sample_documents(test_db, test_user):
    """Create sample documents for testing"""
    documents = []
    
    # Create documents with different statuses
    for i in range(10):
        status = DocumentStatus.PROCESSED if i < 5 else DocumentStatus.UPLOADED
        if i == 9:
            status = DocumentStatus.FAILED
        
        doc = Document(
            filename=f"test_doc_{i}.pdf",
            original_filename=f"test_doc_{i}.pdf",
            file_path=f"/tmp/test_doc_{i}.pdf",
            file_size=1024 * (i + 1),
            file_type="pdf",
            status=status,
            user_id=test_user.id,
            created_at=datetime.now() - timedelta(days=i)
        )
        test_db.add(doc)
        documents.append(doc)
    
    test_db.commit()
    return documents


@pytest.fixture
def sample_queries(test_db, test_user):
    """Create sample query logs for testing"""
    queries = []
    
    for i in range(15):
        query = QueryLog(
            user_id=test_user.id,
            query=f"Test question {i}?",
            response=f"Test answer {i}",
            response_time_ms=100.0 + (i * 10),
            created_at=datetime.now() - timedelta(days=i)
        )
        test_db.add(query)
        queries.append(query)
    
    test_db.commit()
    return queries


class TestStatisticsAPI:
    """Test cases for statistics API endpoints"""
    
    def test_get_dashboard_statistics(self, test_db, test_user, auth_headers, sample_documents, sample_queries):
        """Test dashboard statistics endpoint"""
        response = client.get("/api/v1/statistics/dashboard", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_documents" in data
        assert "processed_documents" in data
        assert "failed_documents" in data
        assert "total_queries" in data
        assert "average_response_time_ms" in data
        assert "recent_documents_7d" in data
        assert "recent_queries_7d" in data
        
        assert data["total_documents"] == 10
        assert data["processed_documents"] == 5
        assert data["failed_documents"] == 1
        assert data["total_queries"] == 15
    
    def test_get_document_statistics(self, test_db, test_user, auth_headers, sample_documents):
        """Test document statistics endpoint"""
        response = client.get("/api/v1/statistics/documents", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_documents" in data
        assert "status_distribution" in data
        assert "documents_over_time" in data
        assert "average_file_size_bytes" in data
        assert "total_chunks" in data
        
        assert data["total_documents"] == 10
        assert data["status_distribution"]["processed"] == 5
        assert data["status_distribution"]["uploaded"] == 4
        assert data["status_distribution"]["failed"] == 1
    
    def test_get_document_statistics_with_date_filter(self, test_db, test_user, auth_headers, sample_documents):
        """Test document statistics with date filter"""
        start_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        
        response = client.get(
            f"/api/v1/statistics/documents?start_date={start_date}&end_date={end_date}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have documents from last 5 days (6 documents: 0-5)
        assert data["total_documents"] == 6
    
    def test_get_query_statistics(self, test_db, test_user, auth_headers, sample_queries):
        """Test query statistics endpoint"""
        response = client.get("/api/v1/statistics/queries", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_queries" in data
        assert "average_response_time_ms" in data
        assert "min_response_time_ms" in data
        assert "max_response_time_ms" in data
        assert "queries_over_time" in data
        
        assert data["total_queries"] == 15
        assert data["min_response_time_ms"] == 100.0
        assert data["max_response_time_ms"] == 240.0  # 100 + (14 * 10)
    
    def test_get_query_statistics_with_date_filter(self, test_db, test_user, auth_headers, sample_queries):
        """Test query statistics with date filter"""
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        
        response = client.get(
            f"/api/v1/statistics/queries?start_date={start_date}&end_date={end_date}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have queries from last 7 days (8 queries: 0-7)
        assert data["total_queries"] == 8
    
    def test_statistics_requires_authentication(self):
        """Test that statistics endpoints require authentication"""
        # Test without authentication headers
        response = client.get("/api/v1/statistics/dashboard")
        assert response.status_code == 401
        
        response = client.get("/api/v1/statistics/documents")
        assert response.status_code == 401
        
        response = client.get("/api/v1/statistics/queries")
        assert response.status_code == 401
    
    def test_invalid_date_format(self, auth_headers):
        """Test with invalid date format"""
        response = client.get(
            "/api/v1/statistics/documents?start_date=invalid-date",
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "Invalid start_date format" in response.json()["detail"]
    
    def test_empty_statistics(self, test_db, test_user, auth_headers):
        """Test statistics with no data"""
        # Query statistics without any queries
        response = client.get("/api/v1/statistics/queries", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_queries"] == 0
        assert data["average_response_time_ms"] == 0
        assert data["min_response_time_ms"] == 0
        assert data["max_response_time_ms"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
