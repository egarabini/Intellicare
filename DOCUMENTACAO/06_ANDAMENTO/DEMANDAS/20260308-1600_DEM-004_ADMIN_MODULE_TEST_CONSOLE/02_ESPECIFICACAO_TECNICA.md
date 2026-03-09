# DEM-004 — Module Test Console: Especificação Técnica

**Demanda:** DEM-004
**Módulo:** intellicare-admin
**Dev:** dev2

---

## Premissas e contexto técnico

- O admin usa **FastAPI** como backend (porta 8010) e um **React SPA** servido por nginx (porta 3003)
- `httpx` já está nas dependências (`pyproject.toml`) — usar para chamadas internas
- Todas as rotas novas exigem `require_platform_admin` (já implementado em `deps.py`)
- Os módulos rodam na rede Docker interna (`intellicare-network`) com hostnames `intellicare-<nome>`
- O backend do admin faz proxy para os módulos — o frontend **nunca chama os módulos diretamente**

---

## Novos arquivos — Backend

```
intellicare-admin/admin/
├── api/
│   ├── module_probe_routes.py      ← Fase 1
│   ├── module_test_routes.py       ← Fase 2
│   └── integration_test_routes.py  ← Fase 3
├── config/
│   └── test_payloads.py            ← payloads pré-configurados
├── models/
│   └── module_test_log.py          ← tabela de histórico
└── services/
    └── module_proxy.py             ← httpx client autenticado
```

---

## `admin/services/module_proxy.py`

Registry dos módulos e client httpx. Todas as chamadas aos módulos passam por aqui.

```python
import asyncio
import time
from typing import Any
import httpx

MODULE_REGISTRY: dict[str, dict] = {
    "florence":    {"display": "FLORENCE",    "url": "http://intellicare-florence:8000",    "port": 8001},
    "oswaldo":     {"display": "OSWALDO",     "url": "http://intellicare-oswaldo:8000",     "port": 8002},
    "donabedian":  {"display": "DONABEDIAN",  "url": "http://intellicare-donabedian:8000",  "port": 8003},
    "wanda":       {"display": "WANDA",       "url": "http://intellicare-wanda:8000",       "port": 8004},
    "comunicacao": {"display": "COMUNICACAO", "url": "http://intellicare-comunicacao:8000", "port": 8005},
    "geralda":     {"display": "GERALDA",     "url": "http://intellicare-geralda:8000",     "port": 8006},
    "zilda":       {"display": "ZILDA",       "url": "http://intellicare-zilda:8000",       "port": 8007},
    "minerva":     {"display": "MINERVA",     "url": "http://intellicare-minerva:8000",     "port": 8008},
    "pierre":      {"display": "PIERRE",      "url": "http://intellicare-pierre:8000",      "port": 8009},
    "grahame":     {"display": "GRAHAME",     "url": "http://intellicare-grahame:8000",     "port": 8012},
    "nise":        {"display": "NISE",        "url": "http://intellicare-nise:8000",        "port": 8013},
}

class ModuleProxyClient:
    """Proxy autenticado admin → módulos via httpx."""

    # Timeout curto para probe (não bloquear o grid)
    PROBE_TIMEOUT = 5.0
    # Timeout maior para análise (LLMs podem demorar)
    ANALYZE_TIMEOUT = 30.0

    @staticmethod
    def _headers() -> dict[str, str]:
        # Header interno identifica origem como admin — módulos podem usar para logging
        return {"X-Internal-Call": "intellicare-admin"}

    @classmethod
    async def probe(cls, module_name: str) -> dict[str, Any]:
        """Chama /health e /info em paralelo. Retorna probe consolidado."""
        meta = MODULE_REGISTRY.get(module_name)
        if not meta:
            return {"health": "unknown", "error": f"módulo '{module_name}' não registrado"}

        base = meta["url"]
        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=cls.PROBE_TIMEOUT) as client:
                health_task = client.get(f"{base}/api/v1/health", headers=cls._headers())
                info_task   = client.get(f"{base}/api/v1/info",   headers=cls._headers())
                health_r, info_r = await asyncio.gather(
                    health_task, info_task, return_exceptions=True
                )
            latency_ms = int((time.monotonic() - start) * 1000)

            # Processar health
            if isinstance(health_r, Exception):
                return {"health": "unreachable", "latency_ms": -1, "error": str(health_r)}

            health_data = health_r.json() if health_r.is_success else {}
            info_data   = info_r.json()   if (not isinstance(info_r, Exception) and info_r.is_success) else {}

            status = "healthy"
            if not health_r.is_success:
                status = "unhealthy"
            elif latency_ms >= 500:
                status = "degraded"

            return {
                "health": status,
                "status_code": health_r.status_code,
                "latency_ms": latency_ms,
                "version": info_data.get("version", health_data.get("version", "?")),
                "uptime_seconds": health_data.get("uptime_seconds"),
                "dependencies": health_data.get("dependencies", {}),
                "last_checked": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        except httpx.TimeoutException:
            return {"health": "unreachable", "latency_ms": -1, "error": "timeout"}
        except Exception as e:
            return {"health": "unreachable", "latency_ms": -1, "error": str(e)}

    @classmethod
    async def probe_all(cls) -> list[dict[str, Any]]:
        """Probe de todos os módulos em paralelo."""
        tasks = [cls.probe(name) for name in MODULE_REGISTRY]
        results = await asyncio.gather(*tasks)
        return [
            {
                "name": name,
                "display_name": MODULE_REGISTRY[name]["display"],
                "port": MODULE_REGISTRY[name]["port"],
                "probe": result,
            }
            for name, result in zip(MODULE_REGISTRY.keys(), results)
        ]

    @classmethod
    async def test_analyze(
        cls, module_name: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Envia POST /api/v1/analyze para o módulo. Retorna resultado enriquecido."""
        meta = MODULE_REGISTRY.get(module_name)
        if not meta:
            return {"success": False, "error": f"módulo '{module_name}' não registrado"}

        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=cls.ANALYZE_TIMEOUT) as client:
                r = await client.post(
                    f"{meta['url']}/api/v1/analyze",
                    json=payload,
                    headers=cls._headers(),
                )
            latency_ms = int((time.monotonic() - start) * 1000)
            return {
                "status_code": r.status_code,
                "latency_ms": latency_ms,
                "success": r.is_success,
                "response": r.json() if r.is_success else None,
                "error": r.text if not r.is_success else None,
            }
        except httpx.TimeoutException:
            return {"status_code": 504, "latency_ms": -1, "success": False, "error": "timeout"}
        except Exception as e:
            return {"status_code": 500, "latency_ms": -1, "success": False, "error": str(e)}
```

