# DEM-004 — Module Test Console no Admin

| Campo | Valor |
|---|---|
| **ID** | DEM-004 |
| **Título** | Painel de diagnóstico e teste de módulos no intellicare-admin |
| **Módulos** | intellicare-admin (8010) — backend + frontend React |
| **Prioridade** | 🟡 ALTA — ferramenta de controle operacional |
| **Status** | APROVADO |
| **Dev responsável** | dev2 |
| **Claude** | Spec aprovada + divergência resolvida em 2026-03-09 |
| **Eduardo** | ✅ Aprovado em 2026-03-09 |
| **Data abertura** | 2026-03-08 |
| **Branch** | `feature/admin-module-test-console` |
| **Depende de** | DEM-002 (admin funcional com auth) |
| **Spec Funcional** | [01_ESPECIFICACAO_FUNCIONAL.md](./01_ESPECIFICACAO_FUNCIONAL.md) |
| **Spec Técnica** | [02_ESPECIFICACAO_TECNICA.md](./02_ESPECIFICACAO_TECNICA.md) |
| **Plano de Impl.** | [03_PLANO_IMPLEMENTACAO.md](./03_PLANO_IMPLEMENTACAO.md) |

---

## Contexto

O admin já exibe o health de cada módulo (verde/vermelho). Isso detecta falhas
de processo (container caído, porta fechada), mas **não detecta falhas funcionais**
— um módulo pode responder 200 no health e estar completamente quebrado no
`/analyze`.

O Module Test Console dá ao administrador a capacidade de:
- Ver diagnóstico completo (health + info + latência) de todos os módulos em um lugar
- Disparar um teste funcional real em qualquer módulo com um payload pré-configurado
- Rodar sequências de teste de integração que cruzam múltiplos módulos
- Consultar histórico de testes para detectar regressões

Toda a comunicação com os módulos é feita **pelo backend do admin** (proxy
autenticado), não pelo frontend diretamente — evita CORS e garante que o token
PLATFORM_ADMIN seja propagado corretamente nos headers internos.

---

## Arquitetura da solução

```
Frontend React (porta 3003)
    │
    │  GET /api/v1/admin/modules
    │  GET /api/v1/admin/modules/{name}/probe
    │  POST /api/v1/admin/modules/{name}/test
    │  POST /api/v1/admin/integration-tests/run
    │  GET  /api/v1/admin/integration-tests/history
    ▼
Backend FastAPI (intellicare-admin, porta 8010)
    │   usa httpx.AsyncClient (já no pyproject.toml)
    │   propaga header: Authorization: Bearer <token interno>
    ▼
Módulos alvo
    GET  /api/v1/health    → HealthCheck
    GET  /api/v1/info      → ModuleInfo
    POST /api/v1/analyze   → AnalysisResponse
```

**Token interno:** o backend do admin usa um service account Keycloak
(`intellicare-admin-sa`) com client credentials grant para chamar os módulos.
Nunca propaga o token do usuário admin para outros módulos.

---

## Escopo — 3 fases incrementais

### FASE 1 — Probe Dashboard (MVP)
*Objetivo: visão unificada de saúde e info de todos os módulos.*

**Endpoint novo no admin:**
```
GET /api/v1/admin/modules
```
Retorna lista com todos os módulos conhecidos + resultado do probe em paralelo:

```json
[
  {
    "name": "florence",
    "display_name": "FLORENCE",
    "description": "RAG + Protocolos Clínicos",
    "base_url": "http://intellicare-florence:8000",
    "port": 8001,
    "probe": {
      "health": "healthy",
      "status_code": 200,
      "latency_ms": 42,
      "version": "2.1.0",
      "uptime_seconds": 86400,
      "dependencies": {"postgres": "ok", "redis": "ok"},
      "last_checked": "2026-03-08T16:00:00Z"
    }
  }
]
```

**Endpoint de probe individual:**
```
GET /api/v1/admin/modules/{name}/probe
```
Chama `/api/v1/health` e `/api/v1/info` do módulo em paralelo e retorna
o probe consolidado (mesmo schema acima).

