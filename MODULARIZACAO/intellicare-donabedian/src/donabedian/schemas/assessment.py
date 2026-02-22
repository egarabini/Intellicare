"""
Assessment schemas for quality evaluation.

Schemas for quality assessment calculations based on Donabedian framework.
"""

from typing import List, Dict
from datetime import date
from pydantic import BaseModel, Field

from donabedian.schemas.indicator import TriadDimensionSchema


class IndicatorScore(BaseModel):
    """Score for a single indicator."""
    indicator_id: int = Field(..., description="Indicator ID")
    indicator_name: str = Field(..., description="Indicator name")
    score: float = Field(..., ge=0.0, le=100.0, description="Score (0-100)")
    weight: float = Field(..., ge=0.0, le=1.0, description="Weight in calculation")
    measurement_count: int = Field(..., ge=0, description="Number of measurements")
    green_count: int = Field(..., ge=0, description="Number of GREEN measurements")
    yellow_count: int = Field(..., ge=0, description="Number of YELLOW measurements")
    red_count: int = Field(..., ge=0, description="Number of RED measurements")


class PillarScore(BaseModel):
    """Score for a single pillar."""
    pillar_id: int = Field(..., description="Pillar ID")
    pillar_name: str = Field(..., description="Pillar name")
    score: float = Field(..., ge=0.0, le=100.0, description="Weighted average score (0-100)")
    indicator_scores: List[IndicatorScore] = Field(..., description="Scores of indicators in this pillar")
    total_measurements: int = Field(..., ge=0, description="Total measurements across all indicators")


class TriadScore(BaseModel):
    """Score for a triad dimension."""
    dimension: TriadDimensionSchema = Field(..., description="Triad dimension")
    score: float = Field(..., ge=0.0, le=100.0, description="Average score (0-100)")
    indicator_count: int = Field(..., ge=0, description="Number of indicators in this dimension")
    measurement_count: int = Field(..., ge=0, description="Total measurements")


class QualityAssessmentRequest(BaseModel):
    """Request for quality assessment calculation."""
    period_start: date = Field(..., description="Start date of assessment period")
    period_end: date = Field(..., description="End date of assessment period")
    pillar_ids: List[int] | None = Field(None, description="Optional: Filter by specific pillars")
    indicator_ids: List[int] | None = Field(None, description="Optional: Filter by specific indicators")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "period_start": "2026-01-01",
                    "period_end": "2026-01-31",
                    "pillar_ids": None,
                    "indicator_ids": None
                }
            ]
        }
    }


class QualityAssessmentResponse(BaseModel):
    """Response with complete quality assessment."""
    period_start: date = Field(..., description="Start date of assessment period")
    period_end: date = Field(..., description="End date of assessment period")
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Overall quality score (0-100)")
    pillar_scores: List[PillarScore] = Field(..., description="Scores for each pillar")
    triad_scores: List[TriadScore] = Field(..., description="Scores for each triad dimension")
    total_indicators: int = Field(..., ge=0, description="Total number of indicators evaluated")
    total_measurements: int = Field(..., ge=0, description="Total number of measurements")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "period_start": "2026-01-01",
                    "period_end": "2026-01-31",
                    "overall_score": 78.5,
                    "pillar_scores": [],
                    "triad_scores": [],
                    "total_indicators": 15,
                    "total_measurements": 120
                }
            ]
        }
    }


class PillarAssessmentResponse(BaseModel):
    """Response with assessment for a specific pillar."""
    pillar_id: int = Field(..., description="Pillar ID")
    pillar_name: str = Field(..., description="Pillar name")
    period_start: date = Field(..., description="Start date of assessment period")
    period_end: date = Field(..., description="End date of assessment period")
    score: float = Field(..., ge=0.0, le=100.0, description="Pillar score (0-100)")
    indicator_scores: List[IndicatorScore] = Field(..., description="Scores of indicators in this pillar")
    total_measurements: int = Field(..., ge=0, description="Total measurements")


class TriadAssessmentResponse(BaseModel):
    """Response with assessment for a specific triad dimension."""
    dimension: TriadDimensionSchema = Field(..., description="Triad dimension")
    period_start: date = Field(..., description="Start date of assessment period")
    period_end: date = Field(..., description="End date of assessment period")
    score: float = Field(..., ge=0.0, le=100.0, description="Dimension score (0-100)")
    indicator_scores: List[IndicatorScore] = Field(..., description="Scores of indicators in this dimension")
    total_measurements: int = Field(..., ge=0, description="Total measurements")

