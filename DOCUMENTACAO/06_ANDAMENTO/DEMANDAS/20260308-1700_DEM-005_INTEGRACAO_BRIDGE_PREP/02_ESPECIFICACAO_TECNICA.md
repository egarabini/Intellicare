# DEM-005 — Portas de Integração HIS: Especificação Técnica

**Demanda:** DEM-005
**Módulo principal:** intellicare-core
**Módulos secundários:** intellicare-grahame · intellicare-wanda · intellicare-auth · intellicare-bridge (novo)
**Dev:** dev3

---

## Premissas e contexto técnico

- `intellicare-auth` fornece `require_role("NOME_DA_ROLE")` para todos os módulos
- GRAHAME tem `grahame/api/routes/fhir_native_routes.py` com router FHIR existente
- WANDA usa middleware em `wanda/api/` para injetar contexto nas requisições
- Todos os módulos Python usam `asyncio`, FastAPI e Pydantic v2
- Redis Streams (`intellicare:events:*`) são o bus de eventos interno
- `intellicare-core` instalado via `pip install -e ../intellicare-core` em todos os módulos

---

## Novos arquivos a criar

```
intellicare-core/
└── intellicare_core/
    └── bridge/                          ← pacote novo (FASE 1)
        ├── __init__.py
        ├── context.py
        ├── adapter.py
        └── registry.py

intellicare-grahame/
└── grahame/
    └── api/
        └── routes/
            └── bridge_routes.py         ← endpoint $process-message (FASE 2)

intellicare-bridge/                      ← módulo novo (FASE 3 — stub)
├── bridge/
│   ├── api/
│   │   ├── app.py
│   │   └── adapter_routes.py
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── feegow/
│   │       └── __init__.py
│   └── config.py
├── pyproject.toml
├── Dockerfile
└── docker-compose.yml
```

---

## Arquivos existentes a modificar

| Arquivo | Módulo | Mudança |
|---|---|---|
| `intellicare_core/__init__.py` | core | Exportar `bridge` no `__init__` |
| `grahame/api/app.py` | grahame | Registrar `bridge_routes.router` |
| `grahame/api/deps.py` | grahame | Adicionar `require_his_adapter` |
| `wanda/api/middleware.py` (ou equivalente) | wanda | Ler e injetar `X-HIS-Context` |
| `wanda/api/routes/` (intent router) | wanda | Propagar `HISContext` no `AnalysisRequest` |
| `docker-compose.full.yml` | raiz | Adicionar serviço `intellicare-bridge` |
| `scripts/smoke_test.sh` | raiz | Adicionar health check do bridge |

---

## FASE 1 — intellicare-core: pacote `bridge`

### `intellicare_core/bridge/__init__.py`

```python
from intellicare_core.bridge.context import HISContext, HISSystem
from intellicare_core.bridge.adapter import BaseHISAdapter
from intellicare_core.bridge.registry import HISAdapterRegistry

__all__ = ["HISContext", "HISSystem", "BaseHISAdapter", "HISAdapterRegistry"]
```

### `intellicare_core/bridge/context.py`

```python
from __future__ import annotations
import base64
import json
from enum import Enum
from pydantic import BaseModel, Field


class HISSystem(str, Enum):
    TASY    = "philips_tasy"
    SOUL_MV = "soul_mv"
    TOTVS   = "totvs_rm"
    FEEGOW  = "feegow"
    PIXEON  = "pixeon"
    SISHOSP = "sishosp"
    OPENEMR = "openemr"
    UNKNOWN = "unknown"


class HISContext(BaseModel):
    """Contexto de sessão originado por um HIS externo.

    Propagado como header X-HIS-Context (JSON base64) entre serviços internos.
    Criado pelo intellicare-bridge ao processar o EHR Launch token do HIS.
    """
    his_system:      HISSystem = HISSystem.UNKNOWN
    his_patient_id:  str = Field(..., description="ID do paciente no HIS de origem")
    fhir_patient_id: str = Field(default="", description="ID FHIR mapeado pelo bridge")
    encounter_id:    str = Field(default="", description="ID do encontro/atendimento")
    practitioner_id: str = Field(default="", description="ID do profissional no HIS")
    tenant_id:       str = Field(..., description="Tenant IntelliCare")
    launch_token:    str = Field(default="", description="Opaque token do EHR Launch")
    iss:             str = Field(default="", description="FHIR Base URL do HIS")
    scopes:          list[str] = Field(default_factory=list)

    def to_header(self) -> str:
        """Serializa para uso como header X-HIS-Context."""
        return base64.b64encode(self.model_dump_json().encode()).decode()

    @classmethod
    def from_header(cls, header_value: str) -> "HISContext":
        """Desserializa do header X-HIS-Context."""
        data = json.loads(base64.b64decode(header_value).decode())
        return cls(**data)
```

