"""Testes para Sala de Caso Multidisciplinar (EF-COM-021)."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from comunicacao.api.app import _state, create_app
from comunicacao.case_room.models import (
    CaseRoom,
    CaseRoomMember,
    CaseRoomStatus,
)
from comunicacao.case_room.service import CaseRoomService
from comunicacao.case_room.store import CaseRoomStore
from comunicacao.rocketchat.models import RCChannel, RCMessageResponse


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _rc_channel(patient_id: str = "p-001") -> RCChannel:
    return RCChannel(
        id=f"rc-{patient_id}",
        name=f"caso-{patient_id}",
        type="p",
        topic=f"Caso clínico - {patient_id}",
        members_count=0,
    )


def _rc_msg_ok() -> RCMessageResponse:
    return RCMessageResponse(
        message_id="msg-abc",
        channel_id="rc-p-001",
        timestamp="2026-02-18T10:00:00Z",
        success=True,
    )


def _make_service(
    channel_service=None,
    rc_client=None,
    store=None,
    jitsi_url: str = "https://meet.test",
) -> CaseRoomService:
    if channel_service is None:
        channel_service = AsyncMock()
        channel_service.create_case_channel = AsyncMock(return_value=_rc_channel())
        channel_service.add_member = AsyncMock(return_value=True)
        channel_service.archive_channel = AsyncMock(return_value=True)
    if rc_client is None:
        rc_client = AsyncMock()
        rc_client.send_message = AsyncMock(return_value=_rc_msg_ok())
    if store is None:
        store = CaseRoomStore()
    return CaseRoomService(
        channel_service=channel_service,
        rc_client=rc_client,
        store=store,
        jitsi_url=jitsi_url,
    )


# ──────────────────────────────────────────────────────────────────────────────
# CaseRoomStore
# ──────────────────────────────────────────────────────────────────────────────

def test_store_get_unknown_returns_none():
    store = CaseRoomStore()
    assert store.get("unknown") is None


def test_store_save_and_get():
    store = CaseRoomStore()
    room = CaseRoom(patient_id="p-001", rc_channel_id="rc-1", rc_channel_name="caso-p-001")
    store.save(room)
    assert store.get("p-001") is not None
    assert store.get("p-001").rc_channel_name == "caso-p-001"


def test_store_save_updates_updated_at():
    store = CaseRoomStore()
    before = datetime.now(UTC)
    room = CaseRoom(patient_id="p-001", rc_channel_id="rc-1", rc_channel_name="caso-p-001")
    store.save(room)
    assert room.updated_at >= before


def test_store_list_active_excludes_archived():
    store = CaseRoomStore()
    store.save(CaseRoom(patient_id="p-001", rc_channel_id="rc-1", rc_channel_name="c-1", status=CaseRoomStatus.ACTIVE))
    store.save(CaseRoom(patient_id="p-002", rc_channel_id="rc-2", rc_channel_name="c-2", status=CaseRoomStatus.ARCHIVED))
    active = store.list_active()
    assert len(active) == 1
    assert active[0].patient_id == "p-001"


def test_store_delete_existing():
    store = CaseRoomStore()
    store.save(CaseRoom(patient_id="p-001", rc_channel_id="rc-1", rc_channel_name="c-1"))
    assert store.delete("p-001") is True
    assert store.get("p-001") is None


def test_store_delete_nonexistent():
    assert CaseRoomStore().delete("nonexistent") is False


def test_store_count():
    store = CaseRoomStore()
    assert store.count() == 0
    store.save(CaseRoom(patient_id="p-001", rc_channel_id="rc-1", rc_channel_name="c-1"))
    store.save(CaseRoom(patient_id="p-002", rc_channel_id="rc-2", rc_channel_name="c-2"))
    assert store.count() == 2


# ──────────────────────────────────────────────────────────────────────────────
# CaseRoomService
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_or_get_creates_new_room():
    service = _make_service()
    room = await service.create_or_get(patient_id="p-001", patient_name="Maria")
    assert room.patient_id == "p-001"
    assert room.patient_name == "Maria"
    assert room.rc_channel_id == "rc-p-001"
    assert room.status == CaseRoomStatus.ACTIVE
    service.channel_service.create_case_channel.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_or_get_returns_existing_without_rc_call():
    store = CaseRoomStore()
    store.save(CaseRoom(patient_id="p-001", rc_channel_id="rc-existing", rc_channel_name="caso-p-001"))
    service = _make_service(store=store)
    room = await service.create_or_get(patient_id="p-001")
    assert room.rc_channel_id == "rc-existing"
    service.channel_service.create_case_channel.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_or_get_passes_members_to_rc():
    service = _make_service()
    members = [
        CaseRoomMember(professional_id="doc-1", username="dr.joao", role="doctor"),
        CaseRoomMember(professional_id="nurse-1", username="enf.ana", role="nurse"),
    ]
    room = await service.create_or_get(patient_id="p-001", members=members)
    assert len(room.members) == 2
    service.channel_service.create_case_channel.assert_awaited_once_with(
        patient_id="p-001",
        patient_name=None,
        members=["dr.joao", "enf.ana"],
    )


@pytest.mark.asyncio
async def test_create_or_get_with_initial_summary_posts_to_rc():
    rc_client = AsyncMock()
    rc_client.send_message = AsyncMock(return_value=_rc_msg_ok())
    service = _make_service(rc_client=rc_client)
    await service.create_or_get(patient_id="p-001", initial_summary="DM2, HbA1c 9.2%")
    rc_client.send_message.assert_awaited_once()
    text_sent = rc_client.send_message.call_args.kwargs["text"]
    assert "DM2, HbA1c 9.2%" in text_sent


@pytest.mark.asyncio
async def test_add_member_success():
    store = CaseRoomStore()
    store.save(CaseRoom(patient_id="p-001", rc_channel_id="rc-001", rc_channel_name="caso-p-001"))
    service = _make_service(store=store)
    ok = await service.add_member("p-001", "doc-1", "dr.joao", "doctor")
    assert ok is True
    room = store.get("p-001")
    assert len(room.members) == 1
    assert room.members[0].username == "dr.joao"
    assert room.members[0].role == "doctor"


@pytest.mark.asyncio
async def test_add_member_room_not_found():
    service = _make_service()
    ok = await service.add_member("nonexistent", "doc-1", "dr.joao")
    assert ok is False


@pytest.mark.asyncio
async def test_add_member_already_member_is_idempotent():
    store = CaseRoomStore()
    room = CaseRoom(
        patient_id="p-001",
        rc_channel_id="rc-001",
        rc_channel_name="caso-p-001",
        members=[CaseRoomMember(professional_id="doc-1", username="dr.joao")],
    )
    store.save(room)
    service = _make_service(store=store)
    ok = await service.add_member("p-001", "doc-1", "dr.joao")
    assert ok is True
    service.channel_service.add_member.assert_not_awaited()


@pytest.mark.asyncio
async def test_post_summary_success():
    store = CaseRoomStore()
    store.save(CaseRoom(patient_id="p-001", rc_channel_id="rc-001", rc_channel_name="caso-p-001"))
    rc_client = AsyncMock()
    rc_client.send_message = AsyncMock(return_value=_rc_msg_ok())
    service = _make_service(store=store, rc_client=rc_client)
    ok = await service.post_summary("p-001", "HbA1c 9.2%, PA 155/95", "wanda")
    assert ok is True
    rc_client.send_message.assert_awaited_once()
    text = rc_client.send_message.call_args.kwargs["text"]
    assert "HbA1c 9.2%, PA 155/95" in text
    assert store.get("p-001").last_summary_at is not None


@pytest.mark.asyncio
async def test_post_summary_room_not_found():
    service = _make_service()
    ok = await service.post_summary("nonexistent", "resumo qualquer")
    assert ok is False


@pytest.mark.asyncio
async def test_post_alert_critical_uses_red_emoji():
    store = CaseRoomStore()
    store.save(CaseRoom(patient_id="p-001", rc_channel_id="rc-001", rc_channel_name="caso-p-001"))
    rc_client = AsyncMock()
    rc_client.send_message = AsyncMock(return_value=_rc_msg_ok())
    service = _make_service(store=store, rc_client=rc_client)
    ok = await service.post_alert("p-001", "eGFR caiu para 25", severity="critical", source_module="oswaldo")
    assert ok is True
    text = rc_client.send_message.call_args.kwargs["text"]
    assert "CRITICAL" in text
    assert "eGFR caiu para 25" in text
    assert ":red_circle:" in text
    assert store.get("p-001").last_alert_at is not None


@pytest.mark.asyncio
async def test_post_alert_room_not_found():
    service = _make_service()
    ok = await service.post_alert("nonexistent", "alert")
    assert ok is False


@pytest.mark.asyncio
async def test_launch_teleconsult_creates_jitsi_url():
    store = CaseRoomStore()
    room = CaseRoom(
        patient_id="p-001",
        patient_name="Maria",
        rc_channel_id="rc-001",
        rc_channel_name="caso-p-001",
        members=[
            CaseRoomMember(professional_id="doc-1", username="dr.joao"),
            CaseRoomMember(professional_id="nurse-1", username="enf.ana"),
        ],
    )
    store.save(room)
    rc_client = AsyncMock()
    rc_client.send_message = AsyncMock(return_value=_rc_msg_ok())
    service = _make_service(store=store, rc_client=rc_client, jitsi_url="https://meet.test")
    result = await service.launch_teleconsult("p-001", "doc-1", "dr.joao", duration_minutes=45)
    assert result.patient_id == "p-001"
    assert result.jitsi_url.startswith("https://meet.test/intellicare-caso-")
    assert result.notified_members == 2
    assert result.initiated_by == "dr.joao"
    assert result.duration_minutes == 45
    rc_client.send_message.assert_awaited_once()
    text = rc_client.send_message.call_args.kwargs["text"]
    assert "meet.test" in text
    assert "Maria" in text


@pytest.mark.asyncio
async def test_launch_teleconsult_room_not_found_raises():
    service = _make_service()
    with pytest.raises(ValueError, match="Sala de caso não encontrada"):
        await service.launch_teleconsult("nonexistent", "doc-1", "dr.joao")


@pytest.mark.asyncio
async def test_archive_marks_status_archived():
    store = CaseRoomStore()
    store.save(CaseRoom(patient_id="p-001", rc_channel_id="rc-001", rc_channel_name="caso-p-001"))
    service = _make_service(store=store)
    ok = await service.archive("p-001")
    assert ok is True
    assert store.get("p-001").status == CaseRoomStatus.ARCHIVED


@pytest.mark.asyncio
async def test_archive_room_not_found():
    service = _make_service()
    ok = await service.archive("nonexistent")
    assert ok is False


# ──────────────────────────────────────────────────────────────────────────────
# API Routes (TestClient)
# ──────────────────────────────────────────────────────────────────────────────

def _inject_service(store: CaseRoomStore | None = None) -> CaseRoomService:
    svc = _make_service(store=store or CaseRoomStore())
    _state["case_room_service"] = svc
    return svc


def test_api_create_case_room_returns_200():
    app = create_app()
    with TestClient(app) as client:
        _inject_service()
        resp = client.post(
            "/api/v1/case-room/patient-001",
            json={"patient_name": "Maria", "professionals": []},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["patient_id"] == "patient-001"
    assert data["status"] == "active"


def test_api_get_case_room_not_found_returns_404():
    app = create_app()
    with TestClient(app) as client:
        _inject_service()
        resp = client.get("/api/v1/case-room/nonexistent")
    assert resp.status_code == 404


def test_api_get_case_room_found_returns_details():
    store = CaseRoomStore()
    store.save(CaseRoom(patient_id="p-123", rc_channel_id="rc-123", rc_channel_name="caso-p-123"))
    app = create_app()
    with TestClient(app) as client:
        _inject_service(store=store)
        resp = client.get("/api/v1/case-room/p-123")
    assert resp.status_code == 200
    data = resp.json()
    assert data["patient_id"] == "p-123"
    assert data["rc_channel_name"] == "caso-p-123"
    assert "members" in data


def test_api_add_member_success():
    store = CaseRoomStore()
    store.save(CaseRoom(patient_id="p-001", rc_channel_id="rc-001", rc_channel_name="caso-p-001"))
    app = create_app()
    with TestClient(app) as client:
        _inject_service(store=store)
        resp = client.post(
            "/api/v1/case-room/p-001/members",
            json={"professional_id": "doc-1", "username": "dr.joao", "role": "doctor"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["username"] == "dr.joao"


def test_api_add_member_not_found_returns_404():
    app = create_app()
    with TestClient(app) as client:
        _inject_service()
        resp = client.post(
            "/api/v1/case-room/nonexistent/members",
            json={"professional_id": "doc-1", "username": "dr.joao"},
        )
    assert resp.status_code == 404


def test_api_post_summary_success():
    store = CaseRoomStore()
    store.save(CaseRoom(patient_id="p-001", rc_channel_id="rc-001", rc_channel_name="caso-p-001"))
    app = create_app()
    with TestClient(app) as client:
        _inject_service(store=store)
        resp = client.post(
            "/api/v1/case-room/p-001/summary",
            json={"summary": "HbA1c 9.2%", "source_module": "wanda"},
        )
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_api_post_summary_not_found_returns_404():
    app = create_app()
    with TestClient(app) as client:
        _inject_service()
        resp = client.post(
            "/api/v1/case-room/nonexistent/summary",
            json={"summary": "Resumo qualquer"},
        )
    assert resp.status_code == 404


def test_api_post_alert_success():
    store = CaseRoomStore()
    store.save(CaseRoom(patient_id="p-001", rc_channel_id="rc-001", rc_channel_name="caso-p-001"))
    app = create_app()
    with TestClient(app) as client:
        _inject_service(store=store)
        resp = client.post(
            "/api/v1/case-room/p-001/alert",
            json={"alert_text": "eGFR caiu", "severity": "high", "source_module": "oswaldo"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["severity"] == "high"


def test_api_launch_teleconsult_success():
    store = CaseRoomStore()
    store.save(CaseRoom(
        patient_id="p-001",
        patient_name="Maria",
        rc_channel_id="rc-001",
        rc_channel_name="caso-p-001",
        members=[CaseRoomMember(professional_id="doc-1", username="dr.joao")],
    ))
    app = create_app()
    with TestClient(app) as client:
        _inject_service(store=store)
        resp = client.post(
            "/api/v1/case-room/p-001/teleconsult",
            json={"initiator_id": "doc-1", "initiator_username": "dr.joao", "duration_minutes": 30},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["patient_id"] == "p-001"
    assert "intellicare-caso-" in data["jitsi_room_name"]
    assert data["initiated_by"] == "dr.joao"
    assert data["notified_members"] == 1


def test_api_launch_teleconsult_not_found_returns_404():
    app = create_app()
    with TestClient(app) as client:
        _inject_service()
        resp = client.post(
            "/api/v1/case-room/nonexistent/teleconsult",
            json={"initiator_id": "doc-1", "initiator_username": "dr.joao"},
        )
    assert resp.status_code == 404


def test_api_archive_case_room_success():
    store = CaseRoomStore()
    store.save(CaseRoom(patient_id="p-001", rc_channel_id="rc-001", rc_channel_name="caso-p-001"))
    app = create_app()
    with TestClient(app) as client:
        _inject_service(store=store)
        resp = client.delete("/api/v1/case-room/p-001/archive")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["archived"] is True


def test_api_archive_not_found_returns_404():
    app = create_app()
    with TestClient(app) as client:
        _inject_service()
        resp = client.delete("/api/v1/case-room/nonexistent/archive")
    assert resp.status_code == 404


def test_api_service_not_configured_returns_503():
    app = create_app()
    with TestClient(app) as client:
        _state["case_room_service"] = None
        resp = client.post("/api/v1/case-room/p-001", json={"patient_name": "Maria"})
    assert resp.status_code == 503
