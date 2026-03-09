# DEM-005 — Preparação das Portas de Integração (intellicare-bridge)

| Campo | Valor |
|---|---|
| **ID** | DEM-005 |
| **Título** | Preparar gatilhos e portas de integração para futuros adaptadores HIS |
| **Módulos** | intellicare-core · intellicare-grahame · intellicare-wanda · intellicare-auth · docker |
| **Prioridade** | 🟡 ALTA — habilita versão futura sem refatoração |
| **Status** | APROVADO |
| **Dev responsável** | dev3 |
| **Claude** | Spec aprovada |
| **Eduardo** | ✅ Aprovado em 2026-03-09 |
| **Data abertura** | 2026-03-08 |
| **Branch** | `feature/bridge-integration-prep` |
| **Depende de** | DEM-002 (auth estável) |
| **Habilita** | intellicare-bridge (versão futura — Tasy, MV, TOTVS, Feegow, Pixeon) |
| **Spec Funcional** | [01_ESPECIFICACAO_FUNCIONAL.md](./01_ESPECIFICACAO_FUNCIONAL.md) |
| **Spec Técnica** | [02_ESPECIFICACAO_TECNICA.md](./02_ESPECIFICACAO_TECNICA.md) |
| **Plano de Impl.** | [03_PLANO_IMPLEMENTACAO.md](./03_PLANO_IMPLEMENTACAO.md) |

---

## Contexto

A proposta de arquitetura de integração dinâmica prevê adaptadores HIS que
traduzem APIs proprietárias (Philips Tasy, SOUL MV, TOTVS, Feegow, Pixeon)
para o padrão FHIR R4 do IntelliCare.

**A boa notícia:** o IntelliCare já tem mais da metade da infraestrutura
necessária implementada e funcionando:

| Componente necessário | Status atual |
|---|---|
| FHIR R4 Server (receptor de dados) | ✅ **GRAHAME** já implementado |
| SMART on FHIR 2.0 | ✅ **intellicare-auth** já implementado |
| EHR Launch (`/smart/launch` com `launch` + `iss`) | ✅ **GRAHAME smart_routes.py** já implementado |
| CDS Hooks 2.0 | ✅ **GRAHAME cds_hooks_routes.py** já implementado |
| HL7v2 ingestão | ✅ **GRAHAME hl7v2_routes.py** já implementado |
| Orquestrador multi-agent | ✅ **WANDA** já implementado |
| RAG clínico | ✅ **FLORENCE** já implementado |

**O que falta para os adaptadores poderem ser conectados no futuro:**
1. `HISContext` — modelo padronizado de contexto que vem do HIS
2. Endpoint de ingestão em batch (`POST /fhir/$process-message`) no GRAHAME
3. Propagação do contexto HIS pelo WANDA para todos os agentes
4. `BaseHISAdapter` — contrato que todo adaptador HIS deve implementar
5. Role Keycloak `HIS_ADAPTER` + service account por HIS
6. Módulo stub `intellicare-bridge` com porta reservada (8014)

Esta demanda **não implementa nenhum adaptador real**. Prepara as portas
para que o bridge possa ser conectado sem refatoração quando chegar a hora.

---

## Arquitetura-alvo (com bridge conectado)

```
HIS Externo (Tasy / MV / Feegow / ...)
    │
    │  1. EHR Launch: GET /smart/launch?launch=TOKEN&iss=HIS_URL
    │  2. OAuth2 token com scope: launch/patient launch/encounter
    │  3. HISContext propagado nos headers internos
    ▼
intellicare-bridge (porta 8014) ← FUTURO
    │  BaseHISAdapter implementado por: TasyAdapter, FeegoAdapter, ...
    │  Traduz HIS proprietário → FHIR R4 Bundle
    ▼
GRAHAME (8012) ← JÁ EXISTE
    │  POST /api/v1/fhir/$process-message  ← NOVO (esta demanda)
    │  GET  /api/v1/fhir/Patient/{id}
    │  POST /api/v1/fhir/Observation
    │  GET  /api/v1/smart/launch           ← JÁ EXISTE
    │  POST /api/v1/cds-hooks/{hook-id}    ← JÁ EXISTE
    ▼
WANDA (8004) ← JÁ EXISTE
    │  Reconhece X-HIS-Context header     ← NOVO (esta demanda)
    │  Propaga contexto para agentes
    ▼
Agentes (OSWALDO, FLORENCE, DONABEDIAN, ...)
```

