"""FastAPI app para intellicare-minerva."""

from __future__ import annotations

from typing import Any

import base64

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from minerva.config import OcrConfig
from minerva.engine.ocr_engine import SuryaOcrEngine
from minerva.engine.vision_engine import Llama4VisionEngine
from minerva.mcp.server import OcrMcpServer
from minerva.storage.chroma_store import build_chroma_store, set_chroma_store
from minerva.utils.file_utils import normalize_file_type


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

    app = FastAPI(title="IntelliCare MINERVA (MINERVA)", version=config.module_version)

    if _HAS_AUTH:
        configure_auth(app, secrets_path="keycloak_client_secrets.json")

    @app.get("/api/v1/health")
    async def health() -> dict[str, Any]:
        cfg: OcrConfig = _state["config"]
        ocr: SuryaOcrEngine = _state["ocr_engine"]
        vision: Llama4VisionEngine = _state["vision_engine"]
        return {
            "status": "healthy",
            "module": cfg.module_name,
            "version": cfg.module_version,
            "engines": {
                "surya": await ocr.is_available(),
                "llama4": await vision.is_available(),
                "llamaparse": bool(cfg.llamaparse_api_key),
            },
            "chromadb": _state.get("chroma_store").__class__.__name__ != "InMemoryChromaStore",
        }

    @app.get("/api/v1/info")
    async def info() -> dict[str, Any]:
        cfg: OcrConfig = _state["config"]
        server: OcrMcpServer = _state["mcp_server"]
        return {
            "agent_name": "MINERVA Forever",
            "code_name": "MINERVA",
            "version": cfg.module_version,
            "port": cfg.module_port,
            "protocol": "MCP + REST",
            "mcp_tools": [tool["name"] for tool in server.list_tools()],
            "capabilities": [
                "document_ocr",
                "lab_extraction",
                "discharge_parsing",
                "document_indexing",
                "semantic_search",
            ],
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