---

## `admin/config/test_payloads.py`

Payloads pré-configurados por módulo. Nunca usar dados reais de pacientes.

```python
"""Payloads de teste pré-configurados por módulo.

Todos os dados são fictícios. Paciente padrão: João Silva, 65 anos.
"""

TEST_PAYLOADS: dict[str, dict[str, dict]] = {
    "florence": {
        "default": {
            "patient_id": "test-001",
            "query": "protocolo hipertensão arterial estágio 2",
            "parameters": {"max_results": 3},
        },
        "drc": {
            "patient_id": "test-001",
            "query": "protocolo doença renal crônica estadio 3",
        },
    },
    "oswaldo": {
        "default": {
            "patient_id": "test-001",
            "query": "análise clínica completa",
            "parameters": {
                "fhir_bundle": {
                    "resourceType": "Bundle",
                    "entry": [
                        {
                            "resource": {
                                "resourceType": "Patient",
                                "id": "test-001",
                                "name": [{"text": "João Silva (FICTÍCIO)"}],
                                "birthDate": "1961-01-15",
                                "gender": "male",
                            }
                        },
                        {
                            "resource": {
                                "resourceType": "Condition",
                                "subject": {"reference": "Patient/test-001"},
                                "code": {"coding": [{"system": "http://snomed.info/sct", "code": "59621000", "display": "Hipertensão arterial"}]},
                            }
                        },
                    ],
                }
            },
        },
    },
    "donabedian": {
        "default": {
            "patient_id": "test-001",
            "query": "indicadores de qualidade",
            "parameters": {"tenant_id": "test", "period": "2026-01"},
        },
    },
    "wanda": {
        "default": {
            "patient_id": "test-001",
            "query": "resumo clínico do paciente",
        },
        "orchestration": {
            "patient_id": "test-001",
            "query": "análise completa com recomendações",
            "parameters": {"include_agents": ["oswaldo", "donabedian", "florence"]},
        },
    },
    "comunicacao": {
        "default": {
            "patient_id": "test-001",
            "query": "teste de envio",
            "parameters": {"channel": "test", "dry_run": True, "to": "test@intellicare.ia.br"},
        },
    },
    "geralda": {
        "default": {
            "patient_id": "test-001",
            "query": "opções de suporte disponíveis",
        },
    },
    "zilda": {
        "default": {
            "patient_id": "test-001",
            "query": "CNES 0000001",
        },
    },
    "minerva": {
        "default": {
            "patient_id": "test-001",
            "query": "extração de documento",
            "parameters": {"dry_run": True},
        },
    },
    "pierre": {
        "default": {
            "patient_id": "test-001",
            "query": "hypertension treatment guidelines 2025",
            "parameters": {"max_results": 2},
        },
    },
    "grahame": {
        "default": {
            "patient_id": "test-001",
            "query": "validar recurso FHIR Patient",
            "parameters": {
                "resource_type": "Patient",
                "action": "validate",
                "resource": {
                    "resourceType": "Patient",
                    "id": "test-001",
                    "name": [{"text": "Teste FHIR (FICTÍCIO)"}],
                },
            },
        },
    },
    "nise": {
        "default": {
            "patient_id": "test-001",
            "query": "olá, preciso de ajuda",
            "parameters": {"session_id": "test-session-001"},
        },
    },
}
```

