from __future__ import annotations

from fastapi import FastAPI

from conhecimento.api.protocolos import router as protocolos_router
from conhecimento.api.rag import router as rag_router
from conhecimento.api.templates import router as templates_router
from conhecimento.api.terminologias import router as terminologias_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="IntelliCare Conhecimento",
        version="1.0.0",
        description="Base de Conhecimento Clinico e Operacional (BCCO)",
    )

    @app.get("/api/v1/health")
    def health():
        return {"status": "healthy", "module_name": "intellicare-conhecimento", "version": "1.0.0"}

    @app.get("/api/v1/info")
    def info():
        return {
            "name": "intellicare-conhecimento",
            "capabilities": ["protocolos", "terminologias", "careplan_templates", "rag"],
        }

    app.include_router(protocolos_router)
    app.include_router(terminologias_router)
    app.include_router(templates_router)
    app.include_router(rag_router)
    return app


app = create_app()

