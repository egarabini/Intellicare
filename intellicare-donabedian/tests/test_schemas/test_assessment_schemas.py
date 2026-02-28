"""
Tests for Assessment Pydantic schemas.
"""

import pytest
from pydantic import ValidationError
from datetime import date, timedelta

from donabedian.schemas.assessment import (
    AssessmentRequest,
    AssessmentResponse,
    PillarScore,
    TriadScore,
    IndicatorScore,
)


@pytest.mark.unit
@pytest.mark.schemas
class TestAssessmentSchemas:
    """Test cases for Assessment schemas."""
    
    def test_assessment_request_minimal(self):
        """Test AssessmentRequest with minimal data."""
        schema = AssessmentRequest()
        
        assert schema.period_start is None
        assert schema.period_end is None
        assert schema.pillar_ids is None
        assert schema.indicator_ids is None
    
    def test_assessment_request_with_period(self):
        """Test AssessmentRequest with period."""
        data = {
            "period_start": date.today() - timedelta(days=30),
            "period_end": date.today(),
        }
        schema = AssessmentRequest(**data)
        
        assert schema.period_start is not None
        assert schema.period_end is not None
    
    def test_assessment_request_with_filters(self):
        """Test AssessmentRequest with filters."""
        data = {
            "pillar_ids": [1, 2, 3],
            "indicator_ids": [10, 20],
        }
        schema = AssessmentRequest(**data)
        
        assert schema.pillar_ids == [1, 2, 3]
        assert schema.indicator_ids == [10, 20]
    
    def test_indicator_score_valid(self):
        """Test IndicatorScore with valid data."""
        data = {
            "indicator_id": 1,
            "indicator_name": "Taxa de Ocupação",
            "score": 85.5,
            "measurement_count": 10,
        }
        schema = IndicatorScore(**data)
        
        assert schema.indicator_id == 1
        assert schema.indicator_name == "Taxa de Ocupação"
        assert schema.score == 85.5
        assert schema.measurement_count == 10
    
    def test_indicator_score_zero_measurements(self):
        """Test IndicatorScore with zero measurements."""
        data = {
            "indicator_id": 1,
            "indicator_name": "Test",
            "score": 0.0,
            "measurement_count": 0,
        }
        schema = IndicatorScore(**data)
        
        assert schema.measurement_count == 0
        assert schema.score == 0.0
    
    def test_pillar_score_valid(self):
        """Test PillarScore with valid data."""
        data = {
            "pillar_id": 1,
            "pillar_name": "Eficácia",
            "pillar_code": "EFF",
            "score": 87.5,
            "indicator_scores": [
                {
                    "indicator_id": 1,
                    "indicator_name": "Test",
                    "score": 85.0,
                    "measurement_count": 5,
                }
            ],
        }
        schema = PillarScore(**data)
        
        assert schema.pillar_id == 1
        assert schema.pillar_name == "Eficácia"
        assert schema.score == 87.5
        assert len(schema.indicator_scores) == 1
    
    def test_pillar_score_empty_indicators(self):
        """Test PillarScore with empty indicators."""
        data = {
            "pillar_id": 1,
            "pillar_name": "Eficácia",
            "pillar_code": "EFF",
            "score": 0.0,
            "indicator_scores": [],
        }
        schema = PillarScore(**data)
        
        assert len(schema.indicator_scores) == 0
    
    def test_triad_score_valid(self):
        """Test TriadScore with valid data."""
        data = {
            "dimension": "structure",
            "score": 82.5,
            "indicator_count": 5,
        }
        schema = TriadScore(**data)
        
        assert schema.dimension == "structure"
        assert schema.score == 82.5
        assert schema.indicator_count == 5
    
    def test_triad_score_all_dimensions(self):
        """Test TriadScore with all dimensions."""
        dimensions = ["structure", "process", "outcome"]
        
        for dimension in dimensions:
            data = {
                "dimension": dimension,
                "score": 80.0,
                "indicator_count": 3,
            }
            schema = TriadScore(**data)
            assert schema.dimension == dimension
    
    def test_assessment_response_valid(self):
        """Test AssessmentResponse with valid data."""
        data = {
            "overall_score": 85.0,
            "pillar_scores": [
                {
                    "pillar_id": 1,
                    "pillar_name": "Eficácia",
                    "pillar_code": "EFF",
                    "score": 87.5,
                    "indicator_scores": [],
                }
            ],
            "triad_scores": [
                {
                    "dimension": "structure",
                    "score": 82.5,
                    "indicator_count": 5,
                }
            ],
            "period_start": date.today() - timedelta(days=30),
            "period_end": date.today(),
        }
        schema = AssessmentResponse(**data)
        
        assert schema.overall_score == 85.0
        assert len(schema.pillar_scores) == 1
        assert len(schema.triad_scores) == 1
    
    def test_assessment_response_empty_scores(self):
        """Test AssessmentResponse with empty scores."""
        data = {
            "overall_score": 0.0,
            "pillar_scores": [],
            "triad_scores": [],
            "period_start": date.today() - timedelta(days=30),
            "period_end": date.today(),
        }
        schema = AssessmentResponse(**data)
        
        assert schema.overall_score == 0.0
        assert len(schema.pillar_scores) == 0
        assert len(schema.triad_scores) == 0
    
    def test_assessment_response_json_serialization(self):
        """Test AssessmentResponse JSON serialization."""
        data = {
            "overall_score": 85.0,
            "pillar_scores": [],
            "triad_scores": [],
            "period_start": date.today() - timedelta(days=30),
            "period_end": date.today(),
        }
        schema = AssessmentResponse(**data)
        
        json_str = schema.model_dump_json()
        assert isinstance(json_str, str)
        assert "85.0" in json_str

