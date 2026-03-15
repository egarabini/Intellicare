from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from intellicare_core.module_loader import ModuleLoader

STATIC_ROOT = Path(__file__).resolve().parent / "static"

app = FastAPI(title="IntelliCare Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
loader = ModuleLoader(app)
loader.load("admin")
loader.load("financeiro")
loader.load("programas")
loader.load("vector")
loader.load("gestor")
loader.load("cuidado")
loader.load("slm")


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
