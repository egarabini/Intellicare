"""Testes unitários para AuditTrailService."""

from __future__ import annotations

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from comunicacao.audit.audit_service import AuditTrailService
from comunicacao.audit.models import AuditEntry
from comunicacao.lgpd.config import LGPDConfig
from comunicacao.lgpd.models import LegalBasis, LGPDDecision
from comunicacao.routing.models import (
    CommunicationIntentRecord,
    DeliveryResultRecord,
    DeliveryStatus,
    RecipientType,
)


@pytest.fixture
def lgpd_config():
    """Configuração LGPD para testes."""
    return LGPDConfig(
        anonymization_hash_salt="test-salt",
    )


@pytest.fixture
def mock_db():
    """Mock de AsyncSession."""
    db = AsyncMock()
    return db


@pytest.fixture
def audit_service(mock_db, lgpd_config):
    """Instância de AuditTrailService para testes."""
    return AuditTrailService(mock_db, lgpd_config)


@pytest.fixture
def sample_intent():
    """Intent de exemplo para testes."""
    return CommunicationIntentRecord(
        source_module="test",
        recipient_type=RecipientType.PATIENT,
        recipient_id="PAT-123",
        severity="MEDIUM",
        category="appointment_reminder",
        correlation_id="test-audit",
    )


# ═══════════════════════════════════════════════════════════════════════════
# TESTES: Log Communication
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_log_communication_creates_entry(audit_service, sample_intent, mock_db):
    """Logar comunicação cria AuditEntry."""
    # Mock: sem entries anteriores (primeira entry)
    mock_db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    delivery = DeliveryResultRecord(
        intent_id=sample_intent.id,
        channel="rocketchat",
        status=DeliveryStatus.SENT,
    )
    lgpd_decision = LGPDDecision(
        allowed=True,
        legal_basis=LegalBasis.CONSENT,
        reason="Consentimento presente",
        override_applied=False,
    )

    entry = await audit_service.log_communication(
        intent=sample_intent,
        delivery=delivery,
        lgpd_decision=lgpd_decision,
        patient_id="PAT-123",
    )

    assert entry is not None
    assert entry.intent_id == str(sample_intent.id)
    assert entry.delivery_id == str(delivery.id)
    assert entry.channel == "rocketchat"
    assert entry.status == "sent"
    assert entry.legal_basis == LegalBasis.CONSENT.value
    assert entry.entry_hash is not None
    mock_db.add.assert_called_once()


@pytest.mark.asyncio
async def test_log_communication_chains_hash(audit_service, sample_intent, mock_db):
    """Logar comunicação encadeia hash com entry anterior."""
    # Mock: entry anterior existe — _get_last_hash retorna "previous-hash-123"
    mock_db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value="previous-hash-123")))
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    delivery = DeliveryResultRecord(
        intent_id=sample_intent.id,
        channel="rocketchat",
        status=DeliveryStatus.SENT,
    )
    lgpd_decision = LGPDDecision(
        allowed=True,
        legal_basis=LegalBasis.CONSENT,
        reason="Consentimento presente",
        override_applied=False,
    )

    entry = await audit_service.log_communication(
        intent=sample_intent,
        delivery=delivery,
        lgpd_decision=lgpd_decision,
        patient_id="PAT-123",
    )

    assert entry.previous_hash == "previous-hash-123"


@pytest.mark.asyncio
async def test_log_communication_pseudonymizes_ids(audit_service, sample_intent, mock_db):
    """Logar comunicação pseudonimiza IDs."""
    # Mock: sem entries anteriores
    mock_db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    delivery = DeliveryResultRecord(
        intent_id=sample_intent.id,
        channel="rocketchat",
        status=DeliveryStatus.SENT,
    )
    lgpd_decision = LGPDDecision(
        allowed=True,
        legal_basis=LegalBasis.CONSENT,
        reason="Consentimento presente",
        override_applied=False,
    )

    entry = await audit_service.log_communication(
        intent=sample_intent,
        delivery=delivery,
        lgpd_decision=lgpd_decision,
        patient_id="PAT-123",
    )

    # Verifica que IDs foram pseudonimizados (hash)
    assert entry.recipient_hash != "PAT-123"
    assert entry.patient_hash != "PAT-123"
    assert len(entry.recipient_hash) == 64  # SHA-256 = 64 chars hex
    assert len(entry.patient_hash) == 64


# ═══════════════════════════════════════════════════════════════════════════
# TESTES: Log LGPD Decision
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_log_lgpd_decision_blocked(audit_service, sample_intent, mock_db):
    """Logar decisão LGPD bloqueada."""
    from comunicacao.lgpd.models import LGPDDecision
    
    # Mock: sem entries anteriores
    mock_db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    
    decision = LGPDDecision(
        allowed=False,
        legal_basis=None,
        reason="Paciente não concedeu consentimento",
        override_applied=False,
    )
    
    entry = await audit_service.log_lgpd_decision(
        intent=sample_intent,
        decision=decision,
        patient_id="PAT-123",
    )
    
    assert entry.status == "blocked_lgpd"
    assert entry.lgpd_override is False
    assert "consentimento" in entry.lgpd_reason.lower()


@pytest.mark.asyncio
async def test_log_lgpd_decision_override(audit_service, mock_db):
    """Logar decisão LGPD com override."""
    from comunicacao.lgpd.models import LGPDDecision
    
    # Mock: sem entries anteriores
    mock_db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    
    intent = CommunicationIntentRecord(
        source_module="test",
        recipient_type=RecipientType.PATIENT,
        recipient_id="PAT-123",
        severity="CRITICAL",
        category="clinical_alert",
        correlation_id="test-critical",
    )
    
    decision = LGPDDecision(
        allowed=True,
        legal_basis=LegalBasis.VITAL_PROTECTION,
        reason="Alerta crítico - proteção da vida",
        override_applied=True,
    )
    
    entry = await audit_service.log_lgpd_decision(
        intent=intent,
        decision=decision,
        patient_id="PAT-123",
    )
    
    assert entry.status == "deferred"
    assert entry.lgpd_override is True
    assert entry.legal_basis == LegalBasis.VITAL_PROTECTION.value

