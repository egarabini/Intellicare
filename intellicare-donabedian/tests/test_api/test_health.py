"""
Tests for Health and Info API endpoints.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.unit
@pytest.mark.api
class TestHealthEndpoints:
    """Test cases for health and info endpoints."""
    
    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    async def test_health_check_database(self, client: AsyncClient):
        """Test health check includes database status."""
        response = await client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "database" in data
        assert data["database"] in ["connected", "disconnected"]
    
    async def test_info_endpoint(self, client: AsyncClient):
        """Test module info endpoint."""
        response = await client.get("/api/v1/info")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "module" in data
        assert "version" in data
        assert "description" in data
        assert data["module"] == "intellicare-donabedian"
    
    async def test_info_endpoint_structure(self, client: AsyncClient):
        """Test info endpoint returns expected structure."""
        response = await client.get("/api/v1/info")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check for expected fields
        expected_fields = ["module", "version", "description", "api_version"]
        for field in expected_fields:
            assert field in data
    
    async def test_health_endpoint_always_available(self, client: AsyncClient):
        """Test that health endpoint is always available."""
        # Make multiple requests
        for _ in range(5):
            response = await client.get("/api/v1/health")
            assert response.status_code == 200
    
    async def test_info_endpoint_consistent(self, client: AsyncClient):
        """Test that info endpoint returns consistent data."""
        response1 = await client.get("/api/v1/info")
        response2 = await client.get("/api/v1/info")
        
        assert response1.json() == response2.json()

