"""
Unit tests for Measurement schemas.
"""

import pytest
from datetime import date, datetime
from pydantic import ValidationError

from donabedian.schemas.measurement import (
    MeasurementCreate,
    MeasurementUpdate,
    MeasurementRead,
    PeriodTypeSchema,
    MeasurementStatusSchema,
)


class TestMeasurementCreate:
    """Tests for MeasurementCreate schema."""
    
    def test_valid_measurement_create(self):
        """Test creating a valid measurement."""
        data = {
            "indicator_id": 1,
            "value": 4.2,
            "period_start": date(2026, 1, 1),
            "period_end": date(2026, 1, 31),
            "period_type": "monthly"
        }
        measurement = MeasurementCreate(**data)
        assert measurement.indicator_id == 1
        assert measurement.value == 4.2
        assert measurement.period_type == PeriodTypeSchema.MONTHLY
    
    def test_period_end_before_start(self):
        """Test that period_end must be >= period_start."""
        data = {
            "indicator_id": 1,
            "value": 4.2,
            "period_start": date(2026, 1, 31),
            "period_end": date(2026, 1, 1),
            "period_type": "monthly"
        }
        with pytest.raises(ValidationError) as exc_info:
            MeasurementCreate(**data)
        assert "period_end" in str(exc_info.value)
    
    def test_negative_value(self):
        """Test that value must be >= 0."""
        data = {
            "indicator_id": 1,
            "value": -1.0,
            "period_start": date(2026, 1, 1),
            "period_end": date(2026, 1, 31),
            "period_type": "monthly"
        }
        with pytest.raises(ValidationError) as exc_info:
            MeasurementCreate(**data)
        assert "value" in str(exc_info.value)
    
    def test_same_start_and_end_date(self):
        """Test that period_start can equal period_end (daily measurement)."""
        data = {
            "indicator_id": 1,
            "value": 4.2,
            "period_start": date(2026, 1, 1),
            "period_end": date(2026, 1, 1),
            "period_type": "daily"
        }
        measurement = MeasurementCreate(**data)
        assert measurement.period_start == measurement.period_end


class TestMeasurementUpdate:
    """Tests for MeasurementUpdate schema."""
    
    def test_valid_partial_update(self):
        """Test updating only value."""
        data = {"value": 5.0}
        measurement = MeasurementUpdate(**data)
        assert measurement.value == 5.0
        assert measurement.period_start is None
    
    def test_empty_update(self):
        """Test that empty update is valid."""
        measurement = MeasurementUpdate()
        assert measurement.value is None
        assert measurement.period_start is None
    
    def test_period_validation_in_update(self):
        """Test that period validation works when both dates are provided."""
        data = {
            "period_start": date(2026, 1, 31),
            "period_end": date(2026, 1, 1)
        }
        with pytest.raises(ValidationError) as exc_info:
            MeasurementUpdate(**data)
        assert "period_end" in str(exc_info.value)


class TestMeasurementRead:
    """Tests for MeasurementRead schema."""
    
    def test_valid_measurement_read(self):
        """Test reading a measurement with status."""
        data = {
            "id": 1,
            "indicator_id": 1,
            "value": 4.2,
            "period_start": date(2026, 1, 1),
            "period_end": date(2026, 1, 31),
            "period_type": "monthly",
            "status": "green",
            "created_at": datetime(2026, 2, 10, 12, 0, 0)
        }
        measurement = MeasurementRead(**data)
        assert measurement.id == 1
        assert measurement.status == MeasurementStatusSchema.GREEN
        assert measurement.created_at == datetime(2026, 2, 10, 12, 0, 0)