### `intellicare_core/bridge/adapter.py`

```python
from abc import ABC, abstractmethod
from typing import Any
from intellicare_core.bridge.context import HISContext


class BaseHISAdapter(ABC):
    """Contrato que todo adaptador HIS deve implementar.

    Cada HIS (Tasy, Feegow, MV...) implementa esta classe em intellicare-bridge,
    traduzindo a API proprietária para FHIR R4 Bundle.
    """

    @property
    @abstractmethod
    def his_system(self) -> str:
        """Identificador do sistema (ex: 'feegow'). Deve coincidir com HISSystem enum."""
        ...

    @abstractmethod
    async def resolve_launch_context(self, launch_token: str, iss: str) -> HISContext:
        """Resolve o launch token do EHR Launch em HISContext completo.

        Chamado pelo GRAHAME quando recebe GET /smart/launch com parâmetros do HIS.
        """
        ...

    @abstractmethod
    async def get_patient_bundle(self, context: HISContext) -> dict[str, Any]:
        """Retorna FHIR Bundle com dados do paciente traduzidos da API do HIS.

        Bundle deve conter: Patient, Condition[], Observation[], MedicationRequest[].
        Tipo: transaction (para ingestão via $process-message).
        """
        ...

    @abstractmethod
    async def push_cds_card(self, context: HISContext, card: dict[str, Any]) -> bool:
        """Envia um CDS Hook card de volta para o HIS (se o HIS suportar write-back).

        Retorna True se o HIS aceitou o card, False caso contrário.
        """
        ...

    async def validate_connection(self) -> bool:
        """Testa conectividade básica com o HIS. Default: False (sem conexão real)."""
        return False
```

### `intellicare_core/bridge/registry.py`

```python
from __future__ import annotations
from intellicare_core.bridge.adapter import BaseHISAdapter


class HISAdapterRegistry:
    """Registro de adaptadores HIS disponíveis no runtime.

    Adaptadores se registram no startup do intellicare-bridge.
    O GRAHAME e o WANDA consultam o registry para descobrir quais HIS estão ativos.
    """
    _adapters: dict[str, BaseHISAdapter] = {}

    @classmethod
    def register(cls, adapter: BaseHISAdapter) -> None:
        """Registra um adaptador. Chamado no lifespan do intellicare-bridge."""
        cls._adapters[adapter.his_system] = adapter

    @classmethod
    def get(cls, his_system: str) -> BaseHISAdapter | None:
        """Retorna o adaptador para um sistema HIS específico, ou None."""
        return cls._adapters.get(his_system)

    @classmethod
    def list_available(cls) -> list[str]:
        """Lista os sistemas HIS com adaptador registrado."""
        return list(cls._adapters.keys())
```

### Adição ao `intellicare_core/__init__.py`

Verificar se existe um `__init__.py` raiz no core. Se existir, adicionar:

```python
# Expor bridge para facilitar import por outros módulos
from intellicare_core import bridge  # noqa: F401
```

Se não existir, não é necessário — os módulos importam diretamente de `intellicare_core.bridge`.

---

## FASE 2 — GRAHAME: endpoint `$process-message`

### Novo arquivo `grahame/api/routes/bridge_routes.py`