---

## Escopo detalhado

### FASE 1 — intellicare-core: pacote `bridge`
*Objetivo: definir o contrato e o modelo de contexto HIS.*

**Novo pacote:** `intellicare_core/bridge/`

```
intellicare_core/bridge/
├── __init__.py
├── context.py      ← HISContext (modelo Pydantic)
├── adapter.py      ← BaseHISAdapter (ABC)
└── registry.py     ← HISAdapterRegistry (discovery)
```

**`context.py` — HISContext:**

```python
from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, Field

class HISSystem(str, Enum):
    TASY      = "philips_tasy"
    SOUL_MV   = "soul_mv"
    TOTVS     = "totvs_rm"
    FEEGOW    = "feegow"
    PIXEON    = "pixeon"
    SISHQSP   = "sishosp"
    OPENEMR   = "openemr"
    UNKNOWN   = "unknown"

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
        import base64, json
        return base64.b64encode(self.model_dump_json().encode()).decode()

    @classmethod
    def from_header(cls, header_value: str) -> "HISContext":
        """Desserializa do header X-HIS-Context."""
        import base64, json
        data = json.loads(base64.b64decode(header_value).decode())
        return cls(**data)
```

**`adapter.py` — BaseHISAdapter:**

```python
from abc import ABC, abstractmethod
from typing import Any
from intellicare_core.bridge.context import HISContext

class BaseHISAdapter(ABC):
    """Contrato que todo adaptador HIS deve implementar.

    Cada HIS (Tasy, Feegow, MV...) terá sua própria implementação
    neste intellicare-bridge que traduz a API proprietária para FHIR R4.
    """

    @property
    @abstractmethod
    def his_system(self) -> str:
        """Identificador do sistema (ex: 'philips_tasy')."""
        ...

    @abstractmethod
    async def resolve_launch_context(
        self, launch_token: str, iss: str
    ) -> HISContext:
        """Resolve o launch token do EHR Launch em HISContext completo."""
        ...

    @abstractmethod
    async def get_patient_bundle(
        self, context: HISContext
    ) -> dict[str, Any]:
        """Retorna FHIR Bundle com dados do paciente (Patient + Conditions +
        Observations + MedicationRequests) traduzidos da API do HIS."""
        ...

    @abstractmethod
    async def push_cds_card(
        self, context: HISContext, card: dict[str, Any]
    ) -> bool:
        """Envia um CDS Hook card de volta para o HIS (se suportado)."""
        ...

    async def validate_connection(self) -> bool:
        """Testa conectividade com o HIS. Implementação default: False."""
        return False
```

**`registry.py` — HISAdapterRegistry:**

```python
from intellicare_core.bridge.adapter import BaseHISAdapter

class HISAdapterRegistry:
    """Registro de adaptadores HIS disponíveis.

    Cada adaptador registra a si mesmo ao ser importado.
    O intellicare-bridge registra os adaptadores no startup.
    """
    _adapters: dict[str, BaseHISAdapter] = {}

    @classmethod
    def register(cls, adapter: BaseHISAdapter) -> None:
        cls._adapters[adapter.his_system] = adapter

    @classmethod
    def get(cls, his_system: str) -> BaseHISAdapter | None:
        return cls._adapters.get(his_system)

    @classmethod
    def list_available(cls) -> list[str]:
        return list(cls._adapters.keys())
```

---

### FASE 2 — GRAHAME: endpoint `$process-message`
*Objetivo: porta de entrada para bundles vindos dos adaptadores HIS.*

O GRAHAME já aceita recursos FHIR individuais (`POST /fhir/Patient`,
`POST /fhir/Observation`, etc.). Falta um endpoint de **ingestão em batch**
que receba um FHIR `Bundle` completo de uma vez — padrão usado por adaptadores.

