"""
Pillar schemas for request/response validation.

Schemas for the 7 pillars of Donabedian quality framework.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional


class PillarBase(BaseModel):
    """Base schema with common pillar fields."""
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Pillar name (efficacy, effectiveness, efficiency, optimality, acceptability, legitimacy, equity)",
        examples=["Eficácia"]
    )
    
    description: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Pillar description in Portuguese",
        examples=["Capacidade de produzir o efeito desejado em condições ideais"]
    )
    
    display_order: int = Field(
        ...,
        ge=1,
        le=7,
        description="Display order (1-7)",
        examples=[1]
    )
    
    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        """Validate that name is not empty or whitespace."""
        if not v or not v.strip():
            raise ValueError('name cannot be empty or whitespace')
        return v.strip()
    
    @field_validator('description')
    @classmethod
    def description_must_not_be_empty(cls, v: str) -> str:
        """Validate that description is not empty or whitespace."""
        if not v or not v.strip():
            raise ValueError('description cannot be empty or whitespace')
        return v.strip()


class PillarCreate(PillarBase):
    """Schema for creating a new pillar."""
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Eficácia",
                "description": "Capacidade de produzir o efeito desejado em condições ideais",
                "display_order": 1
            }
        }
    }


class PillarUpdate(BaseModel):
    """Schema for updating an existing pillar."""
    
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=50,
        description="Pillar name"
    )
    
    description: Optional[str] = Field(
        None,
        min_length=1,
        max_length=500,
        description="Pillar description"
    )
    
    display_order: Optional[int] = Field(
        None,
        ge=1,
        le=7,
        description="Display order (1-7)"
    )
    
    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v: Optional[str]) -> Optional[str]:
        """Validate that name is not empty or whitespace if provided."""
        if v is not None and (not v or not v.strip()):
            raise ValueError('name cannot be empty or whitespace')
        return v.strip() if v else None
    
    @field_validator('description')
    @classmethod
    def description_must_not_be_empty(cls, v: Optional[str]) -> Optional[str]:
        """Validate that description is not empty or whitespace if provided."""
        if v is not None and (not v or not v.strip()):
            raise ValueError('description cannot be empty or whitespace')
        return v.strip() if v else None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "description": "Nova descrição atualizada do pilar"
            }
        }
    }


class PillarRead(PillarBase):
    """Schema for reading a pillar (includes id)."""
    
    id: int = Field(..., description="Pillar ID", examples=[1])
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "name": "Eficácia",
                "description": "Capacidade de produzir o efeito desejado em condições ideais",
                "display_order": 1
            }
        }
    }


class PillarList(BaseModel):
    """Schema for listing pillars (simplified)."""
    
    id: int = Field(..., description="Pillar ID")
    name: str = Field(..., description="Pillar name")
    display_order: int = Field(..., description="Display order")
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "name": "Eficácia",
                "display_order": 1
            }
        }
    }

