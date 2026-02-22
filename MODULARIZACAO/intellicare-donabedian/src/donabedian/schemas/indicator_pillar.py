"""
IndicatorPillar schemas for request/response validation.

Schemas for the N:N relationship between indicators and pillars with weights.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional


class IndicatorPillarBase(BaseModel):
    """Base schema with common indicator-pillar fields."""
    
    indicator_id: int = Field(
        ...,
        gt=0,
        description="Indicator ID",
        examples=[1]
    )
    
    pillar_id: int = Field(
        ...,
        gt=0,
        description="Pillar ID",
        examples=[1]
    )
    
    weight: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Weight/importance of this indicator in this pillar (0.0-1.0)",
        examples=[1.0]
    )
    
    @field_validator('weight')
    @classmethod
    def weight_must_be_valid(cls, v: float) -> float:
        """Validate that weight is between 0.0 and 1.0."""
        if v < 0.0 or v > 1.0:
            raise ValueError('weight must be between 0.0 and 1.0')
        return v


class IndicatorPillarCreate(IndicatorPillarBase):
    """Schema for creating a new indicator-pillar association."""
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "indicator_id": 1,
                "pillar_id": 1,
                "weight": 1.0
            }
        }
    }


class IndicatorPillarUpdate(BaseModel):
    """Schema for updating an existing indicator-pillar association."""
    
    weight: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Weight/importance of this indicator in this pillar (0.0-1.0)"
    )
    
    @field_validator('weight')
    @classmethod
    def weight_must_be_valid(cls, v: Optional[float]) -> Optional[float]:
        """Validate that weight is between 0.0 and 1.0 if provided."""
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError('weight must be between 0.0 and 1.0')
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "weight": 0.8
            }
        }
    }


class IndicatorPillarRead(IndicatorPillarBase):
    """Schema for reading an indicator-pillar association (includes id)."""
    
    id: int = Field(..., description="IndicatorPillar ID")
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "indicator_id": 1,
                "pillar_id": 1,
                "weight": 1.0
            }
        }
    }


class IndicatorPillarWithNames(IndicatorPillarRead):
    """Schema for reading indicator-pillar with related names."""
    
    indicator_name: str = Field(..., description="Indicator name")
    pillar_name: str = Field(..., description="Pillar name")
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "indicator_id": 1,
                "pillar_id": 1,
                "weight": 1.0,
                "indicator_name": "Taxa de Infecção Hospitalar",
                "pillar_name": "Eficácia"
            }
        }
    }


class IndicatorPillarList(BaseModel):
    """Schema for listing indicator-pillar associations (simplified)."""
    
    id: int = Field(..., description="IndicatorPillar ID")
    indicator_id: int = Field(..., description="Indicator ID")
    pillar_id: int = Field(..., description="Pillar ID")
    weight: float = Field(..., description="Weight")
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "indicator_id": 1,
                "pillar_id": 1,
                "weight": 1.0
            }
        }
    }

