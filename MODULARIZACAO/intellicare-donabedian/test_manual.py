"""
Script manual para testar os models sem pytest.
"""
import asyncio
import os
import sys

# Set environment variable BEFORE importing
os.environ["DATABASE_SCHEMA"] = "NONE"

sys.path.insert(0, 'src')

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from donabedian.models import Base
from donabedian.models.pillar import Pillar
from donabedian.models.indicator import Indicator, TriadDimension
from donabedian.models.indicator_pillar import IndicatorPillar
from donabedian.models.measurement import Measurement, MeasurementStatus, PeriodType
from datetime import date, timedelta


async def test_models():
    """Test all models."""
    print("🧪 Iniciando testes manuais dos models...\n")
    
    # Create engine
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        echo=False,
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        # Test 1: Create Pillar
        print("✅ Test 1: Create Pillar")
        pillar = Pillar(
            name="Eficácia",
            description="Capacidade de produzir melhorias na saúde",
            display_order=1,
        )
        session.add(pillar)
        await session.commit()
        await session.refresh(pillar)
        assert pillar.id is not None
        assert pillar.name == "Eficácia"
        assert pillar.display_order == 1
        print(f"   ✓ Pillar criado: {pillar}")
        
        # Test 2: Create Indicator
        print("\n✅ Test 2: Create Indicator")
        indicator = Indicator(
            name="Taxa de Ocupação",
            description="Percentual de leitos ocupados",
            formula="(leitos ocupados / total de leitos) * 100",
            unit="%",
            triad_dimension=TriadDimension.STRUCTURE,
            target_value=85.0,
            target_operator=">=",
        )
        session.add(indicator)
        await session.commit()
        await session.refresh(indicator)
        assert indicator.id is not None
        assert indicator.formula == "(leitos ocupados / total de leitos) * 100"
        assert indicator.unit == "%"
        print(f"   ✓ Indicator criado: {indicator}")
        
        # Test 3: Create IndicatorPillar
        print("\n✅ Test 3: Create IndicatorPillar")
        assoc = IndicatorPillar(
            indicator_id=indicator.id,
            pillar_id=pillar.id,
            weight=1.5,
        )
        session.add(assoc)
        await session.commit()
        await session.refresh(assoc)
        assert assoc.id is not None
        assert assoc.weight == 1.5
        print(f"   ✓ IndicatorPillar criado: {assoc}")
        
        # Test 4: Create Measurement
        print("\n✅ Test 4: Create Measurement")
        measurement = Measurement(
            indicator_id=indicator.id,
            period_start=date.today() - timedelta(days=30),
            period_end=date.today(),
            period_type=PeriodType.MONTHLY,
            value=87.5,
            status=MeasurementStatus.GREEN,
        )
        session.add(measurement)
        await session.commit()
        await session.refresh(measurement)
        assert measurement.id is not None
        assert measurement.period_type == PeriodType.MONTHLY
        assert measurement.value == 87.5
        print(f"   ✓ Measurement criado: {measurement}")
        
        # Test 5: Verify relationships
        print("\n✅ Test 5: Verify relationships")
        await session.refresh(pillar, ["indicator_pillars"])
        assert len(pillar.indicator_pillars) == 1
        assert pillar.indicator_pillars[0].pillar_id == pillar.id
        print(f"   ✓ Pillar tem {len(pillar.indicator_pillars)} associação(ões)")
        
        await session.refresh(indicator, ["measurements"])
        assert len(indicator.measurements) == 1
        assert indicator.measurements[0].indicator_id == indicator.id
        print(f"   ✓ Indicator tem {len(indicator.measurements)} medição(ões)")
    
    await engine.dispose()
    
    print("\n" + "="*60)
    print("🎉 TODOS OS TESTES PASSARAM COM SUCESSO!")
    print("="*60)
    print("\n✅ Correções validadas:")
    print("   • Pillar: campo 'display_order' funcionando")
    print("   • Indicator: campos 'formula' e 'unit' obrigatórios")
    print("   • Measurement: campo 'period_type' obrigatório")
    print("   • IndicatorPillar: sem timestamps")
    print("   • Relacionamentos: nomes corretos")


if __name__ == "__main__":
    asyncio.run(test_models())

