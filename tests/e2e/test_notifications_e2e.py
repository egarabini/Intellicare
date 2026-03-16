"""E2E — DEM-026: Módulo de Notificações."""
from __future__ import annotations
import httpx
import pytest

pytestmark = pytest.mark.e2e


def test_create_notification(api: httpx.Client, gestor_headers: dict):
    """POST /notifications/ cria notificação e retorna 201."""
    resp = api.post(
        "/notifications/",
        json={
            "title": "Teste E2E",
            "message": "Notificação criada pelo teste E2E",
            "category": "info",
        },
        headers=gestor_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["is_read"] is False
    return data["id"]


def test_list_notifications(api: httpx.Client, gestor_headers: dict):
    """GET /notifications/ retorna lista (200)."""
    resp = api.get("/notifications/?limit=10", headers=gestor_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_mark_notification_read(api: httpx.Client, gestor_headers: dict):
    """Ciclo completo: criar → marcar como lida → confirmar is_read=true."""
    create_resp = api.post(
        "/notifications/",
        json={"title": "Para marcar", "message": "Marcar como lida", "category": "info"},
        headers=gestor_headers,
    )
    assert create_resp.status_code == 201
    notif_id = create_resp.json()["id"]

    read_resp = api.patch(f"/notifications/{notif_id}/read", headers=gestor_headers)
    assert read_resp.status_code == 200
    assert read_resp.json()["is_read"] is True


def test_delete_notification(api: httpx.Client, gestor_headers: dict):
    """Criar e deletar notificação retorna 204."""
    create_resp = api.post(
        "/notifications/",
        json={"title": "Para deletar", "message": "Deletar", "category": "info"},
        headers=gestor_headers,
    )
    assert create_resp.status_code == 201
    notif_id = create_resp.json()["id"]

    del_resp = api.delete(f"/notifications/{notif_id}", headers=gestor_headers)
    assert del_resp.status_code == 204


def test_notifications_stream_header(api: httpx.Client, gestor_headers: dict):
    """GET /notifications/stream retorna Content-Type: text/event-stream."""
    token = gestor_headers["Authorization"].split(" ")[1]
    with api.stream("GET", f"/notifications/stream?token={token}") as resp:
        assert resp.status_code == 200
        content_type = resp.headers.get("content-type", "")
        assert "text/event-stream" in content_type
