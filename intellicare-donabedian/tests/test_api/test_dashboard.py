"""
Tests for Dashboard API endpoints.
"""

import pytest
from httpx import AsyncClient
from datetime import date, timedelta


@pytest.mark.unit
@pytest.mark.api
class TestDashboardAPI:
    """Test cases for Dashboard API endpoints."""
    
    async def test_get_dashboard_data_empty(self, client: AsyncClient):
        """Test getting dashboard data with empty database."""
        response = await client.get("/api/v1/dashboard")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "overall_score" in data
        assert "total_pillars" in data
        assert "total_indicators" in data
        assert "total_measurements" in data
        assert "pillar_summaries" in data
        assert "indicator_summaries" in data
    
    async def test_get_dashboard_data_with_period(self, client: AsyncClient):
        """Test getting dashboard data with period filter."""
        params = {
            "period_days": 30,
        }
        
        response = await client.get("/api/v1/dashboard", params=params)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "period_start" in data
        assert "period_end" in data
    
    async def test_get_dashboard_pillars_summary(self, client: AsyncClient):
        """Test getting pillars summary."""
        response = await client.get("/api/v1/dashboard/pillars")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "pillar_summaries" in data
        assert isinstance(data["pillar_summaries"], list)
    
    async def test_get_dashboard_pillars_with_period(self, client: AsyncClient):
        """Test getting pillars summary with period."""
        params = {
            "period_days": 30,
        }
        
        response = await client.get("/api/v1/dashboard/pillars", params=params)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "period_start" in data
        assert "period_end" in data
    
    async def test_get_dashboard_indicators_summary(self, client: AsyncClient):
        """Test getting indicators summary."""
        response = await client.get("/api/v1/dashboard/indicators")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "indicator_summaries" in data
        assert "by_triad" in data
        assert isinstance(data["indicator_summaries"], list)
    
    async def test_get_dashboard_indicators_with_period(self, client: AsyncClient):
        """Test getting indicators summary with period."""
        params = {
            "period_days": 30,
        }
        
        response = await client.get("/api/v1/dashboard/indicators", params=params)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "period_start" in data
        assert "period_end" in data
    
    async def test_dashboard_response_structure(self, client: AsyncClient):
        """Test that dashboard response has correct structure."""
        response = await client.get("/api/v1/dashboard")
        
        assert response.status_code == 200
        data = response.json()
        
        required_fields = [
            "overall_score",
            "total_pillars",
            "total_indicators",
            "total_measurements",
            "pillar_summaries",
            "indicator_summaries",
            "by_triad",
            "by_status",
            "period_start",
            "period_end",
        ]
        for field in required_fields:
            assert field in data
    
    async def test_dashboard_by_triad_structure(self, client: AsyncClient):
        """Test that by_triad has correct structure."""
        response = await client.get("/api/v1/dashboard")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "by_triad" in data
        assert "structure" in data["by_triad"]
        assert "process" in data["by_triad"]
        assert "outcome" in data["by_triad"]
    
    async def test_dashboard_by_status_structure(self, client: AsyncClient):
        """Test that by_status has correct structure."""
        response = await client.get("/api/v1/dashboard")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "by_status" in data
        assert "green" in data["by_status"]
        assert "yellow" in data["by_status"]
        assert "red" in data["by_status"]
    
    async def test_dashboard_period_validation(self, client: AsyncClient):
        """Test dashboard with invalid period."""
        params = {
            "period_days": -1,  # Invalid
        }
        
        response = await client.get("/api/v1/dashboard", params=params)
        
        # Should either reject or use default
        assert response.status_code in [200, 400, 422]

