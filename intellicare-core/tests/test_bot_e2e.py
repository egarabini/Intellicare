import uuid
import pytest
from unittest.mock import patch, MagicMock
from intellicare_core.subscriptions.channels.bot_channel import send_bot_notification
from intellicare_core.subscriptions.models import SubscriptionRecord
from intellicare_core.bots.models import Bot, BotExecution
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

db_url = os.getenv("DATABASE_URL")
if db_url and db_url.startswith("postgresql+asyncpg://"):
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
engine = create_engine(db_url)
SessionLocal = sessionmaker(bind=engine)

@pytest.mark.asyncio
async def test_end_to_end_bot_execution():
    tenant_id = "test-tenant-e2e"
    bot_id = uuid.uuid4()
    sub_id = uuid.uuid4()
    
    with SessionLocal() as db:
        # Create a bot that simply reads an event and logs "Hello, <PatientName>!"
        bot = Bot(
            id=bot_id,
            tenant_id=tenant_id,
            name="E2E Test Bot",
            code='''
name = resource.get('name', [{}])[0].get('given', ['Unknown'])[0]
log(f"Hello, {name}!")
''',
            status="active",
            timeout_seconds=5
        )
        db.add(bot)
        db.commit()

    try:
        sub = SubscriptionRecord(
            id=sub_id,
            tenant_id=tenant_id,
            channel_type="bot",
            channel_endpoint=f"Bot/{bot_id}"
        )
        
        resource = {
            "resourceType": "Patient",
            "id": "e2e-patient",
            "name": [{"given": ["EndToEndUser"]}]
        }
        
        result = await send_bot_notification(sub, resource)
        
        assert result.success is True
        assert result.subscription_id == sub_id
        
        # Verify in DB
        with SessionLocal() as db:
            execution = db.query(BotExecution).filter(
                BotExecution.bot_id == bot_id,
                BotExecution.subscription_id == sub_id
            ).first()
            
            assert execution is not None
            assert execution.success is True
            assert execution.input_resource_id == "e2e-patient"
            assert "Hello, EndToEndUser!" in execution.log_output
            
    finally:
        with SessionLocal() as db:
            db.query(BotExecution).filter(BotExecution.bot_id == bot_id).delete()
            db.query(Bot).filter(Bot.id == bot_id).delete()
            db.commit()
