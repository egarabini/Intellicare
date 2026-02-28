"""
Dashboard schemas for consolidated data views.

Schemas for dashboard endpoints that provide summary statistics and KPIs.
"""

from typing import List, Dict
from datetime import date
from pydantic import BaseModel, Field

from donabedian.schemas.indicator import TriadDimensionSchema
from donabedian.schemas.measurement import MeasurementStatusSchema


class StatusDistribution(BaseModel):
    """Distribution of measurements by status."""
    green: int = Field(..., ge=0, description="Number of GREEN measurements")
    yellow: int = Field(..., ge=0, description="Number of YELLOW measurements")
    red: int = Field(..., ge=0, description="Number of RED measurements")
    total: int = Field(..., ge=0, description="Total measurements")
    green_percent: float = Field(..., ge=0.0, le=100.0, description="Percentage of GREEN")
    yellow_percent: float = Field(..., ge=0.0, le=100.0, description="Percentage of YELLOW")
    red_percent: float = Field(..., ge=0.0, le=100.0, description="Percentage of RED")


class PillarSummary(BaseModel):
    """Summary statistics for a pillar."""
    pillar_id: int = Field(..., description="Pillar ID")
    pillar_name: str = Field(..., description="Pillar name")
    pillar_description: str = Field(..., description="Pillar description")
    indicator_count: int = Field(..., ge=0, description="Number of indicators")
    measurement_count: int = Field(..., ge=0, description="Total measurements")
    current_score: float = Field(..., ge=0.0, le=100.0, description="Current quality score")
    status_distribution: StatusDistribution = Field(..., description="Distribution by status")


class IndicatorSummary(BaseModel):
    """Summary statistics for an indicator."""
    indicator_id: int = Field(..., description="Indicator ID")
    indicator_name: str = Field(..., description="Indicator name")
    triad_dimension: TriadDimensionSchema = Field(..., description="Triad dimension")
    pillar_count: int = Field(..., ge=0, description="Number of pillars associated")
    measurement_count: int = Field(..., ge=0, description="Total measurements")
    current_score: float = Field(..., ge=0.0, le=100.0, description="Current quality score")
    latest_value: float | None = Field(None, description="Latest measured value")
    latest_status: MeasurementStatusSchema | None = Field(None, description="Latest status")
    target_value: float = Field(..., description="Target value")


class TriadSummary(BaseModel):
    """Summary statistics for a triad dimension."""
    dimension: TriadDimensionSchema = Field(..., description="Triad dimension")
    indicator_count: int = Field(..., ge=0, description="Number of indicators")
    measurement_count: int = Field(..., ge=0, description="Total measurements")
    current_score: float = Field(..., ge=0.0, le=100.0, description="Current quality score")
    status_distribution: StatusDistribution = Field(..., description="Distribution by status")


class DashboardOverview(BaseModel):
    """Complete dashboard overview with all KPIs."""
    period_start: date = Field(..., description="Start date of current period")
    period_end: date = Field(..., description="End date of current period")
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Overall quality score")
    total_pillars: int = Field(..., ge=0, description="Total number of pillars")
    total_indicators: int = Field(..., ge=0, description="Total number of indicators")
    total_measurements: int = Field(..., ge=0, description="Total measurements in period")
    status_distribution: StatusDistribution = Field(..., description="Overall status distribution")
    pillar_summaries: List[PillarSummary] = Field(..., description="Summary for each pillar")
    triad_summaries: List[TriadSummary] = Field(..., description="Summary for each triad dimension")
    top_performers: List[IndicatorSummary] = Field(..., description="Top 5 performing indicators")
    bottom_performers: List[IndicatorSummary] = Field(..., description="Bottom 5 performing indicators")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "period_start": "2026-01-01",
                    "period_end": "2026-01-31",
                    "overall_score": 78.5,
                    "total_pillars": 7,
                    "total_indicators": 15,
                    "total_measurements": 120,
                    "status_distribution": {
                        "green": 80,
                        "yellow": 30,
                        "red": 10,
                        "total": 120,
                        "green_percent": 66.7,
                        "yellow_percent": 25.0,
                        "red_percent": 8.3
                    },
                    "pillar_summaries": [],
                    "triad_summaries": [],
                    "top_performers": [],
                    "bottom_performers": []
                }
            ]
        }
    }


class PillarsDashboard(BaseModel):
    """Dashboard focused on pillars."""
    period_start: date = Field(..., description="Start date of current period")
    period_end: date = Field(..., description="End date of current period")
    pillar_summaries: List[PillarSummary] = Field(..., description="Summary for each pillar")
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Overall quality score")


class IndicatorsDashboard(BaseModel):
    """Dashboard focused on indicators."""
    period_start: date = Field(..., description="Start date of current period")
    period_end: date = Field(..., description="End date of current period")
    indicator_summaries: List[IndicatorSummary] = Field(..., description="Summary for each indicator")
    by_triad: Dict[str, List[IndicatorSummary]] = Field(..., description="Indicators grouped by triad dimension")
    total_indicators: int = Field(..., ge=0, description="Total number of indicators")

