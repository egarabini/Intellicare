"""
Tests for Dashboard Pydantic schemas.
"""

import pytest
from datetime import date, timedelta

from donabedian.schemas.dashboard import (
    DashboardResponse,
    PillarSummary,
    IndicatorSummary,
)


@pytest.mark.unit
@pytest.mark.schemas
class TestDashboardSchemas:
    """Test cases for Dashboard schemas."""
    
    def test_pillar_summary_valid(self):
        """Test PillarSummary with valid data."""
        data = {
            "pillar_id": 1,
            "pillar_name": "Eficácia",
            "pillar_code": "EFF",
            "current_score": 87.5,
            "indicator_count": 5,
            "measurement_count": 25,
        }
        schema = PillarSummary(**data)
        
        assert schema.pillar_id == 1
        assert schema.pillar_name == "Eficácia"
        assert schema.current_score == 87.5
        assert schema.indicator_count == 5
    
    def test_pillar_summary_zero_counts(self):
        """Test PillarSummary with zero counts."""
        data = {
            "pillar_id": 1,
            "pillar_name": "Eficácia",
            "pillar_code": "EFF",
            "current_score": 0.0,
            "indicator_count": 0,
            "measurement_count": 0,
        }
        schema = PillarSummary(**data)
        
        assert schema.indicator_count == 0
        assert schema.measurement_count == 0
    
    def test_indicator_summary_valid(self):
        """Test IndicatorSummary with valid data."""
        data = {
            "indicator_id": 1,
            "indicator_name": "Taxa de Ocupação",
            "triad_dimension": "structure",
            "current_score": 85.0,
            "latest_value": 87.5,
            "latest_status": "green",
            "target_value": 85.0,
            "measurement_count": 10,
            "pillar_count": 2,
        }
        schema = IndicatorSummary(**data)
        
        assert schema.indicator_id == 1
        assert schema.indicator_name == "Taxa de Ocupação"
        assert schema.current_score == 85.0
        assert schema.latest_status == "green"
    
    def test_indicator_summary_optional_fields(self):
        """Test IndicatorSummary with optional fields."""
        data = {
            "indicator_id": 1,
            "indicator_name": "Test",
            "triad_dimension": "structure",
            "current_score": 0.0,
            "latest_value": None,
            "latest_status": None,
            "target_value": None,
            "measurement_count": 0,
            "pillar_count": 0,
        }
        schema = IndicatorSummary(**data)
        
        assert schema.latest_value is None
        assert schema.latest_status is None
        assert schema.target_value is None
    
    def test_dashboard_response_valid(self):
        """Test DashboardResponse with valid data."""
        data = {
            "overall_score": 85.0,
            "total_pillars": 7,
            "total_indicators": 20,
            "total_measurements": 100,
            "pillar_summaries": [
                {
                    "pillar_id": 1,
                    "pillar_name": "Eficácia",
                    "pillar_code": "EFF",
                    "current_score": 87.5,
                    "indicator_count": 5,
                    "measurement_count": 25,
                }
            ],
            "indicator_summaries": [
                {
                    "indicator_id": 1,
                    "indicator_name": "Test",
                    "triad_dimension": "structure",
                    "current_score": 85.0,
                    "latest_value": 87.5,
                    "latest_status": "green",
                    "target_value": 85.0,
                    "measurement_count": 10,
                    "pillar_count": 2,
                }
            ],
            "by_triad": {
                "structure": [],
                "process": [],
                "outcome": [],
            },
            "by_status": {
                "green": 15,
                "yellow": 3,
                "red": 2,
            },
            "period_start": date.today() - timedelta(days=30),
            "period_end": date.today(),
        }
        schema = DashboardResponse(**data)
        
        assert schema.overall_score == 85.0
        assert schema.total_pillars == 7
        assert len(schema.pillar_summaries) == 1
        assert len(schema.indicator_summaries) == 1
    
    def test_dashboard_response_empty_data(self):
        """Test DashboardResponse with empty data."""
        data = {
            "overall_score": 0.0,
            "total_pillars": 0,
            "total_indicators": 0,
            "total_measurements": 0,
            "pillar_summaries": [],
            "indicator_summaries": [],
            "by_triad": {
                "structure": [],
                "process": [],
                "outcome": [],
            },
            "by_status": {
                "green": 0,
                "yellow": 0,
                "red": 0,
            },
            "period_start": date.today() - timedelta(days=30),
            "period_end": date.today(),
        }
        schema = DashboardResponse(**data)
        
        assert schema.total_pillars == 0
        assert len(schema.pillar_summaries) == 0
    
    def test_dashboard_response_json_serialization(self):
        """Test DashboardResponse JSON serialization."""
        data = {
            "overall_score": 85.0,
            "total_pillars": 7,
            "total_indicators": 20,
            "total_measurements": 100,
            "pillar_summaries": [],
            "indicator_summaries": [],
            "by_triad": {
                "structure": [],
                "process": [],
                "outcome": [],
            },
            "by_status": {
                "green": 15,
                "yellow": 3,
                "red": 2,
            },
            "period_start": date.today() - timedelta(days=30),
            "period_end": date.today(),
        }
        schema = DashboardResponse(**data)
        
        json_str = schema.model_dump_json()
        assert isinstance(json_str, str)
        assert "85.0" in json_str