**Frontend — página "Módulos":**
- Grid de cards, um por módulo
- Indicador visual: 🟢 healthy / 🟡 degraded / 🔴 unhealthy / ⚫ unreachable
- Latência em ms
- Versão e uptime
- Botão "Atualizar tudo" (re-probe em paralelo)
- Auto-refresh configurável (off / 30s / 60s / 5min)
- Filtro por status

---

### FASE 2 — Teste Funcional por Módulo
*Objetivo: testar o comportamento real do `/analyze` de cada módulo.*

**Endpoint novo no admin:**
```
POST /api/v1/admin/modules/{name}/test
```
Body: `{ "payload_key": "default" }` ou `{ "custom_payload": { ... } }`

O backend do admin:
1. Busca o payload pré-configurado para o módulo (ou usa o custom_payload)
2. Envia `POST /api/v1/analyze` para o módulo alvo via httpx
3. Mede latência
4. Persiste o resultado no histórico (tabela `module_test_log`)
5. Retorna resultado enriquecido:

```json
{
  "module": "oswaldo",
  "payload_key": "default",
  "request_sent_at": "2026-03-08T16:01:00Z",
  "latency_ms": 312,
  "status_code": 200,
  "success": true,
  "response": { ... },
  "error": null
}
```

**Payloads pré-configurados por módulo** (armazenados em
`admin/config/test_payloads.py`):

| Módulo | Payload default | O que testa |
|---|---|---|
| FLORENCE | `{ "query": "protocolo hipertensão arterial", "tenant_id": "test" }` | RAG funcional |
| OSWALDO | FHIR Patient bundle fictício (João Silva, 65 anos, HAS + DRC) | análise clínica |
| DONABEDIAN | `{ "tenant_id": "test", "period": "2026-01" }` | cálculo de indicadores |
| WANDA | `{ "query": "resumo paciente", "patient_id": "test-001" }` | orquestração básica |
| GERALDA | `{ "action": "get_support_options", "tenant_id": "test" }` | suporte ao paciente |
| COMUNICACAO | `{ "channel": "test", "dry_run": true, "to": "test@test.com" }` | envio dry_run |
| ZILDA | `{ "query": "CNES 0000001" }` | busca DATASUS |
| MINERVA | `{ "document_url": "https://example.com/test.pdf", "dry_run": true }` | extração doc |
| PIERRE | `{ "query": "hypertension treatment 2025", "max_results": 1 }` | busca PubMed |
| GRAHAME | `{ "resource_type": "Patient", "action": "validate", "resource": { ... } }` | validação FHIR |
| NISE | `{ "message": "olá", "session_id": "test-session" }` | chatbot básico |

**Frontend — painel expandido de cada módulo:**
- Aba "Diagnóstico" (Fase 1) + aba "Teste Funcional" (Fase 2)
- Dropdown de payloads pré-configurados
- Editor JSON (CodeMirror ou similar) para custom payload
- Botão "Executar Teste"
- Painel de resposta: status code, latência, JSON formatado com syntax highlight
- Indicador success/fail
- Link para histórico daquele módulo

---

### FASE 3 — Testes de Integração
*Objetivo: validar fluxos que cruzam múltiplos módulos.*

**Endpoint novo no admin:**
```
POST /api/v1/admin/integration-tests/run
Body: { "test_id": "basic_patient_flow" }

GET  /api/v1/admin/integration-tests
GET  /api/v1/admin/integration-tests/history?limit=20
```

**Testes de integração pré-definidos:**

**`basic_patient_flow`** — Fluxo básico de paciente
```
Passo 1: WANDA  → POST /analyze (intenção: "análise completa paciente test-001")
Passo 2: OSWALDO → POST /analyze (paciente FHIR fictício)
Passo 3: DONABEDIAN → POST /analyze (qualidade do atendimento)
Resultado esperado: resposta agregada com resumo clínico + indicadores
```

**`rag_protocol_search`** — Busca de protocolo clínico
```
Passo 1: FLORENCE → POST /analyze (query: "protocolo DRC estadio 3")
Passo 2: PIERRE   → POST /analyze (query: "chronic kidney disease stage 3 treatment")
Resultado esperado: protocolo local + referência científica
```

**`full_health_sweep`** — Varredura completa
```
Passo 1..N: probe de todos os módulos em paralelo
Resultado: relatório completo de saúde da plataforma
```

