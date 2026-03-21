"""DEM-063 — Oswaldo E2E: busca CID-10, criação de prescrição e sugestão."""
from __future__ import annotations

import pytest
import httpx

pytestmark = pytest.mark.e2e


def test_cid10_search_returns_results(api: httpx.Client, clinico_headers: dict):
    """GET /oswaldo/cid10/search?q=cefaleia retorna resultados CID-10."""
    resp = api.get(
        "/oswaldo/cid10/search",
        params={"q": "cefaleia"},
        headers=clinico_headers,
    )
    assert resp.status_code == 200, f"CID-10 search falhou: {resp.text}"
    results = resp.json()
    # Deve ter pelo menos 1 resultado (tabela pública cid10 populada)
    assert len(results) >= 1, "Nenhum resultado CID-10 para 'cefaleia'"
    assert "code" in results[0]
    assert "description" in results[0]


def test_create_and_list_prescription(api: httpx.Client, clinico_headers: dict):
    """Cria prescrição e recupera por encounter_id."""
    encounter_id = "e2e-oswaldo-enc-001"
    patient_id = "e2e-oswaldo-pat-001"

    create_resp = api.post(
        "/oswaldo/prescriptions",
        json={
            "encounter_id": encounter_id,
            "patient_id": patient_id,
            "cid10_code": "R51",
            "cid10_desc": "Cefaleia",
            "items": [
                {"drug": "Dipirona 500mg", "posology": "1 comp 6/6h", "duration": "3 dias"},
                {"drug": "Ibuprofeno 400mg", "posology": "1 comp 8/8h"},
            ],
            "notes": "Retorno em 7 dias se persistir.",
        },
        headers=clinico_headers,
    )
    assert create_resp.status_code == 200, f"Criar prescrição falhou: {create_resp.text}"
    rx = create_resp.json()
    assert rx["cid10_code"] == "R51"
    assert len(rx["items"]) == 2
    rx_id = rx["id"]

    # Listar por encounter
    list_resp = api.get(
        f"/oswaldo/prescriptions/encounter/{encounter_id}",
        headers=clinico_headers,
    )
    assert list_resp.status_code == 200
    prescriptions = list_resp.json()
    assert any(p["id"] == rx_id for p in prescriptions), "Prescrição criada não aparece"


def test_oswaldo_suggest_rule_based(api: httpx.Client, clinico_headers: dict):
    """POST /oswaldo/suggest retorna sugestão rule-based com CID-10 e itens."""
    resp = api.post(
        "/oswaldo/suggest",
        json={
            "encounter_id": 999,
            "patient_id": 999,
            "chief_complaint": "Febre persistente há 5 dias",
        },
        headers=clinico_headers,
    )
    assert resp.status_code == 200, f"Suggest falhou: {resp.text}"
    data = resp.json()
    assert data["cid10_code"] != ""
    assert data["model"] in ("rule-based", "llm")
    assert data["confidence"] in ("low", "medium", "high")
