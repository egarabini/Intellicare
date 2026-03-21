"""DEM-063 — Florence E2E: criação de nota SOAP e sugestão via API."""
from __future__ import annotations

import pytest
import httpx

pytestmark = pytest.mark.e2e


def test_create_and_retrieve_soap_note(api: httpx.Client, clinico_headers: dict):
    """Cria nota SOAP e recupera via encounter_id."""
    encounter_id = "e2e-florence-enc-001"
    patient_id = "e2e-florence-pat-001"

    # Criar nota SOAP
    create_resp = api.post(
        "/florence/notes",
        json={
            "encounter_id": encounter_id,
            "patient_id": patient_id,
            "note_type": "SOAP",
            "soap_s": "Paciente relata cefaleia há 2 dias.",
            "soap_o": "PA 120/80, FC 72.",
            "soap_a": "Cefaleia tensional.",
            "soap_p": "Analgésico + orientações.",
        },
        headers=clinico_headers,
    )
    assert create_resp.status_code == 200, f"Criar nota falhou: {create_resp.text}"
    note = create_resp.json()
    assert note["soap_s"] == "Paciente relata cefaleia há 2 dias."
    assert note["note_type"] == "SOAP"
    note_id = note["id"]

    # Recuperar por encounter
    list_resp = api.get(
        f"/florence/notes/encounter/{encounter_id}",
        headers=clinico_headers,
    )
    assert list_resp.status_code == 200
    notes = list_resp.json()
    assert any(n["id"] == note_id for n in notes), "Nota criada não aparece na listagem"


def test_florence_suggest_fills_fields(api: httpx.Client, clinico_headers: dict):
    """POST /florence/notes/suggest retorna os 4 campos SOAP preenchidos."""
    resp = api.post(
        "/florence/notes/suggest",
        json={
            "encounter_id": 999,
            "patient_id": 999,
            "chief_complaint": "Dor abdominal difusa há 1 dia",
        },
        headers=clinico_headers,
    )
    assert resp.status_code == 200, f"Suggest falhou: {resp.text}"
    data = resp.json()
    # Todos os campos devem estar preenchidos (rule-based ou LLM)
    assert data["soap_s"] != ""
    assert data["soap_o"] != ""
    assert data["soap_a"] != ""
    assert data["soap_p"] != ""
    assert data["model"] in ("rule-based", "llm")
    assert data["confidence"] in ("low", "medium", "high")
