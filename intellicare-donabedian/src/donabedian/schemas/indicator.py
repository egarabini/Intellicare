"""
Indicator schemas for request/response validation.

Schemas for quality indicators with triad dimensions and target configuration.
"""

from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from enum import Enum


class TriadDimensionSchema(str, Enum):
    """Triad dimension enum for schemas."""
    STRUCTURE = "structure"
    PROCESS = "process"
    OUTCOME = "outcome"


class TargetOperatorSchema(str, Enum):
    """Target operator enum for schemas."""
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    EQUAL = "=="


class IndicatorBase(BaseModel):
    """Base schema with common indicator fields."""
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Indicator name",
        examples=["Taxa de Infecção Hospitalar"]
    )
    
    description: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Detailed description of the indicator",
        examples=["Percentual de pacientes que desenvolveram infecção durante internação"]
    )
    
    formula: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Calculation formula",
        examples=["(número de infecções / total de pacientes) * 100"]
    )
    
    unit: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Unit of measurement",
        examples=["%"]
    )
    
    target_value: float = Field(
        ...,
        gt=0,
        description="Target value to be achieved",
        examples=[5.0]
    )
    
    target_operator: TargetOperatorSchema = Field(
        ...,
        description="Comparison operator for target",
        examples=["<="]
    )
    
    triad_dimension: TriadDimensionSchema = Field(
        ...,
        description="Donabedian triad dimension",
        examples=["outcome"]
    )
    
    @field_validator('name', 'description', 'formula', 'unit')
    @classmethod
    def string_must_not_be_empty(cls, v: str) -> str:
        """Validate that string fields are not empty or whitespace."""
        if not v or not v.strip():
            raise ValueError('field cannot be empty or whitespace')
        return v.strip()


class IndicatorCreate(IndicatorBase):
    """Schema for creating a new indicator."""
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Taxa de Infecção Hospitalar",
                "description": "Percentual de pacientes que desenvolveram infecção durante internação",
                "formula": "(número de infecções / total de pacientes) * 100",
                "unit": "%",
                "target_value": 5.0,
                "target_operator": "<=",
                "triad_dimension": "outcome"
            }
        }
    }


class IndicatorUpdate(BaseModel):
    """Schema for updating an existing indicator."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1, max_length=1000)
    formula: Optional[str] = Field(None, min_length=1, max_length=500)
    unit: Optional[str] = Field(None, min_length=1, max_length=50)
    target_value: Optional[float] = Field(None, gt=0)
    target_operator: Optional[TargetOperatorSchema] = None
    triad_dimension: Optional[TriadDimensionSchema] = None
    
    @field_validator('name', 'description', 'formula', 'unit')
    @classmethod
    def string_must_not_be_empty(cls, v: Optional[str]) -> Optional[str]:
        """Validate that string fields are not empty or whitespace if provided."""
        if v is not None and (not v or not v.strip()):
            raise ValueError('field cannot be empty or whitespace')
        return v.strip() if v else None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "target_value": 4.5,
                "description": "Nova descrição atualizada"
            }
        }
    }


class IndicatorRead(IndicatorBase):
    """Schema for reading an indicator (includes id and timestamps)."""
    
    id: int = Field(..., description="Indicator ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "name": "Taxa de Infecção Hospitalar",
                "description": "Percentual de pacientes que desenvolveram infecção durante internação",
                "formula": "(número de infecções / total de pacientes) * 100",
                "unit": "%",
                "target_value": 5.0,
                "target_operator": "<=",
                "triad_dimension": "outcome",
                "created_at": "2026-02-10T12:00:00",
                "updated_at": "2026-02-10T12:00:00"
            }
        }
    }


class IndicatorList(BaseModel):
    """Schema for listing indicators (simplified)."""
    
    id: int = Field(..., description="Indicator ID")
    name: str = Field(..., description="Indicator name")
    unit: str = Field(..., description="Unit of measurement")
    target_value: float = Field(..., description="Target value")
    triad_dimension: TriadDimensionSchema = Field(..., description="Triad dimension")
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "name": "Taxa de Infecção Hospitalar",
                "unit": "%",
                "target_value": 5.0,
                "triad_dimension": "outcome"
            }
        }
    }

