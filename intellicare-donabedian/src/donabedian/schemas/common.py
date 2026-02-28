"""
Common schemas used across the application.

Includes generic response schemas, pagination, and error handling.
"""

from typing import TypeVar, Generic, List, Optional
from pydantic import BaseModel, Field


# Generic type for paginated responses
T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response schema."""
    
    items: List[T] = Field(..., description="List of items in current page")
    total: int = Field(..., ge=0, description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Number of items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "items": [],
                "total": 100,
                "page": 1,
                "page_size": 20,
                "total_pages": 5
            }
        }
    }


class ErrorDetail(BaseModel):
    """Error detail schema."""
    
    field: Optional[str] = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Error message")
    type: Optional[str] = Field(None, description="Error type")


class ErrorResponse(BaseModel):
    """Error response schema."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[List[ErrorDetail]] = Field(None, description="Detailed error information")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "ValidationError",
                "message": "Invalid input data",
                "details": [
                    {
                        "field": "target_value",
                        "message": "must be greater than 0",
                        "type": "value_error"
                    }
                ]
            }
        }
    }


class HealthResponse(BaseModel):
    """Health check response schema."""
    
    status: str = Field(..., description="Service status")
    module: str = Field(..., description="Module name")
    version: str = Field(..., description="Module version")
    database: str = Field(..., description="Database connection status")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "module": "intellicare-donabedian",
                "version": "1.0.0",
                "database": "connected"
            }
        }
    }


class InfoResponse(BaseModel):
    """Module information response schema."""
    
    module_name: str = Field(..., description="Module name")
    module_version: str = Field(..., description="Module version")
    description: str = Field(..., description="Module description")
    api_version: str = Field(..., description="API version")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "module_name": "intellicare-donabedian",
                "module_version": "1.0.0",
                "description": "Quality assessment module based on Donabedian framework",
                "api_version": "v1"
            }
        }
    }


class MessageResponse(BaseModel):
    """Simple message response schema."""
    
    message: str = Field(..., description="Response message")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Operation completed successfully"
            }
        }
    }

