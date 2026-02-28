"""
Tests for IndicatorPillar model.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from donabedian.models.indicator_pillar import IndicatorPillar
from donabedian.models.pillar import Pillar
from donabedian.models.indicator import Indicator


@pytest.mark.unit
@pytest.mark.models
class TestIndicatorPillarModel:
    """Test cases for IndicatorPillar model."""
    
    async def test_create_indicator_pillar(
        self,
        db_session: AsyncSession,
        sample_pillar: Pillar,
        sample_indicator: Indicator
    ):
        """Test creating an indicator-pillar association."""
        assoc = IndicatorPillar(
            indicator_id=sample_indicator.id,
            pillar_id=sample_pillar.id,
            weight=1.5,
        )
        
        db_session.add(assoc)
        await db_session.commit()
        await db_session.refresh(assoc)
        
        assert assoc.id is not None
        assert assoc.indicator_id == sample_indicator.id
        assert assoc.pillar_id == sample_pillar.id
        assert assoc.weight == 1.5
    
    async def test_indicator_pillar_default_weight(
        self,
        db_session: AsyncSession,
        sample_pillar: Pillar,
        sample_indicator: Indicator
    ):
        """Test default weight value."""
        assoc = IndicatorPillar(
            indicator_id=sample_indicator.id,
            pillar_id=sample_pillar.id,
        )
        
        db_session.add(assoc)
        await db_session.commit()
        await db_session.refresh(assoc)
        
        assert assoc.weight == 1.0
    
    async def test_indicator_pillar_unique_constraint(
        self,
        db_session: AsyncSession,
        sample_pillar: Pillar,
        sample_indicator: Indicator
    ):
        """Test unique constraint on (indicator_id, pillar_id)."""
        assoc1 = IndicatorPillar(
            indicator_id=sample_indicator.id,
            pillar_id=sample_pillar.id,
            weight=1.0,
        )
        assoc2 = IndicatorPillar(
            indicator_id=sample_indicator.id,
            pillar_id=sample_pillar.id,
            weight=2.0,
        )
        
        db_session.add(assoc1)
        await db_session.commit()
        
        db_session.add(assoc2)
        
        with pytest.raises(Exception):  # IntegrityError
            await db_session.commit()
    
    async def test_indicator_pillar_foreign_keys(
        self,
        db_session: AsyncSession,
        sample_indicator_pillar: IndicatorPillar
    ):
        """Test foreign key relationships."""
        # Load relationships
        await db_session.refresh(sample_indicator_pillar, ["indicator", "pillar"])
        
        assert sample_indicator_pillar.indicator is not None
        assert sample_indicator_pillar.pillar is not None
        assert sample_indicator_pillar.indicator.id == sample_indicator_pillar.indicator_id
        assert sample_indicator_pillar.pillar.id == sample_indicator_pillar.pillar_id
    
    async def test_indicator_pillar_repr(self, sample_indicator_pillar: IndicatorPillar):
        """Test indicator-pillar string representation."""
        repr_str = repr(sample_indicator_pillar)
        assert "IndicatorPillar" in repr_str
    
    async def test_query_indicator_pillar(
        self,
        db_session: AsyncSession,
        sample_indicator_pillar: IndicatorPillar
    ):
        """Test querying an indicator-pillar association."""
        result = await db_session.execute(
            select(IndicatorPillar).where(IndicatorPillar.id == sample_indicator_pillar.id)
        )
        assoc = result.scalar_one()
        
        assert assoc.id == sample_indicator_pillar.id
        assert assoc.weight == sample_indicator_pillar.weight
    
    async def test_update_indicator_pillar(
        self,
        db_session: AsyncSession,
        sample_indicator_pillar: IndicatorPillar
    ):
        """Test updating an indicator-pillar association."""
        original_weight = sample_indicator_pillar.weight

        sample_indicator_pillar.weight = 2.5
        await db_session.commit()
        await db_session.refresh(sample_indicator_pillar)

        assert sample_indicator_pillar.weight == 2.5
        assert sample_indicator_pillar.weight != original_weight
    
    async def test_delete_indicator_pillar(
        self,
        db_session: AsyncSession,
        sample_indicator_pillar: IndicatorPillar
    ):
        """Test deleting an indicator-pillar association."""
        assoc_id = sample_indicator_pillar.id
        
        await db_session.delete(sample_indicator_pillar)
        await db_session.commit()
        
        result = await db_session.execute(
            select(IndicatorPillar).where(IndicatorPillar.id == assoc_id)
        )
        assoc = result.scalar_one_or_none()
        
        assert assoc is None

