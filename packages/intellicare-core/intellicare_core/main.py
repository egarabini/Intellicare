from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from intellicare_core.module_loader import ModuleLoader

STATIC_ROOT = Path(__file__).resolve().parent / "static"

app = FastAPI(title="IntelliCare Service")
loader = ModuleLoader(app)
loader.load("admin")
loader.load("gestor")


@app.get("/health")
async def root_health() -> JSONResponse:
    return JSONResponse({"status": "healthy", "service": "intellicare-service"})


admin_ui_dir = STATIC_ROOT / "admin-ui"
if admin_ui_dir.exists():
    app.mount("/admin-ui", StaticFiles(directory=str(admin_ui_dir), html=True), name="admin-ui")

gestor_ui_dir = STATIC_ROOT / "gestor-ui"
if gestor_ui_dir.exists():
    app.mount("/gestor-ui", StaticFiles(directory=str(gestor_ui_dir), html=True), name="gestor-ui")