```python
"""Rotas de integração com adaptadores HIS (intellicare-bridge).

Endpoint principal: POST /fhir/$process-message
Aceita FHIR Bundle transaction/batch de adaptadores autenticados com role HIS_ADAPTER.
"""
from __future__ import annotations
from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from grahame.api.deps import get_db, require_his_adapter
from intellicare_core.bridge.context import HISContext

router = APIRouter(prefix="/api/v1/fhir", tags=["Bridge"])


@router.post(
    "/$process-message",
    summary="Ingestão de FHIR Bundle (adaptadores HIS)",
    status_code=202,
)
async def process_message_bundle(
    bundle: dict[str, Any],
    request: Request,
    session: AsyncSession = Depends(get_db),
    _: dict = Depends(require_his_adapter),
) -> dict[str, Any]:
    """Recebe FHIR Bundle transaction/batch de um adaptador HIS.

    Para cada entry do bundle:
    - Patient → upsert via FHIRService existente
    - Observation, Condition, MedicationRequest → upsert genérico
    - Outros tipos → aceitos mas sem processamento especial (log + store)

    Publica evento 'his_bundle_ingested' no Redis Stream para WANDA.
    Retorna Bundle de respostas com OperationOutcome por entry.
    """
    his_context_header = request.headers.get("X-HIS-Context")
    his_context: HISContext | None = None
    if his_context_header:
        try:
            his_context = HISContext.from_header(his_context_header)
        except Exception:
            pass  # contexto opcional — continua sem ele

    results = []
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        resource_type = resource.get("resourceType", "Unknown")
        # TODO (dev3): usar FHIRService existente para upsert por resourceType
        results.append({
            "resourceType": "OperationOutcome",
            "issue": [{
                "severity": "information",
                "code": "informational",
                "diagnostics": f"{resource_type} recebido",
            }],
        })

    if his_context:
        await _publish_his_ingestion_event(his_context, len(results))

    return {
        "resourceType": "Bundle",
        "type": "transaction-response",
        "entry": [{"resource": r} for r in results],
    }


async def _publish_his_ingestion_event(
    context: HISContext, entry_count: int
) -> None:
    """Publica evento no Redis Stream para o WANDA processar."""
    # TODO (dev3): usar RedisClient existente do GRAHAME (app.state.redis ou similar)
    # Stream: intellicare:events:his_ingestion
    # Payload:
    # {
    #   "event_type": "his_bundle_ingested",
    #   "his_system": context.his_system,
    #   "tenant_id": context.tenant_id,
    #   "fhir_patient_id": context.fhir_patient_id,
    #   "encounter_id": context.encounter_id,
    #   "bundle_entry_count": entry_count,
    #   "timestamp": datetime.utcnow().isoformat(),
    # }
    pass
```

### Adição em `grahame/api/deps.py`

```python
from intellicare_auth.fastapi import require_role

async def require_his_adapter(payload: dict = Depends(require_role("HIS_ADAPTER"))) -> dict:
    """Guard: exige role HIS_ADAPTER no token (service account do bridge)."""
    return payload
```

### Registro em `grahame/api/app.py`

```python
from grahame.api.routes.bridge_routes import router as bridge_router
# ...dentro do create_application() ou após definição do app:
app.include_router(bridge_router)
```

---

## FASE 3 — WANDA: propagação de HISContext

### Leitura do header (middleware ou dependência)

Localizar onde o WANDA injeta contexto nas requisições (provavelmente `wanda/api/middleware.py` ou `wanda/api/deps.py`). Adicionar:

```python
from intellicare_core.bridge.context import HISContext

# No middleware ou dependência de contexto:
his_context_header = request.headers.get("X-HIS-Context")
if his_context_header:
    try:
        request.state.his_context = HISContext.from_header(his_context_header)
    except Exception:
        request.state.his_context = None
else:
    request.state.his_context = None
```

### Propagação no intent router do WANDA

No ponto onde o WANDA monta o `AnalysisRequest` para enviar aos agentes:

