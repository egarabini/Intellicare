"""
Tests for Pillar Pydantic schemas.
"""

import pytest
from pydantic import ValidationError
from datetime import datetime

from donabedian.schemas.pillar import (
    PillarBase,
    PillarCreate,
    PillarUpdate,
    PillarResponse,
)


@pytest.mark.unit
@pytest.mark.schemas
class TestPillarSchemas:
    """Test cases for Pillar schemas."""
    
    def test_pillar_base_valid(self):
        """Test PillarBase with valid data."""
        data = {
            "name": "Eficácia",
            "description": "Capacidade de produzir melhorias na saúde",
            "code": "EFF",
        }
        schema = PillarBase(**data)
        
        assert schema.name == "Eficácia"
        assert schema.description == "Capacidade de produzir melhorias na saúde"
        assert schema.code == "EFF"
    
    def test_pillar_base_missing_required_fields(self):
        """Test PillarBase with missing required fields."""
        with pytest.raises(ValidationError) as exc_info:
            PillarBase(name="Eficácia")
        
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("code",) for e in errors)
    
    def test_pillar_base_empty_name(self):
        """Test PillarBase with empty name."""
        with pytest.raises(ValidationError):
            PillarBase(name="", description="Test", code="EFF")
    
    def test_pillar_base_empty_code(self):
        """Test PillarBase with empty code."""
        with pytest.raises(ValidationError):
            PillarBase(name="Eficácia", description="Test", code="")
    
    def test_pillar_create_valid(self):
        """Test PillarCreate with valid data."""
        data = {
            "name": "Eficácia",
            "description": "Capacidade de produzir melhorias na saúde",
            "code": "EFF",
        }
        schema = PillarCreate(**data)
        
        assert schema.name == "Eficácia"
        assert schema.code == "EFF"
    
    def test_pillar_create_optional_description(self):
        """Test PillarCreate with optional description."""
        data = {
            "name": "Eficácia",
            "code": "EFF",
        }
        schema = PillarCreate(**data)
        
        assert schema.name == "Eficácia"
        assert schema.description is None
    
    def test_pillar_update_partial(self):
        """Test PillarUpdate with partial data."""
        data = {"name": "Eficácia Atualizada"}
        schema = PillarUpdate(**data)
        
        assert schema.name == "Eficácia Atualizada"
        assert schema.description is None
        assert schema.code is None
    
    def test_pillar_update_all_fields(self):
        """Test PillarUpdate with all fields."""
        data = {
            "name": "Eficácia",
            "description": "Nova descrição",
            "code": "EFF2",
        }
        schema = PillarUpdate(**data)
        
        assert schema.name == "Eficácia"
        assert schema.description == "Nova descrição"
        assert schema.code == "EFF2"
    
    def test_pillar_update_empty(self):
        """Test PillarUpdate with no fields."""
        schema = PillarUpdate()
        
        assert schema.name is None
        assert schema.description is None
        assert schema.code is None
    
    def test_pillar_response_valid(self):
        """Test PillarResponse with valid data."""
        data = {
            "id": 1,
            "name": "Eficácia",
            "description": "Capacidade de produzir melhorias na saúde",
            "code": "EFF",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        schema = PillarResponse(**data)
        
        assert schema.id == 1
        assert schema.name == "Eficácia"
        assert schema.code == "EFF"
        assert isinstance(schema.created_at, datetime)
        assert isinstance(schema.updated_at, datetime)
    
    def test_pillar_response_missing_id(self):
        """Test PillarResponse with missing id."""
        data = {
            "name": "Eficácia",
            "description": "Test",
            "code": "EFF",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        
        with pytest.raises(ValidationError) as exc_info:
            PillarResponse(**data)
        
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("id",) for e in errors)
    
    def test_pillar_response_model_config(self):
        """Test PillarResponse model config."""
        data = {
            "id": 1,
            "name": "Eficácia",
            "description": "Test",
            "code": "EFF",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        schema = PillarResponse(**data)
        
        # Test from_attributes config
        assert schema.model_config.get("from_attributes") is True
    
    def test_pillar_response_json_serialization(self):
        """Test PillarResponse JSON serialization."""
        data = {
            "id": 1,
            "name": "Eficácia",
            "description": "Test",
            "code": "EFF",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        schema = PillarResponse(**data)
        
        json_str = schema.model_dump_json()
        assert isinstance(json_str, str)
        assert "Eficácia" in json_str

