"""API REST do Zilda — dados de saude publica brasileira."""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from zilda.config import ZildaConfig
from zilda.engine.cnes_client import CnesClient
from zilda.engine.territorial import TerritorialEngine

_state: dict[str, Any] = {}


class CnesValidateRequest(BaseModel):
    cnes_code: str


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
    def health() -> dict[str, Any]:
        config: ZildaConfig = _state["config"]
        client: CnesClient = _state["client"]
        try:
            types = client.get_unit_types()
            status = "healthy" if types else "degraded"
        except Exception:
            status = "degraded"
        return {
            "status": status,
            "module_name": config.module_name,
            "version": config.module_version,
        }

    @app.get("/api/v1/info")
    def info() -> dict[str, Any]:
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
    def unit_types() -> list[dict[str, str]]:
        client: CnesClient = _state["client"]
        types = client.get_unit_types()
        return [t.to_dict() for t in types]

    @app.get("/api/v1/establishments")
    def search_establishments(
        state_code: str | None = Query(None, description="Codigo UF (ex: 35 para SP)"),
        city_code: str | None = Query(None, description="Codigo IBGE do municipio"),
        unit_type_code: str | None = Query(None, description="Codigo tipo de unidade"),
        active_only: bool = Query(True, description="Apenas ativos"),
        limit: int = Query(20, ge=1, le=100),
        offset: int = Query(0, ge=0),
    ) -> list[dict[str, Any]]:
        client: CnesClient = _state["client"]
        results = client.search_establishments(
            state_code=state_code,
            city_code=city_code,
            unit_type_code=unit_type_code,
            active_only=active_only,
            limit=limit,
            offset=offset,
        )
        return [e.to_dict() for e in results]

    @app.get("/api/v1/establishment/{cnes_code}")
    def get_establishment(cnes_code: str) -> dict[str, Any]:
        client: CnesClient = _state["client"]
        est = client.get_establishment_by_cnes(cnes_code)
        if not est:
            raise HTTPException(status_code=404, detail=f"CNES {cnes_code} nao encontrado")
        return est.to_dict()

    @app.post("/api/v1/validate")
    def validate_cnes(request: CnesValidateRequest) -> dict[str, Any]:
        client: CnesClient = _state["client"]
        result = client.validate_cnes(request.cnes_code)
        return result.to_dict()

    @app.get("/api/v1/regions")
    def health_regions(
        state_code: str | None = Query(None, description="Codigo UF"),
        limit: int = Query(100, ge=1, le=100),
        offset: int = Query(0, ge=0),
    ) -> list[dict[str, Any]]:
        client: CnesClient = _state["client"]
        regions = client.get_health_regions(
            state_code=state_code,
            limit=limit,
            offset=offset,
        )
        return [r.to_dict() for r in regions]

    @app.get("/api/v1/territorial-summary")
    def territorial_summary(
        state_code: str | None = Query(None, description="Codigo UF"),
        city_code: str | None = Query(None, description="Codigo IBGE do municipio"),
        limit: int = Query(100, ge=1, le=100),
    ) -> dict[str, Any]:
        engine: TerritorialEngine = _state["engine"]
        summary = engine.get_territorial_summary(
            state_code=state_code,
            city_code=city_code,
            limit=limit,
        )
        return summary.to_dict()

    @app.get("/api/v1/region-context/{city_code}")
    def region_context(city_code: str, state_code: str = Query(..., description="Codigo UF")) -> dict[str, Any]:
        engine: TerritorialEngine = _state["engine"]
        return engine.get_region_context(city_code=city_code, state_code=state_code)

    return app
