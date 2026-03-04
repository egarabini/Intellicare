"""FastAPI app para intellicare-minerva."""

from __future__ import annotations

import time
from typing import Any

import base64

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from minerva.config import OcrConfig
from minerva.engine.lab_extractor import LabResultExtractor
from minerva.engine.ocr_engine import SuryaOcrEngine
from minerva.engine.vision_engine import Llama4VisionEngine
from minerva.mcp.server import OcrMcpServer
from minerva.storage.chroma_store import build_chroma_store, set_chroma_store
from minerva.utils.file_utils import normalize_file_type

# Contracts IntelliCare Core
try:
    from intellicare_core.contracts.base_agent import (
        AnalysisRequest,
        AnalysisResponse,
    )
    from intellicare_core.contracts.health import DependencyStatus, HealthCheck
    from intellicare_core.contracts.module_info import ModuleInfo

    _HAS_CORE = True
except ImportError:
    _HAS_CORE = False

# Prometheus metrics (opcional)
try:
    from intellicare_core.monitoring import setup_metrics

    _HAS_METRICS = True
except ImportError:
    _HAS_METRICS = False

_state: dict[str, Any] = {}

# Auth integration (opcional)
try:
    from intellicare_auth.fastapi import configure_auth

    _HAS_AUTH = True
except ImportError:
    _HAS_AUTH = False


class ToolExecuteRequest(BaseModel):
    arguments: dict[str, Any] = Field(default_factory=dict)


