from __future__ import annotations

from fastapi.testclient import TestClient

from minerva.api.app import create_app


def test_health_endpoint_returns_module_info() -> None:
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    # Supports both HealthCheck (module_name) and fallback (module) formats
    module = payload.get("module_name") or payload.get("module")
    assert module == "intellicare-minerva"


def test_info_endpoint_lists_capabilities() -> None:
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/api/v1/info")

    assert response.status_code == 200
    payload = response.json()
    # Supports both ModuleInfo (capabilities list) and fallback (code_name) formats
    capabilities = payload.get("capabilities", [])
    if not capabilities and "metadata" in payload:
        capabilities = payload.get("capabilities", [])
    assert "document_ocr" in capabilities


def test_mcp_tools_endpoint_lists_six_tools() -> None:
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/mcp/tools")

    assert response.status_code == 200
    tools = response.json()["tools"]
    assert len(tools) == 6
    names = {tool["name"] for tool in tools}
    assert "extract_document" in names
    assert "index_document" in names


def test_mcp_tool_execute_success_and_error() -> None:
    import base64

    app = create_app()
    with TestClient(app) as client:
        text_b64 = base64.b64encode("exame: creatinina 2.1".encode("utf-8")).decode("utf-8")
        ok = client.post(
            "/mcp/tools/extract_document",
            json={"arguments": {"file_type": "txt", "file_content_base64": text_b64}},
        )
        bad = client.post("/mcp/tools/tool_inexistente", json={"arguments": {}})

    assert ok.status_code == 200
    assert ok.json()["result"]["status"] == "success"
    assert bad.status_code == 400


def test_mcp_tool_ocr_image_and_parse_lab_result() -> None:
    import base64

    app = create_app()
    with TestClient(app) as client:
        image_b64 = base64.b64encode(b"fake-image-bytes").decode("utf-8")
        ocr = client.post("/mcp/tools/ocr_image", json={"arguments": {"image_base64": image_b64, "image_type": "png"}})

        txt_b64 = base64.b64encode("creatinina 2,3 egfr 38".encode("utf-8")).decode("utf-8")
        lab = client.post(
            "/mcp/tools/parse_lab_result",
            json={"arguments": {"file_content_base64": txt_b64, "file_type": "txt"}},
        )

    assert ocr.status_code == 200
    assert "extracted_text" in ocr.json()["result"]["payload"]
    assert lab.status_code == 200
    payload = lab.json()["result"]["payload"]
    assert "lab_results" in payload
    assert payload["lab_results"].get("creatinine") == 2.3


def test_mcp_index_and_search_documents_flow() -> None:
    app = create_app()
    with TestClient(app) as client:
        indexed = client.post(
            "/mcp/tools/index_document",
            json={
                "arguments": {
                    "document_text": "Creatinina 2.1 mg/dL e potassio 5.0",
                    "document_type": "lab_report",
                    "patient_id": "patient-xyz",
                    "metadata": {"source": "Lab A", "date": "2026-02-10"},
                }
            },
        )
        searched = client.post(
            "/mcp/tools/search_documents",
            json={
                "arguments": {
                    "query": "creatinina potassio",
                    "patient_id": "patient-xyz",
                    "document_type": "lab_report",
                    "top_k": 3,
                }
            },
        )

    assert indexed.status_code == 200
    assert indexed.json()["result"]["payload"]["status"] in {"indexed", "deduplicated"}
    assert searched.status_code == 200
    payload = searched.json()["result"]["payload"]
    assert payload["total_found"] >= 1
    assert payload["patient_document_count"] >= 1
    assert any("Creatinina" in item["chunk"] or "creatinina" in item["chunk"].lower() for item in payload["results"])


def test_parse_discharge_summary_extracts_core_fields() -> None:
    import base64

    app = create_app()
    text = (
        "Alta em 2026-02-10 CID N18.3 paciente estavel. "
        "Metformina 500mg 2x ao dia. "
        "Retorno em 2026-03-10."
    )
    txt_b64 = base64.b64encode(text.encode("utf-8")).decode("utf-8")
    with TestClient(app) as client:
        response = client.post(
            "/mcp/tools/parse_discharge_summary",
            json={"arguments": {"file_content_base64": txt_b64, "file_type": "txt", "patient_id": "p1"}},
        )

    assert response.status_code == 200
    payload = response.json()["result"]["payload"]
    assert payload["patient_id"] == "p1"
    assert payload["discharge_date"] == "2026-02-10"
    assert payload["primary_diagnosis"]["cid10"] == "N18.3"


def test_upload_endpoint_uses_extract_document() -> None:
    app = create_app()
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/upload?document_type=generic&patient_id=abc-1",
            files={"file": ("example.txt", b"texto de alta em 2026-02-10", "text/plain")},
        )

    assert response.status_code == 200
    result = response.json()["result"]
    assert result["status"] == "success"
    assert result["tool"] == "extract_document"
    assert "payload" in result


