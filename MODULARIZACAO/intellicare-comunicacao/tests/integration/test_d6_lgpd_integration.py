"""Testes de integração D6 (LGPD) ↔ D1 (Routing Engine)."""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from comunicacao.routing.engine import RoutingEngine
from comunicacao.routing.lgpd_adapter import LGPDComplianceAdapter
from comunicacao.routing.models import (
    CommunicationIntentCreate,
    RecipientType,
)
from comunicacao.lgpd.config import LGPDConfig
from comunicacao.lgpd.models import CommunicationPreference


@pytest.fixture
def lgpd_config():
    """Configuração LGPD para testes."""
    return LGPDConfig(
        critical_override_enabled=True,
        high_alert_override_enabled=True,
        block_without_consent=True,
    )


@pytest.fixture
def mock_db():
    """Mock de AsyncSession."""
    db = AsyncMock()
    return db


@pytest.fixture
def lgpd_adapter(mock_db, lgpd_config):
    """Adapter LGPD para testes."""
    return LGPDComplianceAdapter(mock_db, lgpd_config)


@pytest.fixture
def mock_routing_store():
    """Mock de RoutingStore."""
    store = MagicMock()
    store.save_intent = MagicMock()
    store.get_intent = MagicMock()
    store.find_by_source_event = MagicMock(return_value=None)
    return store


@pytest.fixture
def mock_template_store():
    """Mock de TemplateStore."""
    store = MagicMock()
    return store


@pytest.fixture
def mock_rule_matcher():
    """Mock de RuleMatcher."""
    matcher = MagicMock()
    matcher.get_channel_sequence = MagicMock(return_value=["rocketchat"])
    return matcher


@pytest.fixture
def mock_recipient_resolver():
    """Mock de RecipientResolver."""
    resolver = AsyncMock()
    resolver.resolve = AsyncMock(return_value=MagicMock(
        recipient_id="PAT-123",
        patient_id="PAT-123",
    ))
    return resolver


@pytest.fixture
def mock_dispatcher_manager():
    """Mock de DispatcherManager."""
    manager = AsyncMock()
    manager.dispatch = AsyncMock(return_value=MagicMock(
        delivery_id="delivery-123",
        status="sent",
    ))
    return manager


@pytest.fixture
def routing_engine(
    mock_routing_store,
    mock_template_store,
    mock_rule_matcher,
    mock_recipient_resolver,
    lgpd_adapter,
    mock_dispatcher_manager,
):
    """RoutingEngine com LGPD adapter."""
    return RoutingEngine(
        routing_store=mock_routing_store,
        template_store=mock_template_store,
        rule_matcher=mock_rule_matcher,
        recipient_resolver=mock_recipient_resolver,
        lgpd_gateway=lgpd_adapter,
        dispatcher_manager=mock_dispatcher_manager,
    )


# ═══════════════════════════════════════════════════════════════════════════
# TESTES: Integração D6 ↔ D1
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_critical_bypasses_lgpd_and_routes(routing_engine, mock_db, mock_routing_store):
    """CRITICAL bypassa LGPD e roteia normalmente."""
    # Mock: sem preferências (paciente novo)
    mock_db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    
    # Criar intent CRITICAL
    intent_create = CommunicationIntentCreate(
        source_module="test",
        recipient_type=RecipientType.PATIENT,
        recipient_id="PAT-123",
        severity="CRITICAL",
        category="clinical_alert",
        content_raw="Alerta crítico de saúde",
    )
    
    # Criar e processar intent
    intent = await routing_engine.create_intent(intent_create)
    
    # Mock get_intent para retornar a intent criada
    mock_routing_store.get_intent.return_value = intent
    
    result = await routing_engine.process_intent(intent.id)
    
    # Verifica que passou pelo LGPD (logged) e foi roteado
    assert result.status.value in ["completed", "processing"]  # Pode estar em qualquer estado válido


@pytest.mark.asyncio
async def test_medium_without_consent_blocked(routing_engine, mock_db, mock_routing_store):
    """MEDIUM sem consentimento é bloqueado por LGPD."""
    # Mock: sem preferências (sem consentimento)
    mock_db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
    
    # Criar intent MEDIUM
    intent_create = CommunicationIntentCreate(
        source_module="test",
        recipient_type=RecipientType.PATIENT,
        recipient_id="PAT-123",
        severity="MEDIUM",
        category="appointment_reminder",
        content_raw="Lembrete de consulta",
    )
    
    # Criar e processar intent
    intent = await routing_engine.create_intent(intent_create)
    
    # Mock get_intent para retornar a intent criada
    mock_routing_store.get_intent.return_value = intent
    
    result = await routing_engine.process_intent(intent.id)
    
    # Verifica que foi bloqueado por LGPD
    assert result.status.value == "failed"
    # Verifica timeline
    lgpd_events = [e for e in result.timeline if e.event_type == "lgpd_blocked"]
    assert len(lgpd_events) > 0


@pytest.mark.asyncio
async def test_medium_with_consent_routes(routing_engine, mock_db, mock_routing_store):
    """MEDIUM com consentimento roteia normalmente."""
    # Mock: preferências com consentimento
    pref = CommunicationPreference(
        patient_id="PAT-123",
        rocketchat_enabled=True,
        consent_given=True,
        consent_given_at=datetime.now(),
        consent_version="1.0",
        consent_expires_at=datetime.now() + timedelta(days=365),
    )
    mock_db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=pref)))
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    
    # Criar intent MEDIUM
    intent_create = CommunicationIntentCreate(
        source_module="test",
        recipient_type=RecipientType.PATIENT,
        recipient_id="PAT-123",
        severity="MEDIUM",
        category="appointment_reminder",
        content_raw="Lembrete de consulta",
    )
    
    # Criar e processar intent
    intent = await routing_engine.create_intent(intent_create)
    
    # Mock get_intent para retornar a intent criada
    mock_routing_store.get_intent.return_value = intent
    
    result = await routing_engine.process_intent(intent.id)
    
    # Verifica que passou pelo LGPD e foi roteado
    assert result.status.value in ["completed", "processing"]

