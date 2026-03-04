from fastapi import FastAPI
from gestor.config import settings

from gestor.api.v1 import users, roles, sectors, settings as tenant_settings, audit, dashboard

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

app.include_router(users.router, prefix=settings.API_V1_STR)
app.include_router(roles.router, prefix=settings.API_V1_STR)
app.include_router(sectors.router, prefix=settings.API_V1_STR)
app.include_router(tenant_settings.router, prefix=settings.API_V1_STR)
app.include_router(audit.router, prefix=settings.API_V1_STR)
app.include_router(dashboard.router, prefix=settings.API_V1_STR)

@app.get(f"{settings.API_V1_STR}/health")
async def health_check():
    return {"status": "ok"}