**Novo endpoint em `grahame/api/routes/fhir_native_routes.py`:**

```python
@router.post(
    "/$process-message",
    summary="Ingestão de FHIR Bundle (adaptadores HIS)",
    status_code=202,
    tags=["Bridge"],
)
async def process_message_bundle(
    bundle: dict[str, Any],
    request: Request,
    session: AsyncSession = Depends(get_db),
    _: dict = Depends(require_his_adapter),   # role HIS_ADAPTER
) -> dict[str, Any]:
    """Recebe um FHIR Bundle transaction/batch de um adaptador HIS.

    Processa cada entry do bundle:
    - Patient → upsert na tabela fhir_resources
    - Observation → upsert com subject reference
    - Condition, MedicationRequest, etc. → upsert genérico

    Publica evento no Redis para WANDA processar de forma assíncrona.

    Retorno: Bundle de respostas (OperationOutcome por entry).
    """
    his_context_header = request.headers.get("X-HIS-Context")
    his_context = HISContext.from_header(his_context_header) \
                  if his_context_header else None

    results = []
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        resource_type = resource.get("resourceType", "Unknown")
        # ... processar cada resource via FHIRService existente
        results.append({
            "resourceType": "OperationOutcome",
            "issue": [{"severity": "information", "code": "informational",
                        "diagnostics": f"{resource_type} processado"}]
        })

    # Publicar evento no Redis para WANDA
    if his_context:
        await _publish_his_event(his_context, bundle, session)

    return {
        "resourceType": "Bundle",
        "type": "transaction-response",
        "entry": [{"resource": r} for r in results],
    }
```

**Novo dep `require_his_adapter`** em `grahame/api/deps.py`:
```python
async def require_his_adapter(payload: dict = Depends(require_role("HIS_ADAPTER"))):
    return payload
```

---

### FASE 3 — WANDA: propagação de HISContext
*Objetivo: WANDA reconhece a origem HIS e propaga para os agentes.*

**Mudança em `wanda/api/middleware.py` (ou equivalente):**

```python
# Ao receber requisição com X-HIS-Context:
his_context_header = request.headers.get("X-HIS-Context")
if his_context_header:
    request.state.his_context = HISContext.from_header(his_context_header)
```

**Mudança no router de intenções do WANDA:**

```python
# No intent router, se vier com HISContext:
# - patient_id já vem resolvido (fhir_patient_id do HISContext)
# - tenant_id já vem no HISContext
# - adicionar ao AnalysisRequest: parameters["his_context"] = his_context.dict()
# - propagar X-HIS-Context para calls internas a OSWALDO, FLORENCE, etc.
```

**Novo evento Redis publicado pelo GRAHAME → consumido pelo WANDA:**

```
Stream: intellicare:events:his_ingestion
Payload: {
  "event_type": "his_bundle_ingested",
  "his_system": "feegow",
  "tenant_id": "...",
  "fhir_patient_id": "...",
  "encounter_id": "...",
  "bundle_entry_count": 12,
  "timestamp": "..."
}
```

WANDA reage a este evento iniciando um workflow de análise automática
do paciente recém-ingerido (OSWALDO → DONABEDIAN).

---

### FASE 4 — intellicare-auth: role e service accounts HIS
*Objetivo: autenticação dos adaptadores no realm `intellicare`.*

**No Keycloak realm `intellicare`:**

```
Nova role realm: HIS_ADAPTER
  Permissões: chamar GRAHAME /$process-message
              chamar WANDA /api/v1/analyze

Um service account por HIS planejado:
  Client: intellicare-bridge-feegow     (confidential, service account)
  Client: intellicare-bridge-tasy       (confidential, service account)
  Client: intellicare-bridge-mv         (confidential, service account)
  [criar apenas quando o adaptador for implementado]

Por ora: criar apenas intellicare-bridge-dev para testes
```

---

### FASE 5 — Módulo stub `intellicare-bridge`
*Objetivo: reservar porta, estrutura e contrato — sem implementação real.*

