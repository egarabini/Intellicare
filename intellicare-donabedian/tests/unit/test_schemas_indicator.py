"""
Unit tests for Indicator schemas.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from donabedian.schemas.indicator import (
    IndicatorCreate,
    IndicatorUpdate,
    IndicatorRead,
    TriadDimensionSchema,
    TargetOperatorSchema,
)


class TestIndicatorCreate:
    """Tests for IndicatorCreate schema."""
    
    def test_valid_indicator_create(self):
        """Test creating a valid indicator."""
        data = {
            "name": "Taxa de Infecção Hospitalar",
            "description": "Percentual de pacientes com infecção",
            "formula": "(infecções / total) * 100",
            "unit": "%",
            "target_value": 5.0,
            "target_operator": "<=",
            "triad_dimension": "outcome"
        }
        indicator = IndicatorCreate(**data)
        assert indicator.name == "Taxa de Infecção Hospitalar"
        assert indicator.target_value == 5.0
        assert indicator.target_operator == TargetOperatorSchema.LESS_EQUAL
        assert indicator.triad_dimension == TriadDimensionSchema.OUTCOME
    
    def test_target_value_must_be_positive(self):
        """Test that target_value must be > 0."""
        data = {
            "name": "Test",
            "description": "Test",
            "formula": "test",
            "unit": "%",
            "target_value": 0.0,
            "target_operator": ">=",
            "triad_dimension": "outcome"
        }
        with pytest.raises(ValidationError) as exc_info:
            IndicatorCreate(**data)
        assert "target_value" in str(exc_info.value)
    
    def test_empty_formula(self):
        """Test that formula cannot be empty."""
        data = {
            "name": "Test",
            "description": "Test",
            "formula": "   ",
            "unit": "%",
            "target_value": 5.0,
            "target_operator": ">=",
            "triad_dimension": "outcome"
        }
        with pytest.raises(ValidationError) as exc_info:
            IndicatorCreate(**data)
        assert "empty" in str(exc_info.value).lower()
    
    def test_invalid_triad_dimension(self):
        """Test that invalid triad_dimension is rejected."""
        data = {
            "name": "Test",
            "description": "Test",
            "formula": "test",
            "unit": "%",
            "target_value": 5.0,
            "target_operator": ">=",
            "triad_dimension": "invalid"
        }
        with pytest.raises(ValidationError) as exc_info:
            IndicatorCreate(**data)
        assert "triad_dimension" in str(exc_info.value)


class TestIndicatorUpdate:
    """Tests for IndicatorUpdate schema."""
    
    def test_valid_partial_update(self):
        """Test updating only target_value."""
        data = {"target_value": 4.5}
        indicator = IndicatorUpdate(**data)
        assert indicator.target_value == 4.5
        assert indicator.name is None
    
    def test_empty_update(self):
        """Test that empty update is valid."""
        indicator = IndicatorUpdate()
        assert indicator.name is None
        assert indicator.target_value is None
    
    def test_invalid_target_value_in_update(self):
        """Test that target_value validation works in update."""
        data = {"target_value": -1.0}
        with pytest.raises(ValidationError) as exc_info:
            IndicatorUpdate(**data)
        assert "target_value" in str(exc_info.value)


class TestIndicatorRead:
    """Tests for IndicatorRead schema."""
    
    def test_valid_indicator_read(self):
        """Test reading an indicator with timestamps."""
        data = {
            "id": 1,
            "name": "Taxa de Infecção",
            "description": "Test",
            "formula": "test",
            "unit": "%",
            "target_value": 5.0,
            "target_operator": "<=",
            "triad_dimension": "outcome",
            "created_at": datetime(2026, 2, 10, 12, 0, 0),
            "updated_at": datetime(2026, 2, 10, 12, 0, 0)
        }
        indicator = IndicatorRead(**data)
        assert indicator.id == 1
        assert indicator.created_at == datetime(2026, 2, 10, 12, 0, 0)

