from fastapi.testclient import TestClient

from comunicacao.api.app import _state, create_app


def test_health_endpoint_returns_module_metadata() -> None:
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["module_name"] == "intellicare-comunicacao"
    assert "status" in payload


def test_info_endpoint_returns_capabilities() -> None:
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/api/v1/info")

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "intellicare-comunicacao"
    assert "matrix-room-send" in payload["capabilities"]


class _FakeMatrix:
    async def send_text_message(self, room_id: str, message: str) -> dict:
        if room_id == "!fail:matrix.gsi.srv.br":
            return {"ok": False, "error": "send falhou"}
        return {"ok": True, "room_id": room_id, "event_id": "$event123"}

    async def create_room(self, name: str, topic: str | None, is_direct: bool, invite: list[str]) -> dict:
        if name == "erro":
            return {"ok": False, "error": "falha simulada"}
        return {"ok": True, "room_id": "!room123:matrix.gsi.srv.br"}

    async def invite_user_to_room(self, room_id: str, user_id: str) -> dict:
        if user_id == "@fail:matrix.gsi.srv.br":
            return {"ok": False, "error": "invite falhou"}
        return {"ok": True, "room_id": room_id, "user_id": user_id}

    def bot_status(self) -> dict:
        return {"ok": True, "running": False, "mode": "geralda-basic"}

    async def start_bot(self, help_message: str | None = None) -> dict:
        if help_message == "erro":
            return {"ok": False, "error": "falha bot"}
        return {"ok": True, "running": True}

    async def stop_bot(self) -> dict:
        return {"ok": True, "running": False}


class _FakeConsumer:
    def status(self) -> dict:
        return {"ok": True, "running": False, "stream": "intellicare:alert.created"}

    async def start(self) -> dict:
        return {"ok": True, "running": True}

    async def stop(self) -> dict:
        return {"ok": True, "running": False}


class _FakeRepository:
    def __init__(self) -> None:
        self.links: dict[str, str] = {}

    def upsert_link(self, patient_id: str, room_id: str) -> None:
        self.links[patient_id] = room_id

    def get_room_id(self, patient_id: str) -> str | None:
        return self.links.get(patient_id)

    def list_links(self, limit: int, offset: int) -> list[dict[str, str]]:
        items = sorted(self.links.items(), key=lambda x: x[0])
        page = items[offset : offset + limit]
        return [{"patient_id": patient_id, "room_id": room_id} for patient_id, room_id in page]

    def delete_link(self, patient_id: str) -> bool:
        if patient_id not in self.links:
            return False
        del self.links[patient_id]
        return True

    def close(self) -> None:
        return


