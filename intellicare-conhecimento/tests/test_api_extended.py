"""Testes complementares da API REST — cobre gaps de cobertura em endpoints de protocolo,
terminologia e templates (EF paths não cobertos pelos testes originais)."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from conhecimento.api.app import create_app
from conhecimento.api.dependencies import get_protocol_service, get_workflow_service
from conhecimento.services import ProtocolService, WorkflowService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PROTO_PAYLOAD = {
    "metadata": {
        "id": "proto-ext-001",
        "version": "1.0.0",
        "title": "Protocolo Estendido de Teste",
        "specialty": "clinica",
        "condition": "test",
        "status": "draft",
        "author": "AutorTeste",
    },
    "summary": "Resumo do protocolo estendido",
    "sections": [{"title": "Secao 1", "content": "Conteudo de teste padrao", "order": 1}],
    "criteria": [],
    "interventions": [],
}


def _client_with_temp_services() -> tuple[TestClient, Path]:
    """Retorna TestClient com serviços isolados em diretório temporário."""
    tmp = Path(tempfile.mkdtemp())
    data_dir = tmp / "protocolos"
    versions_dir = data_dir / ".versions"
    proto_svc = ProtocolService(data_dir=data_dir, versions_dir=versions_dir)
    wf_svc = WorkflowService(proto_svc)
    app = create_app()
    app.dependency_overrides[get_protocol_service] = lambda: proto_svc
    app.dependency_overrides[get_workflow_service] = lambda: wf_svc
    return TestClient(app), tmp


# ---------------------------------------------------------------------------
# Testes de protocolo — CRUD via API
# ---------------------------------------------------------------------------


def test_get_protocol_not_found() -> None:
    client = TestClient(create_app())
    r = client.get("/api/v1/protocolos/protocolo-xyz-nao-existe")
    assert r.status_code == 404


def test_protocol_create_via_api() -> None:
    client, tmp = _client_with_temp_services()
    try:
        r = client.post("/api/v1/protocolos", json=_PROTO_PAYLOAD)
        assert r.status_code == 200
        assert r.json()["metadata"]["id"] == "proto-ext-001"
        # Confirmar GET por ID
        r2 = client.get("/api/v1/protocolos/proto-ext-001")
        assert r2.status_code == 200
        assert r2.json()["summary"] == "Resumo do protocolo estendido"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_protocol_update_via_api() -> None:
    client, tmp = _client_with_temp_services()
    try:
        client.post("/api/v1/protocolos", json=_PROTO_PAYLOAD)
        updated_payload = dict(_PROTO_PAYLOAD)
        updated_payload["summary"] = "Resumo atualizado v2"
        r = client.put("/api/v1/protocolos/proto-ext-001?author=AutorV2", json=updated_payload)
        assert r.status_code == 200
        assert r.json()["metadata"]["version"] == "1.0.1"
        assert r.json()["summary"] == "Resumo atualizado v2"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_protocol_update_not_found() -> None:
    client, tmp = _client_with_temp_services()
    try:
        r = client.put("/api/v1/protocolos/nao-existe?author=test", json=_PROTO_PAYLOAD)
        assert r.status_code == 404
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------------------
# Testes de protocolo — transições de status
# ---------------------------------------------------------------------------


def test_protocol_transition_via_api() -> None:
    client, tmp = _client_with_temp_services()
    try:
        client.post("/api/v1/protocolos", json=_PROTO_PAYLOAD)
        r = client.post(
            "/api/v1/protocolos/proto-ext-001/transition",
            json={"actor": "Revisor", "target_status": "review", "reason": "Submetido para revisao"},
        )
        assert r.status_code == 200
        assert r.json()["metadata"]["status"] == "review"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_protocol_transition_invalid_via_api() -> None:
    """draft → published é transição inválida (deve passar por review e approval)."""
    client, tmp = _client_with_temp_services()
    try:
        client.post("/api/v1/protocolos", json=_PROTO_PAYLOAD)
        r = client.post(
            "/api/v1/protocolos/proto-ext-001/transition",
            json={"actor": "Admin", "target_status": "published", "reason": "Publicacao direta"},
        )
        assert r.status_code == 400
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_protocol_transition_not_found_via_api() -> None:
    client, tmp = _client_with_temp_services()
    try:
        r = client.post(
            "/api/v1/protocolos/protocolo-inexistente/transition",
            json={"actor": "User", "target_status": "review", "reason": "Test"},
        )
        assert r.status_code == 404
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------------------
# Testes de protocolo — histórico e busca
# ---------------------------------------------------------------------------


def test_protocol_history_via_api() -> None:
    client, tmp = _client_with_temp_services()
    try:
        client.post("/api/v1/protocolos", json=_PROTO_PAYLOAD)
        r = client.get("/api/v1/protocolos/proto-ext-001/history")
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert len(r.json()) >= 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_protocol_search_via_api() -> None:
    client = TestClient(create_app())
    r = client.post("/api/v1/protocolos/search", json={"query": "DRC KDIGO nefrologia", "limit": 5})
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# ---------------------------------------------------------------------------
# Testes de terminologia
# ---------------------------------------------------------------------------


def test_terminology_code_not_found() -> None:
    client = TestClient(create_app())
    r = client.get("/api/v1/terminologias/cid10/CODIGO_INEXISTENTE_XYZ")
    assert r.status_code == 404


def test_terminology_search_via_api() -> None:
    client = TestClient(create_app())
    r = client.post("/api/v1/terminologias/search", json={"query": "renal", "limit": 5})
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_terminology_search_with_system_via_api() -> None:
    client = TestClient(create_app())
    r = client.post("/api/v1/terminologias/search", json={"query": "N18", "system": "cid10", "limit": 3})
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# ---------------------------------------------------------------------------
# Testes de templates de CarePlan
# ---------------------------------------------------------------------------


def test_templates_list_via_api() -> None:
    client = TestClient(create_app())
    r = client.get("/api/v1/templates/careplan")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert len(r.json()) >= 1


def test_template_not_found_via_api() -> None:
    client = TestClient(create_app())
    r = client.get("/api/v1/templates/careplan/condicao_que_nao_existe?stage=StageFake")
    assert r.status_code == 404


def test_careplan_generate_not_found_via_api() -> None:
    client = TestClient(create_app())
    r = client.post(
        "/api/v1/templates/careplan/generate",
        json={"patient_id": "p-nf", "condition": "condicao_inexistente", "stage": "X"},
    )
    assert r.status_code == 404
