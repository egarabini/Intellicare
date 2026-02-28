"""Testes unitários para PreferencesService."""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from comunicacao.lgpd.preferences_service import PreferencesService
from comunicacao.lgpd.config import LGPDConfig
from comunicacao.lgpd.models import CommunicationPreference, ConsentLogEntry, ConsentStatus


@pytest.fixture
def lgpd_config():
    """Configuração LGPD para testes."""
    return LGPDConfig(
        consent_version="1.0",
        consent_expiration_days=365,
    )


@pytest.fixture
def mock_db():
    """Mock de AsyncSession."""
    db = AsyncMock()
    return db


@pytest.fixture
def preferences_service(mock_db, lgpd_config):
    """Instância de PreferencesService para testes."""
    return PreferencesService(mock_db, lgpd_config)


# ═══════════════════════════════════════════════════════════════════════════
# TESTES: Get Preferences
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_get_preferences_existing(preferences_service, mock_db):
    """Buscar preferências existentes."""
    # Mock: preferências existentes
    pref = CommunicationPreference(
        patient_id="PAT-123",
        rocketchat_enabled=True,
        email_enabled=True,
        consent_given=True,
        consent_given_at=datetime.now(),
        consent_version="1.0",
    )
    mock_db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=pref)))
    
    result = await preferences_service.get_preferences("PAT-123")
    
    assert result is not None
    assert result.patient_id == "PAT-123"
    assert result.rocketchat_enabled is True


@pytest.mark.asyncio
async def test_get_preferences_not_found(preferences_service, mock_db):
    """Buscar preferências inexistentes retorna None."""
    # Mock: sem preferências
    mock_db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
    
    result = await preferences_service.get_preferences("PAT-999")
    
    assert result is None


# ═══════════════════════════════════════════════════════════════════════════
# TESTES: Update Preferences
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_update_preferences_creates_if_not_exists(preferences_service, mock_db):
    """Atualizar preferências cria se não existir."""
    # Mock: sem preferências existentes
    mock_db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    
    updates = {
        "rocketchat_enabled": True,
        "email_enabled": False,
    }
    
    result = await preferences_service.update_preferences("PAT-123", updates)
    
    assert result is not None
    assert result.patient_id == "PAT-123"
    mock_db.add.assert_called_once()


@pytest.mark.asyncio
async def test_update_preferences_updates_existing(preferences_service, mock_db):
    """Atualizar preferências existentes."""
    # Mock: preferências existentes
    pref = CommunicationPreference(
        patient_id="PAT-123",
        rocketchat_enabled=False,
        email_enabled=False,
        consent_given=False,
    )
    mock_db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=pref)))
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    
    updates = {
        "rocketchat_enabled": True,
        "email_enabled": True,
    }
    
    result = await preferences_service.update_preferences("PAT-123", **updates)

    assert result.rocketchat_enabled is True
    assert result.email_enabled is True


# ═══════════════════════════════════════════════════════════════════════════
# TESTES: Opt-in/Opt-out
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_opt_out_channel(preferences_service, mock_db):
    """Opt-out de canal."""
    # Mock: preferências existentes
    pref = CommunicationPreference(
        patient_id="PAT-123",
        rocketchat_enabled=True,
    )
    mock_db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=pref)))
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    
    result = await preferences_service.opt_out_channel("PAT-123", "rocketchat")
    
    assert result.rocketchat_enabled is False


@pytest.mark.asyncio
async def test_opt_in_channel(preferences_service, mock_db):
    """Opt-in de canal."""
    # Mock: preferências existentes
    pref = CommunicationPreference(
        patient_id="PAT-123",
        rocketchat_enabled=False,
    )
    mock_db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=pref)))
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    
    result = await preferences_service.opt_in_channel("PAT-123", "rocketchat")
    
    assert result.rocketchat_enabled is True


# ═══════════════════════════════════════════════════════════════════════════
# TESTES: Consentimento
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_grant_consent(preferences_service, mock_db, lgpd_config):
    """Conceder consentimento."""
    # Mock: preferências existentes
    pref = CommunicationPreference(
        patient_id="PAT-123",
        consent_given=False,
    )
    mock_db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=pref)))
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    
    result = await preferences_service.grant_consent("PAT-123", "1.0")
    
    assert result.consent_given is True
    assert result.consent_version == "1.0"
    assert result.consent_given_at is not None
    assert result.consent_expires_at is not None
    
    # Verifica que ConsentLogEntry foi criado
    mock_db.add.assert_called()


@pytest.mark.asyncio
async def test_withdraw_consent(preferences_service, mock_db):
    """Revogar consentimento."""
    # Mock: preferências com consentimento
    pref = CommunicationPreference(
        patient_id="PAT-123",
        consent_given=True,
        consent_given_at=datetime.now(),
        consent_version="1.0",
    )
    mock_db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=pref)))
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    
    result = await preferences_service.withdraw_consent("PAT-123")
    
    assert result.consent_given is False
    assert result.consent_given_at is None
    assert result.consent_version is None

