"""
Tests for IndicatorPillar Pydantic schemas.
"""

import pytest
from pydantic import ValidationError
from datetime import datetime

from donabedian.schemas.indicator_pillar import (
    IndicatorPillarBase,
    IndicatorPillarCreate,
    IndicatorPillarUpdate,
    IndicatorPillarResponse,
)


@pytest.mark.unit
@pytest.mark.schemas
class TestIndicatorPillarSchemas:
    """Test cases for IndicatorPillar schemas."""
    
    def test_indicator_pillar_base_valid(self):
        """Test IndicatorPillarBase with valid data."""
        data = {
            "indicator_id": 1,
            "pillar_id": 1,
            "weight": 1.5,
        }
        schema = IndicatorPillarBase(**data)
        
        assert schema.indicator_id == 1
        assert schema.pillar_id == 1
        assert schema.weight == 1.5
    
    def test_indicator_pillar_base_default_weight(self):
        """Test IndicatorPillarBase with default weight."""
        data = {
            "indicator_id": 1,
            "pillar_id": 1,
        }
        schema = IndicatorPillarBase(**data)
        
        assert schema.weight == 1.0
    
    def test_indicator_pillar_base_negative_weight(self):
        """Test IndicatorPillarBase with negative weight."""
        data = {
            "indicator_id": 1,
            "pillar_id": 1,
            "weight": -1.0,
        }
        
        # Should allow negative weights or raise validation error
        # Depending on schema validation rules
        schema = IndicatorPillarBase(**data)
        assert schema.weight == -1.0
    
    def test_indicator_pillar_base_zero_weight(self):
        """Test IndicatorPillarBase with zero weight."""
        data = {
            "indicator_id": 1,
            "pillar_id": 1,
            "weight": 0.0,
        }
        schema = IndicatorPillarBase(**data)
        
        assert schema.weight == 0.0
    
    def test_indicator_pillar_create_valid(self):
        """Test IndicatorPillarCreate with valid data."""
        data = {
            "indicator_id": 1,
            "pillar_id": 1,
            "weight": 2.0,
        }
        schema = IndicatorPillarCreate(**data)
        
        assert schema.indicator_id == 1
        assert schema.pillar_id == 1
        assert schema.weight == 2.0
    
    def test_indicator_pillar_create_missing_required_fields(self):
        """Test IndicatorPillarCreate with missing required fields."""
        with pytest.raises(ValidationError) as exc_info:
            IndicatorPillarCreate(indicator_id=1)
        
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("pillar_id",) for e in errors)
    
    def test_indicator_pillar_update_partial(self):
        """Test IndicatorPillarUpdate with partial data."""
        data = {"weight": 3.0}
        schema = IndicatorPillarUpdate(**data)
        
        assert schema.weight == 3.0
        assert schema.indicator_id is None
        assert schema.pillar_id is None
    
    def test_indicator_pillar_update_all_fields(self):
        """Test IndicatorPillarUpdate with all fields."""
        data = {
            "indicator_id": 2,
            "pillar_id": 2,
            "weight": 2.5,
        }
        schema = IndicatorPillarUpdate(**data)
        
        assert schema.indicator_id == 2
        assert schema.pillar_id == 2
        assert schema.weight == 2.5
    
    def test_indicator_pillar_update_empty(self):
        """Test IndicatorPillarUpdate with no fields."""
        schema = IndicatorPillarUpdate()
        
        assert schema.indicator_id is None
        assert schema.pillar_id is None
        assert schema.weight is None
    
    def test_indicator_pillar_response_valid(self):
        """Test IndicatorPillarResponse with valid data."""
        data = {
            "id": 1,
            "indicator_id": 1,
            "pillar_id": 1,
            "weight": 1.5,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        schema = IndicatorPillarResponse(**data)
        
        assert schema.id == 1
        assert schema.indicator_id == 1
        assert schema.pillar_id == 1
        assert schema.weight == 1.5
        assert isinstance(schema.created_at, datetime)
        assert isinstance(schema.updated_at, datetime)
    
    def test_indicator_pillar_response_missing_id(self):
        """Test IndicatorPillarResponse with missing id."""
        data = {
            "indicator_id": 1,
            "pillar_id": 1,
            "weight": 1.5,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        
        with pytest.raises(ValidationError) as exc_info:
            IndicatorPillarResponse(**data)
        
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("id",) for e in errors)
    
    def test_indicator_pillar_response_json_serialization(self):
        """Test IndicatorPillarResponse JSON serialization."""
        data = {
            "id": 1,
            "indicator_id": 1,
            "pillar_id": 1,
            "weight": 1.5,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        schema = IndicatorPillarResponse(**data)
        
        json_str = schema.model_dump_json()
        assert isinstance(json_str, str)
        assert "1.5" in json_str

