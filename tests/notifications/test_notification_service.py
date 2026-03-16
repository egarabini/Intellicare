"""Testes unitarios do NotificationService (com mocks de DB e Redis)."""
from __future__ import annotations

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from intellicare_core.contracts.base import TenantContext
from modules.notifications.schemas import (
    NotificationCreate,
    NotificationBroadcast,
    NotificationPreferencesUpdate,
)
from modules.notifications.service import NotificationService

CTX = TenantContext(
    tenant_id="tenant_dev",
    schema="tenant_tenant_dev",
    user_id="user-abc-123",
    roles=["CLINICO"],
    email="clinico@test.dev",
)

FAKE_NOTIFICATION = {
    "id": uuid4(),
    "user_id": "user-abc-123",
    "type": "appointment",
    "priority": "normal",
    "title": "Consulta",
    "body": "Consulta agendada",
    "data": {},
    "read": False,
    "read_at": None,
    "created_at": datetime.now(timezone.utc),
}


def _mock_session_factory(rows=None, scalar=None, rowcount=0):
    """Cria mock do TenantAwareSessionFactory."""
    mock_result = MagicMock()
    mock_result.mappings.return_value.first.return_value = rows[0] if rows else None
    mock_result.mappings.return_value.all.return_value = rows or []
    mock_result.scalar_one.return_value = scalar if scalar is not None else 0
    mock_result.rowcount = rowcount

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.__aenter__ = AsyncMock(return_value=mock_db)
    mock_db.__aexit__ = AsyncMock(return_value=False)

    return mock_db


@pytest.mark.asyncio
@patch("modules.notifications.service.publish_notification", new_callable=AsyncMock)
@patch("modules.notifications.service._factory")
async def test_send_notification(mock_factory, mock_publish):
    mock_db = _mock_session_factory(rows=[FAKE_NOTIFICATION])
    mock_factory.session.return_value = mock_db

    svc = NotificationService()
    result = await svc.send(
        CTX,
        NotificationCreate(
            user_id="user-abc-123",
            type="appointment",
            title="Consulta",
            body="Consulta agendada",
        ),
    )

    assert result["user_id"] == "user-abc-123"
    assert result["type"] == "appointment"
    mock_publish.assert_called_once()


@pytest.mark.asyncio
@patch("modules.notifications.service.publish_broadcast", new_callable=AsyncMock)
async def test_broadcast_notification(mock_publish):
    svc = NotificationService()
    result = await svc.broadcast(
        CTX,
        NotificationBroadcast(
            type="system",
            title="Manutencao",
            body="Sistema em manutencao",
        ),
    )

    assert result["type"] == "system"
    assert result["title"] == "Manutencao"
    mock_publish.assert_called_once()


@pytest.mark.asyncio
@patch("modules.notifications.service._factory")
async def test_list_for_user(mock_factory):
    mock_db = _mock_session_factory(rows=[FAKE_NOTIFICATION], scalar=1)
    mock_factory.session.return_value = mock_db

    # Configure execute to return different results for COUNT vs SELECT
    count_result = MagicMock()
    count_result.scalar_one.return_value = 1

    select_result = MagicMock()
    select_result.mappings.return_value.all.return_value = [FAKE_NOTIFICATION]

    mock_db.execute = AsyncMock(side_effect=[count_result, select_result])

    svc = NotificationService()
    items, total = await svc.list_for_user(CTX, page=1, size=20)

    assert total == 1
    assert len(items) == 1
    assert items[0]["user_id"] == "user-abc-123"


@pytest.mark.asyncio
@patch("modules.notifications.service._factory")
async def test_get_by_id(mock_factory):
    mock_db = _mock_session_factory(rows=[FAKE_NOTIFICATION])
    mock_factory.session.return_value = mock_db

    svc = NotificationService()
    result = await svc.get_by_id(CTX, FAKE_NOTIFICATION["id"])

    assert result is not None
    assert result["id"] == FAKE_NOTIFICATION["id"]