**Frontend — página "Testes de Integração":**
- Lista de testes disponíveis com descrição
- Botão "Executar"
- Visualização step-by-step: cada passo com status, latência, resposta colapsável
- Linha do tempo visual (Gantt simplificado) mostrando execução paralela vs. sequencial
- Exportar resultado como JSON

---

## Especificação técnica

### Backend — novos arquivos

```
intellicare-admin/
└── admin/
    ├── api/
    │   ├── module_probe_routes.py    ← Fase 1: probe + lista
    │   ├── module_test_routes.py     ← Fase 2: test funcional
    │   └── integration_test_routes.py ← Fase 3: flows
    ├── config/
    │   └── test_payloads.py          ← payloads pré-config por módulo
    ├── models/
    │   └── module_test_log.py        ← tabela histórico de testes
    └── services/
        └── module_proxy.py           ← httpx client com auth interno
```

### `admin/services/module_proxy.py`

```python
import httpx
from typing import Any

MODULE_REGISTRY: dict[str, str] = {
    "florence":    "http://intellicare-florence:8000",
    "oswaldo":     "http://intellicare-oswaldo:8000",
    "donabedian":  "http://intellicare-donabedian:8000",
    "wanda":       "http://intellicare-wanda:8000",
    "comunicacao": "http://intellicare-comunicacao:8000",
    "geralda":     "http://intellicare-geralda:8000",
    "zilda":       "http://intellicare-zilda:8000",
    "minerva":     "http://intellicare-minerva:8000",
    "pierre":      "http://intellicare-pierre:8000",
    "grahame":     "http://intellicare-grahame:8000",
    "nise":        "http://intellicare-nise:8000",
}

class ModuleProxyClient:
    """httpx client autenticado para chamadas internas admin → módulos."""

    def __init__(self, internal_token: str):
        self._token = internal_token
        self._headers = {
            "Authorization": f"Bearer {internal_token}",
            "X-Internal-Call": "intellicare-admin",
        }

    async def probe(self, module_name: str) -> dict[str, Any]:
        """Chama /health e /info em paralelo e retorna probe consolidado."""
        base = MODULE_REGISTRY[module_name]
        async with httpx.AsyncClient(timeout=5.0) as client:
            import asyncio, time
            start = time.monotonic()
            try:
                health_r, info_r = await asyncio.gather(
                    client.get(f"{base}/api/v1/health", headers=self._headers),
                    client.get(f"{base}/api/v1/info",   headers=self._headers),
                    return_exceptions=True,
                )
                latency_ms = int((time.monotonic() - start) * 1000)
                # ... montar e retornar dict consolidado
            except Exception as e:
                return {"health": "unreachable", "error": str(e), "latency_ms": -1}

    async def test_analyze(
        self, module_name: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Envia POST /analyze para o módulo e retorna resultado enriquecido."""
        base = MODULE_REGISTRY[module_name]
        async with httpx.AsyncClient(timeout=30.0) as client:
            import time
            start = time.monotonic()
            try:
                r = await client.post(
                    f"{base}/api/v1/analyze",
                    json=payload,
                    headers=self._headers,
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
                return {"status_code": 504, "success": False, "error": "timeout"}
```

### `admin/models/module_test_log.py`

```python
from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, func
from admin.db.base import Base

class ModuleTestLog(Base):
    __tablename__ = "module_test_log"

    id             = Column(Integer, primary_key=True)
    module_name    = Column(String(64), nullable=False, index=True)
    test_type      = Column(String(32), nullable=False)  # "probe"|"functional"|"integration"
    payload_key    = Column(String(64))
    status_code    = Column(Integer)
    latency_ms     = Column(Integer)
    success        = Column(Boolean)
    response_json  = Column(JSON)
    error_message  = Column(String(512))
    triggered_by   = Column(String(128))  # user sub do JWT
    created_at     = Column(DateTime(timezone=True), server_default=func.now(), index=True)
```

### Rotas novas no `app.py`

```python
from admin.api.module_probe_routes import router as probe_router
from admin.api.module_test_routes  import router as test_router
from admin.api.integration_test_routes import router as integration_router

app.include_router(probe_router,       prefix="/api/v1")
app.include_router(test_router,        prefix="/api/v1")
app.include_router(integration_router, prefix="/api/v1")
```

### Service account Keycloak (pré-requisito da Fase 2)

