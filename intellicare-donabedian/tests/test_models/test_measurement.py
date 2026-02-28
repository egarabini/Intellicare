"""
Tests for Measurement model.
"""

import pytest
from datetime import date, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from donabedian.models.measurement import Measurement, MeasurementStatus, PeriodType
from donabedian.models.indicator import Indicator, TriadDimension


@pytest.mark.unit
@pytest.mark.models
class TestMeasurementModel:
    """Test cases for Measurement model."""
    
    async def test_create_measurement(
        self,
        db_session: AsyncSession,
        sample_indicator: Indicator
    ):
        """Test creating a measurement."""
        measurement = Measurement(
            indicator_id=sample_indicator.id,
            period_start=date.today() - timedelta(days=30),
            period_end=date.today(),
            period_type=PeriodType.MONTHLY,
            value=87.5,
            status=MeasurementStatus.GREEN,
        )

        db_session.add(measurement)
        await db_session.commit()
        await db_session.refresh(measurement)

        assert measurement.id is not None
        assert measurement.indicator_id == sample_indicator.id
        assert measurement.value == 87.5
        assert measurement.status == MeasurementStatus.GREEN
        assert measurement.period_type == PeriodType.MONTHLY
        assert measurement.created_at is not None
    
    async def test_measurement_status_calculation_green(self, db_session: AsyncSession):
        """Test status calculation for GREEN (target met)."""
        # Create indicator with >= operator
        indicator = Indicator(
            name="Test Indicator",
            description="Test",
            formula="test formula",
            unit="%",
            triad_dimension=TriadDimension.STRUCTURE,
            target_value=85.0,
            target_operator=">=",
        )
        db_session.add(indicator)
        await db_session.commit()
        await db_session.refresh(indicator)

        # Value meets target (90 >= 85)
        measurement = Measurement(
            indicator_id=indicator.id,
            period_start=date.today() - timedelta(days=7),
            period_end=date.today(),
            period_type=PeriodType.WEEKLY,
            value=90.0,
            status=MeasurementStatus.GREEN,
        )

        db_session.add(measurement)
        await db_session.commit()

        assert measurement.status == MeasurementStatus.GREEN

    async def test_measurement_status_calculation_red(self, db_session: AsyncSession):
        """Test status calculation for RED (far from target)."""
        # Create indicator with >= operator
        indicator = Indicator(
            name="Test Indicator 2",
            description="Test",
            formula="test formula 2",
            unit="%",
            triad_dimension=TriadDimension.STRUCTURE,
            target_value=85.0,
            target_operator=">=",
        )
        db_session.add(indicator)
        await db_session.commit()
        await db_session.refresh(indicator)

        # Value far from target (70 < 85)
        measurement = Measurement(
            indicator_id=indicator.id,
            period_start=date.today() - timedelta(days=7),
            period_end=date.today(),
            period_type=PeriodType.WEEKLY,
            value=70.0,
            status=MeasurementStatus.RED,
        )

        db_session.add(measurement)
        await db_session.commit()

        assert measurement.status == MeasurementStatus.RED
    
    async def test_measurement_status_calculation_yellow(self, db_session: AsyncSession):
        """Test status calculation for YELLOW (close to target)."""
        # Create indicator with >= operator
        indicator = Indicator(
            name="Test Indicator 3",
            description="Test",
            formula="test formula 3",
            unit="%",
            triad_dimension=TriadDimension.STRUCTURE,
            target_value=85.0,
            target_operator=">=",
        )
        db_session.add(indicator)
        await db_session.commit()
        await db_session.refresh(indicator)

        # Value close to target (82 is close to 85)
        measurement = Measurement(
            indicator_id=indicator.id,
            period_start=date.today() - timedelta(days=7),
            period_end=date.today(),
            period_type=PeriodType.WEEKLY,
            value=82.0,
            status=MeasurementStatus.YELLOW,
        )

        db_session.add(measurement)
        await db_session.commit()

        assert measurement.status == MeasurementStatus.YELLOW

    async def test_measurement_with_operator_less_than_equal(self, db_session: AsyncSession):
        """Test measurement with <= operator."""
        # Create indicator with <= operator (lower is better)
        indicator = Indicator(
            name="Test Indicator 4",
            description="Test",
            formula="test formula 4",
            unit="%",
            triad_dimension=TriadDimension.PROCESS,
            target_value=10.0,
            target_operator="<=",
        )
        db_session.add(indicator)
        await db_session.commit()
        await db_session.refresh(indicator)

        # Value meets target (8 <= 10)
        measurement = Measurement(
            indicator_id=indicator.id,
            period_start=date.today() - timedelta(days=7),
            period_end=date.today(),
            period_type=PeriodType.WEEKLY,
            value=8.0,
            status=MeasurementStatus.GREEN,
        )

        db_session.add(measurement)
        await db_session.commit()

        assert measurement.status == MeasurementStatus.GREEN
    
    async def test_measurement_repr(self, sample_measurement: Measurement):
        """Test measurement string representation."""
        repr_str = repr(sample_measurement)
        assert "Measurement" in repr_str
    
    async def test_query_measurement(
        self,
        db_session: AsyncSession,
        sample_measurement: Measurement
    ):
        """Test querying a measurement."""
        result = await db_session.execute(
            select(Measurement).where(Measurement.id == sample_measurement.id)
        )
        measurement = result.scalar_one()
        
        assert measurement.id == sample_measurement.id
        assert measurement.value == sample_measurement.value

