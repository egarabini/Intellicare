"""API REST do Zilda — dados de saude publica brasileira."""

from contextlib import asynccontextmanager
from typing import Any


from fastapi import Depends
from zilda.api.auth import get_tenant_context, check_module_active
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from zilda.config import ZildaConfig
from zilda.engine.cnes_client import CnesClient
from zilda.engine.territorial import TerritorialEngine

_state: dict[str, Any] = {}


class CnesValidateRequest(BaseModel):
    cnes_code: str


class AnalyzeRequest(BaseModel):
    patient_id: str
    query: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)


def _detect_query_type(query: str, parameters: dict[str, Any]) -> str:
    """Resolve query type with explicit parameter taking precedence."""
    explicit = parameters.get("query_type")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip().lower()

    q = query.lower()
    if "cnes" in q or "estabelecimento" in q:
        return "cnes_lookup"
    if "territ" in q or "regiao" in q:
        return "territorial_context"
    return "network_mapping"


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    """Inicializa e finaliza recursos."""
    config = _state.get("config") or ZildaConfig()
    client = _state.get("client") or CnesClient(
        base_url=config.cnes_base_url,
        timeout=config.cnes_timeout,
        cache_ttl_static=config.cache_ttl_static,
        cache_ttl_dynamic=config.cache_ttl_dynamic,
    )
    engine = _state.get("engine") or TerritorialEngine(client)

    _state["config"] = config
    _state["client"] = client
    _state["engine"] = engine
    yield
    client.close()


# Auth integration (opcional)
try:
    from intellicare_auth.fastapi import configure_auth
    _HAS_AUTH = True
except ImportError:
    _HAS_AUTH = False


