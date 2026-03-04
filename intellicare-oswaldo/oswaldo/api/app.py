"""Aplicacao FastAPI do Oswaldo."""

from __future__ import annotations

import asyncio
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator


from fastapi import Depends
from oswaldo.api.auth import get_tenant_context, check_module_active
from fastapi import FastAPI

from intellicare_core.contracts import HealthCheck, ModuleInfo
from oswaldo.config import OswaldoConfig
from oswaldo.datastore.fhir_datastore import FHIRDataStore
from oswaldo.engine.core_logic import ChronicDiseaseEngine
from oswaldo.integrations.knowledge_client import KnowledgeClient
from oswaldo.profiles.registry import DiseaseProfileRegistry

# Estado global da aplicacao
_state: dict[str, Any] = {}
_start_time: float = 0.0


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Inicializa e encerra recursos."""
    global _start_time
    _start_time = time.time()

    config = OswaldoConfig()
    datastore = FHIRDataStore(db_url=config.database_url)

    # Run sync database operations in thread pool to avoid blocking async event loop
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, datastore.ensure_schema)

    registry = DiseaseProfileRegistry(config.profiles_dir)
    registry.load_all()

    engine = ChronicDiseaseEngine(datastore, registry)
    knowledge_client = None
    if config.enable_knowledge_integration:
        knowledge_client = KnowledgeClient(
            base_url=config.knowledge_base_url,
            timeout_seconds=config.knowledge_timeout_seconds,
        )

    _state["config"] = config
    _state["datastore"] = datastore
    _state["registry"] = registry
    _state["engine"] = engine
    _state["knowledge_client"] = knowledge_client

    yield

    _state.clear()


# Auth integration (opcional)
try:
    from intellicare_auth.fastapi import configure_auth
    _HAS_AUTH = True
except ImportError:
    _HAS_AUTH = False


def create_app() -> FastAPI:
    app = FastAPI(
        title="IntelliCare Oswaldo",
        description="Motor generico de doencas cronicas",
        version="1.0.0",
        lifespan=lifespan,
    )

    if _HAS_AUTH:
        configure_auth(app, secrets_path="keycloak_client_secrets.json")

    @app.get("/api/v1/health")
    async def health(ctx: Any = Depends(get_tenant_context), _check: Any = Depends(check_module_active('intellicare-oswaldo'))) -> dict[str, Any]:
        registry = _state.get("registry")
        config = _state.get("config")
        uptime = time.time() - _start_time
        status = "healthy" if registry and len(registry) > 0 else "degraded"
        check = HealthCheck(
            status=status,
            module_name=config.module_name if config else "intellicare-oswaldo",
            version=config.module_version if config else "1.0.0",
            uptime_seconds=uptime,
        )
        return check.model_dump()

    @app.get("/api/v1/info")
    async def info(ctx: Any = Depends(get_tenant_context), _check: Any = Depends(check_module_active('intellicare-oswaldo'))) -> dict[str, Any]:
        registry = _state.get("registry")
        config = _state.get("config")
        diseases = registry.list_ids() if registry else []
        module_info = ModuleInfo(
            name=config.module_name if config else "intellicare-oswaldo",
            version=config.module_version if config else "1.0.0",
            capabilities=["chronic-disease-monitoring", "staging", "alerts"],
            description="Motor generico de doencas cronicas",
            metadata={"diseases": diseases},
        )
        return module_info.model_dump()

    @app.get("/api/v1/diseases")
    async def list_diseases(ctx: Any = Depends(get_tenant_context), _check: Any = Depends(check_module_active('intellicare-oswaldo'))) -> list[dict[str, Any]]:
        registry = _state.get("registry")
        if not registry:
            return []
        return [
            {"id": p.id, "name": p.name, "version": p.version, "snomed_code": p.snomed_code}
            for p in registry.get_all()
        ]

    @app.get("/api/v1/staging/{patient_id}")
    async def get_staging(patient_id: str, disease: str | None = None, ctx: Any = Depends(get_tenant_context), _check: Any = Depends(check_module_active('intellicare-oswaldo'))) -> dict[str, Any]:
        engine: ChronicDiseaseEngine = _state["engine"]
        if disease:
            result = engine.calculate_staging(patient_id, disease, ctx=ctx)
            return result.to_dict()
        # Todas as doencas
        registry = _state["registry"]
        results = {}
        for disease_id in registry.list_ids():
            try:
                results[disease_id] = engine.calculate_staging(patient_id, disease_id, ctx=ctx).to_dict()
            except Exception as e:
                results[disease_id] = {"error": str(e)}
        return {"patient_id": patient_id, "staging": results}

    @app.get("/api/v1/alerts/{patient_id}")
    async def get_alerts(patient_id: str, ctx: Any = Depends(get_tenant_context), _check: Any = Depends(check_module_active('intellicare-oswaldo'))) -> dict[str, Any]:
        engine: ChronicDiseaseEngine = _state["engine"]
        registry = _state["registry"]
        all_alerts = []
        for disease_id in registry.list_ids():
            try:
                staging = engine.calculate_staging(patient_id, disease_id, ctx=ctx)
                trends = engine.calculate_trends(patient_id, disease_id, ctx=ctx)
                alerts = engine.generate_alerts(patient_id, disease_id, staging, trends, ctx=ctx)
                all_alerts.extend([a.to_dict() for a in alerts])
            except Exception:
                pass
        return {"patient_id": patient_id, "alerts": all_alerts, "total": len(all_alerts)}

    @app.post("/api/v1/analyze")
    async def analyze(patient_id: str, diseases: list[str] | None = None, ctx: Any = Depends(get_tenant_context), _check: Any = Depends(check_module_active('intellicare-oswaldo'))) -> dict[str, Any]:
        engine: ChronicDiseaseEngine = _state["engine"]
        knowledge_client: KnowledgeClient | None = _state.get("knowledge_client")
        summary = engine.get_patient_summary(patient_id, diseases, ctx=ctx)
        payload = summary.to_dict()

        if knowledge_client:
            diseases_for_query = diseases or payload.get("diseases", [])
            query = "protocolos clinicos e linhas de cuidado"
            if diseases_for_query:
                query = f"{', '.join(diseases_for_query)} protocolos clinicos e careplan"

            try:
                knowledge_results = await knowledge_client.query_rag(
                    query=query,
                    top_k=5,
                    source="protocol",
                )
                payload.setdefault("metadata", {})
                payload["metadata"]["knowledge_context"] = {
                    "query": query,
                    "results_count": len(knowledge_results),
                    "results": knowledge_results,
                }
            except Exception as exc:
                payload.setdefault("metadata", {})
                payload["metadata"]["knowledge_context"] = {
                    "query": query,
                    "results_count": 0,
                    "warning": f"knowledge_integration_error: {exc}",
                }

        return payload

    return app
