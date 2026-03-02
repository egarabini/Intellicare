"""FastAPI application do Grahame."""

from contextlib import asynccontextmanager

import structlog
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from grahame.config import config
from grahame.models.base import Base
from grahame.models import CodeSystemConcept, FHIRResource  # noqa: F401 — registra tabelas no metadata
from grahame.models import Subscription, SubscriptionAudit  # noqa: F401 — registra tabelas no metadata
from grahame.models import Bot, BotSecret, BotExecution  # noqa: F401 — registra tabelas no metadata
from grahame.models import AccessPolicy, TenantMembership  # noqa: F401 — registra tabelas no metadata
from grahame.models import CustomOperation, CustomOperationAudit  # noqa: F401 — registra tabelas no metadata

from .fhir_routes import router as fhir_router
from .routes.fhir_operations import router as operations_router
from .routes.subscription_routes import router as subscription_router
from .routes.bot_routes import router as bot_router
from .routes.access_policy_routes import router as access_policy_router
from .routes.fhir_native_routes import router as fhir_native_router
from .routes.smart_routes import router as smart_router
from .routes.terminology_routes import terminology_router
from .routes.ccda_routes import router as ccda_router
from .routes.hl7v2_routes import router as hl7v2_router, init_hl7v2_publisher
from .routes.hl7v2_admin import router as hl7v2_admin_router
from .routes.hl7v2_audit_routes import router as hl7v2_audit_router
from .routes.ai_routes import router as ai_router
from .routes.custom_operations_routes import (
    admin_custom_ops_router,
    fhir_custom_ops_router,
)
try:
    from .routes.excalidraw_routes import router as excalidraw_router
except ImportError:
    excalidraw_router = APIRouter(tags=["Excalidraw"])

try:
    from .routes.cds_hooks_routes import cds_router
except ImportError:
    cds_router = APIRouter(tags=["CDS Hooks"])

try:
    from .routes.bulk_export_routes import bulk_router
except ImportError:
    bulk_router = APIRouter(tags=["Bulk Export"])

logger = structlog.get_logger(__name__)

# Auth integration (opcional)
try:
    from intellicare_auth.fastapi import configure_auth
    _HAS_AUTH = True
except ImportError:
    _HAS_AUTH = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Multi-tenancy (opcional — não falha se intellicare_core não estiver instalado)
    try:
        from intellicare_core.tenant.startup import init_tenant_resolver
        init_tenant_resolver()
    except ImportError:
        pass

    # ── Startup ────────────────────────────────────────────────────────────
    # Resolve FHIR Storage Base (optional — graceful if not installed)
    _fhir_storage_base = None
    try:
        from intellicare_core.fhir_storage.models import FHIRStorageBase  # noqa: PLC0415
        _fhir_storage_base = FHIRStorageBase
    except ImportError:
        pass

    if config.grahame_database_url:
        engine = create_async_engine(config.grahame_database_url, echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            if _fhir_storage_base:
                await conn.run_sync(_fhir_storage_base.metadata.create_all)
        app.state.session_factory = async_sessionmaker(
            engine, expire_on_commit=False
        )
        logger.info("grahame.db.ready", url=config.grahame_database_url)
    else:
        # Fallback para testes sem DATABASE_URL configurada
        from sqlalchemy.ext.asyncio import create_async_engine as _cae

        _engine = _cae("sqlite+aiosqlite:///:memory:", echo=False)
        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            if _fhir_storage_base:
                await conn.run_sync(_fhir_storage_base.metadata.create_all)
        app.state.session_factory = async_sessionmaker(
            _engine, expire_on_commit=False
        )
        logger.warning("grahame.db.fallback", msg="Using in-memory SQLite")

    # Initialize HL7v2 Event Publisher
    redis_url = config.redis_url or "redis://localhost:6379"
    init_hl7v2_publisher(redis_url)
    logger.info("hl7v2.publisher.initialized", redis_url=redis_url)

    # Initialize Rate Limiter
    try:
        import redis.asyncio as aioredis
        from grahame.services.rate_limiter import RateLimiter

        redis_client = await aioredis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        app.state.rate_limiter = RateLimiter(redis_client)
        logger.info("rate_limiter.initialized", redis_url=redis_url)
    except Exception as e:
        logger.warning("rate_limiter.init_failed", error=str(e))
        app.state.rate_limiter = None

    yield

    # ── Shutdown ───────────────────────────────────────────────────────────
    # Close Redis connection
    if hasattr(app.state, "rate_limiter") and app.state.rate_limiter:
        try:
            await app.state.rate_limiter.redis.close()
            logger.info("rate_limiter.closed")
        except Exception as e:
            logger.warning("rate_limiter.close_failed", error=str(e))

    logger.info("grahame.shutdown")


app = FastAPI(
    title="IntelliCare Grahame",
    description="Agente de Interoperabilidade FHIR R4 — homenagem a Grahame Grieve",
    version=config.module_version,
    lifespan=lifespan,
)

# Prometheus metrics (opcional)
try:
    from intellicare_core.monitoring.metrics import setup_metrics
    setup_metrics(app, module_name="grahame")
except ImportError:
    pass

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# W9-C: On-behalf-of header (delegação)
try:
    from grahame.middleware.on_behalf_of import OnBehalfOfMiddleware
    app.add_middleware(OnBehalfOfMiddleware, enabled=getattr(config, "on_behalf_of_enabled", True))
except ImportError:
    pass

if _HAS_AUTH:
    configure_auth(app, secrets_path="keycloak_client_secrets.json")


# ── Contrato do módulo ─────────────────────────────────────────────────────


@app.get("/api/v1/health", tags=["Sistema"])
async def health():
    return {
        "status": "healthy",
        "module": config.module_name,
        "version": config.module_version,
    }


@app.get("/api/v1/info", tags=["Sistema"])
async def info():
    return {
        "module": config.module_name,
        "version": config.module_version,
        "description": "Agente de Interoperabilidade FHIR R4",
        "fhir_version": "R4",
        "homage": "Grahame Grieve — criador do padrão HL7 FHIR",
        "environment": config.environment,
    }


# ── Rotas FHIR ─────────────────────────────────────────────────────────────

app.include_router(admin_custom_ops_router, prefix="/api/v1")
app.include_router(fhir_router, prefix="/api/v1")
app.include_router(operations_router, prefix="/api/v1")
app.include_router(subscription_router, prefix="/api/v1")
app.include_router(bot_router, prefix="/api/v1")
app.include_router(access_policy_router, prefix="/api/v1")
app.include_router(fhir_native_router, prefix="/api/v1")
app.include_router(smart_router, prefix="/api/v1")
app.include_router(cds_router, prefix="/api/v1")
app.include_router(terminology_router, prefix="/api/v1")
app.include_router(bulk_router, prefix="/api/v1")
app.include_router(ccda_router, prefix="/api/v1")
app.include_router(hl7v2_router, prefix="/api/v1")
app.include_router(hl7v2_admin_router, prefix="/api/v1")
app.include_router(hl7v2_audit_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")
app.include_router(fhir_custom_ops_router, prefix="/api/v1")
app.include_router(excalidraw_router, prefix="/api/v1")
