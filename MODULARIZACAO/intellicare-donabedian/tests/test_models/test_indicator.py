"""
Tests for Indicator model.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from donabedian.models.indicator import Indicator, TriadDimension


@pytest.mark.unit
@pytest.mark.models
class TestIndicatorModel:
    """Test cases for Indicator model."""
    
    async def test_create_indicator(self, db_session: AsyncSession):
        """Test creating an indicator."""
        indicator = Indicator(
            name="Taxa de Ocupação",
            description="Percentual de leitos ocupados",
            formula="(leitos ocupados / total de leitos) * 100",
            unit="%",
            triad_dimension=TriadDimension.STRUCTURE,
            target_value=85.0,
            target_operator=">=",
        )

        db_session.add(indicator)
        await db_session.commit()
        await db_session.refresh(indicator)

        assert indicator.id is not None
        assert indicator.name == "Taxa de Ocupação"
        assert indicator.formula == "(leitos ocupados / total de leitos) * 100"
        assert indicator.unit == "%"
        assert indicator.triad_dimension == TriadDimension.STRUCTURE
        assert indicator.target_value == 85.0
        assert indicator.target_operator == ">="
        assert indicator.created_at is not None
        assert indicator.updated_at is not None

    async def test_indicator_unique_name(self, db_session: AsyncSession):
        """Test that indicator name must be unique."""
        indicator1 = Indicator(
            name="Taxa de Ocupação",
            description="Test",
            formula="test formula",
            unit="%",
            triad_dimension=TriadDimension.STRUCTURE,
            target_value=85.0,
            target_operator=">=",
        )
        indicator2 = Indicator(
            name="Taxa de Ocupação",
            description="Test 2",
            formula="test formula 2",
            unit="%",
            triad_dimension=TriadDimension.PROCESS,
            target_value=90.0,
            target_operator=">=",
        )

        db_session.add(indicator1)
        await db_session.commit()

        db_session.add(indicator2)

        with pytest.raises(Exception):  # IntegrityError
            await db_session.commit()

    async def test_indicator_triad_dimensions(self, db_session: AsyncSession):
        """Test all triad dimensions."""
        dimensions = [
            TriadDimension.STRUCTURE,
            TriadDimension.PROCESS,
            TriadDimension.OUTCOME,
        ]

        for i, dimension in enumerate(dimensions):
            indicator = Indicator(
                name=f"Indicator {i}",
                description=f"Test {dimension.value}",
                formula=f"formula {i}",
                unit="%",
                triad_dimension=dimension,
                target_value=80.0,
                target_operator=">=",
            )
            db_session.add(indicator)

        await db_session.commit()

        result = await db_session.execute(select(Indicator))
        indicators = result.scalars().all()

        assert len(indicators) == 3
        assert set(ind.triad_dimension for ind in indicators) == set(dimensions)

    async def test_indicator_target_operators(self, db_session: AsyncSession):
        """Test different target operators."""
        operators = [">=", "<=", "=="]

        for i, operator in enumerate(operators):
            indicator = Indicator(
                name=f"Indicator {i}",
                description=f"Test {operator}",
                formula=f"formula {i}",
                unit="%",
                triad_dimension=TriadDimension.STRUCTURE,
                target_value=80.0,
                target_operator=operator,
            )
            db_session.add(indicator)
        
        await db_session.commit()
        
        result = await db_session.execute(select(Indicator))
        indicators = result.scalars().all()
        
        assert len(indicators) == 3
        assert set(ind.target_operator for ind in indicators) == set(operators)
    
    async def test_indicator_repr(self, sample_indicator: Indicator):
        """Test indicator string representation."""
        repr_str = repr(sample_indicator)
        assert "Indicator" in repr_str
        assert "Taxa de Ocupação" in repr_str
    
    async def test_query_indicator(self, db_session: AsyncSession, sample_indicator: Indicator):
        """Test querying an indicator."""
        result = await db_session.execute(
            select(Indicator).where(Indicator.id == sample_indicator.id)
        )
        indicator = result.scalar_one()
        
        assert indicator.id == sample_indicator.id
        assert indicator.name == sample_indicator.name
    
    async def test_update_indicator(self, db_session: AsyncSession, sample_indicator: Indicator):
        """Test updating an indicator."""
        original_updated_at = sample_indicator.updated_at
        
        sample_indicator.target_value = 90.0
        await db_session.commit()
        await db_session.refresh(sample_indicator)
        
        assert sample_indicator.target_value == 90.0
        assert sample_indicator.updated_at > original_updated_at
    
    async def test_delete_indicator(self, db_session: AsyncSession, sample_indicator: Indicator):
        """Test deleting an indicator."""
        indicator_id = sample_indicator.id
        
        await db_session.delete(sample_indicator)
        await db_session.commit()
        
        result = await db_session.execute(
            select(Indicator).where(Indicator.id == indicator_id)
        )
        indicator = result.scalar_one_or_none()
        
        assert indicator is None