---

## `admin/models/module_test_log.py`

```python
from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, func
from admin.db.base import Base

class ModuleTestLog(Base):
    __tablename__ = "module_test_log"
    __table_args__ = {"schema": "platform"}  # schema de plataforma, não tenant

    id            = Column(Integer, primary_key=True, autoincrement=True)
    module_name   = Column(String(64),  nullable=False, index=True)
    test_type     = Column(String(32),  nullable=False)  # "probe" | "functional" | "integration"
    payload_key   = Column(String(64))                   # ex: "default", "drc", None
    status_code   = Column(Integer)
    latency_ms    = Column(Integer)
    success       = Column(Boolean)
    response_json = Column(JSON)
    error_message = Column(String(512))
    triggered_by  = Column(String(128))                  # sub do JWT do usuário admin
    created_at    = Column(DateTime(timezone=True), server_default=func.now(), index=True)
```

**Migração Alembic:**
```bash
# A partir de intellicare-admin/
alembic revision --autogenerate -m "add module_test_log"
alembic upgrade head
```

---

## `admin/api/module_probe_routes.py` — Fase 1

```python
from fastapi import APIRouter, Depends
from admin.api.deps import require_platform_admin
from admin.services.module_proxy import ModuleProxyClient, MODULE_REGISTRY

router = APIRouter(prefix="/admin/modules", tags=["Module Probe"],
                   dependencies=[Depends(require_platform_admin)])

@router.get("", summary="Lista todos os módulos com probe em paralelo")
async def list_modules():
    return await ModuleProxyClient.probe_all()

@router.get("/{module_name}/probe", summary="Probe individual de um módulo")
async def probe_module(module_name: str):
    if module_name not in MODULE_REGISTRY:
        from fastapi import HTTPException
        raise HTTPException(404, f"Módulo '{module_name}' não encontrado")
    result = await ModuleProxyClient.probe(module_name)
    return {"name": module_name, **MODULE_REGISTRY[module_name], "probe": result}
```

---

## `admin/api/module_test_routes.py` — Fase 2

```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from admin.api.deps import require_platform_admin, get_db
from admin.services.module_proxy import ModuleProxyClient, MODULE_REGISTRY
from admin.config.test_payloads import TEST_PAYLOADS
from admin.models.module_test_log import ModuleTestLog

router = APIRouter(prefix="/admin/modules", tags=["Module Test"],
                   dependencies=[Depends(require_platform_admin)])

class TestRequest(BaseModel):
    payload_key: str = "default"
    custom_payload: dict[str, Any] | None = None

@router.post("/{module_name}/test", summary="Executa teste funcional no módulo")
async def test_module(
    module_name: str,
    body: TestRequest,
    session: AsyncSession = Depends(get_db),
    actor: dict = Depends(require_platform_admin),
):
    if module_name not in MODULE_REGISTRY:
        raise HTTPException(404, f"Módulo '{module_name}' não encontrado")

    # Determinar payload
    payload = body.custom_payload
    if payload is None:
        module_payloads = TEST_PAYLOADS.get(module_name, {})
        payload = module_payloads.get(body.payload_key) or module_payloads.get("default")
        if not payload:
            raise HTTPException(400, f"Payload '{body.payload_key}' não encontrado para '{module_name}'")

    result = await ModuleProxyClient.test_analyze(module_name, payload)

    # Persistir no histórico
    log = ModuleTestLog(
        module_name=module_name,
        test_type="functional",
        payload_key=body.payload_key if not body.custom_payload else "custom",
        status_code=result.get("status_code"),
        latency_ms=result.get("latency_ms"),
        success=result.get("success", False),
        response_json=result.get("response"),
        error_message=result.get("error"),
        triggered_by=actor.get("sub", "unknown"),
    )
    session.add(log)
    await session.commit()

    return {
        "module": module_name,
        "payload_key": body.payload_key,
        **result,
    }

@router.get("/{module_name}/test/history", summary="Histórico de testes do módulo")
async def test_history(
    module_name: str,
    limit: int = 20,
    session: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select, desc
    rows = (await session.execute(
        select(ModuleTestLog)
        .where(ModuleTestLog.module_name == module_name)
        .order_by(desc(ModuleTestLog.created_at))
        .limit(limit)
    )).scalars().all()
    return [
        {
            "id": r.id, "test_type": r.test_type, "payload_key": r.payload_key,
            "status_code": r.status_code, "latency_ms": r.latency_ms,
            "success": r.success, "error_message": r.error_message,
            "triggered_by": r.triggered_by, "created_at": r.created_at,
        }
        for r in rows
    ]

@router.get("/{module_name}/test/payloads", summary="Lista payloads disponíveis")
async def list_payloads(module_name: str):
    return {"module": module_name, "payloads": list(TEST_PAYLOADS.get(module_name, {}).keys())}
```

