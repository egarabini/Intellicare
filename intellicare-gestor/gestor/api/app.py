"""FastAPI app — intellicare-gestor (porta 8011)."""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from intellicare_core.tenant import TenantAwareSessionFactory

from gestor.config import config
from gestor.api import user_routes, role_routes, sector_routes, settings_routes, audit_routes, dashboard_routes

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida: inicializa e encerra recursos."""
    # Multi-tenancy
    from intellicare_core.tenant.startup import init_tenant_resolver
    init_tenant_resolver()

    logger.info(
        "gestor.startup",
        module=config.module_name,
        version=config.module_version,
        multi_tenant=config.multi_tenant_enabled,
        port=config.gestor_port,
    )

    # Inicializar session factory
    if config.database_url:
        app.state.session_factory = TenantAwareSessionFactory(config.database_url)
        logger.info("gestor.db.connected", url=config.database_url.split("@")[-1])
    else:
        app.state.session_factory = None
        logger.warning("gestor.db.no_url", msg="DATABASE_URL não configurada")

    yield

    # Encerramento
    if app.state.session_factory:
        await app.state.session_factory.dispose()
    logger.info("gestor.shutdown")


# Auth integration (opcional)
try:
    from intellicare_auth.fastapi import configure_auth
    _HAS_AUTH = True
except ImportError:
    _HAS_AUTH = False

app = FastAPI(
    title="IntelliCare Gestor",
    description="Gestão de usuários, RBAC e setores por tenant",
    version=config.module_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Prometheus metrics
from intellicare_core.monitoring.metrics import setup_metrics  # noqa: E402
setup_metrics(app, module_name="gestor")

if _HAS_AUTH:
    configure_auth(app, secrets_path="keycloak_client_secrets.json")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Rotas de plataforma ────────────────────────────────────────────────

@app.get("/api/v1/health", tags=["platform"])
async def health():
    return {
        "status": "healthy",
        "module": config.module_name,
        "version": config.module_version,
    }


@app.get("/api/v1/info", tags=["platform"])
async def info():
    return {
        "module": config.module_name,
        "version": config.module_version,
        "environment": config.environment.value,
        "multi_tenant_enabled": config.multi_tenant_enabled,
        "port": config.gestor_port,
    }


# ── Rotas de negócio ───────────────────────────────────────────────────

app.include_router(user_routes.router, prefix="/gestor", tags=["users"])
app.include_router(role_routes.router, prefix="/gestor", tags=["roles"])
app.include_router(sector_routes.router, prefix="/gestor", tags=["sectors"])
app.include_router(settings_routes.router, prefix="/gestor", tags=["settings"])
app.include_router(audit_routes.router, prefix="/gestor", tags=["audit"])
app.include_router(dashboard_routes.router, prefix="/gestor", tags=["dashboard"])