```python
# Se vier com HISContext, incluir nos parameters e propagar o header
his_context: HISContext | None = getattr(request.state, "his_context", None)
if his_context:
    analysis_request.parameters["his_context"] = his_context.model_dump()
    # Adicionar header X-HIS-Context nas chamadas internas (httpx):
    # headers["X-HIS-Context"] = his_context.to_header()
```

### Consumer do evento Redis `his_bundle_ingested`

Localizar onde o WANDA registra consumers de Redis Streams (provavelmente `wanda/events/` ou `wanda/api/app.py lifespan`). Adicionar consumer para:

```
Stream: intellicare:events:his_ingestion
Group: wanda-his-consumer
```

Ao receber `his_bundle_ingested`:
1. Monta `HISContext` a partir do payload do evento
2. Dispara análise automática do paciente (POST `/api/v1/analyze` interno com `fhir_patient_id`)
3. Loga evento com `his_system` e `tenant_id`

---

## FASE 4 — Keycloak: role `HIS_ADAPTER` e service account

Executado manualmente via Keycloak Admin Console ou script de provisionamento.

```
Realm: intellicare

Nova role realm:
  Nome: HIS_ADAPTER
  Descrição: Permite ingerir FHIR Bundles via $process-message e chamar WANDA /analyze

Novo client (service account para testes):
  Client ID: intellicare-bridge-dev
  Access Type: confidential
  Service Accounts Enabled: true
  Standard Flow: false
  Service Account Roles: HIS_ADAPTER

Gerar client secret e salvar em:
  intellicare-bridge/keycloak_client_secrets.json
  (mesmo formato de intellicare-admin/keycloak_client_secrets.json)
```

**Para cada HIS real (implementar no futuro, um por vez):**
- Client: `intellicare-bridge-feegow`, `intellicare-bridge-tasy`, etc.
- Service account com role `HIS_ADAPTER`
- Secret salvo de forma segura (não commitar — usar `.env` ou vault)

---

## FASE 5 — Módulo stub `intellicare-bridge`

### `intellicare-bridge/pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "intellicare-bridge"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "intellicare-core",
    "intellicare-auth",
    "fastapi>=0.115",
    "uvicorn[standard]>=0.29",
    "httpx>=0.27",
    "pydantic>=2.7",
]

[project.optional-dependencies]
dev = ["pytest>=8", "pytest-asyncio>=0.23", "mypy>=1.10", "ruff>=0.4"]

