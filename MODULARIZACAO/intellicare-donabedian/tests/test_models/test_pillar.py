"""
Tests for Pillar model.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from donabedian.models.pillar import Pillar


@pytest.mark.unit
@pytest.mark.models
class TestPillarModel:
    """Test cases for Pillar model."""
    
    async def test_create_pillar(self, db_session: AsyncSession):
        """Test creating a pillar."""
        pillar = Pillar(
            name="Eficácia",
            description="Capacidade de produzir melhorias na saúde",
            display_order=1,
        )

        db_session.add(pillar)
        await db_session.commit()
        await db_session.refresh(pillar)

        assert pillar.id is not None
        assert pillar.name == "Eficácia"
        assert pillar.display_order == 1
    
    async def test_pillar_unique_name(self, db_session: AsyncSession):
        """Test that pillar name must be unique."""
        pillar1 = Pillar(name="Eficácia", description="Test", display_order=1)
        pillar2 = Pillar(name="Eficácia", description="Test 2", display_order=2)

        db_session.add(pillar1)
        await db_session.commit()

        db_session.add(pillar2)

        with pytest.raises(Exception):  # IntegrityError
            await db_session.commit()

    async def test_pillar_display_order(self, db_session: AsyncSession):
        """Test pillar display order."""
        pillar1 = Pillar(name="Eficácia", description="Test", display_order=1)
        pillar2 = Pillar(name="Efetividade", description="Test 2", display_order=2)

        db_session.add(pillar1)
        db_session.add(pillar2)
        await db_session.commit()

        result = await db_session.execute(select(Pillar).order_by(Pillar.display_order))
        pillars = result.scalars().all()

        assert len(pillars) == 2
        assert pillars[0].display_order == 1
        assert pillars[1].display_order == 2
    
    async def test_pillar_repr(self, sample_pillar: Pillar):
        """Test pillar string representation."""
        repr_str = repr(sample_pillar)
        assert "Pillar" in repr_str
        assert "Eficácia" in repr_str
    
    async def test_query_pillar(self, db_session: AsyncSession, sample_pillar: Pillar):
        """Test querying a pillar."""
        result = await db_session.execute(
            select(Pillar).where(Pillar.id == sample_pillar.id)
        )
        pillar = result.scalar_one()
        
        assert pillar.id == sample_pillar.id
        assert pillar.name == sample_pillar.name
    
    async def test_update_pillar(self, db_session: AsyncSession, sample_pillar: Pillar):
        """Test updating a pillar."""
        original_description = sample_pillar.description

        sample_pillar.description = "Updated description"
        await db_session.commit()
        await db_session.refresh(sample_pillar)

        assert sample_pillar.description == "Updated description"
        assert sample_pillar.description != original_description
    
    async def test_delete_pillar(self, db_session: AsyncSession, sample_pillar: Pillar):
        """Test deleting a pillar."""
        pillar_id = sample_pillar.id
        
        await db_session.delete(sample_pillar)
        await db_session.commit()
        
        result = await db_session.execute(
            select(Pillar).where(Pillar.id == pillar_id)
        )
        pillar = result.scalar_one_or_none()
        
        assert pillar is None
    
    async def test_pillar_relationships(
        self,
        db_session: AsyncSession,
        sample_indicator_pillar
    ):
        """Test pillar relationships with indicators."""
        pillar_id = sample_indicator_pillar.pillar_id

        result = await db_session.execute(
            select(Pillar).where(Pillar.id == pillar_id)
        )
        pillar = result.scalar_one()

        # Load relationships
        await db_session.refresh(pillar, ["indicator_pillars"])

        assert len(pillar.indicator_pillars) > 0
        assert pillar.indicator_pillars[0].pillar_id == pillar.id

