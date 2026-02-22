"""
Tests for Trends Pydantic schemas.
"""

import pytest
from datetime import date, timedelta

from donabedian.schemas.trends import (
    TrendResponse,
    TrendAnalysis,
    TimeSeriesPoint,
)


@pytest.mark.unit
@pytest.mark.schemas
class TestTrendsSchemas:
    """Test cases for Trends schemas."""
    
    def test_time_series_point_valid(self):
        """Test TimeSeriesPoint with valid data."""
        data = {
            "date": date.today(),
            "value": 87.5,
            "score": 95.0,
            "status": "green",
        }
        schema = TimeSeriesPoint(**data)
        
        assert schema.date == date.today()
        assert schema.value == 87.5
        assert schema.score == 95.0
        assert schema.status == "green"
    
    def test_time_series_point_all_statuses(self):
        """Test TimeSeriesPoint with all statuses."""
        statuses = ["green", "yellow", "red"]
        
        for status in statuses:
            data = {
                "date": date.today(),
                "value": 80.0,
                "score": 80.0,
                "status": status,
            }
            schema = TimeSeriesPoint(**data)
            assert schema.status == status
    
    def test_trend_analysis_valid(self):
        """Test TrendAnalysis with valid data."""
        data = {
            "direction": "improving",
            "change_percent": 15.5,
            "first_value": 75.0,
            "last_value": 87.5,
            "average_value": 81.0,
            "min_value": 70.0,
            "max_value": 90.0,
            "data_points": 10,
        }
        schema = TrendAnalysis(**data)
        
        assert schema.direction == "improving"
        assert schema.change_percent == 15.5
        assert schema.first_value == 75.0
        assert schema.last_value == 87.5
        assert schema.data_points == 10
    
    def test_trend_analysis_all_directions(self):
        """Test TrendAnalysis with all directions."""
        directions = ["improving", "stable", "declining", "insufficient_data"]
        
        for direction in directions:
            data = {
                "direction": direction,
                "change_percent": 0.0,
                "first_value": 80.0,
                "last_value": 80.0,
                "average_value": 80.0,
                "min_value": 80.0,
                "max_value": 80.0,
                "data_points": 5,
            }
            schema = TrendAnalysis(**data)
            assert schema.direction == direction
    
    def test_trend_analysis_negative_change(self):
        """Test TrendAnalysis with negative change."""
        data = {
            "direction": "declining",
            "change_percent": -20.0,
            "first_value": 90.0,
            "last_value": 72.0,
            "average_value": 81.0,
            "min_value": 70.0,
            "max_value": 90.0,
            "data_points": 8,
        }
        schema = TrendAnalysis(**data)
        
        assert schema.change_percent == -20.0
        assert schema.direction == "declining"
    
    def test_trend_analysis_insufficient_data(self):
        """Test TrendAnalysis with insufficient data."""
        data = {
            "direction": "insufficient_data",
            "change_percent": None,
            "first_value": None,
            "last_value": None,
            "average_value": None,
            "min_value": None,
            "max_value": None,
            "data_points": 0,
        }
        schema = TrendAnalysis(**data)
        
        assert schema.direction == "insufficient_data"
        assert schema.data_points == 0
        assert schema.change_percent is None
    
    def test_trend_response_valid(self):
        """Test TrendResponse with valid data."""
        data = {
            "indicator_id": 1,
            "indicator_name": "Taxa de Ocupação",
            "time_series": [
                {
                    "date": date.today() - timedelta(days=7),
                    "value": 85.0,
                    "score": 90.0,
                    "status": "green",
                },
                {
                    "date": date.today(),
                    "value": 87.5,
                    "score": 95.0,
                    "status": "green",
                },
            ],
            "trend_analysis": {
                "direction": "improving",
                "change_percent": 2.9,
                "first_value": 85.0,
                "last_value": 87.5,
                "average_value": 86.25,
                "min_value": 85.0,
                "max_value": 87.5,
                "data_points": 2,
            },
            "target_value": 85.0,
            "current_score": 95.0,
            "period_start": date.today() - timedelta(days=30),
            "period_end": date.today(),
        }
        schema = TrendResponse(**data)
        
        assert schema.indicator_id == 1
        assert schema.indicator_name == "Taxa de Ocupação"
        assert len(schema.time_series) == 2
        assert schema.trend_analysis.direction == "improving"
        assert schema.target_value == 85.0
    
    def test_trend_response_empty_time_series(self):
        """Test TrendResponse with empty time series."""
        data = {
            "indicator_id": 1,
            "indicator_name": "Test",
            "time_series": [],
            "trend_analysis": {
                "direction": "insufficient_data",
                "change_percent": None,
                "first_value": None,
                "last_value": None,
                "average_value": None,
                "min_value": None,
                "max_value": None,
                "data_points": 0,
            },
            "target_value": None,
            "current_score": 0.0,
            "period_start": date.today() - timedelta(days=30),
            "period_end": date.today(),
        }
        schema = TrendResponse(**data)
        
        assert len(schema.time_series) == 0
        assert schema.trend_analysis.direction == "insufficient_data"
    
    def test_trend_response_json_serialization(self):
        """Test TrendResponse JSON serialization."""
        data = {
            "indicator_id": 1,
            "indicator_name": "Test",
            "time_series": [],
            "trend_analysis": {
                "direction": "insufficient_data",
                "change_percent": None,
                "first_value": None,
                "last_value": None,
                "average_value": None,
                "min_value": None,
                "max_value": None,
                "data_points": 0,
            },
            "target_value": 85.0,
            "current_score": 0.0,
            "period_start": date.today() - timedelta(days=30),
            "period_end": date.today(),
        }
        schema = TrendResponse(**data)
        
        json_str = schema.model_dump_json()
        assert isinstance(json_str, str)
        assert "Test" in json_str