[tool.setuptools.packages.find]
where = ["."]
include = ["bridge*"]
```

### `intellicare-bridge/bridge/api/app.py`

```python
"""intellicare-bridge — Adaptadores HIS para FHIR R4.

Status: STUB — estrutura definida, aguardando implementação dos adaptadores.
Porta: 8014

Adaptadores planejados:
  - feegow     (MVP — API REST v1.0, token estático)
  - totvs_rm   (API REST, TOTVS Developers)
  - soul_mv    (Plataforma de Interoperabilidade MV)
  - philips_tasy (SOAP/REST híbrido)
  - pixeon     (barramento local, por demanda)
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from intellicare_core.contracts import ModuleInfo, HealthCheck
from intellicare_core.bridge.registry import HISAdapterRegistry


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Registrar adaptadores aqui quando implementados:
    # from bridge.adapters.feegow import FeegoAdapter
    # HISAdapterRegistry.register(FeegoAdapter())
    yield


app = FastAPI(
    title="intellicare-bridge",
    description="Adaptadores HIS → FHIR R4 (stub)",
    version="0.1.0-stub",
    lifespan=lifespan,
)


@app.get("/api/v1/health")
async def health() -> dict:
    return HealthCheck(
        status="healthy",
        module="intellicare-bridge",
        details={
            "mode": "stub",
            "adapters_loaded": HISAdapterRegistry.list_available(),
            "adapters_planned": ["feegow", "philips_tasy", "soul_mv", "totvs_rm", "pixeon"],
        },
    ).model_dump()


@app.get("/api/v1/info")
async def info() -> dict:
    return ModuleInfo(
        name="BRIDGE",
        description="Adaptadores de Interoperabilidade HIS → FHIR R4",
        version="0.1.0-stub",
        capabilities=["his_adapter", "ehr_launch", "fhir_bundle_translation"],
    ).model_dump()


@app.get("/api/v1/bridge/adapters")
async def list_adapters() -> dict:
    """Lista adaptadores HIS registrados e planejados."""
    return {
        "registered": HISAdapterRegistry.list_available(),
        "planned": ["feegow", "philips_tasy", "soul_mv", "totvs_rm", "pixeon"],
    }
```

### `intellicare-bridge/bridge/adapters/base.py`

```python
# Re-export para facilitar imports dentro do bridge
from intellicare_core.bridge.adapter import BaseHISAdapter
from intellicare_core.bridge.context import HISContext, HISSystem

__all__ = ["BaseHISAdapter", "HISContext", "HISSystem"]
```

### `intellicare-bridge/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY ../intellicare-core /deps/intellicare-core
COPY ../intellicare-auth /deps/intellicare-auth

RUN pip install --no-cache-dir -e /deps/intellicare-core -e /deps/intellicare-auth

COPY . .
RUN pip install --no-cache-dir -e .

EXPOSE 8000
CMD ["uvicorn", "bridge.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Adição ao `docker-compose.full.yml` (raiz do projeto)

```yaml
  intellicare-bridge:
    build:
      context: .
      dockerfile: ./intellicare-bridge/Dockerfile
    container_name: intellicare-bridge
    environment:
      - KEYCLOAK_URL=${KEYCLOAK_URL}
      - KEYCLOAK_REALM=intellicare
      - KEYCLOAK_CLIENT_ID=intellicare-bridge-dev
      - KEYCLOAK_CLIENT_SECRET=${BRIDGE_CLIENT_SECRET:-changeme}
      - GRAHAME_BASE_URL=http://intellicare-grahame:8000
      - WANDA_BASE_URL=http://intellicare-wanda:8000
      # Preencher quando adaptadores forem implementados:
      # FEEGOW_API_URL=https://api.feegow.com.br/api
      # FEEGOW_API_TOKEN=${FEEGOW_API_TOKEN:-}
    ports:
      - "8014:8000"
    networks:
      - intellicare-network
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.bridge.rule=Host(`bridge.intellicare.ia.br`)"
    depends_on:
      - intellicare-grahame
      - intellicare-wanda
```

---

## Variáveis de ambiente necessárias

| Variável | Módulo | Descrição | Obrigatória agora? |
|---|---|---|---|
| `BRIDGE_CLIENT_SECRET` | bridge | Secret do client `intellicare-bridge-dev` | Apenas para testes |
| `GRAHAME_BASE_URL` | bridge | URL interna do GRAHAME | Apenas para testes |
| `WANDA_BASE_URL` | bridge | URL interna do WANDA | Apenas para testes |
| `FEEGOW_API_URL` | bridge | API Feegow | Não (implementação futura) |
| `FEEGOW_API_TOKEN` | bridge | Token API Feegow | Não (implementação futura) |

---

## Pontos de atenção

**Autenticação no `$process-message`:** o endpoint exige role `HIS_ADAPTER`. Testar com service account `intellicare-bridge-dev` antes de declarar pronto.

**HISContext é opcional no `$process-message`:** o endpoint aceita bundles sem header `X-HIS-Context` (para compatibilidade futura com ingestões diretas). Tratar `None` sem erro.

**Redis consumer no WANDA:** verificar se o WANDA usa consumer groups ou listen simples. O evento `his_bundle_ingested` deve estar no group correto para não ser perdido se o WANDA reiniciar.

**Dockerfile do bridge:** o padrão de copiar `../intellicare-core` no build context requer que o build seja executado a partir da raiz do projeto (onde está o `docker-compose.full.yml`). Verificar se outros módulos usam o mesmo padrão.

**`HISAdapterRegistry` é in-memory:** em multi-processo (gunicorn com workers), cada worker tem seu próprio registry. O bridge deve usar apenas 1 worker por enquanto (stub não tem carga real). Anotar como limitação futura.
