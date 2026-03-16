"""Testes unitarios dos schemas de notificacoes."""
from __future__ import annotations

import pytest
from uuid import uuid4

from modules.notifications.schemas import (
    NotificationCreate,
    NotificationBroadcast,
    NotificationListResponse,
    NotificationPreferencesResponse,
    NotificationPreferencesUpdate,
    NotificationResponse,
    UnreadCountResponse,
)


# ── NotificationCreate ───────────────────────────────────────

def test_notification_create_valid():
    n = NotificationCreate(
        user_id="user-123",
        type="appointment",
        priority="high",
        title="Consulta agendada",
        body="Sua consulta foi agendada para 15/03 às 14:00",
        data={"appointment_id": "abc"},
    )
    assert n.user_id == "user-123"
    assert n.type == "appointment"
    assert n.priority == "high"


def test_notification_create_defaults():
    n = NotificationCreate(
        user_id="user-123",
        title="Aviso",
        body="Mensagem de teste",
    )
    assert n.type == "system"
    assert n.priority == "normal"
    assert n.data == {}


def test_notification_create_empty_user_id():
    with pytest.raises(ValueError):
        NotificationCreate(user_id="", title="X", body="Y")


def test_notification_create_empty_title():
    with pytest.raises(ValueError):
        NotificationCreate(user_id="u1", title="", body="Y")


def test_notification_create_empty_body():
    with pytest.raises(ValueError):
        NotificationCreate(user_id="u1", title="X", body="")


def test_notification_create_invalid_type():
    with pytest.raises(ValueError):
        NotificationCreate(user_id="u1", type="invalid", title="X", body="Y")


def test_notification_create_invalid_priority():
    with pytest.raises(ValueError):
        NotificationCreate(user_id="u1", priority="super_high", title="X", body="Y")


def test_notification_create_title_max_length():
    with pytest.raises(ValueError):
        NotificationCreate(user_id="u1", title="X" * 201, body="Y")


def test_notification_create_body_max_length():
    with pytest.raises(ValueError):
        NotificationCreate(user_id="u1", title="X", body="Y" * 2001)


# ── NotificationBroadcast ────────────────────────────────────

def test_broadcast_valid():
    b = NotificationBroadcast(
        type="system",
        priority="urgent",
        title="Manutencao",
        body="Sistema em manutencao",
    )
    assert b.type == "system"
    assert b.priority == "urgent"


def test_broadcast_defaults():
    b = NotificationBroadcast(title="Aviso", body="Msg")
    assert b.type == "system"
    assert b.priority == "normal"


# ── NotificationResponse ─────────────────────────────────────

def test_notification_response_valid():
    from datetime import datetime, timezone

    r = NotificationResponse(
        id=uuid4(),
        user_id="u1",
        type="clinical",
        priority="high",
        title="Resultado",
        body="Exame disponivel",
        data={},
        read=False,
        read_at=None,
        created_at=datetime.now(timezone.utc),
    )
    assert r.read is False
    assert r.read_at is None


# ── NotificationListResponse ─────────────────────────────────

def test_notification_list_response():
    resp = NotificationListResponse(items=[], total=0, page=1, size=20)
    assert resp.total == 0
    assert resp.items == []


# ── UnreadCountResponse ──────────────────────────────────────

def test_unread_count_response():
    r = UnreadCountResponse(count=5)
    assert r.count == 5


# ── NotificationPreferencesResponse ──────────────────────────

def test_preferences_response():
    p = NotificationPreferencesResponse(
        user_id="u1",
        enabled=True,
        types_enabled=["appointment", "clinical"],
        priority_min="normal",
    )
    assert p.enabled is True
    assert len(p.types_enabled) == 2


# ── NotificationPreferencesUpdate ────────────────────────────

def test_preferences_update_partial():
    u = NotificationPreferencesUpdate(enabled=False)
    assert u.enabled is False
    assert u.types_enabled is None
    assert u.priority_min is None


def test_preferences_update_full():
    u = NotificationPreferencesUpdate(
        enabled=True,
        types_enabled=["alert"],
        priority_min="high",
    )
    assert u.types_enabled == ["alert"]
    assert u.priority_min == "high"


def test_preferences_update_invalid_priority_min():
    with pytest.raises(ValueError):
        NotificationPreferencesUpdate(priority_min="critical")