@pytest.mark.asyncio
@patch("modules.notifications.service._factory")
async def test_get_by_id_not_found(mock_factory):
    mock_db = _mock_session_factory(rows=[])
    mock_factory.session.return_value = mock_db
    # Override first to return None
    mock_result = MagicMock()
    mock_result.mappings.return_value.first.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)

    svc = NotificationService()
    result = await svc.get_by_id(CTX, uuid4())

    assert result is None


@pytest.mark.asyncio
@patch("modules.notifications.service._factory")
async def test_unread_count(mock_factory):
    mock_db = _mock_session_factory(scalar=5)
    mock_factory.session.return_value = mock_db

    svc = NotificationService()
    count = await svc.unread_count(CTX)

    assert count == 5


@pytest.mark.asyncio
@patch("modules.notifications.service._factory")
async def test_mark_read_found(mock_factory):
    mock_db = _mock_session_factory(rowcount=1)
    mock_factory.session.return_value = mock_db

    svc = NotificationService()
    result = await svc.mark_read(CTX, FAKE_NOTIFICATION["id"])

    assert result is True


@pytest.mark.asyncio
@patch("modules.notifications.service._factory")
async def test_mark_read_not_found(mock_factory):
    mock_db = _mock_session_factory(rowcount=0)
    mock_factory.session.return_value = mock_db

    svc = NotificationService()
    result = await svc.mark_read(CTX, uuid4())

    assert result is False


@pytest.mark.asyncio
@patch("modules.notifications.service._factory")
async def test_mark_all_read(mock_factory):
    mock_db = _mock_session_factory(rowcount=3)
    mock_factory.session.return_value = mock_db

    svc = NotificationService()
    count = await svc.mark_all_read(CTX)

    assert count == 3


@pytest.mark.asyncio
@patch("modules.notifications.service._factory")
async def test_delete_found(mock_factory):
    mock_db = _mock_session_factory(rowcount=1)
    mock_factory.session.return_value = mock_db

    svc = NotificationService()
    result = await svc.delete(CTX, FAKE_NOTIFICATION["id"])

    assert result is True


@pytest.mark.asyncio
@patch("modules.notifications.service._factory")
async def test_delete_not_found(mock_factory):
    mock_db = _mock_session_factory(rowcount=0)
    mock_factory.session.return_value = mock_db

    svc = NotificationService()
    result = await svc.delete(CTX, uuid4())

    assert result is False


@pytest.mark.asyncio
@patch("modules.notifications.service._factory")
async def test_get_preferences_default(mock_factory):
    """Quando usuario nao tem preferencias, retorna defaults."""
    mock_db = _mock_session_factory(rows=[])
    mock_factory.session.return_value = mock_db
    mock_result = MagicMock()
    mock_result.mappings.return_value.first.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)

    svc = NotificationService()
    prefs = await svc.get_preferences(CTX)

    assert prefs.user_id == "user-abc-123"
    assert prefs.enabled is True
    assert len(prefs.types_enabled) == 5


@pytest.mark.asyncio
@patch("modules.notifications.service._factory")
async def test_update_preferences(mock_factory):
    # Mock get_preferences (first call returns None)
    mock_db = _mock_session_factory()
    mock_factory.session.return_value = mock_db

    prefs_result_none = MagicMock()
    prefs_result_none.mappings.return_value.first.return_value = None

    updated_prefs = {
        "user_id": "user-abc-123",
        "enabled": False,
        "types_enabled": ["alert"],
        "priority_min": "high",
        "updated_at": datetime.now(timezone.utc),
    }
    upsert_result = MagicMock()
    upsert_result.mappings.return_value.first.return_value = updated_prefs

    mock_db.execute = AsyncMock(side_effect=[prefs_result_none, upsert_result])

    svc = NotificationService()
    prefs = await svc.update_preferences(
        CTX,
        NotificationPreferencesUpdate(enabled=False, types_enabled=["alert"], priority_min="high"),
    )

    assert prefs.enabled is False
    assert prefs.types_enabled == ["alert"]
    assert prefs.priority_min == "high"