```
Realm: intellicare
Client: intellicare-admin-sa
  Access Type: confidential
  Service Accounts Enabled: true
  Service Account Roles: [módulos que precisam de auth internamente]
```

Segredo armazenado em `keycloak_client_secrets.json` ou env var
`ADMIN_SA_CLIENT_SECRET`.

---

## Frontend — componentes React

```
intellicare-admin-frontend/src/
└── pages/
    └── Diagnostico/
        ├── index.tsx                 ← roteamento da página
        ├── ModuleGrid.tsx            ← Fase 1: grid de cards
        ├── ModuleCard.tsx            ← card individual c/ probe
        ├── ModuleTestPanel.tsx       ← Fase 2: aba teste funcional
        ├── PayloadEditor.tsx         ← editor JSON com CodeMirror
        ├── ResponseViewer.tsx        ← viewer JSON formatado
        ├── IntegrationTests.tsx      ← Fase 3: lista + runner
        ├── IntegrationTestRunner.tsx ← step-by-step viewer
        └── TestHistory.tsx           ← histórico paginado
```

**Biblioteca sugerida para editor JSON:** `@uiw/react-codemirror` com
extensão `@codemirror/lang-json` (já disponível no npm, MIT license).

**Esquema de cores dos status:**

| Status | Cor | Critério |
|---|---|---|
| `healthy` | 🟢 verde | health 200 + latência < 500ms |
| `degraded` | 🟡 amarelo | health 200 + latência ≥ 500ms |
| `unhealthy` | 🔴 vermelho | health ≠ 200 |
| `unreachable` | ⚫ cinza | timeout / connection refused |

---

## Plano de implementação

### Sprint 1 — Fase 1 (estimativa: 1–2 dias)
- [x] `admin/services/module_proxy.py` com `probe()`
- [x] `admin/api/module_probe_routes.py` — `GET /modules` e `GET /modules/{name}/probe`
- [x] Registrar rotas no `app.py`
- [x] Frontend: `ModuleGrid.tsx` + `ModuleCard.tsx` com probe
- [x] Frontend: auto-refresh com intervalo configurável
- [x] Migração Alembic para tabela `module_test_log`

### Sprint 2 — Fase 2 (estimativa: 2–3 dias)
- [x] `admin/config/test_payloads.py` com todos os payloads default
- [x] `admin/services/module_proxy.py` — adicionar `test_analyze()`
- [x] `admin/api/module_test_routes.py` — `POST /modules/{name}/test`
- [x] Persistência no `module_test_log`
- [x] Service account Keycloak `intellicare-admin-sa`
- [x] Frontend: `ModuleTestPanel.tsx` + `PayloadEditor.tsx` + `ResponseViewer.tsx`
- [x] Frontend: `TestHistory.tsx` com paginação

### Sprint 3 — Fase 3 (estimativa: 2–3 dias)
- [x] `admin/config/integration_tests.py` com definição dos 3 flows
- [x] `admin/api/integration_test_routes.py` — `POST /admin/integration-flows/{flow_id}/run` + `GET /history`
- [x] Frontend: `IntegrationTests.tsx` + `IntegrationTestRunner.tsx`
- [x] Frontend: visualização step-by-step (Gantt simplificado)

---

## Log de execução

### 2026-03-08 — Sprint 1: Fase 1 — Probe Dashboard (dev2)

- `admin/services/module_proxy.py`: `ModuleProxyClient` com `probe()` usando `asyncio.gather()` em paralelo nos 11 módulos
- `admin/api/module_probe_routes.py`: `GET /api/v1/admin/modules` e `GET /api/v1/admin/modules/{name}/probe`
- Rotas registradas no `app.py`
- Frontend: `ModuleGrid.tsx` + `ModuleCard.tsx` com indicador visual 🟢🟡🔴⚫, latência ms, versão e uptime
- Auto-refresh configurável (off / 30s / 60s / 5min)
- Migração Alembic para tabela `module_test_log`
- Disponível em: `http://localhost:3003/admin/diagnostico`

### 2026-03-08 — Sprint 2: Fase 2 — Testes Funcionais e Histórico (dev2)

