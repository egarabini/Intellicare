"""
Measurement schemas for request/response validation.

Schemas for time-series measurements of indicators.
"""

from datetime import datetime, date
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional
from enum import Enum


class PeriodTypeSchema(str, Enum):
    """Period type enum for schemas."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class MeasurementStatusSchema(str, Enum):
    """Measurement status enum for schemas."""
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


class MeasurementBase(BaseModel):
    """Base schema with common measurement fields."""
    
    indicator_id: int = Field(
        ...,
        gt=0,
        description="Indicator ID",
        examples=[1]
    )
    
    value: float = Field(
        ...,
        ge=0.0,
        description="Measured value",
        examples=[4.2]
    )
    
    period_start: date = Field(
        ...,
        description="Start date of measurement period",
        examples=["2026-01-01"]
    )
    
    period_end: date = Field(
        ...,
        description="End date of measurement period",
        examples=["2026-01-31"]
    )
    
    period_type: PeriodTypeSchema = Field(
        ...,
        description="Type of period",
        examples=["monthly"]
    )
    
    @model_validator(mode='after')
    def validate_period_dates(self):
        """Validate that period_end >= period_start."""
        if self.period_end < self.period_start:
            raise ValueError('period_end must be greater than or equal to period_start')
        return self


class MeasurementCreate(MeasurementBase):
    """
    Schema for creating a new measurement.
    
    Note: status is NOT included here as it will be auto-calculated
    based on the indicator's target_value and target_operator.
    """
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "indicator_id": 1,
                "value": 4.2,
                "period_start": "2026-01-01",
                "period_end": "2026-01-31",
                "period_type": "monthly"
            }
        }
    }


class MeasurementUpdate(BaseModel):
    """Schema for updating an existing measurement."""
    
    value: Optional[float] = Field(None, ge=0.0, description="Measured value")
    period_start: Optional[date] = Field(None, description="Start date of measurement period")
    period_end: Optional[date] = Field(None, description="End date of measurement period")
    period_type: Optional[PeriodTypeSchema] = Field(None, description="Type of period")
    
    @model_validator(mode='after')
    def validate_period_dates(self):
        """Validate that period_end >= period_start if both are provided."""
        if self.period_start and self.period_end:
            if self.period_end < self.period_start:
                raise ValueError('period_end must be greater than or equal to period_start')
        return self
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "value": 4.5
            }
        }
    }


class MeasurementRead(MeasurementBase):
    """Schema for reading a measurement (includes id, status, and timestamps)."""
    
    id: int = Field(..., description="Measurement ID")
    status: MeasurementStatusSchema = Field(..., description="Status (green/yellow/red)")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "indicator_id": 1,
                "value": 4.2,
                "period_start": "2026-01-01",
                "period_end": "2026-01-31",
                "period_type": "monthly",
                "status": "green",
                "created_at": "2026-02-10T12:00:00"
            }
        }
    }


class MeasurementList(BaseModel):
    """Schema for listing measurements (simplified)."""
    
    id: int = Field(..., description="Measurement ID")
    indicator_id: int = Field(..., description="Indicator ID")
    value: float = Field(..., description="Measured value")
    period_start: date = Field(..., description="Period start date")
    period_end: date = Field(..., description="Period end date")
    status: MeasurementStatusSchema = Field(..., description="Status")
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "indicator_id": 1,
                "value": 4.2,
                "period_start": "2026-01-01",
                "period_end": "2026-01-31",
                "status": "green"
            }
        }
    }


class MeasurementWithIndicator(MeasurementRead):
    """Schema for reading measurement with indicator name."""
    
    indicator_name: str = Field(..., description="Indicator name")
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "indicator_id": 1,
                "value": 4.2,
                "period_start": "2026-01-01",
                "period_end": "2026-01-31",
                "period_type": "monthly",
                "status": "green",
                "created_at": "2026-02-10T12:00:00",
                "indicator_name": "Taxa de Infecção Hospitalar"
            }
        }
    }

