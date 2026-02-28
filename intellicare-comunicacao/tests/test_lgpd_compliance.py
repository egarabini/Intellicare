"""Testes unitários para LGPDComplianceService."""

from __future__ import annotations

import pytest
from datetime import datetime, time, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from comunicacao.lgpd.compliance_service import LGPDComplianceService
from comunicacao.lgpd.config import LGPDConfig
from comunicacao.lgpd.models import (
    CommunicationPreference,
    ConsentStatus,
    LegalBasis,
    QuietHours,
)
from comunicacao.routing.models import (
    CommunicationIntentRecord,
    RecipientType,
)


@pytest.fixture
def lgpd_config():
    """Configuração LGPD para testes."""
    return LGPDConfig(
        critical_override_enabled=True,
        high_alert_override_enabled=True,
        block_without_consent=True,
        default_quiet_hours_start="22:00",
        default_quiet_hours_end="07:00",
        audit_retention_years=5,
        consent_version="1.0",
        consent_renewal_days=365,
        anonymization_hash_salt="test-salt",
    )


@pytest.fixture
def mock_db():
    """Mock de AsyncSession."""
    db = AsyncMock()
    return db


@pytest.fixture
def compliance_service(mock_db, lgpd_config):
    """Instância de LGPDComplianceService para testes."""
    return LGPDComplianceService(mock_db, lgpd_config)


@pytest.fixture
def critical_intent():
    """Intent CRITICAL para testes."""
    return CommunicationIntentRecord(
        source_module="test",
        recipient_type=RecipientType.PATIENT,
        recipient_id="PAT-123",
        severity="CRITICAL",
        category="clinical_alert",
        correlation_id="test-critical",
    )


@pytest.fixture
def high_intent():
    """Intent HIGH para testes."""
    return CommunicationIntentRecord(
        source_module="test",
        recipient_type=RecipientType.PATIENT,
        recipient_id="PAT-123",
        severity="HIGH",
        category="clinical_alert",
        correlation_id="test-high",
    )


@pytest.fixture
def medium_intent():
    """Intent MEDIUM para testes."""
    return CommunicationIntentRecord(
        source_module="test",
        recipient_type=RecipientType.PATIENT,
        recipient_id="PAT-123",
        severity="MEDIUM",
        category="appointment_reminder",
        correlation_id="test-medium",
    )


# ═══════════════════════════════════════════════════════════════════════════
# TESTES: CRITICAL Override
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_critical_always_allowed(compliance_service, critical_intent, mock_db):
    """CRITICAL sempre permitido (Art. 7º, VII + Art. 11, II, f)."""
    # Mock: sem preferências (paciente novo)
    mock_db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
    
    decision = await compliance_service.check_compliance(critical_intent, "rocketchat")
    
    assert decision.allowed is True
    assert decision.override_applied is True
    assert decision.legal_basis == LegalBasis.HEALTH_PROTECTION
    assert "crítico" in decision.reason.lower() or "critical" in decision.reason.lower() or "saúde" in decision.reason.lower()


@pytest.mark.asyncio
async def test_critical_ignores_quiet_hours(compliance_service, critical_intent, mock_db):
    """CRITICAL ignora quiet hours."""
    # Mock: preferências com quiet hours
    pref = CommunicationPreference(
        patient_id="PAT-123",
        rocketchat_enabled=True,
        quiet_hours={"start": "22:00", "end": "07:00"},
        consent_given=True,
        consent_given_at=datetime.now(),
        consent_version="1.0",
    )
    mock_db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=pref)))
    
    # Simular horário dentro de quiet hours (23:00)
    with patch('comunicacao.lgpd.compliance_service.datetime') as mock_datetime:
        mock_datetime.now.return_value = datetime(2026, 2, 18, 23, 0, 0)
        
        decision = await compliance_service.check_compliance(critical_intent, "rocketchat")
    
    assert decision.allowed is True
    assert decision.override_applied is True
    assert decision.deferred_until is None  # Não adia


@pytest.mark.asyncio
async def test_critical_ignores_opt_out(compliance_service, critical_intent, mock_db):
    """CRITICAL ignora opt-out do canal."""
    # Mock: preferências com rocketchat desabilitado
    pref = CommunicationPreference(
        patient_id="PAT-123",
        rocketchat_enabled=False,  # Opt-out
        consent_given=True,
        consent_given_at=datetime.now(),
        consent_version="1.0",
    )
    mock_db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=pref)))
    
    decision = await compliance_service.check_compliance(critical_intent, "rocketchat")
    
    assert decision.allowed is True
    assert decision.override_applied is True


# ═══════════════════════════════════════════════════════════════════════════
# TESTES: HIGH Override
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_high_clinical_alert_allowed(compliance_service, high_intent, mock_db):
    """HIGH clinical_alert permitido (Art. 7º, VII)."""
    # Mock: sem preferências
    mock_db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))

    decision = await compliance_service.check_compliance(high_intent, "rocketchat")

    assert decision.allowed is True
    assert decision.override_applied is True
    assert decision.legal_basis == LegalBasis.VITAL_PROTECTION