---

## Registro das rotas em `app.py`

```python
# Adicionar junto com os outros include_router:
from admin.api.module_probe_routes import router as probe_router
from admin.api.module_test_routes   import router as module_test_router

app.include_router(probe_router,       prefix="/api/v1")
app.include_router(module_test_router, prefix="/api/v1")
```

---

## Frontend React — estrutura de componentes

```
intellicare-admin-frontend/src/pages/Diagnostico/
├── index.tsx                 ← rota /diagnostico
├── ModuleGrid.tsx            ← grid de cards (Fase 1)
├── ModuleCard.tsx            ← card individual
├── ModuleTestPanel.tsx       ← aba teste funcional (Fase 2)
├── PayloadEditor.tsx         ← editor JSON com CodeMirror
├── ResponseViewer.tsx        ← viewer JSON com syntax highlight
├── IntegrationTests.tsx      ← Fase 3
└── TestHistory.tsx           ← histórico paginado
```

**Biblioteca de editor JSON:** `@uiw/react-codemirror` + `@codemirror/lang-json`
(instalar via npm — MIT license, não requer configuração adicional).

**Esquema de cores (Tailwind):**

| Status | Classe Tailwind | Hex |
|---|---|---|
| healthy | `bg-green-500` | #22c55e |
| degraded | `bg-yellow-400` | #facc15 |
| unhealthy | `bg-red-500` | #ef4444 |
| unreachable | `bg-gray-400` | #9ca3af |

**Chamadas de API do frontend:**

```typescript
// Fase 1 — probe de todos
GET /api/v1/admin/modules

// Fase 1 — probe individual
GET /api/v1/admin/modules/{name}/probe

// Fase 2 — listar payloads disponíveis
GET /api/v1/admin/modules/{name}/test/payloads

// Fase 2 — executar teste funcional
POST /api/v1/admin/modules/{name}/test
{ "payload_key": "default" }

// Fase 2 — histórico
GET /api/v1/admin/modules/{name}/test/history?limit=20
```

---

## Variáveis de ambiente necessárias

Nenhuma nova variável. Os hostnames dos módulos são fixos na rede Docker
(`intellicare-<nome>:8000`) e configurados diretamente no `MODULE_REGISTRY`.

Se o ambiente não usar Docker (dev local), o dev pode sobrescrever via
env vars — sugestão de implementação futura, não necessária no MVP.

---

## Pontos de atenção

**Timeout no probe:** 5 segundos é intencional. Se um módulo não responder
em 5s, ele está efetivamente indisponível para o administrador.

**Timeout no analyze:** 30 segundos porque módulos com LLM (FLORENCE, WANDA,
NISE, PIERRE) podem demorar mais em ambientes carregados.

**Probe em paralelo:** `asyncio.gather()` — todos os 11 módulos são provados
simultaneamente. O tempo total do grid é limitado pelo mais lento, não pela soma.

**Autenticação nos módulos:** Neste MVP, as chamadas internas admin → módulos
**não carregam token de auth** (apenas o header `X-Internal-Call`). Os módulos
aceitam chamadas internas sem auth na rede Docker. Se futuramente os módulos
exigirem auth interna, será necessário adicionar o service account (ver DEM-005).