**Estrutura do diretório:**

```
intellicare-bridge/
├── bridge/
│   ├── api/
│   │   ├── app.py          ← FastAPI com /health /info e stub /analyze
│   │   └── adapter_routes.py ← endpoints de teste de adaptador
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── base.py         ← re-export de intellicare_core.bridge.adapter
│   │   └── feegow/         ← MVP futuro (primeiro a implementar)
│   │       └── __init__.py
│   └── config.py
├── pyproject.toml          ← depende de intellicare-core e intellicare-auth
├── Dockerfile
└── docker-compose.yml      ← porta 8014:8000
```

**`bridge/api/app.py` — stub funcional:**

```python
"""intellicare-bridge — Adaptadores HIS para FHIR R4.

Status: STUB — módulo estruturado, aguardando implementação dos adaptadores.
Porta: 8014

Adaptadores planejados:
  - Feegow (MVP — API REST v1.0, Token-based)
  - Philips Tasy (API HTML5 / SOAP / REST)
  - SOUL MV (Plataforma de Interoperabilidade MV)
  - TOTVS RM (API REST documentada)
  - Pixeon / SisHOSP (barramento / APIs locais)
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from intellicare_core.contracts import ModuleInfo, HealthCheck
from intellicare_core.bridge.registry import HISAdapterRegistry

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Futuramente: importar e registrar adaptadores aqui
    # from bridge.adapters.feegow import FeegoAdapter
    # HISAdapterRegistry.register(FeegoAdapter())
    yield

app = FastAPI(
    title="intellicare-bridge",
    description="Adaptadores HIS → FHIR R4",
    version="0.1.0-stub",
    lifespan=lifespan,
)

@app.get("/api/v1/health")
async def health() -> dict:
    return HealthCheck(
        status="healthy",
        module="intellicare-bridge",
        details={"adapters_loaded": HISAdapterRegistry.list_available()},
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
    """Lista adaptadores HIS disponíveis (registrados)."""
    return {
        "registered": HISAdapterRegistry.list_available(),
        "planned": ["feegow", "philips_tasy", "soul_mv", "totvs_rm", "pixeon"],
    }
```

