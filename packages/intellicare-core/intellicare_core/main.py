from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from prometheus_fastapi_instrumentator import Instrumentator

from intellicare_core.module_loader import ModuleLoader

STATIC_ROOT = Path(__file__).resolve().parent / "static"
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    # Startup: call startup() on all loaded modules
    for name, mod in loader.loaded.items():
        if hasattr(mod, "startup") and callable(mod.startup):
            try:
                await mod.startup()
                logger.info("Modulo '%s' startup concluido.", name)
            except Exception:
                logger.exception("Erro no startup do modulo '%s'", name)
    yield

app = FastAPI(title="IntelliCare Service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/health", "/metrics"],
    env_var_name="ENABLE_METRICS",
    inprogress_name="intellicare_requests_inprogress",
    inprogress_labels=True,
).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

loader = ModuleLoader(app)
loader.load("admin")
loader.load("financeiro")
loader.load("programas")
loader.load("vector")
loader.load("gestor")
loader.load("cuidado")
loader.load("slm")
loader.load("notifications")
loader.load("careplanner")
loader.load("florence")
loader.load("oswaldo")


@app.get("/health")
async def root_health() -> JSONResponse:
    return JSONResponse({"status": "healthy", "service": "intellicare-service"})


admin_ui_dir = STATIC_ROOT / "admin-ui"
if admin_ui_dir.exists():
    app.mount("/admin-ui", StaticFiles(directory=str(admin_ui_dir), html=True), name="admin-ui")

gestor_ui_dir = STATIC_ROOT / "gestor-ui"
if gestor_ui_dir.exists():
    app.mount("/gestor-ui", StaticFiles(directory=str(gestor_ui_dir), html=True), name="gestor-ui")

clinico_ui_dir = STATIC_ROOT / "clinico-ui"
if clinico_ui_dir.exists():
    app.mount("/clinico-ui", StaticFiles(directory=str(clinico_ui_dir), html=True), name="clinico-ui")

paciente_ui_dir = STATIC_ROOT / "paciente-ui"
if paciente_ui_dir.exists():
    app.mount("/paciente-ui", StaticFiles(directory=str(paciente_ui_dir), html=True), name="paciente-ui")

# Portal por último — captura /
portal_dir = STATIC_ROOT / "portal"
if portal_dir.exists():
    app.mount("/", StaticFiles(directory=str(portal_dir), html=True), name="portal")
