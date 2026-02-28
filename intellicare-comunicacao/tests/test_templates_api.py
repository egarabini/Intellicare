from __future__ import annotations

from fastapi.testclient import TestClient

from comunicacao.api.app import _state, create_app
from comunicacao.templates.renderer import TemplateRenderer
from comunicacao.templates.store import InMemoryTemplateStore


def _seed_template_services() -> None:
    _state["template_store"] = InMemoryTemplateStore()
    _state["template_renderer"] = TemplateRenderer()


def _sample_template_payload() -> dict:
    return {
        "id": "clinical_alert_generic",
        "name": "Alerta Clinico",
        "category": "clinical_alert",
        "params_schema": {"required": ["patient_name", "message"]},
        "sample_params": {"patient_name": "Maria", "message": "Queda eGFR"},
        "channel_variants": {
            "matrix": {"format": "plain", "body": "Paciente {{patient_name}}: {{message}}"},
            "email": {"format": "html", "subject": "Alerta {{patient_name}}", "body": "<p>{{message}}</p>"},
        },
    }


def _medication_reminder_payload() -> dict:
    return {
        "id": "medication_reminder",
        "name": "Lembrete de Medicação",
        "category": "medication",
        "params_schema": {"required": ["patient_name", "medication_name", "dosage", "time"]},
        "sample_params": {
            "patient_name": "João Silva",
            "medication_name": "Losartana",
            "dosage": "50mg",
            "time": "08:00",
        },
        "channel_variants": {
            "rocketchat": {
                "format": "markdown",
                "body": "💊 **Lembrete de Medicação**\n\nOlá {{patient_name}}!\n\nHora de tomar: **{{medication_name}} {{dosage}}**\nHorário: {{time}}",
            },
            "sms": {
                "format": "plain",
                "body": "Lembrete: Tomar {{medication_name}} {{dosage}} às {{time}}",
                "max_length": 160,
            },
            "whatsapp": {
                "format": "plain",
                "body": "💊 Olá {{patient_name}}! Lembrete: Tomar {{medication_name}} {{dosage}} às {{time}}",
            },
        },
    }


def test_template_crud_preview_and_validate() -> None:
    app = create_app()
    with TestClient(app) as client:
        _seed_template_services()
        create = client.post("/api/v1/templates", json=_sample_template_payload())
        list_resp = client.get("/api/v1/templates")
        get_resp = client.get("/api/v1/templates/clinical_alert_generic")
        preview = client.post("/api/v1/templates/clinical_alert_generic/preview", json={})
        validate_ok = client.post(
            "/api/v1/templates/clinical_alert_generic/validate",
            json={"params": {"patient_name": "Ana", "message": "Teste"}},
        )
        validate_fail = client.post(
            "/api/v1/templates/clinical_alert_generic/validate",
            json={"params": {"patient_name": "Ana"}},
        )
        delete_resp = client.delete("/api/v1/templates/clinical_alert_generic")

    assert create.status_code == 201
    assert create.json()["id"] == "clinical_alert_generic"
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 1
    assert get_resp.status_code == 200
    assert preview.status_code == 200
    assert "matrix" in preview.json()
    assert validate_ok.status_code == 200
    assert validate_ok.json()["valid"] is True
    assert validate_fail.status_code == 200
    assert validate_fail.json()["valid"] is False
    assert delete_resp.status_code == 200
    assert delete_resp.json()["deactivated"] is True


def test_template_create_with_all_channels() -> None:
    """Testa criação de template com múltiplas variantes de canal."""
    app = create_app()
    with TestClient(app) as client:
        _seed_template_services()
        create = client.post("/api/v1/templates", json=_medication_reminder_payload())
        get_resp = client.get("/api/v1/templates/medication_reminder")

    assert create.status_code == 201
    assert create.json()["id"] == "medication_reminder"
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["category"] == "medication"
    assert "rocketchat" in data["channel_variants"]
    assert "sms" in data["channel_variants"]
    assert "whatsapp" in data["channel_variants"]
    assert data["channel_variants"]["sms"]["max_length"] == 160


def test_template_create_duplicate_returns_409() -> None:
    """Testa que criar template duplicado retorna 409."""
    app = create_app()
    with TestClient(app) as client:
        _seed_template_services()
        first = client.post("/api/v1/templates", json=_sample_template_payload())
        second = client.post("/api/v1/templates", json=_sample_template_payload())

    assert first.status_code == 201
    assert second.status_code == 409