**Adição ao `docker-compose.full.yml`:**

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
      # Adaptadores HIS (preenchidos quando implementados):
      # FEEGOW_API_URL=https://api.feegow.com.br/api
      # FEEGOW_API_TOKEN=${FEEGOW_API_TOKEN:-}
      # TASY_BASE_URL=${TASY_BASE_URL:-}
      # MV_BASE_URL=${MV_BASE_URL:-}
    ports:
      - "8014:8000"
    networks:
      - intellicare-network
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.bridge.rule=Host(`bridge.intellicare.ia.br`)"
```

---

## Ordem de prioridade para implementação dos adaptadores

Quando chegar a hora de implementar os adaptadores reais, esta é a sequência recomendada:

**1º — Feegow** (MVP)
API REST v1.0 com token estático. Mais simples. Boa para validar o fluxo end-to-end de EHR Launch → FHIR Bundle → GRAHAME → WANDA.

**2º — TOTVS RM**
API REST bem documentada no portal TOTVS Developers. Segundo em maturidade digital.

**3º — SOUL MV**
Plataforma de Interoperabilidade MV com foco em FHIR. Terceiro por complexidade.

**4º — Philips Tasy**
SOAP/REST híbrido. Mais complexo. Alta penetração em hospitais públicos.

**5º — Pixeon / SisHOSP**
Requer adaptadores de barramento local. Implementar por demanda de cliente.

---

## Checklist de implementação

### Sprint 1 — Core + GRAHAME (2–3 dias)
- [x] Criar `intellicare_core/bridge/__init__.py`
- [x] Criar `intellicare_core/bridge/context.py` — `HISContext` + `HISSystem`
- [x] Criar `intellicare_core/bridge/adapter.py` — `BaseHISAdapter`
- [x] Criar `intellicare_core/bridge/registry.py` — `HISAdapterRegistry`
- [x] Adicionar `bridge` ao `__init__.py` do intellicare-core
- [x] Adicionar endpoint `POST /fhir/$process-message` no GRAHAME
- [x] Adicionar `require_his_adapter` dep em GRAHAME
- [x] Testes unitários do HISContext (serialização / deserialização de header)

### Sprint 2 — WANDA + Auth (2 dias)
- [x] Adicionar leitura e injeção de `X-HIS-Context` no WANDA
- [x] Adicionar publicação do evento `his_bundle_ingested` no GRAHAME
- [x] Adicionar consumer do evento `his_bundle_ingested` no WANDA
- [x] Criar role `HIS_ADAPTER` no Keycloak realm `intellicare`
- [x] Criar client `intellicare-bridge-dev` com service account
- [x] Testar: bridge-dev autentica → token HIS_ADAPTER

### Sprint 3 — Módulo stub + Docker (1–2 dias)
- [x] Criar diretório `intellicare-bridge/` com estrutura completa
- [x] Implementar `bridge/api/app.py` stub funcional
- [x] `pyproject.toml` com dependências corretas
- [x] `Dockerfile` baseado no padrão dos outros módulos
- [x] Adicionar serviço ao `docker-compose.full.yml`
- [x] Adicionar ao `scripts/smoke_test.sh`
- [x] Health endpoint respondendo 200 com lista de adapters (vazia no stub)

---

## Log de execução

### 2026-03-08 — Sprint 1: intellicare-core pacote `bridge` + GRAHAME `$process-message` (dev3)

- Criado `intellicare_core/bridge/` com `__init__.py`, `context.py` (`HISContext`, `HISSystem`), `adapter.py` (`BaseHISAdapter`), `registry.py` (`HISAdapterRegistry`)
- Adicionado `bridge` ao `__init__.py` do intellicare-core
- Adicionado endpoint `POST /api/v1/fhir/$process-message` em `grahame/api/routes/bridge_routes.py`
- Adicionada dep `require_his_adapter` em `grahame/api/deps.py`
- Testes unitários do `HISContext` (serialização/deserialização de header base64) passando

### 2026-03-08 — Sprint 2: WANDA propagação HISContext + consumer Redis (dev3)

- `wanda/api/app.py`: import de `Request` corrigido; `_get_his_context()` lê header `X-HIS-Context` e injeta `HISContext` no contexto da requisição; endpoint `/api/v1/chat` repassa `his_context` para `orchestrator.chat()`
- `wanda/orchestrator/orchestrator.py`: `chat()` passa a aceitar `his_context` como parâmetro; `_call_module_for_query()` e `_resolve_endpoint()` propagam `his_context` em `parameters` para o OSWALDO; `patient_id` obtido de `his_context.fhir_patient_id` quando ausente na requisição
- Consumer Redis registrado para stream `intellicare:events:his_ingestion`
- Keycloak local atualizado: role `HIS_ADAPTER` + client `intellicare-bridge-dev` com service account

### 2026-03-08 — Sprint 3: Módulo stub `intellicare-bridge` + Docker (dev3)

- Criado `intellicare-bridge/` com estrutura completa:
  - `bridge/api/app.py` — FastAPI com `/api/v1/health`, `/api/v1/info`, `/api/v1/bridge/adapters`
  - `bridge/adapters/base.py` — re-export de `BaseHISAdapter`, `HISContext`, `HISSystem`
  - `bridge/adapters/feegow/__init__.py` — vazio (implementação futura)
  - `bridge/config.py` — `GRAHAME_BASE_URL` e `WANDA_BASE_URL`
  - `pyproject.toml` e `Dockerfile`
- `docker-compose.full.yml`: serviço `bridge` porta 8014, dependendo de grahame e wanda
- `scripts/smoke_test.sh` e `scripts/smoke_tests.py`: health check do bridge incluídos

**Verificações realizadas pelo dev3:**

| Verificação | Resultado | Status |
|---|---|---|
| Bridge sobe em `http://localhost:8014` | OK | ✅ |
| `GET /api/v1/health` | 200 `{"mode": "stub", ...}` | ✅ |
| `GET /api/v1/bridge/adapters` | 200 `{"registered": [], "planned": [...]}` | ✅ |