def create_app() -> FastAPI:
    """Cria a aplicacao FastAPI."""
    app = FastAPI(
        title="IntelliCare Zilda",
        description="Agente de dados de saude publica brasileira",
        version="1.0.0",
        lifespan=lifespan,
    )

    if _HAS_AUTH:
        configure_auth(app, secrets_path="keycloak_client_secrets.json")

    @app.get("/api/v1/health")
    def health(ctx: Any = Depends(get_tenant_context), _check: Any = Depends(check_module_active('intellicare-zilda'))) -> dict[str, Any]:
        config: ZildaConfig = _state["config"]
        client: CnesClient = _state["client"]
        try:
            types = client.get_unit_types(ctx=ctx)
            status = "healthy" if types else "degraded"
        except Exception:
            status = "degraded"
        return {
            "status": status,
            "module_name": config.module_name,
            "version": config.module_version,
        }

    @app.get("/api/v1/info")
    def info(ctx: Any = Depends(get_tenant_context), _check: Any = Depends(check_module_active('intellicare-zilda'))) -> dict[str, Any]:
        config: ZildaConfig = _state["config"]
        return {
            "name": config.module_name,
            "version": config.module_version,
            "description": "Agente de dados de saude publica brasileira (CNES/DATASUS)",
            "capabilities": [
                "cnes-lookup",
                "cnes-validation",
                "territorial-analysis",
                "health-region-context",
            ],
            "metadata": {
                "cnes_base_url": config.cnes_base_url,
                "cache_ttl_static": config.cache_ttl_static,
                "cache_ttl_dynamic": config.cache_ttl_dynamic,
                "datasus_enabled": config.enable_datasus,
                "esus_enabled": config.enable_esus,
            },
        }

    @app.get("/api/v1/unit-types")
    def unit_types(ctx: Any = Depends(get_tenant_context), _check: Any = Depends(check_module_active('intellicare-zilda'))) -> list[dict[str, str]]:
        client: CnesClient = _state["client"]
        types = client.get_unit_types(ctx=ctx)
        return [t.to_dict() for t in types]

    @app.get("/api/v1/establishments")
    def search_establishments(
        state_code: str | None = Query(None, description="Codigo UF (ex: 35 para SP)"),
        city_code: str | None = Query(None, description="Codigo IBGE do municipio"),
        unit_type_code: str | None = Query(None, description="Codigo tipo de unidade"),
        active_only: bool = Query(True, description="Apenas ativos"),
        limit: int = Query(20, ge=1, le=100),
        offset: int = Query(0, ge=0),
        ctx: Any = Depends(get_tenant_context),
        _check: Any = Depends(check_module_active('intellicare-zilda'))
    ) -> list[dict[str, Any]]:
        client: CnesClient = _state["client"]
        results = client.search_establishments(
            state_code=state_code,
            city_code=city_code,
            unit_type_code=unit_type_code,
            active_only=active_only,
            limit=limit,
            offset=offset,
            ctx=ctx,
        )
        return [e.to_dict() for e in results]

    @app.get("/api/v1/establishment/{cnes_code}")
    def get_establishment(cnes_code: str, ctx: Any = Depends(get_tenant_context), _check: Any = Depends(check_module_active('intellicare-zilda'))) -> dict[str, Any]:
        client: CnesClient = _state["client"]
        est = client.get_establishment_by_cnes(cnes_code, ctx=ctx)
        if not est:
            raise HTTPException(status_code=404, detail=f"CNES {cnes_code} nao encontrado")
        return est.to_dict()

    @app.post("/api/v1/validate")
    def validate_cnes(request: CnesValidateRequest, ctx: Any = Depends(get_tenant_context), _check: Any = Depends(check_module_active('intellicare-zilda'))) -> dict[str, Any]:
        client: CnesClient = _state["client"]
        result = client.validate_cnes(request.cnes_code, ctx=ctx)
        return result.to_dict()

    @app.get("/api/v1/regions")
    def health_regions(
        state_code: str | None = Query(None, description="Codigo UF"),
        limit: int = Query(100, ge=1, le=100),
        offset: int = Query(0, ge=0),
        ctx: Any = Depends(get_tenant_context),
        _check: Any = Depends(check_module_active('intellicare-zilda'))
    ) -> list[dict[str, Any]]:
        client: CnesClient = _state["client"]
        regions = client.get_health_regions(
            state_code=state_code,
            limit=limit,
            offset=offset,
            ctx=ctx,
        )
        return [r.to_dict() for r in regions]

    @app.get("/api/v1/territorial-summary")
    def territorial_summary(
        state_code: str | None = Query(None, description="Codigo UF"),
        city_code: str | None = Query(None, description="Codigo IBGE do municipio"),
        limit: int = Query(100, ge=1, le=100),
        ctx: Any = Depends(get_tenant_context),
        _check: Any = Depends(check_module_active('intellicare-zilda'))
    ) -> dict[str, Any]:
        engine: TerritorialEngine = _state["engine"]
        summary = engine.get_territorial_summary(
            state_code=state_code,
            city_code=city_code,
            limit=limit,
            ctx=ctx,
        )
        return summary.to_dict()

    @app.get("/api/v1/region-context/{city_code}")
    def region_context(city_code: str, state_code: str = Query(..., description="Codigo UF"), ctx: Any = Depends(get_tenant_context), _check: Any = Depends(check_module_active("intellicare-zilda"))) -> dict[str, Any]:
        engine: TerritorialEngine = _state["engine"]
        return engine.get_region_context(city_code=city_code, state_code=state_code, ctx=ctx)

    @app.post("/api/v1/analyze")
    async def analyze(request: AnalyzeRequest, ctx: Any = Depends(get_tenant_context), _check: Any = Depends(check_module_active('intellicare-zilda'))) -> dict[str, Any]:
        """Endpoint padrao de analise para orquestracao da Wanda."""
        client: CnesClient = _state["client"]
        engine: TerritorialEngine = _state["engine"]
        parameters = request.parameters or {}
        query_type = _detect_query_type(request.query, parameters)

        try:
            if query_type == "cnes_lookup":
                cnes_code = str(parameters.get("cnes_code", "")).strip()
                if cnes_code:
                    est = client.get_establishment_by_cnes(cnes_code, ctx=ctx)
                    establishments = [est.to_dict()] if est else []
                else:
                    found = client.search_establishments(
                        state_code=parameters.get("state_code"),
                        city_code=parameters.get("city_code"),
                        unit_type_code=parameters.get("unit_type_code"),
                        active_only=True,
                        limit=int(parameters.get("limit", 20)),
                        ctx=ctx,
                    )
                    establishments = [item.to_dict() for item in found]

                analysis = {
                    "query_type": "cnes_lookup",
                    "establishments": establishments,
                    "total": len(establishments),
                }
            elif query_type == "territorial_context":
                state_code = parameters.get("state_code")
                city_code = parameters.get("city_code")
                summary = engine.get_territorial_summary(
                    state_code=state_code,
                    city_code=city_code,
                    limit=int(parameters.get("limit", 100)),
                    ctx=ctx,
                )
                context = None
                if state_code and city_code:
                    context = engine.get_region_context(city_code=city_code, state_code=state_code, ctx=ctx)

                analysis = {
                    "query_type": "territorial_context",
                    "territorial_summary": summary.to_dict(),
                    "region_context": context,
                }
            else:
                nearby = engine.find_nearby_establishments(
                    city_code=str(parameters.get("city_code", "")),
                    unit_type_code=parameters.get("unit_type_code"),
                    limit=int(parameters.get("limit", 20)),
                    ctx=ctx,
                )
                analysis = {
                    "query_type": "network_mapping",
                    "establishments": [item.to_dict() for item in nearby],
                    "total": len(nearby),
                }

            return {
                "success": True,
                "patient_id": request.patient_id,
                "analysis": analysis,
                "recommendations": [],
                "alerts": [],
                "confidence": 0.8,
                "source": "intellicare-zilda",
            }
        except Exception as exc:  # pragma: no cover - protective fallback
            return {
                "success": False,
                "patient_id": request.patient_id,
                "analysis": {"error": str(exc), "query_type": query_type},
                "recommendations": [],
                "alerts": [],
                "confidence": 0.0,
                "source": "intellicare-zilda",
            }

    return app