def create_app() -> FastAPI:
    config = OcrConfig()
    ocr_engine = SuryaOcrEngine()
    vision_engine = Llama4VisionEngine(config=config)
    mcp_server = OcrMcpServer(config=config)
    lab_extractor = LabResultExtractor()
    chroma_store = build_chroma_store(
        host=config.chroma_host,
        port=config.chroma_port,
        collection=config.chroma_collection,
    )
    set_chroma_store(chroma_store)
    _state["config"] = config
    _state["ocr_engine"] = ocr_engine
    _state["mcp_server"] = mcp_server
    _state["chroma_store"] = chroma_store
    _state["vision_engine"] = vision_engine
    _state["lab_extractor"] = lab_extractor
    _state["start_time"] = time.monotonic()

    app = FastAPI(title="IntelliCare MINERVA (MINERVA)", version=config.module_version)

    if _HAS_AUTH:
        configure_auth(app, secrets_path="keycloak_client_secrets.json")

    if _HAS_METRICS:
        setup_metrics(app, module_name="minerva")

    # ── Standard contract endpoints ─────────────────────────────────────

    @app.get("/api/v1/health")
    async def health() -> dict[str, Any]:
        cfg: OcrConfig = _state["config"]
        ocr: SuryaOcrEngine = _state["ocr_engine"]
        vision: Llama4VisionEngine = _state["vision_engine"]
        uptime = time.monotonic() - _state["start_time"]

        deps: list[dict[str, Any]] = []
        surya_ok = await ocr.is_available()
        llama_ok = await vision.is_available()
        llamaparse_ok = bool(cfg.llamaparse_api_key)
        chroma_ok = _state.get("chroma_store").__class__.__name__ != "InMemoryChromaStore"

        deps.append({"name": "surya_ocr", "status": "connected" if surya_ok else "disconnected"})
        deps.append({"name": "llama4_vision", "status": "connected" if llama_ok else "disconnected"})
        deps.append({"name": "llamaparse", "status": "connected" if llamaparse_ok else "disconnected"})
        deps.append({"name": "chromadb", "status": "connected" if chroma_ok else "disconnected"})

        # MINERVA é funcional mesmo sem engines (pode processar texto bruto)
        status = "healthy"

        if _HAS_CORE:
            result = HealthCheck(
                status=status,
                module_name=cfg.module_name,
                version=cfg.module_version,
                uptime_seconds=uptime,
                dependencies=[DependencyStatus(**d) for d in deps],
            )
            return result.model_dump(mode="json")

        return {
            "status": status,
            "module": cfg.module_name,
            "version": cfg.module_version,
            "uptime_seconds": uptime,
            "engines": {
                "surya": surya_ok,
                "llama4": llama_ok,
                "llamaparse": llamaparse_ok,
            },
            "chromadb": chroma_ok,
        }

    @app.get("/api/v1/info")
    async def info() -> dict[str, Any]:
        cfg: OcrConfig = _state["config"]
        server: OcrMcpServer = _state["mcp_server"]
        capabilities = [
            "document_ocr",
            "lab_extraction",
            "discharge_parsing",
            "document_indexing",
            "semantic_search",
        ]

        if _HAS_CORE:
            result = ModuleInfo(
                name=cfg.module_name,
                version=cfg.module_version,
                status="healthy",
                capabilities=capabilities,
                description="MINERVA — Extração inteligente de documentos clínicos (OCR, labs, altas)",
                metadata={
                    "agent_name": "MINERVA Forever",
                    "code_name": "MINERVA",
                    "port": cfg.module_port,
                    "protocol": "MCP + REST",
                    "mcp_tools": [tool["name"] for tool in server.list_tools()],
                },
            )
            return result.model_dump()

        return {
            "agent_name": "MINERVA Forever",
            "code_name": "MINERVA",
            "version": cfg.module_version,
            "port": cfg.module_port,
            "protocol": "MCP + REST",
            "mcp_tools": [tool["name"] for tool in server.list_tools()],
            "capabilities": capabilities,
        }

    @app.post("/api/v1/analyze")
    async def analyze(request: dict[str, Any]) -> dict[str, Any]:
        """Endpoint de análise padrão IntelliCare.

        Aceita AnalysisRequest (patient_id, query, parameters) e retorna
        AnalysisResponse com resultados de extração documental.

        parameters aceitos:
          - text: texto bruto para extração de labs
          - file_content_base64: documento codificado em base64
          - file_type: tipo do arquivo (pdf, png, jpg)
          - document_type: tipo do documento (lab_report, discharge_summary, generic)
        """
        patient_id = request.get("patient_id", "")
        query = request.get("query", "")
        params = request.get("parameters", {})

        text = params.get("text", "")
        file_b64 = params.get("file_content_base64", "")
        file_type = params.get("file_type", "pdf")
        doc_type = params.get("document_type", "lab_report")

        analysis: dict[str, Any] = {}
        recommendations: list[str] = []
        alerts: list[dict[str, Any]] = []
        confidence = 0.0

        try:
            # Caminho 1: texto bruto → extração laboratorial direta
            if text:
                extractor: LabResultExtractor = _state["lab_extractor"]
                report = extractor.extract_detailed(text)
                analysis = report.to_dict()
                confidence = report.confidence

                for r in report.results:
                    if r.is_critical:
                        alerts.append({
                            "type": "critical_lab",
                            "exam": r.canonical_name,
                            "value": r.value,
                            "status": r.status,
                            "message": f"Valor crítico: {r.exam_name} = {r.value} {r.unit}",
                        })
                    elif r.status in ("alto", "baixo"):
                        recommendations.append(
                            f"Atenção: {r.exam_name} = {r.value} {r.unit} ({r.status})"
                        )

            # Caminho 2: documento base64 → OCR + extração via MCP
            elif file_b64:
                server: OcrMcpServer = _state["mcp_server"]
                payload: dict[str, Any] = {
                    "file_content_base64": file_b64,
                    "file_type": file_type,
                    "document_type": doc_type,
                }
                if patient_id:
                    payload["patient_id"] = patient_id

                result = await server.call_tool("extract_document", payload)
                if result.get("status") == "failed":
                    raise ValueError(result.get("error", "extraction failed"))

                analysis = result
                confidence = result.get("confidence", 0.7)

                # Se for lab_report, extrair labs do texto OCR
                extracted_text = result.get("text", "")
                if extracted_text and doc_type == "lab_report":
                    extractor = _state["lab_extractor"]
                    lab_report = extractor.extract_detailed(extracted_text)
                    analysis["lab_results"] = lab_report.to_dict()
                    confidence = max(confidence, lab_report.confidence)

                    for r in lab_report.results:
                        if r.is_critical:
                            alerts.append({
                                "type": "critical_lab",
                                "exam": r.canonical_name,
                                "value": r.value,
                                "status": r.status,
                                "message": f"Valor crítico: {r.exam_name} = {r.value} {r.unit}",
                            })

            else:
                analysis = {"message": "Nenhum texto ou documento fornecido para análise."}
                confidence = 0.0

        except Exception as exc:
            if _HAS_CORE:
                return AnalysisResponse(
                    success=False,
                    patient_id=patient_id,
                    analysis={"error": str(exc)},
                    confidence=0.0,
                    source="minerva",
                ).model_dump()
            return {
                "success": False,
                "patient_id": patient_id,
                "analysis": {"error": str(exc)},
                "recommendations": [],
                "alerts": [],
                "confidence": 0.0,
                "source": "minerva",
            }

        if _HAS_CORE:
            return AnalysisResponse(
                success=True,
                patient_id=patient_id,
                analysis=analysis,
                recommendations=recommendations,
                alerts=alerts,
                confidence=confidence,
                source="minerva",
            ).model_dump()

        return {
            "success": True,
            "patient_id": patient_id,
            "analysis": analysis,
            "recommendations": recommendations,
            "alerts": alerts,
            "confidence": confidence,
            "source": "minerva",
        }

    @app.get("/mcp/tools")
    async def list_mcp_tools() -> dict[str, Any]:
        server: OcrMcpServer = _state["mcp_server"]
        return {"tools": server.list_tools()}

    @app.post("/mcp/tools/{tool_name}")
    async def execute_mcp_tool(tool_name: str, payload: ToolExecuteRequest) -> dict[str, Any]:
        server: OcrMcpServer = _state["mcp_server"]
        result = await server.call_tool(tool_name=tool_name, arguments=payload.arguments)
        if result.get("status") == "failed":
            error_type = result.get("error_type")
            if error_type == "unknown_tool":
                raise HTTPException(status_code=400, detail=result.get("error"))
            if error_type == "validation_error":
                raise HTTPException(status_code=422, detail=result.get("error"))
            raise HTTPException(status_code=500, detail=result.get("error"))
        return {"result": result}

    @app.post("/api/v1/upload")
    async def upload_document(
        file: UploadFile = File(...),
        document_type: str = "generic",
        patient_id: str | None = None,
    ) -> dict[str, Any]:
        cfg: OcrConfig = _state["config"]
        server: OcrMcpServer = _state["mcp_server"]
        raw = await file.read()
        if not raw:
            raise HTTPException(status_code=422, detail="arquivo vazio")
        max_size_bytes = cfg.max_file_size_mb * 1024 * 1024
        if len(raw) > max_size_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"arquivo excede limite de {cfg.max_file_size_mb}MB",
            )
        suffix = (file.filename.split(".")[-1] if file.filename and "." in file.filename else "txt").lower()
        try:
            file_type = normalize_file_type(suffix)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        payload = {
            "file_content_base64": base64.b64encode(raw).decode("utf-8"),
            "file_type": file_type,
            "document_type": document_type,
        }
        if patient_id:
            payload["patient_id"] = patient_id
        result = await server.call_tool("extract_document", payload)
        if result.get("status") == "failed":
            error_type = result.get("error_type")
            if error_type == "validation_error":
                raise HTTPException(status_code=422, detail=result.get("error"))
            raise HTTPException(status_code=500, detail=result.get("error"))
        return {"result": result}

    return app


app = create_app()