def test_mcp_tool_validation_error_returns_422() -> None:
    app = create_app()
    with TestClient(app) as client:
        response = client.post("/mcp/tools/search_documents", json={"arguments": {"query": "x", "top_k": 99}})
    assert response.status_code == 422


def test_upload_endpoint_rejects_empty_file() -> None:
    app = create_app()
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/upload",
            files={"file": ("empty.txt", b"", "text/plain")},
        )
    assert response.status_code == 422


def test_upload_endpoint_rejects_unsupported_extension() -> None:
    app = create_app()
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/upload",
            files={"file": ("bad.exe", b"123", "application/octet-stream")},
        )
    assert response.status_code == 422


def test_upload_endpoint_rejects_file_too_large() -> None:
    from minerva.api import app as app_module

    app = create_app()
    app_module._state["config"].max_file_size_mb = 1
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/upload",
            files={"file": ("big.txt", b"a" * (2 * 1024 * 1024), "text/plain")},
        )
    assert response.status_code == 413


def test_e2e_upload_parse_index_search_flow() -> None:
    import base64

    app = create_app()
    with TestClient(app) as client:
        uploaded = client.post(
            "/api/v1/upload?document_type=lab_report&patient_id=pipeline-1",
            files={"file": ("lab.txt", b"Creatinina 2,1\nPotassio 5,0", "text/plain")},
        )
        assert uploaded.status_code == 200
        raw_text = uploaded.json()["result"]["payload"]["raw_text"]

        parsed = client.post("/mcp/tools/parse_lab_result", json={"arguments": {"document_text": raw_text}})
        assert parsed.status_code == 200
        labs = parsed.json()["result"]["payload"]["lab_results"]
        assert labs["creatinine"] == 2.1
        assert labs["potassium"] == 5.0

        indexed = client.post(
            "/mcp/tools/index_document",
            json={
                "arguments": {
                    "document_text": raw_text,
                    "document_type": "lab_report",
                    "patient_id": "pipeline-1",
                    "metadata": {"source": "Pipeline Test", "date": "2026-02-17"},
                }
            },
        )
        assert indexed.status_code == 200
        assert indexed.json()["result"]["payload"]["status"] in {"indexed", "deduplicated"}

        searched = client.post(
            "/mcp/tools/search_documents",
            json={
                "arguments": {
                    "query": "creatinina",
                    "patient_id": "pipeline-1",
                    "document_type": "lab_report",
                    "top_k": 3,
                }
            },
        )
        assert searched.status_code == 200
        assert searched.json()["result"]["payload"]["total_found"] >= 1


# ── Analyze endpoint tests ───────────────────────────────────────────


def test_analyze_with_text_extracts_lab_results() -> None:
    """POST /api/v1/analyze com texto bruto extrai resultados laboratoriais."""
    app = create_app()
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/analyze",
            json={
                "patient_id": "patient-123",
                "query": "extrair exames",
                "parameters": {
                    "text": "Hemoglobina: 12.5 g/dL\nCreatinina: 2.3 mg/dL\nGlicose: 95 mg/dL",
                },
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["patient_id"] == "patient-123"
    assert payload["source"] == "minerva"
    assert payload["confidence"] > 0
    results = payload["analysis"]["results"]
    canonical_names = {r["canonical_name"] for r in results}
    assert "hemoglobin" in canonical_names
    assert "creatinine" in canonical_names
    assert "glucose" in canonical_names


def test_analyze_with_critical_values_generates_alerts() -> None:
    """POST /api/v1/analyze com valores críticos gera alerts."""
    app = create_app()
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/analyze",
            json={
                "patient_id": "patient-crit",
                "parameters": {
                    "text": "Hemoglobina: 5.0 g/dL\nPotássio: 7.0 mEq/L",
                },
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert len(payload["alerts"]) >= 1
    alert_exams = {a["exam"] for a in payload["alerts"]}
    assert "hemoglobin" in alert_exams or "potassium" in alert_exams


def test_analyze_without_text_or_file_returns_message() -> None:
    """POST /api/v1/analyze sem texto nem arquivo retorna mensagem."""
    app = create_app()
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/analyze",
            json={"patient_id": "patient-empty", "parameters": {}},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert "message" in payload["analysis"]
    assert payload["confidence"] == 0.0


def test_analyze_with_abnormal_values_generates_recommendations() -> None:
    """POST /api/v1/analyze com valores alterados gera recommendations."""
    app = create_app()
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/analyze",
            json={
                "patient_id": "patient-alto",
                "parameters": {
                    "text": "Colesterol Total: 280 mg/dL\nTriglicerídeos: 250 mg/dL",
                },
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert len(payload["recommendations"]) >= 1