def test_create_room_endpoint_success() -> None:
    app = create_app()
    with TestClient(app) as client:
        _state["matrix"] = _FakeMatrix()
        _state["consumer"] = _FakeConsumer()
        _state["repository"] = _FakeRepository()
        response = client.post(
            "/api/v1/rooms",
            json={"name": "Sala Clinica", "topic": "Acompanhamento", "is_direct": False, "invite": []},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["room_id"].startswith("!")


def test_create_room_endpoint_failure() -> None:
    app = create_app()
    with TestClient(app) as client:
        _state["matrix"] = _FakeMatrix()
        _state["consumer"] = _FakeConsumer()
        _state["repository"] = _FakeRepository()
        response = client.post("/api/v1/rooms", json={"name": "erro"})

    assert response.status_code == 502
    assert response.json()["detail"] == "falha simulada"


def test_invite_user_endpoint_success() -> None:
    app = create_app()
    with TestClient(app) as client:
        _state["matrix"] = _FakeMatrix()
        _state["consumer"] = _FakeConsumer()
        _state["repository"] = _FakeRepository()
        response = client.post(
            "/api/v1/rooms/!room123:matrix.gsi.srv.br/invite",
            json={"user_id": "@medico:matrix.gsi.srv.br"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["user_id"] == "@medico:matrix.gsi.srv.br"


def test_invite_user_endpoint_failure() -> None:
    app = create_app()
    with TestClient(app) as client:
        _state["matrix"] = _FakeMatrix()
        _state["consumer"] = _FakeConsumer()
        _state["repository"] = _FakeRepository()
        response = client.post(
            "/api/v1/rooms/!room123:matrix.gsi.srv.br/invite",
            json={"user_id": "@fail:matrix.gsi.srv.br"},
        )

    assert response.status_code == 502
    assert response.json()["detail"] == "invite falhou"


def test_bot_status_endpoint() -> None:
    app = create_app()
    with TestClient(app) as client:
        _state["matrix"] = _FakeMatrix()
        _state["consumer"] = _FakeConsumer()
        _state["repository"] = _FakeRepository()
        response = client.get("/api/v1/bot/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "geralda-basic"
    assert payload["running"] is False


def test_bot_start_endpoint_success() -> None:
    app = create_app()
    with TestClient(app) as client:
        _state["matrix"] = _FakeMatrix()
        _state["consumer"] = _FakeConsumer()
        _state["repository"] = _FakeRepository()
        response = client.post("/api/v1/bot/start", json={"help_message": "texto de ajuda"})

    assert response.status_code == 200
    assert response.json()["running"] is True


def test_bot_start_endpoint_failure() -> None:
    app = create_app()
    with TestClient(app) as client:
        _state["matrix"] = _FakeMatrix()
        _state["consumer"] = _FakeConsumer()
        _state["repository"] = _FakeRepository()
        response = client.post("/api/v1/bot/start", json={"help_message": "erro"})

    assert response.status_code == 502
    assert response.json()["detail"] == "falha bot"


def test_bot_stop_endpoint() -> None:
    app = create_app()
    with TestClient(app) as client:
        _state["matrix"] = _FakeMatrix()
        _state["consumer"] = _FakeConsumer()
        _state["repository"] = _FakeRepository()
        response = client.post("/api/v1/bot/stop")

    assert response.status_code == 200
    assert response.json()["running"] is False


def test_patient_room_link_upsert_and_get() -> None:
    app = create_app()
    with TestClient(app) as client:
        _state["matrix"] = _FakeMatrix()
        _state["consumer"] = _FakeConsumer()
        _state["repository"] = _FakeRepository()
        save = client.post(
            "/api/v1/links/patient-room",
            json={"patient_id": "pac-001", "room_id": "!room123:matrix.gsi.srv.br"},
        )
        get = client.get("/api/v1/links/patient-room/pac-001")

    assert save.status_code == 200
    assert get.status_code == 200
    assert get.json()["room_id"] == "!room123:matrix.gsi.srv.br"


def test_patient_room_list_pagination() -> None:
    app = create_app()
    with TestClient(app) as client:
        _state["matrix"] = _FakeMatrix()
        _state["consumer"] = _FakeConsumer()
        _state["repository"] = _FakeRepository()

        client.post(
            "/api/v1/links/patient-room",
            json={"patient_id": "pac-001", "room_id": "!room1:matrix.gsi.srv.br"},
        )
        client.post(
            "/api/v1/links/patient-room",
            json={"patient_id": "pac-002", "room_id": "!room2:matrix.gsi.srv.br"},
        )
        client.post(
            "/api/v1/links/patient-room",
            json={"patient_id": "pac-003", "room_id": "!room3:matrix.gsi.srv.br"},
        )
        response = client.get("/api/v1/links/patient-room?limit=2&offset=1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["count"] == 2
    assert payload["limit"] == 2
    assert payload["offset"] == 1
    assert payload["items"][0]["patient_id"] == "pac-002"
    assert payload["items"][1]["patient_id"] == "pac-003"


def test_patient_room_link_not_found() -> None:
    app = create_app()
    with TestClient(app) as client:
        _state["matrix"] = _FakeMatrix()
        _state["consumer"] = _FakeConsumer()
        _state["repository"] = _FakeRepository()
        response = client.get("/api/v1/links/patient-room/pac-inexistente")

    assert response.status_code == 404


def test_patient_room_link_delete_success() -> None:
    app = create_app()
    with TestClient(app) as client:
        _state["matrix"] = _FakeMatrix()
        _state["consumer"] = _FakeConsumer()
        _state["repository"] = _FakeRepository()
        client.post(
            "/api/v1/links/patient-room",
            json={"patient_id": "pac-del-1", "room_id": "!roomDel:matrix.gsi.srv.br"},
        )
        response = client.delete("/api/v1/links/patient-room/pac-del-1")
        check = client.get("/api/v1/links/patient-room/pac-del-1")

    assert response.status_code == 200
    assert response.json()["deleted"] is True
    assert check.status_code == 404


def test_patient_room_link_delete_not_found() -> None:
    app = create_app()
    with TestClient(app) as client:
        _state["matrix"] = _FakeMatrix()
        _state["consumer"] = _FakeConsumer()
        _state["repository"] = _FakeRepository()
        response = client.delete("/api/v1/links/patient-room/pac-del-x")

    assert response.status_code == 404


def test_route_clinical_alert_with_payload_room_id() -> None:
    app = create_app()
    with TestClient(app) as client:
        _state["matrix"] = _FakeMatrix()
        _state["consumer"] = _FakeConsumer()
        _state["repository"] = _FakeRepository()
        response = client.post(
            "/api/v1/events/clinical-alert",
            json={
                "patient_id": "pac-001",
                "source_module": "intellicare-oswaldo",
                "alert_type": "queda-egfr",
                "severity": "alta",
                "message": "Queda rapida no eGFR",
                "room_id": "!room123:matrix.gsi.srv.br",
                "correlation_id": "corr-123",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["room_id"] == "!room123:matrix.gsi.srv.br"


def test_route_clinical_alert_with_mapped_room() -> None:
    app = create_app()
    with TestClient(app) as client:
        _state["matrix"] = _FakeMatrix()
        _state["consumer"] = _FakeConsumer()
        _state["repository"] = _FakeRepository()
        client.post(
            "/api/v1/links/patient-room",
            json={"patient_id": "pac-002", "room_id": "!roomMapped:matrix.gsi.srv.br"},
        )
        response = client.post(
            "/api/v1/events/clinical-alert",
            json={
                "patient_id": "pac-002",
                "source_module": "intellicare-oswaldo",
                "alert_type": "hiperglicemia",
                "severity": "media",
                "message": "Glicemia acima da faixa alvo",
            },
        )

    assert response.status_code == 200
    assert response.json()["room_id"] == "!roomMapped:matrix.gsi.srv.br"


def test_route_clinical_alert_without_room_fails() -> None:
    app = create_app()
    with TestClient(app) as client:
        _state["matrix"] = _FakeMatrix()
        _state["consumer"] = _FakeConsumer()
        _state["repository"] = _FakeRepository()
        response = client.post(
            "/api/v1/events/clinical-alert",
            json={
                "patient_id": "pac-003",
                "source_module": "intellicare-oswaldo",
                "alert_type": "pressao-elevada",
                "severity": "baixa",
                "message": "PA acima do habitual",
            },
        )

    assert response.status_code == 400


def test_route_clinical_alert_send_failure() -> None:
    app = create_app()
    with TestClient(app) as client:
        _state["matrix"] = _FakeMatrix()
        _state["consumer"] = _FakeConsumer()
        _state["repository"] = _FakeRepository()
        response = client.post(
            "/api/v1/events/clinical-alert",
            json={
                "patient_id": "pac-004",
                "source_module": "intellicare-oswaldo",
                "alert_type": "queda-egfr",
                "severity": "alta",
                "message": "Queda rapida no eGFR",
                "room_id": "!fail:matrix.gsi.srv.br",
            },
        )

    assert response.status_code == 502
    assert response.json()["detail"] == "send falhou"


def test_event_consumer_status_start_stop() -> None:
    app = create_app()
    with TestClient(app) as client:
        _state["matrix"] = _FakeMatrix()
        _state["consumer"] = _FakeConsumer()
        _state["repository"] = _FakeRepository()
        status = client.get("/api/v1/events/consumer/status")
        start = client.post("/api/v1/events/consumer/start")
        stop = client.post("/api/v1/events/consumer/stop")

    assert status.status_code == 200
    assert status.json()["stream"] == "intellicare:alert.created"
    assert start.status_code == 200
    assert start.json()["running"] is True
    assert stop.status_code == 200
    assert stop.json()["running"] is False


def test_event_metrics_get_and_reset() -> None:
    app = create_app()
    with TestClient(app) as client:
        _state["matrix"] = _FakeMatrix()
        _state["consumer"] = _FakeConsumer()
        _state["repository"] = _FakeRepository()
        _state["event_metrics"] = {
            "received": 3,
            "routed_ok": 2,
            "routed_error": 1,
            "last_error": "x",
            "last_event": {"patient_id": "pac-1"},
        }
        metrics = client.get("/api/v1/events/metrics")
        reset = client.post("/api/v1/events/metrics/reset")
        metrics_after = client.get("/api/v1/events/metrics")

    assert metrics.status_code == 200
    assert metrics.json()["received"] == 3
    assert reset.status_code == 200
    assert metrics_after.status_code == 200
    assert metrics_after.json()["received"] == 0
    assert metrics_after.json()["routed_ok"] == 0
