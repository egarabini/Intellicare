"""
Tests for Trends API endpoints.
"""

import pytest
from httpx import AsyncClient
from datetime import date, timedelta

from donabedian.models.indicator import Indicator
from donabedian.models.pillar import Pillar


@pytest.mark.unit
@pytest.mark.api
class TestTrendsAPI:
    """Test cases for Trends API endpoints."""
    
    async def test_get_indicator_trend_empty(
        self,
        client: AsyncClient,
        sample_indicator: Indicator
    ):
        """Test getting indicator trend with no measurements."""
        response = await client.get(f"/api/v1/trends/{sample_indicator.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "indicator_id" in data
        assert "indicator_name" in data
        assert "time_series" in data
        assert "trend_analysis" in data
        assert data["indicator_id"] == sample_indicator.id
    
    async def test_get_indicator_trend_not_found(self, client: AsyncClient):
        """Test getting trend for non-existent indicator."""
        response = await client.get("/api/v1/trends/99999")
        
        assert response.status_code == 404
    
    async def test_get_indicator_trend_with_period(
        self,
        client: AsyncClient,
        sample_indicator: Indicator
    ):
        """Test getting indicator trend with period filter."""
        params = {
            "period_days": 30,
        }
        
        response = await client.get(f"/api/v1/trends/{sample_indicator.id}", params=params)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "period_start" in data
        assert "period_end" in data
    
    async def test_get_indicator_trend_with_custom_period(
        self,
        client: AsyncClient,
        sample_indicator: Indicator
    ):
        """Test getting indicator trend with custom period."""
        params = {
            "period_start": str(date.today() - timedelta(days=60)),
            "period_end": str(date.today() - timedelta(days=30)),
        }
        
        response = await client.get(f"/api/v1/trends/{sample_indicator.id}", params=params)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "time_series" in data
    
    async def test_get_pillar_trend_empty(
        self,
        client: AsyncClient,
        sample_pillar: Pillar
    ):
        """Test getting pillar trend with no data."""
        response = await client.get(f"/api/v1/trends/pillar/{sample_pillar.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "pillar_id" in data
        assert "pillar_name" in data
        assert "time_series" in data
        assert "trend_analysis" in data
    
    async def test_get_pillar_trend_not_found(self, client: AsyncClient):
        """Test getting trend for non-existent pillar."""
        response = await client.get("/api/v1/trends/pillar/99999")
        
        assert response.status_code == 404
    
    async def test_get_pillar_trend_with_period(
        self,
        client: AsyncClient,
        sample_pillar: Pillar
    ):
        """Test getting pillar trend with period filter."""
        params = {
            "period_days": 30,
        }
        
        response = await client.get(f"/api/v1/trends/pillar/{sample_pillar.id}", params=params)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "period_start" in data
        assert "period_end" in data
    
    async def test_trend_response_structure(
        self,
        client: AsyncClient,
        sample_indicator: Indicator
    ):
        """Test that trend response has correct structure."""
        response = await client.get(f"/api/v1/trends/{sample_indicator.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        required_fields = [
            "indicator_id",
            "indicator_name",
            "time_series",
            "trend_analysis",
            "target_value",
            "current_score",
            "period_start",
            "period_end",
        ]
        for field in required_fields:
            assert field in data
    
    async def test_trend_analysis_structure(
        self,
        client: AsyncClient,
        sample_indicator: Indicator
    ):
        """Test that trend_analysis has correct structure."""
        response = await client.get(f"/api/v1/trends/{sample_indicator.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "trend_analysis" in data
        trend_analysis = data["trend_analysis"]
        
        required_fields = [
            "direction",
            "change_percent",
            "first_value",
            "last_value",
            "average_value",
            "min_value",
            "max_value",
            "data_points",
        ]
        for field in required_fields:
            assert field in trend_analysis
    
    async def test_trend_direction_values(
        self,
        client: AsyncClient,
        sample_indicator: Indicator
    ):
        """Test that trend direction has valid values."""
        response = await client.get(f"/api/v1/trends/{sample_indicator.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        direction = data["trend_analysis"]["direction"]
        valid_directions = ["improving", "stable", "declining", "insufficient_data"]
        assert direction in valid_directions
    
    async def test_time_series_point_structure(
        self,
        client: AsyncClient,
        sample_indicator: Indicator,
        sample_measurement
    ):
        """Test that time series points have correct structure."""
        response = await client.get(f"/api/v1/trends/{sample_indicator.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        if len(data["time_series"]) > 0:
            point = data["time_series"][0]
            required_fields = ["date", "value", "score", "status"]
            for field in required_fields:
                assert field in point
    
    async def test_trend_period_validation(
        self,
        client: AsyncClient,
        sample_indicator: Indicator
    ):
        """Test trend with invalid period."""
        params = {
            "period_days": -1,  # Invalid
        }
        
        response = await client.get(f"/api/v1/trends/{sample_indicator.id}", params=params)
        
        # Should either reject or use default
        assert response.status_code in [200, 400, 422]