@pytest.mark.asyncio
async def test_high_escalation_allowed(compliance_service, mock_db):
    """HIGH escalation permitido."""
    intent = CommunicationIntentRecord(
        source_module="test",
        recipient_type=RecipientType.PATIENT,
        recipient_id="PAT-123",
        severity="HIGH",
        category="escalation",
        correlation_id="test-escalation",
    )
    mock_db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))

    decision = await compliance_service.check_compliance(intent, "rocketchat")

    assert decision.allowed is True
    assert decision.override_applied is True


# ═══════════════════════════════════════════════════════════════════════════
# TESTES: Consentimento
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_medium_requires_consent(compliance_service, medium_intent, mock_db):
    """MEDIUM requer consentimento."""
    # Mock: sem preferências (sem consentimento)
    mock_db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))

    decision = await compliance_service.check_compliance(medium_intent, "rocketchat")

    assert decision.allowed is False
    assert decision.override_applied is False
    assert "consentimento" in decision.reason.lower()


@pytest.mark.asyncio
async def test_medium_with_consent_allowed(compliance_service, medium_intent, mock_db):
    """MEDIUM com consentimento permitido."""
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

    decision = await compliance_service.check_compliance(medium_intent, "rocketchat")

    assert decision.allowed is True
    assert decision.legal_basis == LegalBasis.CONSENT


@pytest.mark.asyncio
async def test_expired_consent_blocked(compliance_service, medium_intent, mock_db):
    """Consentimento expirado bloqueia comunicação."""
    # Mock: preferências com consentimento expirado
    pref = CommunicationPreference(
        patient_id="PAT-123",
        rocketchat_enabled=True,
        consent_given=True,
        consent_given_at=datetime.now() - timedelta(days=400),
        consent_version="1.0",
        consent_expires_at=datetime.now() - timedelta(days=35),  # Expirado há 35 dias
    )
    mock_db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=pref)))

    decision = await compliance_service.check_compliance(medium_intent, "rocketchat")

    assert decision.allowed is False
    assert "expirado" in decision.reason.lower()


# ═══════════════════════════════════════════════════════════════════════════
# TESTES: Quiet Hours
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_quiet_hours_defers_medium(compliance_service, medium_intent, mock_db):
    """Quiet hours adia MEDIUM."""
    # Mock: preferências com quiet hours
    pref = CommunicationPreference(
        patient_id="PAT-123",
        rocketchat_enabled=True,
        quiet_hours={"start": "22:00", "end": "07:00"},
        consent_given=True,
        consent_given_at=datetime.now(),
        consent_version="1.0",
    )
    mock_db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=pref)))

    # Simular horário dentro de quiet hours (23:00)
    with patch('comunicacao.lgpd.compliance_service.datetime') as mock_datetime:
        mock_datetime.now.return_value = datetime(2026, 2, 18, 23, 0, 0)
        mock_datetime.combine = datetime.combine  # preserve real combine

        decision = await compliance_service.check_compliance(medium_intent, "rocketchat")

    assert decision.allowed is False
    assert decision.deferred_until is not None
    assert "quiet hours" in decision.reason.lower()


@pytest.mark.asyncio
async def test_outside_quiet_hours_allowed(compliance_service, medium_intent, mock_db):
    """Fora de quiet hours permite comunicação."""
    # Mock: preferências com quiet hours
    pref = CommunicationPreference(
        patient_id="PAT-123",
        rocketchat_enabled=True,
        quiet_hours={"start": "22:00", "end": "07:00"},
        consent_given=True,
        consent_given_at=datetime.now(),
        consent_version="1.0",
    )
    mock_db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=pref)))

    # Simular horário fora de quiet hours (10:00)
    with patch('comunicacao.lgpd.compliance_service.datetime') as mock_datetime:
        mock_datetime.now.return_value = datetime(2026, 2, 18, 10, 0, 0)

        decision = await compliance_service.check_compliance(medium_intent, "rocketchat")

    assert decision.allowed is True


# ═══════════════════════════════════════════════════════════════════════════
# TESTES: Opt-out de Canal
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_opt_out_channel_blocked(compliance_service, medium_intent, mock_db):
    """Opt-out de canal bloqueia comunicação."""
    # Mock: preferências com rocketchat desabilitado
    pref = CommunicationPreference(
        patient_id="PAT-123",
        rocketchat_enabled=False,  # Opt-out
        consent_given=True,
        consent_given_at=datetime.now(),
        consent_version="1.0",
    )
    mock_db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=pref)))

    decision = await compliance_service.check_compliance(medium_intent, "rocketchat")

    assert decision.allowed is False
    assert any(kw in decision.reason.lower() for kw in ("desabilitado", "opt-out", "optou", "n\xe3o receber"))

