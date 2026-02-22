"""
Unit tests for SQLAlchemy models.
"""

import pytest
from datetime import datetime, date
from sqlalchemy import select

from donabedian.models import Pillar, Indicator, IndicatorPillar, Measurement
from donabedian.models.indicator import TriadDimension, TargetOperator
from donabedian.models.measurement import PeriodType, MeasurementStatus


class TestPillarModel:
    """Tests for Pillar model."""
    
    async def test_create_pillar(self, db_session):
        """Test creating a pillar."""
        pillar = Pillar(
            name="efficacy",
            description="O cuidado funciona em condições ideais?",
            display_order=1
        )
        
        db_session.add(pillar)
        await db_session.commit()
        await db_session.refresh(pillar)
        
        assert pillar.id is not None
        assert pillar.name == "efficacy"
        assert pillar.display_order == 1
    
    async def test_pillar_unique_name(self, db_session):
        """Test that pillar names must be unique."""
        pillar1 = Pillar(name="efficacy", description="Test 1", display_order=1)
        pillar2 = Pillar(name="efficacy", description="Test 2", display_order=2)
        
        db_session.add(pillar1)
        await db_session.commit()
        
        db_session.add(pillar2)
        with pytest.raises(Exception):  # IntegrityError
            await db_session.commit()


class TestIndicatorModel:
    """Tests for Indicator model."""
    
    async def test_create_indicator(self, db_session):
        """Test creating an indicator."""
        indicator = Indicator(
            name="Taxa de Infecção Hospitalar",
            description="Percentual de pacientes que desenvolvem infecção hospitalar",
            formula="(infecções / total_pacientes) * 100",
            unit="%",
            target_value=5.0,
            target_operator=TargetOperator.LESS_EQUAL,
            triad_dimension=TriadDimension.OUTCOME
        )
        
        db_session.add(indicator)
        await db_session.commit()
        await db_session.refresh(indicator)
        
        assert indicator.id is not None
        assert indicator.name == "Taxa de Infecção Hospitalar"
        assert indicator.target_operator == TargetOperator.LESS_EQUAL
        assert indicator.triad_dimension == TriadDimension.OUTCOME
        assert indicator.created_at is not None
        assert indicator.updated_at is not None


class TestIndicatorPillarModel:
    """Tests for IndicatorPillar model (N:N with weight)."""
    
    async def test_create_indicator_pillar_with_weight(self, db_session):
        """Test creating indicator-pillar association with weight."""
        # Create pillar
        pillar = Pillar(name="efficacy", description="Test", display_order=1)
        db_session.add(pillar)
        
        # Create indicator
        indicator = Indicator(
            name="Test Indicator",
            description="Test",
            formula="test",
            unit="%",
            target_value=90.0,
            target_operator=TargetOperator.GREATER_EQUAL,
            triad_dimension=TriadDimension.PROCESS
        )
        db_session.add(indicator)
        await db_session.commit()
        
        # Create association with weight
        indicator_pillar = IndicatorPillar(
            indicator_id=indicator.id,
            pillar_id=pillar.id,
            weight=0.8
        )
        db_session.add(indicator_pillar)
        await db_session.commit()
        await db_session.refresh(indicator_pillar)
        
        assert indicator_pillar.id is not None
        assert indicator_pillar.weight == 0.8
        assert indicator_pillar.indicator_id == indicator.id
        assert indicator_pillar.pillar_id == pillar.id


class TestMeasurementModel:
    """Tests for Measurement model."""
    
    async def test_create_measurement(self, db_session):
        """Test creating a measurement."""
        # Create indicator first
        indicator = Indicator(
            name="Test Indicator",
            description="Test",
            formula="test",
            unit="%",
            target_value=90.0,
            target_operator=TargetOperator.GREATER_EQUAL,
            triad_dimension=TriadDimension.OUTCOME
        )
        db_session.add(indicator)
        await db_session.commit()
        
        # Create measurement
        measurement = Measurement(
            indicator_id=indicator.id,
            value=95.5,
            period_start=date(2026, 1, 1),
            period_end=date(2026, 1, 31),
            period_type=PeriodType.MONTHLY,
            status=MeasurementStatus.GREEN
        )
        db_session.add(measurement)
        await db_session.commit()
        await db_session.refresh(measurement)
        
        assert measurement.id is not None
        assert measurement.value == 95.5
        assert measurement.status == MeasurementStatus.GREEN
        assert measurement.period_type == PeriodType.MONTHLY
        assert measurement.created_at is not None