- `admin/config/test_payloads.py`: dicionário de payloads estáticos e realísticos para os 11 módulos (florence → protocolo hipertensão, wanda → resumo paciente, oswaldo → João Silva FHIR bundle, etc.)
- `admin/services/module_proxy.py`: `test_analyze()` intercepta status, latência e response; grava assincronamente no SQLAlchemy (`module_test_log`)
- `admin/api/module_test_routes.py`: `POST /api/v1/admin/modules/{name}/test` + `GET .../history`
- Frontend `ModuleTestPanel`: modal com layout de tabs — "Execução" (payload padrão ou JSON customizado + feedback visual ms/status + Show Payload) e "Histórico" (`ModuleTestHistory` com renderização cronológica, destacando custom/default e sucesso verde/vermelho)
- Verificado em `http://localhost:3003/admin/diagnostico` — modal interativa funcionando

### 2026-03-08 — Correção de branch (dev2)

Commits das Fases 1 e 2 estavam incorretamente na `fix/admin-gestor-auth` (branch do DEM-002).
`cherry-pick` executado para `feature/admin-module-test-console` derivada de `staging`. Branch correta.

### 2026-03-08 — Sprint 3: Fase 3 — Testes de Integração E2E (dev2)

- `admin/config/integration_tests.py`: motor de fluxos com os 3 testes definidos:
  - `basic_patient_flow` — cadeia sequencial WANDA → OSWALDO → DONABEDIAN, com short-circuit em falha
  - `rag_protocol_search` — busca clínica sequencial FLORENCE → PIERRE
  - `full_health_sweep` — varredura paralela de todos os módulos
- `admin/api/integration_test_routes.py`: endpoint `POST /admin/integration-flows/{flow_id}/run` com execução de steps em loop, modo sequencial com abortamento, e `GET /history`
- Frontend: página `/admin/diagnostico` com abas "Módulos Individuais" e "Esteiras de Integração E2E"
- `IntegrationTestRunner`: visualização step-by-step com status por módulo, latência total, log individual colapsável e Gantt simplificado
- Docs: `walkthrough.md` atualizado com as melhorias do DEM-004 Fases 1–3
- Verificado em `http://localhost:3003/admin/diagnostico` — fluxos E2E funcionando

### 2026-03-09 — Revisão e resolução de divergência (Claude)

**Divergência identificada:** dev2 implementou as rotas de integração com o prefixo `integration-flows` e `flow_id` como path param, enquanto a spec DEM-004 definia `integration-tests` com `test_id` no body. Além disso, o endpoint `GET /admin/integration-tests/history` estava ausente.

**Resolução aplicada** em `admin/api/integration_test_routes.py`:
- Lógica de execução extraída para função privada `_execute_flow(flow_id)` — reutilizada por ambos os grupos de rotas
- **Mantidas** as rotas `integration-flows` (usadas pelo frontend atual — nenhuma quebra)
- **Adicionadas** as rotas canônicas da spec como aliases backward-compat:
  - `GET  /api/v1/admin/integration-tests` → lista flows (alias de `/integration-flows`)
  - `POST /api/v1/admin/integration-tests/run` com body `{"test_id": "..."}` → executa flow
  - `GET  /api/v1/admin/integration-tests/history?limit=N` → histórico de execuções de integração (endpoint **novo**, faltava na entrega do dev2)

**Impacto:** zero quebra. Frontend continua usando `/integration-flows`. Clientes que seguirem a spec DEM-004 também funcionam.

---

## Revisão

**Resultado:** ✅ APROVADO

**Eduardo:** Aprovado. A resolução backward-compat é a abordagem correta — mantém o frontend funcionando e adiciona o endpoint de histórico que estava faltando. O pattern de alias é aceitável para este tipo de divergência de naming.

---

## Aprendizados

- Quando o dev implementa URLs diferentes da spec mas também entrega o frontend usando as mesmas URLs, o sistema fica internamente consistente — porém quebra a spec. A resolução correta é adicionar aliases backward-compat, não reescrever.
- O endpoint de histórico (`/history`) não deve ser esquecido — faz parte do ciclo de auditoria e é necessário para detectar regressões ao longo do tempo.
- O `test_id` no body (spec) vs. `flow_id` no path (dev2): ambos têm mérito — path param é mais RESTful para recursos identificáveis; body param facilita extensibilidade futura (parâmetros extras). Manter os dois como aliases é a solução pragmática.
