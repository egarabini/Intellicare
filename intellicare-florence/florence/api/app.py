"""Aplicacao FastAPI do Florence."""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, AsyncIterator

from fastapi import FastAPI
from pydantic import BaseModel

from intellicare_core.contracts import HealthCheck, ModuleInfo
from florence.config import FlorenceConfig
from florence.engine.clinical_analyzer import ClinicalAnalyzer
from florence.engine.correlations.detector import CorrelationDetector
from florence.engine.reference_ranges.loader import ReferenceRangeLoader
from florence.engine.trend_detector import TrendDetector
from florence.integrations.knowledge_client import KnowledgeClient

# Estado global
_state: dict[str, Any] = {}
_start_time: float = 0.0


# Request/Response models
class LabResultsRequest(BaseModel):
    """Request para interpretacao de exames."""

    patient_id: str
    results: dict[str, float]
    timestamp: str | None = None


class TrendDataPoint(BaseModel):
    timestamp: str
    value: float


class AnalyzeRequest(BaseModel):
    """Request para analise clinica completa."""

    patient_id: str
    results: dict[str, float]
    historical: dict[str, list[TrendDataPoint]] | None = None
    timestamp: str | None = None


class AnalyzeWithRAGRequest(BaseModel):
    """Request para análise clínica com RAG."""

    patient_id: str
    results: dict[str, float]
    query: str | None = None
    timestamp: str | None = None
    top_k: int = 3