def test_template_get_not_found_returns_404() -> None:
    """Testa que buscar template inexistente retorna 404."""
    app = create_app()
    with TestClient(app) as client:
        _seed_template_services()
        get_resp = client.get("/api/v1/templates/nonexistent_template")

    assert get_resp.status_code == 404


def test_template_update_increments_version() -> None:
    """Testa que atualizar template incrementa a versão."""
    app = create_app()
    with TestClient(app) as client:
        _seed_template_services()
        create = client.post("/api/v1/templates", json=_sample_template_payload())
        original_version = create.json()["version"]

        # Atualizar template
        updated_payload = _sample_template_payload()
        updated_payload["name"] = "Alerta Clinico Atualizado"
        update = client.put("/api/v1/templates/clinical_alert_generic", json=updated_payload)

    assert create.status_code == 201
    assert update.status_code == 200
    assert update.json()["version"] > original_version


def test_template_update_with_mismatched_id_returns_400() -> None:
    """Testa que atualizar com ID diferente retorna 400."""
    app = create_app()
    with TestClient(app) as client:
        _seed_template_services()
        client.post("/api/v1/templates", json=_sample_template_payload())

        # Tentar atualizar com ID diferente
        wrong_payload = _sample_template_payload()
        wrong_payload["id"] = "different_id"
        update = client.put("/api/v1/templates/clinical_alert_generic", json=wrong_payload)

    assert update.status_code == 400


def test_template_preview_with_custom_params() -> None:
    """Testa preview de template com parâmetros customizados."""
    app = create_app()
    with TestClient(app) as client:
        _seed_template_services()
        client.post("/api/v1/templates", json=_medication_reminder_payload())

        preview = client.post(
            "/api/v1/templates/medication_reminder/preview",
            json={
                "params": {
                    "patient_name": "Carlos",
                    "medication_name": "Enalapril",
                    "dosage": "10mg",
                    "time": "20:00",
                }
            },
        )

    assert preview.status_code == 200
    data = preview.json()
    assert "rocketchat" in data
    assert "Carlos" in data["rocketchat"]["body"]
    assert "Enalapril" in data["rocketchat"]["body"]
    assert "10mg" in data["rocketchat"]["body"]


def test_template_preview_single_channel() -> None:
    """Testa preview de template para um canal específico."""
    app = create_app()
    with TestClient(app) as client:
        _seed_template_services()
        client.post("/api/v1/templates", json=_medication_reminder_payload())

        preview = client.post(
            "/api/v1/templates/medication_reminder/preview",
            json={
                "channel": "sms",
                "params": {
                    "patient_name": "Ana",
                    "medication_name": "Losartana",
                    "dosage": "50mg",
                    "time": "08:00",
                },
            },
        )

    assert preview.status_code == 200
    data = preview.json()
    assert "sms" in data
    assert "body" in data["sms"]
    assert "Losartana" in data["sms"]["body"]


def test_template_validate_with_all_required_params() -> None:
    """Testa validação com todos os parâmetros obrigatórios."""
    app = create_app()
    with TestClient(app) as client:
        _seed_template_services()
        client.post("/api/v1/templates", json=_medication_reminder_payload())

        validate = client.post(
            "/api/v1/templates/medication_reminder/validate",
            json={
                "params": {
                    "patient_name": "João",
                    "medication_name": "Losartana",
                    "dosage": "50mg",
                    "time": "08:00",
                }
            },
        )

    assert validate.status_code == 200
    data = validate.json()
    assert data["valid"] is True
    assert len(data["errors"]) == 0


def test_template_validate_with_missing_params() -> None:
    """Testa validação com parâmetros faltando."""
    app = create_app()
    with TestClient(app) as client:
        _seed_template_services()
        client.post("/api/v1/templates", json=_medication_reminder_payload())

        validate = client.post(
            "/api/v1/templates/medication_reminder/validate",
            json={"params": {"patient_name": "João", "medication_name": "Losartana"}},
        )

    assert validate.status_code == 200
    data = validate.json()
    assert data["valid"] is False
    assert len(data["errors"]) > 0
    assert any("dosage" in error for error in data["errors"])
    assert any("time" in error for error in data["errors"])


def test_template_list_returns_all_templates() -> None:
    """Testa que listar retorna todos os templates."""
    app = create_app()
    with TestClient(app) as client:
        _seed_template_services()
        client.post("/api/v1/templates", json=_sample_template_payload())
        client.post("/api/v1/templates", json=_medication_reminder_payload())

        list_resp = client.get("/api/v1/templates")

    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    ids = [item["id"] for item in data["items"]]
    assert "clinical_alert_generic" in ids
    assert "medication_reminder" in ids

