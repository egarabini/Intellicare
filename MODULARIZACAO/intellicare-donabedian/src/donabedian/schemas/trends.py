"""
Trends schemas for temporal analysis.

Schemas for trend analysis endpoints that show evolution over time.
"""

from typing import List, Optional
from datetime import date
from pydantic import BaseModel, Field
from enum import Enum


class TrendDirection(str, Enum):
    """Direction of trend."""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    INSUFFICIENT_DATA = "insufficient_data"


class DataPoint(BaseModel):
    """Single data point in a time series."""
    measurement_date: date = Field(..., description="Date of the measurement")
    value: float = Field(..., description="Measured value")
    score: float = Field(..., ge=0.0, le=100.0, description="Quality score (0-100)")
    status_label: str = Field(..., description="Status (green, yellow, red)")


class TrendAnalysis(BaseModel):
    """Trend analysis result."""
    direction: TrendDirection = Field(..., description="Overall trend direction")
    slope: Optional[float] = Field(None, description="Slope of the trend line (if calculable)")
    change_percent: Optional[float] = Field(None, description="Percentage change from first to last")
    data_points: int = Field(..., ge=0, description="Number of data points")
    first_value: Optional[float] = Field(None, description="First value in period")
    last_value: Optional[float] = Field(None, description="Last value in period")
    average_value: Optional[float] = Field(None, description="Average value in period")
    min_value: Optional[float] = Field(None, description="Minimum value in period")
    max_value: Optional[float] = Field(None, description="Maximum value in period")


class IndicatorTrend(BaseModel):
    """Trend data for a single indicator."""
    indicator_id: int = Field(..., description="Indicator ID")
    indicator_name: str = Field(..., description="Indicator name")
    period_start: date = Field(..., description="Start date of analysis period")
    period_end: date = Field(..., description="End date of analysis period")
    target_value: float = Field(..., description="Target value")
    time_series: List[DataPoint] = Field(..., description="Time series data points")
    trend_analysis: TrendAnalysis = Field(..., description="Trend analysis")
    current_score: float = Field(..., ge=0.0, le=100.0, description="Current quality score")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "indicator_id": 1,
                    "indicator_name": "Taxa de Ocupação",
                    "period_start": "2025-12-01",
                    "period_end": "2026-01-31",
                    "target_value": 85.0,
                    "time_series": [
                        {"measurement_date": "2025-12-01", "value": 82.0, "score": 50.0, "status_label": "yellow"},
                        {"measurement_date": "2026-01-01", "value": 87.0, "score": 100.0, "status_label": "green"}
                    ],
                    "trend_analysis": {
                        "direction": "improving",
                        "slope": 0.16,
                        "change_percent": 6.1,
                        "data_points": 2,
                        "first_value": 82.0,
                        "last_value": 87.0,
                        "average_value": 84.5,
                        "min_value": 82.0,
                        "max_value": 87.0
                    },
                    "current_score": 100.0
                }
            ]
        }
    }


class PillarTrend(BaseModel):
    """Trend data for a pillar (aggregated from its indicators)."""
    pillar_id: int = Field(..., description="Pillar ID")
    pillar_name: str = Field(..., description="Pillar name")
    period_start: date = Field(..., description="Start date of analysis period")
    period_end: date = Field(..., description="End date of analysis period")
    indicator_trends: List[IndicatorTrend] = Field(..., description="Trends for each indicator in this pillar")
    aggregated_time_series: List[DataPoint] = Field(..., description="Aggregated time series (weighted average)")
    trend_analysis: TrendAnalysis = Field(..., description="Aggregated trend analysis")
    current_score: float = Field(..., ge=0.0, le=100.0, description="Current pillar score")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "pillar_id": 1,
                    "pillar_name": "Eficácia",
                    "period_start": "2025-12-01",
                    "period_end": "2026-01-31",
                    "indicator_trends": [],
                    "aggregated_time_series": [],
                    "trend_analysis": {
                        "direction": "improving",
                        "slope": 0.5,
                        "change_percent": 10.0,
                        "data_points": 10,
                        "first_value": 75.0,
                        "last_value": 82.5,
                        "average_value": 78.5,
                        "min_value": 72.0,
                        "max_value": 85.0
                    },
                    "current_score": 82.5
                }
            ]
        }
    }

