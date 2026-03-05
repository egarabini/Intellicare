from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine

from gestor.config import settings
from gestor.api import (
    user_routes as users,
    role_routes as roles,
    sector_routes as sectors,
    settings_routes as tenant_settings,
    audit_routes as audit,
    dashboard_routes as dashboard,
    bot_routes as bots,
)
from intellicare_core.tenant import TenantAwareSessionFactory

try:
    from intellicare_auth.fastapi import configure_auth
    _HAS_AUTH = True
except ImportError:
    _HAS_AUTH = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializa engine multi-tenant configurado via TenantAwareSessionFactory
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    app.state.session_factory = TenantAwareSessionFactory(engine)
    yield
    await engine.dispose()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

if _HAS_AUTH:
    configure_auth(app, secrets_path="keycloak_client_secrets.json")

app.include_router(users.router, prefix=settings.API_V1_STR)
app.include_router(roles.router, prefix=settings.API_V1_STR)
app.include_router(sectors.router, prefix=settings.API_V1_STR)
app.include_router(tenant_settings.router, prefix=settings.API_V1_STR)
app.include_router(audit.router, prefix=settings.API_V1_STR)
app.include_router(dashboard.router, prefix=settings.API_V1_STR)
app.include_router(bots.router, prefix=settings.API_V1_STR)

@app.get(f"{settings.API_V1_STR}/health")
async def health_check():
    return {"status": "ok"}
