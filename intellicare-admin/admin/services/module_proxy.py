import asyncio
import time
from typing import Any

import httpx

MODULE_REGISTRY: dict[str, dict[str, Any]] = {
    "florence": {
        "url": "http://intellicare-florence:8000",
        "display_name": "FLORENCE",
        "description": "RAG + Protocolos Clínicos",
        "port": 8001,
    },
    "oswaldo": {
        "url": "http://intellicare-oswaldo:8000",
        "display_name": "OSWALDO",
        "description": "Análise Clínica + FHIR",
        "port": 8002,
    },
    "donabedian": {
        "url": "http://intellicare-donabedian:8000",
        "display_name": "DONABEDIAN",
        "description": "Qualidade + Indicadores",
        "port": 8003,
    },
    "wanda": {
        "url": "http://intellicare-wanda:8000",
        "display_name": "WANDA",
        "description": "Orquestração + Workflows",
        "port": 8004,
    },
    "comunicacao": {
        "url": "http://intellicare-comunicacao:8000",
        "display_name": "COMUNICAÇÃO",
        "description": "Comunicação + Notificações",
        "port": 8005,
    },
    "geralda": {
        "url": "http://intellicare-geralda:8000",
        "display_name": "GERALDA",
        "description": "Gestão + Administrativo",
        "port": 8006,
    },
    "zilda": {
        "url": "http://intellicare-zilda:8000",
        "display_name": "ZILDA",
        "description": "CNES + DATASUS",
        "port": 8007,
    },
    "minerva": {
        "url": "http://intellicare-minerva:8008",
        "display_name": "MINERVA",
        "description": "OCR + Document Extraction",
        "port": 8008,
    },
    "pierre": {
        "url": "http://intellicare-pierre:8009",
        "display_name": "PIERRE",
        "description": "Scientific Search",
        "port": 8009,
    },
    "grahame": {
        "url": "http://intellicare-grahame:8000",
        "display_name": "GRAHAME",
        "description": "FHIR R4 + CDS Hooks",
        "port": 8012,
    },
    "nise": {
        "url": "http://intellicare-nise:8000",
        "display_name": "NISE",
        "description": "Chatbot + Training",
        "port": 8013,
    },
}


class ModuleProxyClient:
    """httpx client for internal admin -> modules calls."""

    def __init__(self, internal_token: str = ""):
        self._token = internal_token
        # TODO: Add dynamic internal token matching in Fase 2
        self._headers = {
            "Authorization": f"Bearer {internal_token}" if internal_token else "",
            "X-Internal-Call": "intellicare-admin",
        }

    async def probe(self, module_name: str) -> dict[str, Any]:
        """Calls /health and /info in parallel and returns consolidated probe."""
        if module_name not in MODULE_REGISTRY:
            return {"health": "unreachable", "error": f"Module {module_name} not found in registry", "latency_ms": -1}

        module_config = MODULE_REGISTRY[module_name]
        base = module_config["url"]

        async with httpx.AsyncClient(timeout=5.0) as client:
            start = time.monotonic()
            try:
                health_r, info_r = await asyncio.gather(
                    client.get(f"{base}/api/v1/health", headers=self._headers),
                    client.get(f"{base}/api/v1/info", headers=self._headers),
                    return_exceptions=True,
                )
                latency_ms = int((time.monotonic() - start) * 1000)

                if isinstance(health_r, Exception):
                    return {"health": "unreachable", "error": str(health_r), "latency_ms": -1}

                health_data = health_r.json() if health_r.is_success else {}
                info_data = info_r.json() if not isinstance(info_r, Exception) and info_r.is_success else {}

                status_mapped = "healthy"
                if health_r.status_code != 200:
                    status_mapped = "unhealthy"
                elif latency_ms >= 500:
                    status_mapped = "degraded"

                return {
                    "health": status_mapped,
                    "status_code": health_r.status_code,
                    "latency_ms": latency_ms,
                    "version": info_data.get("version", "unknown"),
                    "uptime_seconds": health_data.get("uptime_seconds", 0),
                    "dependencies": health_data.get("dependencies", {}),
                    "last_checked": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }

            except Exception as e:
                return {"health": "unreachable", "error": str(e), "latency_ms": -1}

