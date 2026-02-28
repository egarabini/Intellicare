"""
Unit tests for Pillar schemas.
"""

import pytest
from pydantic import ValidationError

from donabedian.schemas.pillar import (
    PillarCreate,
    PillarUpdate,
    PillarRead,
)


class TestPillarCreate:
    """Tests for PillarCreate schema."""
    
    def test_valid_pillar_create(self):
        """Test creating a valid pillar."""
        data = {
            "name": "Eficácia",
            "description": "Capacidade de produzir o efeito desejado",
            "display_order": 1
        }
        pillar = PillarCreate(**data)
        assert pillar.name == "Eficácia"
        assert pillar.description == "Capacidade de produzir o efeito desejado"
        assert pillar.display_order == 1
    
    def test_name_too_long(self):
        """Test that name cannot exceed 50 characters."""
        data = {
            "name": "A" * 51,
            "description": "Test description",
            "display_order": 1
        }
        with pytest.raises(ValidationError) as exc_info:
            PillarCreate(**data)
        assert "name" in str(exc_info.value)
    
    def test_display_order_out_of_range(self):
        """Test that display_order must be between 1 and 7."""
        data = {
            "name": "Test",
            "description": "Test description",
            "display_order": 8
        }
        with pytest.raises(ValidationError) as exc_info:
            PillarCreate(**data)
        assert "display_order" in str(exc_info.value)
    
    def test_empty_name(self):
        """Test that name cannot be empty."""
        data = {
            "name": "   ",
            "description": "Test description",
            "display_order": 1
        }
        with pytest.raises(ValidationError) as exc_info:
            PillarCreate(**data)
        assert "empty" in str(exc_info.value).lower()
    
    def test_name_whitespace_trimmed(self):
        """Test that name whitespace is trimmed."""
        data = {
            "name": "  Eficácia  ",
            "description": "Test description",
            "display_order": 1
        }
        pillar = PillarCreate(**data)
        assert pillar.name == "Eficácia"


class TestPillarUpdate:
    """Tests for PillarUpdate schema."""
    
    def test_valid_partial_update(self):
        """Test updating only description."""
        data = {"description": "Nova descrição"}
        pillar = PillarUpdate(**data)
        assert pillar.description == "Nova descrição"
        assert pillar.name is None
        assert pillar.display_order is None
    
    def test_empty_update(self):
        """Test that empty update is valid."""
        pillar = PillarUpdate()
        assert pillar.name is None
        assert pillar.description is None
        assert pillar.display_order is None
    
    def test_invalid_display_order(self):
        """Test that display_order validation works in update."""
        data = {"display_order": 0}
        with pytest.raises(ValidationError) as exc_info:
            PillarUpdate(**data)
        assert "display_order" in str(exc_info.value)


class TestPillarRead:
    """Tests for PillarRead schema."""
    
    def test_valid_pillar_read(self):
        """Test reading a pillar with id."""
        data = {
            "id": 1,
            "name": "Eficácia",
            "description": "Capacidade de produzir o efeito desejado",
            "display_order": 1
        }
        pillar = PillarRead(**data)
        assert pillar.id == 1
        assert pillar.name == "Eficácia"
    
    def test_from_orm_model(self):
        """Test that from_attributes is enabled."""
        # This would work with actual ORM model
        assert PillarRead.model_config.get("from_attributes") is True

