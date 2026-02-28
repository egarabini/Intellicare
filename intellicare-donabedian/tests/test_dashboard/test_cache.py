"""
Tests for Dashboard Cache utilities.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from donabedian.dashboard.utils.cache import (
    get_cached_dashboard,
    get_cached_pillars,
    get_cached_indicators,
    get_cached_dashboard_indicators,
    get_cached_indicator_trend,
    get_cached_pillar_trend,
)


@pytest.mark.unit
@pytest.mark.dashboard
class TestCacheUtilities:
    """Test cases for cache utilities."""
    
    @pytest.mark.asyncio
    async def test_get_cached_dashboard_success(self):
        """Test get_cached_dashboard with successful API call."""
        mock_client = Mock()
        mock_client.get_dashboard = AsyncMock(return_value={
            "overall_score": 85.5,
            "total_pillars": 7
        })
        
        result = await get_cached_dashboard(mock_client)
        
        assert result["overall_score"] == 85.5
        assert result["total_pillars"] == 7
        mock_client.get_dashboard.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_cached_dashboard_with_period(self):
        """Test get_cached_dashboard with period parameter."""
        mock_client = Mock()
        mock_client.get_dashboard = AsyncMock(return_value={
            "overall_score": 85.5,
            "period_days": 30
        })
        
        result = await get_cached_dashboard(mock_client, period_days=30)
        
        assert result["period_days"] == 30
        mock_client.get_dashboard.assert_called_once_with(period_days=30)
    
    @pytest.mark.asyncio
    async def test_get_cached_dashboard_error_handling(self):
        """Test get_cached_dashboard error handling."""
        mock_client = Mock()
        mock_client.get_dashboard = AsyncMock(side_effect=Exception("API Error"))
        
        with pytest.raises(Exception):
            await get_cached_dashboard(mock_client)
    
    @pytest.mark.asyncio
    async def test_get_cached_pillars_success(self):
        """Test get_cached_pillars with successful API call."""
        mock_client = Mock()
        mock_client.get_pillars = AsyncMock(return_value=[
            {"id": 1, "name": "Eficácia"},
            {"id": 2, "name": "Efetividade"}
        ])
        
        result = await get_cached_pillars(mock_client)
        
        assert len(result) == 2
        assert result[0]["name"] == "Eficácia"
        mock_client.get_pillars.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_cached_pillars_empty(self):
        """Test get_cached_pillars with empty result."""
        mock_client = Mock()
        mock_client.get_pillars = AsyncMock(return_value=[])
        
        result = await get_cached_pillars(mock_client)
        
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_get_cached_indicators_success(self):
        """Test get_cached_indicators with successful API call."""
        mock_client = Mock()
        mock_client.get_indicators = AsyncMock(return_value={
            "items": [{"id": 1, "name": "Taxa de Ocupação"}],
            "total": 1
        })
        
        result = await get_cached_indicators(mock_client)
        
        assert result["total"] == 1
        assert len(result["items"]) == 1
        mock_client.get_indicators.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_cached_indicators_with_params(self):
        """Test get_cached_indicators with parameters."""
        mock_client = Mock()
        mock_client.get_indicators = AsyncMock(return_value={
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": 10
        })
        
        result = await get_cached_indicators(mock_client, page=1, page_size=10)
        
        assert result["page"] == 1
        assert result["page_size"] == 10
    
    @pytest.mark.asyncio
    async def test_get_cached_dashboard_indicators_success(self):
        """Test get_cached_dashboard_indicators with successful API call."""
        mock_client = Mock()
        mock_client.get_dashboard_indicators = AsyncMock(return_value={
            "indicator_summaries": [
                {"id": 1, "name": "Taxa de Ocupação", "score": 85.5}
            ],
            "by_triad": {
                "structure": 3,
                "process": 2,
                "outcome": 1
            }
        })
        
        result = await get_cached_dashboard_indicators(mock_client)
        
        assert len(result["indicator_summaries"]) == 1
        assert result["by_triad"]["structure"] == 3
        mock_client.get_dashboard_indicators.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_cached_dashboard_indicators_with_period(self):
        """Test get_cached_dashboard_indicators with period."""
        mock_client = Mock()
        mock_client.get_dashboard_indicators = AsyncMock(return_value={
            "indicator_summaries": [],
            "period_days": 30
        })
        
        result = await get_cached_dashboard_indicators(mock_client, period_days=30)
        
        assert result["period_days"] == 30
    
    @pytest.mark.asyncio
    async def test_get_cached_indicator_trend_success(self):
        """Test get_cached_indicator_trend with successful API call."""
        mock_client = Mock()
        mock_client.get_indicator_trend = AsyncMock(return_value={
            "indicator_id": 1,
            "indicator_name": "Taxa de Ocupação",
            "time_series": [
                {"date": "2024-01-01", "value": 85.0, "score": 85.0}
            ],
            "trend_analysis": {
                "direction": "improving",
                "change_percent": 5.0
            }
        })
        
        result = await get_cached_indicator_trend(mock_client, indicator_id=1)
        
        assert result["indicator_id"] == 1
        assert len(result["time_series"]) == 1
        assert result["trend_analysis"]["direction"] == "improving"
        mock_client.get_indicator_trend.assert_called_once_with(1, period_days=None)
    
    @pytest.mark.asyncio
    async def test_get_cached_indicator_trend_with_period(self):
        """Test get_cached_indicator_trend with period."""
        mock_client = Mock()
        mock_client.get_indicator_trend = AsyncMock(return_value={
            "indicator_id": 1,
            "time_series": [],
            "period_days": 30
        })
        
        result = await get_cached_indicator_trend(mock_client, indicator_id=1, period_days=30)
        
        assert result["period_days"] == 30
        mock_client.get_indicator_trend.assert_called_once_with(1, period_days=30)
    
    @pytest.mark.asyncio
    async def test_get_cached_pillar_trend_success(self):
        """Test get_cached_pillar_trend with successful API call."""
        mock_client = Mock()
        mock_client.get_pillar_trend = AsyncMock(return_value={
            "pillar_id": 1,
            "pillar_name": "Eficácia",
            "time_series": [
                {"date": "2024-01-01", "value": 85.0, "score": 85.0}
            ],
            "trend_analysis": {
                "direction": "stable",
                "change_percent": 0.5
            }
        })
        
        result = await get_cached_pillar_trend(mock_client, pillar_id=1)
        
        assert result["pillar_id"] == 1
        assert result["pillar_name"] == "Eficácia"
        assert result["trend_analysis"]["direction"] == "stable"
        mock_client.get_pillar_trend.assert_called_once_with(1, period_days=None)
    
    @pytest.mark.asyncio
    async def test_get_cached_pillar_trend_with_period(self):
        """Test get_cached_pillar_trend with period."""
        mock_client = Mock()
        mock_client.get_pillar_trend = AsyncMock(return_value={
            "pillar_id": 1,
            "time_series": [],
            "period_days": 60
        })
        
        result = await get_cached_pillar_trend(mock_client, pillar_id=1, period_days=60)
        
        assert result["period_days"] == 60
        mock_client.get_pillar_trend.assert_called_once_with(1, period_days=60)

