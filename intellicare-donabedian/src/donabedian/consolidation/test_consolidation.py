"""
E2E tests for donabedian consolidation.

Tests the full consolidation flow:
1. CREATE pilar event in Redis
2. DonabedianConsolidationConsumer processes it
3. Data is consolidated to analitico schema
4. Verify consolidated_at timestamp and consolidation_source

Requires:
- Redis 7+ running
- PostgreSQL 15+ with migrations 001-005 applied
- Donabedian operacional + analitico schemas
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

import pytest
import redis.asyncio as aioredis
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Suppress verbose logging during tests
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# Configuration from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://admin_intellicare:Crazy%23-57@161.97.141.186:5432/IntellicareDB")


@pytest.fixture
async def redis_client():
    """Get Redis client."""
    r = await aioredis.from_url(REDIS_URL)
    yield r
    await r.close()


@pytest.fixture
async def db_engine():
    """Create async SQLAlchemy engine."""
    engine = create_async_engine(DATABASE_URL, echo=False)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine):
    """Create async session."""
    async_session = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        yield session


@pytest.fixture
async def consolidation_service():
    """Create consolidation service."""
    from donabedian.consolidation.service import DonabedianConsolidationService
    service = DonabedianConsolidationService(db_url=DATABASE_URL)
    yield service
    await service.close()


@pytest.fixture
async def clean_redis(redis_client):
    """Clean Redis before each test."""
    # Delete all donabedian streams
    streams = [
        "intellicare:donabedian:pilar.create",
        "intellicare:donabedian:pilar.update",
        "intellicare:donabedian:pilar.delete",
        "intellicare:donabedian:indicator.create",
        "intellicare:donabedian:indicator.update",
        "intellicare:donabedian:indicator.delete",
        "intellicare:donabedian:measurement.create",
        "intellicare:donabedian:measurement.update",
        "intellicare:donabedian:measurement.delete",
    ]
    
    for stream in streams:
        try:
            await redis_client.delete(stream)
            logger.info(f"Cleaned stream: {stream}")
        except Exception as e:
            logger.warning(f"Could not clean {stream}: {e}")
    
    yield redis_client


@pytest.fixture
async def clean_db(db_session):
    """Clean donabedian analitico tables before each test."""
    # Delete from analitico schema
    try:
        await db_session.execute(text("DELETE FROM donabedian.analitico.medida"))
        await db_session.execute(text("DELETE FROM donabedian.analitico.indicador_pilar"))
        await db_session.execute(text("DELETE FROM donabedian.analitico.pilar_medida"))
        await db_session.execute(text("DELETE FROM donabedian.analitico.indicador"))
        await db_session.execute(text("DELETE FROM donabedian.analitico.pilar"))
        await db_session.commit()
        logger.info("Cleaned donabedian analitico schema")
    except Exception as e:
        logger.warning(f"Could not clean analitico tables: {e}")
    
    yield db_session


class TestConsolidationConsumer:
    """Test donabedian consolidation consumer."""

    async def test_pilar_create_event_consolidation(
        self,
        clean_redis,
        clean_db,
        consolidation_service
    ):
        """Test that Pilar CREATE event is consolidated to analitico."""
        # Create test data
        pilar_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        # Create event message
        event = {
            "entity_id": pilar_id,
            "operation": "CREATE",
            "data": json.dumps({
                "old_values": None,
                "new_values": {
                    "nome": "Test Pilar",
                    "descricao": "Test description",
                    "tipo": "OUTCOME",
                    "ordem_exibicao": 1,
                    "ativo": True,
                }
            }),
            "timestamp": timestamp,
        }

        # Publish to Redis
        await clean_redis.xadd(
            "intellicare:donabedian:pilar.create",
            event
        )
        logger.info(f"Published pilar.create event for {pilar_id}")

        # Process event
        success = await consolidation_service.consolidate(
            entity_type="Pilar",
            entity_id=pilar_id,
            operation="CREATE",
            old_values=None,
            new_values=event["data"] and json.loads(event["data"]).get("new_values"),
            timestamp=timestamp
        )

        assert success, "Consolidation should succeed"

        # Verify in analitico
        result = await clean_db.execute(
            text(f"""
                SELECT id, nome, descricao, tipo, consolidation_source, consolidated_at
                FROM donabedian.analitico.pilar
                WHERE id = :id
            """),
            {"id": pilar_id}
        )

        row = result.first()
        assert row is not None, "Pilar should be in analitico"
        assert row[1] == "Test Pilar"
        assert row[4] == "pilar.CREATE"
        assert row[5] is not None, "consolidated_at should be set"

        logger.info(f"✅ Pilar {pilar_id} successfully consolidated")

    async def test_pilar_update_event_consolidation(
        self,
        clean_redis,
        clean_db,
        consolidation_service
    ):
        """Test that Pilar UPDATE event is consolidated."""
        pilar_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        # First, insert into analitico
        await clean_db.execute(text("""
            INSERT INTO donabedian.analitico.pilar 
            (id, nome, descricao, tipo, ordem_exibicao, ativo, rowversion, valid_to, consolidation_source, consolidated_at)
            VALUES (:id, :nome, :descricao, :tipo, 1, true, 1, NULL, 'initial', NOW())
        """), {
            "id": pilar_id,
            "nome": "Old Name",
            "descricao": "Old Description",
            "tipo": "OUTCOME",
        })
        await clean_db.commit()
        logger.info(f"Inserted initial pilar {pilar_id}") 

        # Update event
        success = await consolidation_service.consolidate(
            entity_type="Pilar",
            entity_id=pilar_id,
            operation="UPDATE",
            old_values={"nome": "Old Name"},
            new_values={"nome": "Updated Name", "descricao": "Updated Description"},
            timestamp=timestamp
        )

        assert success, "Update consolidation should succeed"

        # Verify update
        result = await clean_db.execute(
            text(f"""
                SELECT nome, descricao, consolidation_source
                FROM donabedian.analitico.pilar
                WHERE id = :id
            """),
            {"id": pilar_id}
        )

        row = result.first()
        assert row is not None
        assert row[0] == "Updated Name"
        assert row[2] == "pilar.UPDATE"

        logger.info(f"✅ Pilar {pilar_id} successfully updated")

    async def test_pilar_delete_event_consolidation(
        self,
        clean_redis,
        clean_db,
        consolidation_service
    ):
        """Test that Pilar DELETE event sets valid_to (soft delete)."""
        pilar_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        # First, insert into analitico
        await clean_db.execute(text("""
            INSERT INTO donabedian.analitico.pilar 
            (id, nome, descricao, tipo, ordem_exibicao, ativo, rowversion, valid_to, consolidation_source, consolidated_at)
            VALUES (:id, 'Test', 'Desc', 'OUTCOME', 1, true, 1, NULL, 'initial', NOW())
        """), {"id": pilar_id})
        await clean_db.commit()

        # Delete event
        success = await consolidation_service.consolidate(
            entity_type="Pilar",
            entity_id=pilar_id,
            operation="DELETE",
            old_values={"id": pilar_id},
            new_values=None,
            timestamp=timestamp
        )

        assert success, "Delete consolidation should succeed"

        # Verify soft delete
        result = await clean_db.execute(
            text(f"""
                SELECT valid_to, consolidation_source
                FROM donabedian.analitico.pilar
                WHERE id = :id
            """),
            {"id": pilar_id}
        )

        row = result.first()
        assert row is not None
        assert row[0] is not None, "valid_to should be set for soft delete"
        assert row[1] == "pilar.DELETE"

        logger.info(f"✅ Pilar {pilar_id} successfully soft-deleted")

    async def test_consolidation_consumer_worker(self, clean_redis, clean_db):
        """Test the full consolidation consumer loop."""
        from donabedian.consolidation.worker import DonabedianConsolidationConsumer

        pilar_id = str(uuid.uuid4())
        event_data = {
            "entity_id": pilar_id,
            "operation": "CREATE",
            "data": json.dumps({
                "old_values": None,
                "new_values": {
                    "nome": "Consumer Test Pilar",
                    "descricao": "Testing consumer",
                    "tipo": "OUTCOME",
                    "ordem_exibicao": 1,
                    "ativo": True,
                }
            }),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Add event to Redis
        await clean_redis.xadd(
            "intellicare:donabedian:pilar.create",
            event_data,
            maxlen=100
        )
        logger.info(f"Added event to Redis for {pilar_id}")

        # Initialize consumer
        consumer = DonabedianConsolidationConsumer(
            redis_url=REDIS_URL,
            db_url=DATABASE_URL,
            consumer_id="test-consumer-1",
            batch_size=10,
        )

        # Setup consumer groups
        await consumer.setup_consumer_groups()

        # Process one batch
        redis = clean_redis
        group_name = "donabedian-consolidation"
        
        messages = await redis.xreadgroup(
            {"intellicare:donabedian:pilar.create": ">"},
            group_name,
            "test-consumer-1",
            count=1,
            block=1000,
        )

        if messages:
            for stream_key, stream_messages in messages:
                for stream_id, message in stream_messages:
                    msg_id = stream_id if isinstance(stream_id, str) else stream_id.decode()
                    
                    # Decode message
                    decoded = {}
                    for k, v in message.items():
                        key = k if isinstance(k, str) else k.decode()
                        val = v if isinstance(v, str) else v.decode()
                        decoded[key] = val
                    
                    # Process
                    success = await consumer.process_event(
                        "intellicare:donabedian:pilar.create",
                        decoded
                    )
                    
                    if success:
                        await redis.xack(
                            "intellicare:donabedian:pilar.create",
                            group_name,
                            msg_id
                        )
                        logger.info(f"✅ Processed and ACK'd {msg_id}")

        await consumer.close()

        # Verify in analitico
        result = await clean_db.execute(
            text(f"""
                SELECT id, nome
                FROM donabedian.analitico.pilar
                WHERE id = :id
            """),
            {"id": pilar_id}
        )

        row = result.first()
        assert row is not None, "Pilar should be in analitico after consumer processing"
        assert row[1] == "Consumer Test Pilar"

        logger.info(f"✅ Full consumer loop successful")

    async def test_consolidated_at_timestamp(self, clean_db, consolidation_service):
        """Test that consolidated_at timestamp is recent."""
        pilar_id = str(uuid.uuid4())
        before_time = datetime.now(timezone.utc)

        success = await consolidation_service.consolidate(
            entity_type="Pilar",
            entity_id=pilar_id,
            operation="CREATE",
            old_values=None,
            new_values={"nome": "Test", "tipo": "OUTCOME"},
            timestamp=before_time.isoformat(),
        )

        assert success

        after_time = datetime.now(timezone.utc)

        # Check consolidated_at is between before and after
        result = await clean_db.execute(
            text(f"""
                SELECT consolidated_at
                FROM donabedian.analitico.pilar
                WHERE id = :id
            """),
            {"id": pilar_id}
        )

        row = result.first()
        assert row is not None
        consolidated_at = row[0]

        # Convert to datetime if needed
        if isinstance(consolidated_at, str):
            consolidated_at = datetime.fromisoformat(consolidated_at)

        assert before_time <= consolidated_at <= after_time, \
            "consolidated_at should be within test window"

        logger.info(f"✅ consolidated_at timestamp verified")

    async def test_indicator_create_event_consolidation(
        self,
        clean_redis,
        clean_db,
        consolidation_service
    ):
        """Test that Indicator CREATE event is consolidated to analitico."""
        indicator_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        # Create event message
        event = {
            "entity_id": indicator_id,
            "operation": "CREATE",
            "data": json.dumps({
                "old_values": None,
                "new_values": {
                    "nome": "Test Indicator",
                    "descricao": "Test indicator description",
                    "formula": "x + y",
                    "unidade": "%",
                    "valor_meta": 85.0,
                    "operador_meta": ">=",
                    "dimensao_triado": "SAFE",
                    "ativo": True,
                }
            }),
            "timestamp": timestamp,
        }

        # Publish to Redis
        await clean_redis.xadd(
            "intellicare:donabedian:indicator.create",
            event
        )
        logger.info(f"Published indicator.create event for {indicator_id}")

        # Process event
        success = await consolidation_service.consolidate(
            entity_type="Indicator",
            entity_id=indicator_id,
            operation="CREATE",
            old_values=None,
            new_values=event["data"] and json.loads(event["data"]).get("new_values"),
            timestamp=timestamp
        )

        assert success, "Indicator consolidation should succeed"

        # Verify in analitico
        result = await clean_db.execute(
            text(f"""
                SELECT id, nome, descricao, formula, unidade, valor_meta, consolidation_source, consolidated_at
                FROM donabedian.analitico.indicador
                WHERE id = :id
            """),
            {"id": indicator_id}
        )

        row = result.first()
        assert row is not None, "Indicator should be in analitico"
        assert row[1] == "Test Indicator"
        assert row[3] == "x + y"
        assert row[6] == "indicator.CREATE"
        assert row[7] is not None, "consolidated_at should be set"

        logger.info(f"✅ Indicator {indicator_id} successfully consolidated")

    async def test_indicator_update_event_consolidation(
        self,
        clean_redis,
        clean_db,
        consolidation_service
    ):
        """Test that Indicator UPDATE event is consolidated."""
        indicator_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        # First, insert into analitico
        await clean_db.execute(text("""
            INSERT INTO donabedian.analitico.indicador 
            (id, nome, descricao, formula, unidade, valor_meta, operador_meta, dimensao_triado, 
             ativo, rowversion, valid_to, consolidation_source, consolidated_at)
            VALUES (:id, :nome, :descricao, :formula, :unidade, :valor_meta, :operador_meta, 
                    :dimensao_triado, true, 1, NULL, 'initial', NOW())
        """), {
            "id": indicator_id,
            "nome": "Old Indicator",
            "descricao": "Old description",
            "formula": "x",
            "unidade": "%",
            "valor_meta": 80.0,
            "operador_meta": ">=",
            "dimensao_triado": "SAFE",
        })
        await clean_db.commit()
        logger.info(f"Inserted initial indicator {indicator_id}")

        # Update event
        success = await consolidation_service.consolidate(
            entity_type="Indicator",
            entity_id=indicator_id,
            operation="UPDATE",
            old_values={"nome": "Old Indicator"},
            new_values={"nome": "Updated Indicator", "valor_meta": 90.0},
            timestamp=timestamp
        )

        assert success, "Update consolidation should succeed"

        # Verify update
        result = await clean_db.execute(
            text(f"""
                SELECT nome, valor_meta, consolidation_source
                FROM donabedian.analitico.indicador
                WHERE id = :id
            """),
            {"id": indicator_id}
        )

        row = result.first()
        assert row is not None
        assert row[0] == "Updated Indicator"
        assert row[1] == 90.0
        assert row[2] == "indicator.UPDATE"

        logger.info(f"✅ Indicator {indicator_id} successfully updated")

    async def test_indicator_delete_event_consolidation(
        self,
        clean_redis,
        clean_db,
        consolidation_service
    ):
        """Test that Indicator DELETE event sets valid_to (soft delete)."""
        indicator_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        # First, insert into analitico
        await clean_db.execute(text("""
            INSERT INTO donabedian.analitico.indicador 
            (id, nome, descricao, formula, unidade, valor_meta, operador_meta, dimensao_triado,
             ativo, rowversion, valid_to, consolidation_source, consolidated_at)
            VALUES (:id, 'Test', 'Desc', 'x+y', '%', 85.0, '>=', 'SAFE', true, 1, NULL, 'initial', NOW())
        """), {"id": indicator_id})
        await clean_db.commit()

        # Delete event
        success = await consolidation_service.consolidate(
            entity_type="Indicator",
            entity_id=indicator_id,
            operation="DELETE",
            old_values={"id": indicator_id},
            new_values=None,
            timestamp=timestamp
        )

        assert success, "Delete consolidation should succeed"

        # Verify soft delete
        result = await clean_db.execute(
            text(f"""
                SELECT valid_to, consolidation_source
                FROM donabedian.analitico.indicador
                WHERE id = :id
            """),
            {"id": indicator_id}
        )

        row = result.first()
        assert row is not None
        assert row[0] is not None, "valid_to should be set for soft delete"
        assert row[1] == "indicator.DELETE"

        logger.info(f"✅ Indicator {indicator_id} successfully soft-deleted")

    async def test_measurement_create_event_consolidation(
        self,
        clean_redis,
        clean_db,
        consolidation_service
    ):
        """Test that Measurement CREATE event is consolidated to analitico."""
        measurement_id = str(uuid.uuid4())
        indicator_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        # Create event message
        event = {
            "entity_id": measurement_id,
            "operation": "CREATE",
            "data": json.dumps({
                "old_values": None,
                "new_values": {
                    "indicator_id": indicator_id,
                    "valor": 87.5,
                    "periodo_inicio": "2024-01-01",
                    "periodo_fim": "2024-01-31",
                    "tipo_periodo": "MONTHLY",
                    "status": "APPROVED",
                }
            }),
            "timestamp": timestamp,
        }

        # Publish to Redis
        await clean_redis.xadd(
            "intellicare:donabedian:measurement.create",
            event
        )
        logger.info(f"Published measurement.create event for {measurement_id}")

        # Process event
        success = await consolidation_service.consolidate(
            entity_type="Measurement",
            entity_id=measurement_id,
            operation="CREATE",
            old_values=None,
            new_values=event["data"] and json.loads(event["data"]).get("new_values"),
            timestamp=timestamp
        )

        assert success, "Measurement consolidation should succeed"

        # Verify in analitico
        result = await clean_db.execute(
            text(f"""
                SELECT id, indicator_id, valor, tipo_periodo, status, consolidation_source, consolidated_at
                FROM donabedian.analitico.medida
                WHERE id = :id
            """),
            {"id": measurement_id}
        )

        row = result.first()
        assert row is not None, "Measurement should be in analitico"
        assert row[2] == 87.5  # valor
        assert row[3] == "MONTHLY"  # tipo_periodo
        assert row[4] == "APPROVED"  # status
        assert row[5] == "measurement.CREATE"
        assert row[6] is not None, "consolidated_at should be set"

        logger.info(f"✅ Measurement {measurement_id} successfully consolidated")

    async def test_measurement_update_event_consolidation(
        self,
        clean_redis,
        clean_db,
        consolidation_service
    ):
        """Test that Measurement UPDATE event is consolidated."""
        measurement_id = str(uuid.uuid4())
        indicator_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        # First, insert into analitico
        await clean_db.execute(text("""
            INSERT INTO donabedian.analitico.medida 
            (id, indicator_id, valor, periodo_inicio, periodo_fim, tipo_periodo, status,
             rowversion, valid_to, consolidation_source, consolidated_at)
            VALUES (:id, :indicator_id, :valor, :periodo_inicio, :periodo_fim, :tipo_periodo, 
                    :status, 1, NULL, 'initial', NOW())
        """), {
            "id": measurement_id,
            "indicator_id": indicator_id,
            "valor": 85.0,
            "periodo_inicio": "2024-01-01",
            "periodo_fim": "2024-01-31",
            "tipo_periodo": "MONTHLY",
            "status": "DRAFT",
        })
        await clean_db.commit()
        logger.info(f"Inserted initial measurement {measurement_id}")

        # Update event
        success = await consolidation_service.consolidate(
            entity_type="Measurement",
            entity_id=measurement_id,
            operation="UPDATE",
            old_values={"valor": 85.0, "status": "DRAFT"},
            new_values={"valor": 89.5, "status": "APPROVED"},
            timestamp=timestamp
        )

        assert success, "Update consolidation should succeed"

        # Verify update
        result = await clean_db.execute(
            text(f"""
                SELECT valor, status, consolidation_source
                FROM donabedian.analitico.medida
                WHERE id = :id
            """),
            {"id": measurement_id}
        )

        row = result.first()
        assert row is not None
        assert row[0] == 89.5
        assert row[1] == "APPROVED"
        assert row[2] == "measurement.UPDATE"

        logger.info(f"✅ Measurement {measurement_id} successfully updated")

    async def test_measurement_delete_event_consolidation(
        self,
        clean_redis,
        clean_db,
        consolidation_service
    ):
        """Test that Measurement DELETE event sets valid_to (soft delete)."""
        measurement_id = str(uuid.uuid4())
        indicator_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        # First, insert into analitico
        await clean_db.execute(text("""
            INSERT INTO donabedian.analitico.medida 
            (id, indicator_id, valor, periodo_inicio, periodo_fim, tipo_periodo, status,
             rowversion, valid_to, consolidation_source, consolidated_at)
            VALUES (:id, :indicator_id, 87.5, '2024-01-01', '2024-01-31', 'MONTHLY', 'APPROVED',
                    1, NULL, 'initial', NOW())
        """), {
            "id": measurement_id,
            "indicator_id": indicator_id,
        })
        await clean_db.commit()

        # Delete event
        success = await consolidation_service.consolidate(
            entity_type="Measurement",
            entity_id=measurement_id,
            operation="DELETE",
            old_values={"id": measurement_id},
            new_values=None,
            timestamp=timestamp
        )

        assert success, "Delete consolidation should succeed"

        # Verify soft delete
        result = await clean_db.execute(
            text(f"""
                SELECT valid_to, consolidation_source
                FROM donabedian.analitico.medida
                WHERE id = :id
            """),
            {"id": measurement_id}
        )

        row = result.first()
        assert row is not None
        assert row[0] is not None, "valid_to should be set for soft delete"
        assert row[1] == "measurement.DELETE"

        logger.info(f"✅ Measurement {measurement_id} successfully soft-deleted")

    async def test_full_pipeline_three_entities(
        self,
        clean_redis,
        clean_db,
        consolidation_service
    ):
        """Test full consolidation pipeline with all 3 entities."""
        pilar_id = str(uuid.uuid4())
        indicator_id = str(uuid.uuid4())
        measurement_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        # 1. Consolidate Pilar
        success_pilar = await consolidation_service.consolidate(
            entity_type="Pilar",
            entity_id=pilar_id,
            operation="CREATE",
            old_values=None,
            new_values={"nome": "Test Pilar", "tipo": "OUTCOME"},
            timestamp=timestamp
        )
        assert success_pilar, "Pilar consolidation should succeed"
        logger.info(f"✅ Pilar created: {pilar_id}")

        # 2. Consolidate Indicator
        success_indicator = await consolidation_service.consolidate(
            entity_type="Indicator",
            entity_id=indicator_id,
            operation="CREATE",
            old_values=None,
            new_values={
                "nome": "Test Indicator",
                "descricao": "Test",
                "formula": "x+y",
                "unidade": "%",
                "valor_meta": 85.0,
                "operador_meta": ">=",
                "dimensao_triado": "SAFE",
                "ativo": True,
            },
            timestamp=timestamp
        )
        assert success_indicator, "Indicator consolidation should succeed"
        logger.info(f"✅ Indicator created: {indicator_id}")

        # 3. Consolidate Measurement
        success_measurement = await consolidation_service.consolidate(
            entity_type="Measurement",
            entity_id=measurement_id,
            operation="CREATE",
            old_values=None,
            new_values={
                "indicator_id": indicator_id,
                "valor": 87.5,
                "periodo_inicio": "2024-01-01",
                "periodo_fim": "2024-01-31",
                "tipo_periodo": "MONTHLY",
                "status": "APPROVED",
            },
            timestamp=timestamp
        )
        assert success_measurement, "Measurement consolidation should succeed"
        logger.info(f"✅ Measurement created: {measurement_id}")

        # Verify all in analitico
        result_pilar = await clean_db.execute(
            text("SELECT id FROM donabedian.analitico.pilar WHERE id = :id"),
            {"id": pilar_id}
        )
        assert result_pilar.first() is not None, "Pilar should be in analitico"

        result_indicator = await clean_db.execute(
            text("SELECT id FROM donabedian.analitico.indicador WHERE id = :id"),
            {"id": indicator_id}
        )
        assert result_indicator.first() is not None, "Indicator should be in analitico"

        result_measurement = await clean_db.execute(
            text("SELECT id FROM donabedian.analitico.medida WHERE id = :id"),
            {"id": measurement_id}
        )
        assert result_measurement.first() is not None, "Measurement should be in analitico"

        logger.info(f"✅ Full pipeline successful: all 3 entities consolidated")


class TestConsolidationErrorHandling:
    """Test error handling in consolidation."""

    async def test_invalid_entity_type_returns_false(self, consolidation_service):
        """Test that invalid entity type returns False."""
        success = await consolidation_service.consolidate(
            entity_type="InvalidType",
            entity_id=str(uuid.uuid4()),
            operation="CREATE",
            old_values=None,
            new_values={},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        assert success is False, "Invalid entity type should return False"

    async def test_invalid_operation_returns_false(self, consolidation_service):
        """Test that invalid operation returns False."""
        success = await consolidation_service.consolidate(
            entity_type="Pilar",
            entity_id=str(uuid.uuid4()),
            operation="INVALID_OP",
            old_values=None,
            new_values={},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        assert success is False, "Invalid operation should return False"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
