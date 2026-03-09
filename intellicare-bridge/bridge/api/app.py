"""intellicare-bridge — Adaptadores HIS para FHIR R4.

Status: STUB — estrutura definida, aguardando implementação dos adaptadores.
Porta: 8014

Adaptadores planejados:
  - feegow     (MVP — API REST v1.0, token estático)
  - totvs_rm   (API REST, TOTVS Developers)
  - soul_mv    (Plataforma de Interoperabilidade MV)
  - philips_tasy (SOAP/REST híbrido)
  - pixeon     (barramento local, por demanda)
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from intellicare_core.contracts import HealthCheck, ModuleInfo
from intellicare_core.bridge.registry import HISAdapterRegistry


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Registrar adaptadores aqui quando implementados:
    # from bridge.adapters.feegow import FeegoAdapter
    # HISAdapterRegistry.register(FeegoAdapter())
    yield


app = FastAPI(
    title="intellicare-bridge",
    description="Adaptadores HIS → FHIR R4 (stub)",
    version="0.1.0-stub",
    lifespan=lifespan,
)


@app.get("/api/v1/health")
async def health() -> dict:
    hc = HealthCheck(
        status="healthy",
        module_name="intellicare-bridge",
        version="0.1.0-stub",
        dependencies=[],
    )
    out = hc.model_dump()
    out["details"] = {
        "mode": "stub",
        "adapters_loaded": HISAdapterRegistry.list_available(),
        "adapters_planned": ["feegow", "philips_tasy", "soul_mv", "totvs_rm", "pixeon"],
    }
    return out


@app.get("/api/v1/info")
async def info() -> dict:
    return ModuleInfo(
        name="BRIDGE",
        description="Adaptadores de Interoperabilidade HIS → FHIR R4",
        version="0.1.0-stub",
        capabilities=["his_adapter", "ehr_launch", "fhir_bundle_translation"],
    ).model_dump()


@app.get("/api/v1/bridge/adapters")
async def list_adapters() -> dict:
    """Lista adaptadores HIS registrados e planejados."""
    return {
        "registered": HISAdapterRegistry.list_available(),
        "planned": ["feegow", "philips_tasy", "soul_mv", "totvs_rm", "pixeon"],
    }
