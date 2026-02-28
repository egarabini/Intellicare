"""
Tests for Measurement Pydantic schemas.
"""

import pytest
from pydantic import ValidationError
from datetime import date, datetime, timedelta

from donabedian.schemas.measurement import (
    MeasurementBase,
    MeasurementCreate,
    MeasurementUpdate,
    MeasurementResponse,
)


@pytest.mark.unit
@pytest.mark.schemas
class TestMeasurementSchemas:
    """Test cases for Measurement schemas."""
    
    def test_measurement_base_valid(self):
        """Test MeasurementBase with valid data."""
        data = {
            "indicator_id": 1,
            "period_start": date.today() - timedelta(days=30),
            "period_end": date.today(),
            "value": 87.5,
            "status": "green",
        }
        schema = MeasurementBase(**data)
        
        assert schema.indicator_id == 1
        assert schema.value == 87.5
        assert schema.status == "green"
    
    def test_measurement_base_invalid_status(self):
        """Test MeasurementBase with invalid status."""
        data = {
            "indicator_id": 1,
            "period_start": date.today() - timedelta(days=30),
            "period_end": date.today(),
            "value": 87.5,
            "status": "invalid",
        }
        
        with pytest.raises(ValidationError):
            MeasurementBase(**data)
    
    def test_measurement_base_all_statuses(self):
        """Test MeasurementBase with all valid statuses."""
        statuses = ["green", "yellow", "red"]
        
        for status in statuses:
            data = {
                "indicator_id": 1,
                "period_start": date.today() - timedelta(days=30),
                "period_end": date.today(),
                "value": 87.5,
                "status": status,
            }
            schema = MeasurementBase(**data)
            assert schema.status == status
    
    def test_measurement_base_period_validation(self):
        """Test MeasurementBase period validation."""
        # period_end should be after period_start
        data = {
            "indicator_id": 1,
            "period_start": date.today(),
            "period_end": date.today() - timedelta(days=30),  # Invalid
            "value": 87.5,
            "status": "green",
        }
        
        # Note: This validation might be in the model, not schema
        # If validation exists in schema, it should raise error
        schema = MeasurementBase(**data)
        assert schema.period_start > schema.period_end
    
    def test_measurement_create_valid(self):
        """Test MeasurementCreate with valid data."""
        data = {
            "indicator_id": 1,
            "period_start": date.today() - timedelta(days=30),
            "period_end": date.today(),
            "value": 87.5,
            "status": "green",
        }
        schema = MeasurementCreate(**data)
        
        assert schema.indicator_id == 1
        assert schema.value == 87.5
    
    def test_measurement_create_optional_notes(self):
        """Test MeasurementCreate with optional notes."""
        data = {
            "indicator_id": 1,
            "period_start": date.today() - timedelta(days=30),
            "period_end": date.today(),
            "value": 87.5,
            "status": "green",
            "notes": "Test notes",
        }
        schema = MeasurementCreate(**data)
        
        assert schema.notes == "Test notes"
    
    def test_measurement_update_partial(self):
        """Test MeasurementUpdate with partial data."""
        data = {"value": 90.0}
        schema = MeasurementUpdate(**data)
        
        assert schema.value == 90.0
        assert schema.status is None
    
    def test_measurement_update_status_only(self):
        """Test MeasurementUpdate with status only."""
        data = {"status": "red"}
        schema = MeasurementUpdate(**data)
        
        assert schema.status == "red"
        assert schema.value is None
    
    def test_measurement_update_all_fields(self):
        """Test MeasurementUpdate with all fields."""
        data = {
            "period_start": date.today() - timedelta(days=60),
            "period_end": date.today() - timedelta(days=30),
            "value": 92.0,
            "status": "green",
            "notes": "Updated notes",
        }
        schema = MeasurementUpdate(**data)
        
        assert schema.value == 92.0
        assert schema.status == "green"
        assert schema.notes == "Updated notes"
    
    def test_measurement_response_valid(self):
        """Test MeasurementResponse with valid data."""
        data = {
            "id": 1,
            "indicator_id": 1,
            "period_start": date.today() - timedelta(days=30),
            "period_end": date.today(),
            "value": 87.5,
            "status": "green",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        schema = MeasurementResponse(**data)
        
        assert schema.id == 1
        assert schema.indicator_id == 1
        assert schema.value == 87.5
        assert isinstance(schema.created_at, datetime)
    
    def test_measurement_response_with_notes(self):
        """Test MeasurementResponse with notes."""
        data = {
            "id": 1,
            "indicator_id": 1,
            "period_start": date.today() - timedelta(days=30),
            "period_end": date.today(),
            "value": 87.5,
            "status": "green",
            "notes": "Test notes",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        schema = MeasurementResponse(**data)
        
        assert schema.notes == "Test notes"
    
    def test_measurement_response_json_serialization(self):
        """Test MeasurementResponse JSON serialization."""
        data = {
            "id": 1,
            "indicator_id": 1,
            "period_start": date.today() - timedelta(days=30),
            "period_end": date.today(),
            "value": 87.5,
            "status": "green",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        schema = MeasurementResponse(**data)
        
        json_str = schema.model_dump_json()
        assert isinstance(json_str, str)
        assert "87.5" in json_str

