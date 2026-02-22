"""
Tests for Indicator Pydantic schemas.
"""

import pytest
from pydantic import ValidationError
from datetime import datetime

from donabedian.schemas.indicator import (
    IndicatorBase,
    IndicatorCreate,
    IndicatorUpdate,
    IndicatorResponse,
)
from donabedian.models.indicator import TriadDimension


@pytest.mark.unit
@pytest.mark.schemas
class TestIndicatorSchemas:
    """Test cases for Indicator schemas."""
    
    def test_indicator_base_valid(self):
        """Test IndicatorBase with valid data."""
        data = {
            "name": "Taxa de Ocupação",
            "description": "Percentual de leitos ocupados",
            "triad_dimension": "structure",
            "target_value": 85.0,
            "target_operator": ">=",
            "unit": "%",
        }
        schema = IndicatorBase(**data)
        
        assert schema.name == "Taxa de Ocupação"
        assert schema.triad_dimension == "structure"
        assert schema.target_value == 85.0
        assert schema.target_operator == ">="
        assert schema.unit == "%"
    
    def test_indicator_base_invalid_triad_dimension(self):
        """Test IndicatorBase with invalid triad dimension."""
        data = {
            "name": "Test",
            "description": "Test",
            "triad_dimension": "invalid",
            "target_value": 85.0,
            "target_operator": ">=",
        }
        
        with pytest.raises(ValidationError):
            IndicatorBase(**data)
    
    def test_indicator_base_invalid_operator(self):
        """Test IndicatorBase with invalid operator."""
        data = {
            "name": "Test",
            "description": "Test",
            "triad_dimension": "structure",
            "target_value": 85.0,
            "target_operator": ">",  # Invalid, only >=, <=, == allowed
        }
        
        with pytest.raises(ValidationError):
            IndicatorBase(**data)
    
    def test_indicator_base_all_triad_dimensions(self):
        """Test IndicatorBase with all valid triad dimensions."""
        dimensions = ["structure", "process", "outcome"]
        
        for dimension in dimensions:
            data = {
                "name": f"Test {dimension}",
                "description": "Test",
                "triad_dimension": dimension,
                "target_value": 85.0,
                "target_operator": ">=",
            }
            schema = IndicatorBase(**data)
            assert schema.triad_dimension == dimension
    
    def test_indicator_base_all_operators(self):
        """Test IndicatorBase with all valid operators."""
        operators = [">=", "<=", "=="]
        
        for operator in operators:
            data = {
                "name": f"Test {operator}",
                "description": "Test",
                "triad_dimension": "structure",
                "target_value": 85.0,
                "target_operator": operator,
            }
            schema = IndicatorBase(**data)
            assert schema.target_operator == operator
    
    def test_indicator_create_valid(self):
        """Test IndicatorCreate with valid data."""
        data = {
            "name": "Taxa de Ocupação",
            "description": "Percentual de leitos ocupados",
            "triad_dimension": "structure",
            "target_value": 85.0,
            "target_operator": ">=",
            "unit": "%",
        }
        schema = IndicatorCreate(**data)
        
        assert schema.name == "Taxa de Ocupação"
        assert schema.target_value == 85.0
    
    def test_indicator_create_optional_fields(self):
        """Test IndicatorCreate with optional fields."""
        data = {
            "name": "Test",
            "triad_dimension": "structure",
            "target_value": 85.0,
            "target_operator": ">=",
        }
        schema = IndicatorCreate(**data)
        
        assert schema.description is None
        assert schema.unit is None
    
    def test_indicator_update_partial(self):
        """Test IndicatorUpdate with partial data."""
        data = {"name": "Updated Name"}
        schema = IndicatorUpdate(**data)
        
        assert schema.name == "Updated Name"
        assert schema.target_value is None
    
    def test_indicator_update_target_value(self):
        """Test IndicatorUpdate with target value change."""
        data = {
            "target_value": 90.0,
            "target_operator": "<=",
        }
        schema = IndicatorUpdate(**data)
        
        assert schema.target_value == 90.0
        assert schema.target_operator == "<="
    
    def test_indicator_response_valid(self):
        """Test IndicatorResponse with valid data."""
        data = {
            "id": 1,
            "name": "Taxa de Ocupação",
            "description": "Test",
            "triad_dimension": "structure",
            "target_value": 85.0,
            "target_operator": ">=",
            "unit": "%",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        schema = IndicatorResponse(**data)
        
        assert schema.id == 1
        assert schema.name == "Taxa de Ocupação"
        assert isinstance(schema.created_at, datetime)
    
    def test_indicator_response_json_serialization(self):
        """Test IndicatorResponse JSON serialization."""
        data = {
            "id": 1,
            "name": "Taxa de Ocupação",
            "description": "Test",
            "triad_dimension": "structure",
            "target_value": 85.0,
            "target_operator": ">=",
            "unit": "%",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        schema = IndicatorResponse(**data)
        
        json_str = schema.model_dump_json()
        assert isinstance(json_str, str)
        assert "Taxa de Ocupação" in json_str