class RAGQueryRequest(BaseModel):
    """Request para query RAG direta."""

    query: str
    top_k: int = 3
    filters: dict[str, Any] | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Inicializa e encerra recursos."""
    global _start_time
    _start_time = time.time()

    config = FlorenceConfig()

    ref_loader = ReferenceRangeLoader(config.reference_ranges_dir)
    ref_loader.load_all()

    corr_detector = CorrelationDetector(config.correlations_dir)
    corr_detector.load_all()

    trend_detector = TrendDetector(min_data_points=config.trend_min_data_points)

    # Inicializar RAG retriever se habilitado
    rag_retriever = None
    if config.enable_rag:
        try:
            from florence.engine.rag.retriever import ProtocolRetriever
            rag_retriever = ProtocolRetriever(
                chroma_persist_dir=config.rag_chroma_dir,
                collection_name="clinical_protocols",
            )
            _state["rag_retriever"] = rag_retriever
        except Exception as e:
            print(f"Warning: Failed to initialize RAG retriever: {e}")
            rag_retriever = None

    analyzer = ClinicalAnalyzer(
        ref_loader,
        corr_detector,
        trend_detector,
        rag_retriever=rag_retriever,
    )
    knowledge_client = None
    if config.enable_knowledge_integration:
        knowledge_client = KnowledgeClient(
            base_url=config.knowledge_base_url,
            timeout_seconds=config.knowledge_timeout_seconds,
        )

    _state["config"] = config
    _state["ref_loader"] = ref_loader
    _state["corr_detector"] = corr_detector
    _state["analyzer"] = analyzer
    _state["knowledge_client"] = knowledge_client

    yield

    _state.clear()


def create_app() -> FastAPI:
    app = FastAPI(
        title="IntelliCare Florence",
        description="Deep Clinical Intelligence Agent",
        version="1.0.0",
        lifespan=lifespan,
    )

    @app.get("/api/v1/health")
    async def health() -> dict[str, Any]:
        config = _state.get("config")
        ref_loader = _state.get("ref_loader")
        uptime = time.time() - _start_time
        status = "healthy" if ref_loader and len(ref_loader) > 0 else "degraded"
        check = HealthCheck(
            status=status,
            module_name=config.module_name if config else "intellicare-florence",
            version=config.module_version if config else "1.0.0",
            uptime_seconds=uptime,
        )
        return check.model_dump()

    @app.get("/api/v1/info")
    async def info() -> dict[str, Any]:
        config = _state.get("config")
        ref_loader = _state.get("ref_loader")
        corr_detector = _state.get("corr_detector")
        module_info = ModuleInfo(
            name=config.module_name if config else "intellicare-florence",
            version=config.module_version if config else "1.0.0",
            capabilities=["lab-interpretation", "trend-detection", "clinical-correlation"],
            description="Deep Clinical Intelligence Agent",
            metadata={
                "labs_available": ref_loader.list_labs() if ref_loader else [],
                "panels_available": ref_loader.list_panels() if ref_loader else [],
                "patterns_available": corr_detector.list_patterns() if corr_detector else [],
            },
        )
        return module_info.model_dump()

    @app.get("/api/v1/panels")
    async def list_panels() -> list[dict[str, Any]]:
        ref_loader: ReferenceRangeLoader = _state["ref_loader"]
        panels = []
        for panel_id in ref_loader.list_panels():
            labs = ref_loader.get_panel(panel_id)
            panels.append({
                "id": panel_id,
                "labs": [{"id": l.lab_id, "name": l.name, "loinc_code": l.loinc_code, "unit": l.unit} for l in labs],
            })
        return panels

    @app.get("/api/v1/labs")
    async def list_labs() -> list[dict[str, Any]]:
        ref_loader: ReferenceRangeLoader = _state["ref_loader"]
        labs = []
        for lab_id in ref_loader.list_labs():
            ref = ref_loader.get(lab_id)
            if ref:
                labs.append({
                    "id": ref.lab_id,
                    "name": ref.name,
                    "loinc_code": ref.loinc_code,
                    "unit": ref.unit,
                    "normal_range": f"{ref.normal_min}-{ref.normal_max}" if ref.normal_min is not None else "N/A",
                })
        return labs

    @app.post("/api/v1/interpret")
    async def interpret_labs(request: LabResultsRequest) -> dict[str, Any]:
        analyzer: ClinicalAnalyzer = _state["analyzer"]
        ts = datetime.fromisoformat(request.timestamp) if request.timestamp else None
        analysis = analyzer.analyze_labs(request.patient_id, request.results, ts)
        return analysis.to_dict()

    @app.post("/api/v1/analyze")
    async def analyze(request: AnalyzeRequest) -> dict[str, Any]:
        analyzer: ClinicalAnalyzer = _state["analyzer"]
        ts = datetime.fromisoformat(request.timestamp) if request.timestamp else None

        if request.historical:
            historical = {}
            for lab_id, points in request.historical.items():
                historical[lab_id] = [
                    (datetime.fromisoformat(p.timestamp), p.value) for p in points
                ]
            analysis = analyzer.analyze_with_trends(
                request.patient_id, request.results, historical, ts
            )
        else:
            analysis = analyzer.analyze_labs(request.patient_id, request.results, ts)

        return analysis.to_dict()

    @app.post("/api/v1/analyze-with-rag")
    async def analyze_with_rag(request: AnalyzeWithRAGRequest) -> dict[str, Any]:
        """Análise clínica com consulta a protocolos via RAG."""
        analyzer: ClinicalAnalyzer = _state["analyzer"]
        ts = datetime.fromisoformat(request.timestamp) if request.timestamp else None

        analysis = analyzer.analyze_with_rag(
            patient_id=request.patient_id,
            lab_results=request.results,
            query=request.query,
            timestamp=ts,
            top_k=request.top_k,
        )

        return analysis.to_dict()

    @app.post("/api/v1/rag/query")
    async def rag_query(request: RAGQueryRequest) -> dict[str, Any]:
        """Query direta ao RAG para buscar protocolos clínicos."""
        rag_retriever = _state.get("rag_retriever")
        knowledge_client: KnowledgeClient | None = _state.get("knowledge_client")
        combined_results: list[dict[str, Any]] = []
        errors: list[str] = []

        if rag_retriever:
            from florence.engine.rag.models import RAGQuery

            rag_query_obj = RAGQuery(
                query=request.query,
                top_k=request.top_k,
                filters=request.filters,
            )

            response = rag_retriever.query(rag_query_obj)
            combined_results.extend(
                [
                    {
                        "protocol_id": r.protocol_id,
                        "title": r.title,
                        "content": r.content,
                        "score": r.score,
                        "metadata": r.metadata,
                    }
                    for r in response.results
                ]
            )
        elif not knowledge_client:
            return {
                "error": "RAG not enabled",
                "message": "RAG retriever is not configured. Set enable_rag=true in config.",
                "query": request.query,
                "results": [],
            }

        if knowledge_client:
            try:
                external_results = await knowledge_client.query_rag(
                    query=request.query,
                    top_k=request.top_k,
                    source="protocol",
                )
                combined_results.extend(
                    [
                        {
                            "protocol_id": item.get("id", "knowledge"),
                            "title": item.get("metadata", {}).get("title", "Knowledge Protocol"),
                            "content": item.get("text", ""),
                            "score": item.get("score", 0.0),
                            "metadata": {
                                **item.get("metadata", {}),
                                "source": item.get("source", "conhecimento"),
                            },
                        }
                        for item in external_results
                    ]
                )
            except Exception as exc:
                errors.append(f"knowledge_integration_error: {exc}")

        response_payload: dict[str, Any] = {
            "query": request.query,
            "results": combined_results[: request.top_k],
            "total_results": len(combined_results[: request.top_k]),
            "execution_time_ms": None if not rag_retriever else response.execution_time_ms,
        }
        if errors:
            response_payload["warnings"] = errors
        return response_payload

    @app.get("/api/v1/rag/protocols")
    async def list_protocols() -> dict[str, Any]:
        """Lista todos os protocolos indexados."""
        rag_retriever = _state.get("rag_retriever")

        if not rag_retriever:
            return {
                "error": "RAG not enabled",
                "protocols": [],
            }

        try:
            # Buscar metadados de todos os protocolos
            collection = rag_retriever.collection
            results = collection.get()

            # Extrair protocolos únicos
            protocols_dict = {}
            if results["metadatas"]:
                for metadata in results["metadatas"]:
                    protocol_id = metadata.get("title", "Unknown")
                    if protocol_id not in protocols_dict:
                        protocols_dict[protocol_id] = {
                            "id": protocol_id,
                            "title": metadata.get("title", "Unknown"),
                            "specialty": metadata.get("specialty", "N/A"),
                            "version": metadata.get("version", "N/A"),
                            "date": metadata.get("date", "N/A"),
                        }

            return {
                "protocols": list(protocols_dict.values()),
                "total": len(protocols_dict),
            }
        except Exception as e:
            return {
                "error": str(e),
                "protocols": [],
            }

    return app
