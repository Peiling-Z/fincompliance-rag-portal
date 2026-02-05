"""
Unit tests for statistics API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestStatisticsAPI:
    """Test cases for statistics API endpoints"""
    
    def test_dashboard_endpoint_exists(self):
        """Test that dashboard endpoint exists and requires auth"""
        response = client.get("/api/v1/statistics/dashboard")
        # Should return 401 without auth, not 404
        assert response.status_code == 401, "Dashboard endpoint should require authentication"
    
    def test_documents_endpoint_exists(self):
        """Test that documents statistics endpoint exists and requires auth"""
        response = client.get("/api/v1/statistics/documents")
        # Should return 401 without auth, not 404
        assert response.status_code == 401, "Documents endpoint should require authentication"
    
    def test_queries_endpoint_exists(self):
        """Test that queries statistics endpoint exists and requires auth"""
        response = client.get("/api/v1/statistics/queries")
        # Should return 401 without auth, not 404
        assert response.status_code == 401, "Queries endpoint should require authentication"
    
    def test_health_check_still_works(self):
        """Test that health check endpoint still works after adding statistics"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_api_root_still_works(self):
        """Test that root endpoint still works after adding statistics"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "FinCompliance" in data["message"]
    
    def test_documents_endpoint_with_query_params(self):
        """Test that documents endpoint accepts query parameters"""
        # Without auth, should still fail with 401, not 422 (validation error)
        response = client.get("/api/v1/statistics/documents?start_date=2024-01-01&end_date=2024-12-31")
        assert response.status_code == 401, "Should require auth before validating params"
    
    def test_queries_endpoint_with_query_params(self):
        """Test that queries endpoint accepts query parameters"""
        # Without auth, should still fail with 401, not 422 (validation error)
        response = client.get("/api/v1/statistics/queries?start_date=2024-01-01&end_date=2024-12-31")
        assert response.status_code == 401, "Should require auth before validating params"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