### 2026-03-09 — Sprint 5: Keycloak local (concluído)

Checagem e criação realizadas no ambiente **LOCAL** (`http://localhost:8080`, realm `intellicare`):

| Verificação | Resultado | Status |
|---|---|---|
| Realm role `HIS_ADAPTER` existe | Sim | ✅ |
| Client `intellicare-bridge-dev` existe | Sim | ✅ |
| Service account com role `HIS_ADAPTER` | Sim | ✅ |
| Token `client_credentials` com claim `HIS_ADAPTER` | Sim | ✅ |

Artefato gerado:
- `intellicare-bridge/keycloak_client_secrets.json`

---

## Revisão

### 2026-03-09 — Revisão Eduardo

**Auth/Keycloak:** ✅ Resolvido — role `HIS_ADAPTER` funcionando.

**Bug identificado — `$process-message` não registrado no GRAHAME:**

O endpoint `POST /api/v1/fhir/$process-message` foi criado em `grahame/api/routes/bridge_routes.py` mas o router **não foi incluído** no `app.py` do GRAHAME. O app não carrega a rota e por isso a operação não aparece nem no OpenAPI (`/docs`) nem no runtime.

**Correção necessária (dev3):** em `grahame/api/app.py`, adicionar:

```python
from grahame.api.routes.bridge_routes import router as bridge_router

app.include_router(bridge_router, prefix="/api/v1/fhir")
```

Verificar após o fix:
```bash
curl http://localhost:8012/api/v1/fhir/\$process-message   # deve retornar 422 (falta body), não 404
curl http://localhost:8012/docs                             # deve listar o endpoint em "Bridge"
```

**Status da revisão:** 🔴 `BLOQUEADO` até o fix do registro do router.

### 2026-03-09 — Follow-up técnico (desenv local)

Correções e validações executadas **somente em ambiente local**:

- Confirmado include do `bridge_router` sem duplicar prefixo (router já usa `prefix="/api/v1/fhir"`)
- Ajustado `grahame/api/deps.py`: implementado `require_his_adapter` com fallback local para leitura de claims JWT quando helper `require_role` não estiver disponível
- Validado Keycloak local (`realm intellicare` + client `intellicare-bridge-dev`)

Resultados de teste local (`localhost:18113`):

| Verificação | Resultado | Status |
|---|---|---|
| `POST /api/v1/fhir/$process-message` sem token | `401` (Missing bearer token) | ✅ |
| `POST /api/v1/fhir/$process-message` com token `HIS_ADAPTER` e sem body | `422` (Field required) | ✅ |
| OpenAPI contém `/api/v1/fhir/$process-message` | Sim | ✅ |
| Endpoint listado com tag `Bridge` | Sim | ✅ |

**Status da revisão:** ✅ `DESBLOQUEADO` — fix confirmado por dev3 em 2026-03-09.

### 2026-03-09 — Aprovação final (Eduardo)

Fix validado:
- Linha 30: `from .routes.bridge_routes import router as bridge_router`
- Linha 230: `app.include_router(bridge_router)`
- `POST /api/v1/fhir/$process-message` aparece na tag Bridge em `/docs` ✅

✅ **APROVADO** — DEM-005 concluída.

---

## Aprendizados

*(Preenchido após conclusão)*

---

## Referências

- [Proposta de Arquitetura de Integração Dinâmica](../../../../docs/INTEGRACAO/🏥%20Proposta%20de%20Arquitetura%20de%20Integração%20Dinâmica_%20INTELLICARE.md)
- [SMART App Launch 2.0](https://hl7.org/fhir/smart-app-launch/)
- [FHIR R4 Bundle transaction](https://hl7.org/fhir/http.html#transaction)
- [CDS Hooks 2.0](https://cds-hooks.org/)
- [Feegow API v1.0](https://api.feegow.com.br/api/docs)
- [TOTVS Developers](https://developers.totvs.com)
