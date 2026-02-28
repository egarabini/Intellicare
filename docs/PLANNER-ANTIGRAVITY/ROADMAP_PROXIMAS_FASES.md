# Roadmap — Próximas Fases IntelliCare
**Gerado:** 2026-02-22
**Versão atual:** 1.1.0

---

## Legenda

| Símbolo | Significado |
|---------|-------------|
| 🔴 | Bloqueador — afeta outros itens |
| 🟠 | Alta prioridade |
| 🟡 | Média prioridade |
| ✅ | Pré-requisito já satisfeito |
| ⚙️ | Tarefa técnica |
| 🧪 | Tarefa de testes |
| 📦 | Tarefa de entrega/deploy |

---

# NÍVEL 1 — Desbloqueadores Críticos

---

## FASE 1.1 — Comunicacao: Correção e Finalização (DEV2)

**Módulo:** `intellicare-comunicacao` (porta 8005)
**Responsável:** DEV2
**Prioridade:** 🔴 BLOQUEADOR

### Contexto
O módulo Comunicacao tem **Fases 1–5 implementadas** (Rocket.Chat, WhatsApp/WAHA, SMS, Email, Jitsi, routing engine, templates, fallback/retry, Redis consumer, Prometheus). O que resta é corrigir erros de dependência e finalizar testes quebrados.

### 1.1.A — Corrigir dependências e erros de coleta de testes

**Problema:** 11 arquivos de teste falham na coleta com `ModuleNotFoundError: No module named 'email_validator'`

**Tarefas:**

- [ ] ⚙️ Adicionar `email-validator` ao `pyproject.toml` em `[project.dependencies]`
  ```toml
  "email-validator>=2.1.0",
  ```
- [ ] ⚙️ Re-executar `pip install -e ".[dev]"` no venv
- [ ] 🧪 Verificar coleta: `pytest --co -q` deve mostrar **0 errors**

**Arquivos afetados:**
- `pyproject.toml` — adicionar dependência
- Nenhum código Python precisa mudar

---

### 1.1.B — Corrigir 4 testes falhando

Após 1.1.A, executar suite completa. Testes com falha conhecida:

| Teste | Erro | Ação |
|-------|------|------|
| `test_sms/test_dispatcher.py::test_get_status` | `sqlalchemy.exc.ArgumentError` | Verificar setup da sessão no fixture |
| `test_sms/test_providers.py::test_twilio_send` | `TypeError: 'coroutine'` | Adicionar `await` ou marcar teste como `async` |
| `test_sms/test_providers.py::test_zenvia_send` | `TypeError: 'coroutine'` | Idem |
| `test_whatsapp/test_webhook.py::test_handle_status_update` | `sqlalchemy.exc.ArgumentError` | Verificar fixture de sessão |

**Tarefas:**

- [ ] ⚙️ Inspecionar fixtures em `tests/conftest.py` — session factory para testes
- [ ] ⚙️ Para testes async: garantir `@pytest.mark.asyncio` + `async def test_...`
- [ ] 🧪 `pytest -q` deve atingir **≥ 80% cobertura** e **0 falhas**

---

### 1.1.C — Smoke test de integração Comunicacao

**Pré-requisito:** Rocket.Chat e WAHA rodando (já deployados)

**Tarefas:**

- [ ] 📦 `docker compose up` no diretório `intellicare-comunicacao/`
- [ ] 📦 `curl http://localhost:8005/api/v1/health` → `{"status": "healthy"}`
- [ ] 📦 `curl http://localhost:8005/api/v1/info` → versão e descrição
- [ ] 📦 Verificar conexão com Rocket.Chat: `GET /api/v1/channels` retorna canais
- [ ] 📦 Verificar conexão com WAHA: `GET /api/v1/whatsapp/status` retorna sessão ativa
- [ ] 📦 Enviar mensagem de teste via Rocket.Chat (endpoint real)

**Critérios de aceite:**
- Health check 200
- Mensagem enviada via RC aparece na interface
- Logs sem erros de conexão

---

## FASE 1.2 — GERALDA v2.0 Fase 1: Persistência PostgreSQL (DEV0)

**Módulo:** `intellicare-geralda` (porta 8006)
**Responsável:** DEV0
**Prioridade:** 🔴 BLOQUEADOR
**Spec:** `intellicare-geralda/docs/specs/fase-01-fundacao-persistencia/EF-001_PERSISTENCIA_POSTGRESQL.md`

### Contexto
Geralda v1.0 usa dicionários em memória (`_plans`, `_tasks`, `_reminders`). Todo restart perde dados. Esta fase migra para PostgreSQL.

### 1.2.A — Modelos SQLAlchemy + Alembic

**Tarefas:**

- [ ] ⚙️ Criar `geralda/models/care_plan.py` — modelo `CarePlan`
  ```python
  # Tabela: care_plans
  # Colunas: id (UUID PK), patient_id, patient_name, conditions (JSONB),
  #          goals (JSONB), active (bool), created_at, updated_at,
  #          created_by, deactivated_at, deactivation_reason
  # Índices: idx_care_plans_patient_id, idx_care_plans_active
  ```

- [ ] ⚙️ Criar `geralda/models/care_task.py` — modelo `CareTask`
  ```python
  # Tabela: care_tasks
  # Colunas: id (UUID PK), plan_id (FK), patient_id, title, description,
  #          category (enum), status (enum), due_date, due_time,
  #          completed_at, completed_by, notes, created_at, recurrence_rule
  # Índices: idx_care_tasks_plan_id, idx_care_tasks_patient_id,
  #          idx_care_tasks_status, idx_care_tasks_due_date
  ```

- [ ] ⚙️ Criar `geralda/models/reminder.py` — modelo `Reminder`
  ```python
  # Tabela: reminders
  # Colunas: id (UUID PK), plan_id (FK), patient_id, task_id (FK nullable),
  #          message, scheduled_at, sent_at, channel, status
  ```

- [ ] ⚙️ Criar `geralda/models/educational_material.py` — modelo `EducationalMaterial`
  ```python
  # Tabela: educational_materials
  # Colunas: id (UUID PK), plan_id (FK), patient_id, title, content,
  #          category, condition_codes (JSONB), language, created_at
  ```

- [ ] ⚙️ Criar `geralda/models/__init__.py` — exportar todos os modelos
- [ ] ⚙️ Gerar migração Alembic: `alembic revision --autogenerate -m "initial_geralda_tables"`
- [ ] ⚙️ Aplicar migração: `alembic upgrade head`
- [ ] ⚙️ Atualizar `geralda/api/app.py` — lifespan cria engine PostgreSQL (igual padrão dos outros módulos)

---

### 1.2.B — Refatorar serviços para usar PostgreSQL

**Tarefas:**

- [ ] ⚙️ Criar `geralda/services/care_plan_service.py` — substituir lógica in-memory
  ```python
  # Funções: create_plan(), get_plan(), list_plans_by_patient(),
  #          update_plan(), deactivate_plan()
  # Usar AsyncSession do SQLAlchemy
  ```

- [ ] ⚙️ Criar `geralda/services/care_task_service.py`
  ```python
  # Funções: create_task(), get_task(), list_tasks_by_plan(),
  #          complete_task(), skip_task(), list_overdue_tasks()
  ```

- [ ] ⚙️ Criar `geralda/services/reminder_service.py`
  ```python
  # Funções: schedule_reminder(), list_pending_reminders(),
  #          mark_sent(), cancel_reminder()
  ```

- [ ] ⚙️ Criar `geralda/database/deps.py` — `get_db()` dependency (igual padrão grahame)
  ```python
  async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
      async with request.app.state.session_factory() as session:
          yield session
  ```

- [ ] ⚙️ Atualizar rotas em `geralda/api/routes/` — injetar `db: AsyncSession = Depends(get_db)` em vez de usar dicionários

---

### 1.2.C — Testes PostgreSQL (SQLite in-memory para CI)

**Tarefas:**

- [ ] ⚙️ Criar `tests/conftest.py` com fixture de sessão (SQLite in-memory, igual padrão grahame)
  ```python
  @pytest_asyncio.fixture
  async def session() -> AsyncGenerator[AsyncSession, None]:
      engine = create_async_engine("sqlite+aiosqlite:///:memory:")
      async with engine.begin() as conn:
          await conn.run_sync(Base.metadata.create_all)
      async with AsyncSession(engine) as s:
          yield s
  ```

- [ ] 🧪 Criar `tests/test_care_plan_service.py` — mínimo 10 testes:
  - criar plano, listar por paciente, desativar, verificar campo `active`
- [ ] 🧪 Criar `tests/test_care_task_service.py` — mínimo 10 testes:
  - criar tarefa, completar, pular, listar por status, listar vencidas
- [ ] 🧪 Atualizar `tests/test_routes.py` — usar fixture de DB real
- [ ] 🧪 Meta: `pytest -q` → **≥ 80% cobertura, 0 falhas**

**Critérios de aceite EF-001:**
- Todos os dados persistem após restart do container
- Queries por `patient_id` usam índice (verificar com EXPLAIN)
- Testes passando com SQLite in-memory no CI

---

## FASE 1.3 — GERALDA v2.0 Fase 2: Integração FHIR CarePlan (DEV0)

**Spec:** `EF-002_INTEGRACAO_FHIR_CAREPLAN.md`
**Pré-requisito:** Fase 1.2 concluída, Grahame (8012) acessível

### 1.3.A — Mapper Geralda ↔ FHIR CarePlan

**Tarefas:**

- [ ] ⚙️ Criar `geralda/fhir/careplan_mapper.py`
  ```python
  def to_fhir_careplan(plan: CarePlan, tasks: list[CareTask]) -> dict:
      # Retorna dict FHIR CarePlan R4
      # resourceType, id, status, intent, title, subject (Patient ref),
      # period, category, activity (cada CareTask → activity)

  def from_fhir_careplan(resource: dict) -> CarePlan:
      # Constrói CarePlan local a partir de FHIR
  ```

- [ ] ⚙️ Criar `geralda/fhir/client.py` — cliente HTTP para Grahame
  ```python
  class GrahameClient:
      base_url: str  # http://grahame:8012/api/v1/fhir
      async def put_careplan(self, fhir_resource: dict) -> dict
      async def get_careplan(self, fhir_id: str) -> dict
      async def search_careplans(self, patient_id: str) -> list[dict]
  ```

- [ ] ⚙️ Atualizar `care_plan_service.py` — ao criar/atualizar plano, sincronizar com Grahame (fire-and-forget, não bloqueia se Grahame estiver offline)

### 1.3.B — Testes do mapper FHIR (sem rede)

- [ ] 🧪 Criar `tests/test_fhir_mapper.py` — mínimo 8 testes:
  - to_fhir_careplan gera estrutura válida
  - from_fhir_careplan recupera campos corretamente
  - round-trip (to → from → campos iguais)
  - mapper não falha com campos opcionais ausentes

**Critérios de aceite EF-002:**
- CarePlan criado na Geralda aparece no Grahame (FHIR R4 válido)
- Se Grahame offline, Geralda continua funcionando (graceful degradation)
- Mapper tem testes unitários sem dependência de rede

---

# NÍVEL 2 — Alta Alavancagem Técnica

---

## FASE 2.1 — Integration Smoke Test: Todos os 13 Módulos

**Responsável:** DEV0 (infra)
**Prioridade:** 🟠
**Pré-requisito:** Nível 1 concluído

### Contexto
`docker-compose.full.yml` define 13 backends + 1 frontend + infraestrutura (PostgreSQL, Redis). **Nunca foram testados todos juntos.** Esta fase valida que o sistema completo sobe sem conflitos.

### 2.1.A — Preparar ambiente

**Tarefas:**

- [ ] ⚙️ Copiar `.env.example` → `.env` para cada módulo que precisar
  ```bash
  # Verificar quais módulos têm .env.example:
  for d in intellicare-*/; do
      [ -f "$d/.env.example" ] && echo "$d"
  done
  ```
- [ ] ⚙️ Criar `.env.full` para o docker-compose.full.yml com todas as variáveis:
  ```env
  # PostgreSQL
  POSTGRES_DB=intellicare
  POSTGRES_USER=intellicare
  POSTGRES_PASSWORD=<senha>

  # Redis
  REDIS_URL=redis://redis:6379/0

  # Rocket.Chat
  ROCKETCHAT_URL=http://rocketchat:3000
  ROCKETCHAT_ADMIN_USER=admin
  ROCKETCHAT_ADMIN_PASS=<senha>

  # WAHA
  WAHA_BASE_URL=http://waha:3000
  WAHA_SESSION=default
  WAHA_API_KEY=<chave>

  # Ollama
  OLLAMA_URL=http://ollama:11434

  # Kestra
  KESTRA_API_URL=http://kestra:8080

  # Jitsi
  JITSI_BASE_URL=https://jitsi.example.com
  ```

- [ ] ⚙️ Verificar que todos os `Dockerfile` têm `HEALTHCHECK` correto
  ```dockerfile
  HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
      CMD curl -sf http://localhost:${PORT}/api/v1/health || exit 1
  ```

---

### 2.1.B — Subir e validar

**Tarefas:**

- [ ] 📦 `docker compose -f docker-compose.full.yml up -d --build`
- [ ] 📦 Aguardar 2 minutos e executar smoke test:
  ```bash
  python scripts/smoke_tests.py
  ```
  **Meta:** 13/13 backends healthy + portal healthy

- [ ] 📦 Para cada módulo que falhar, verificar:
  1. `docker logs intellicare-<modulo>` — erro de startup?
  2. Variável de ambiente faltando?
  3. Dependência de serviço não estava ready (order de startup no compose)?

- [ ] ⚙️ Corrigir `depends_on` com `condition: service_healthy` no compose para dependências críticas:
  ```yaml
  depends_on:
    postgres:
      condition: service_healthy
    redis:
      condition: service_healthy
  ```

---

### 2.1.C — Validar comunicação entre módulos

**Tarefas:**

- [ ] 📦 WANDA → Oswaldo: `curl http://localhost:8007/api/v1/query` com request FHIR
- [ ] 📦 WANDA → Florence: `curl http://localhost:8007/api/v1/summarize`
- [ ] 📦 WANDA → Grahame: `curl http://localhost:8007/api/v1/fhir-proxy`
- [ ] 📦 Portal → qualquer backend: abrir `http://localhost:3000` e verificar que dados carregam
- [ ] 📦 Geralda → Grahame: criar plano e verificar que aparece no FHIR

**Critérios de aceite:**
- `smoke_tests.py` → 100% healthy
- Pelo menos 3 fluxos cross-módulo funcionando
- Nenhum container em CrashLoopBackOff após 5 minutos

---

## FASE 2.2 — Portal: Integração Real com APIs

**Módulo:** `intellicare-portal` (porta 3000)
**Responsável:** DEV0 (frontend)
**Prioridade:** 🟠
**Pré-requisito:** Fase 2.1 concluída

### Contexto
O portal tem 15 páginas implementadas. A maioria provavelmente usa dados mock/hardcoded. Esta fase conecta as páginas às APIs reais dos backends.

### 2.2.A — Camada de API client

**Tarefas:**

- [ ] ⚙️ Criar `src/lib/api/` com clients por módulo:
  ```
  src/lib/api/
    oswaldo.ts    → http://oswaldo:8001/api/v1
    florence.ts   → http://florence:8002/api/v1
    geralda.ts    → http://geralda:8006/api/v1
    wanda.ts      → http://wanda:8007/api/v1
    grahame.ts    → http://grahame:8012/api/v1/fhir
    zilda.ts      → http://zilda:8003/api/v1
  ```
- [ ] ⚙️ Criar `src/lib/api/base.ts` — fetch wrapper com:
  - Injeção de token de auth (header `Authorization`)
  - Error handling padronizado
  - Timeout de 30s
  - Retry automático para 503 (1x)

- [ ] ⚙️ Criar `src/hooks/` com React Query hooks por recurso:
  ```typescript
  // usePatient(id) → GET /fhir/Patient/{id}
  // useCarePlan(patientId) → GET /geralda/care-plans?patient={id}
  // useAlerts(patientId) → GET /wanda/alerts?patient={id}
  // useClinicalSummary(patientId) → GET /florence/summary/{id}
  ```

---

### 2.2.B — Substituir mocks por dados reais (por página)

**Páginas prioritárias:**

- [ ] ⚙️ **Dashboard** — conectar a:
  - Contagem de pacientes ativos (Geralda ou FHIR Patient count)
  - Alertas recentes (WANDA AlertHub)
  - Indicadores de qualidade resumidos (Donabedian)

- [ ] ⚙️ **Prontuário do paciente** — conectar a:
  - Dados FHIR Patient (Grahame)
  - Condições ativas `Condition?patient={id}&clinical-status=active` (Grahame)
  - Medicamentos `MedicationRequest?patient={id}` (Grahame)
  - Resumo clínico (Florence)

- [ ] ⚙️ **Plano de cuidado** — conectar a:
  - Lista de planos (Geralda `/care-plans?patient={id}`)
  - Tarefas do plano (Geralda `/care-tasks?plan={id}`)
  - Completar tarefa (PATCH Geralda)

- [ ] ⚙️ **Busca de UBS/CNES** — conectar a Zilda (`/cnes/establishments`)

---

### 2.2.C — Testes E2E mínimos

- [ ] 🧪 Criar `tests/e2e/` com Playwright (ou Cypress):
  - Login → Dashboard carrega com dados reais
  - Buscar paciente → prontuário abre
  - Criar tarefa no plano de cuidado
- [ ] 🧪 Meta: 5 testes E2E passando com backends mockados via MSW

**Critérios de aceite:**
- Nenhuma página usa dados hardcoded
- Dashboard mostra dados reais ao subir com docker compose
- Console do browser sem erros 404/500 de API

---

# NÍVEL 3 — Alto Valor Clínico

---

## FASE 3.1 — WANDA MCP Client (EF-W011): MINERVA + PIERRE

**Módulo:** `intellicare-wanda` (porta 8007)
**Responsável:** DEV0
**Prioridade:** 🟡
**Spec:** `intellicare-wanda/docs/specs/EF-W011_MCP_CLIENT.md`
**Pré-requisitos:** MINERVA (8008) e PIERRE (8009) com implementação básica funcionando

### Contexto
WANDA deve consumir MINERVA (OCR de documentos médicos) e PIERRE (busca científica PubMed+Tavily) como **ferramentas MCP**. Quando um médico perguntar "qual o protocolo para DRC estágio 3?", WANDA invoca PIERRE. Quando enviar um PDF de exame, WANDA invoca MINERVA.

### 3.1.A — MCP Client base

**Tarefas:**

- [ ] ⚙️ Instalar SDK MCP: `pip install mcp` (Anthropic MCP SDK)
- [ ] ⚙️ Criar `wanda/mcp/client.py` — `MCPClient` base
  ```python
  class MCPClient:
      server_url: str  # SSE endpoint do servidor MCP
      async def list_tools(self) -> list[MCPTool]
      async def call_tool(self, name: str, arguments: dict) -> MCPResult
      async def connect(self) -> None  # estabelece conexão SSE
      async def disconnect(self) -> None
  ```

- [ ] ⚙️ Criar `wanda/mcp/minerva_client.py` — cliente específico MINERVA
  ```python
  class MinervaClient(MCPClient):
      # Ferramentas esperadas:
      async def extract_text(self, file_b64: str, mime_type: str) -> str
      async def extract_structured(self, file_b64: str, schema: dict) -> dict
      async def extract_lab_results(self, file_b64: str) -> list[dict]
  ```

- [ ] ⚙️ Criar `wanda/mcp/pierre_client.py` — cliente específico PIERRE
  ```python
  class PierreClient(MCPClient):
      # Ferramentas esperadas:
      async def search_pubmed(self, query: str, max_results: int = 5) -> list[dict]
      async def search_web(self, query: str) -> list[dict]  # Tavily
      async def search_bvs(self, query: str) -> list[dict]  # BVS/BIREME
      async def synthesize(self, question: str, sources: list[dict]) -> str
  ```

---

### 3.1.B — Integração com LangGraph (WANDA orquestrador)

**Tarefas:**

- [ ] ⚙️ Criar `wanda/tools/mcp_tools.py` — wrap MCP tools como LangChain Tools
  ```python
  def get_pierre_tools(client: PierreClient) -> list[BaseTool]:
      return [
          PubMedSearchTool(client=client),
          WebSearchTool(client=client),
          BVSSearchTool(client=client),
      ]

  def get_minerva_tools(client: MinervaClient) -> list[BaseTool]:
      return [
          DocumentExtractTool(client=client),
          LabResultExtractTool(client=client),
      ]
  ```

- [ ] ⚙️ Atualizar `wanda/agent/graph.py` — adicionar nó MCP dispatcher
  ```python
  # Novo nó: "mcp_dispatcher"
  # Condição: se intent detectada requer pesquisa científica → PIERRE
  # Condição: se payload contém documento → MINERVA
  # Output: resultado normalizado → nó de síntese
  ```

- [ ] ⚙️ Atualizar lifespan do WANDA — inicializar MCP clients
  ```python
  # No startup:
  app.state.pierre = PierreClient(url=config.pierre_mcp_url)
  app.state.minerva = MinervaClient(url=config.minerva_mcp_url)
  await app.state.pierre.connect()
  await app.state.minerva.connect()
  ```

---

### 3.1.C — Testes com MCP mockado

- [ ] 🧪 Criar `tests/test_mcp_client.py` — mock do servidor SSE
- [ ] 🧪 Criar `tests/test_mcp_tools.py` — tools LangChain com cliente mockado
- [ ] 🧪 Criar `tests/test_graph_mcp.py` — grafo LangGraph processa query e invoca PIERRE
- [ ] 🧪 Meta: 15 testes, 0 falhas

**Critérios de aceite EF-W011:**
- Query "protocolo DRC" → WANDA invoca PIERRE → retorna artigos PubMed + síntese
- PDF de exame → WANDA invoca MINERVA → retorna resultados estruturados
- Se PIERRE/MINERVA offline → WANDA responde sem as ferramentas (graceful degradation)

---

## FASE 3.2 — GERALDA v2.0 Fases 2–3: Motor IA + Eventos

**Specs:** EF-003 (Ollama), EF-004 (Linguagem), EF-005 (Educação), EF-006 (Motor Eventos)
**Pré-requisito:** Fases 1.2 e 1.3 concluídas, Ollama rodando

### 3.2.A — Integração Ollama (EF-003)

- [ ] ⚙️ Criar `geralda/llm/ollama_client.py`
  ```python
  class OllamaClient:
      base_url: str  # http://ollama:11434
      model: str     # "qwen2.5:7b" ou "llama3.2:3b" (menor, mais rápido)
      async def generate(self, prompt: str, system: str = "") -> str
      async def is_available(self) -> bool
  ```
- [ ] ⚙️ Criar `geralda/llm/prompts.py` — prompts para geração de tarefas e educação
- [ ] 🧪 Testes com Ollama mockado (respeityfont httpx mock)

### 3.2.B — Linguagem Acessível (EF-004)

- [ ] ⚙️ Criar `geralda/services/language_service.py`
  ```python
  # simplify_medical_text(text: str, reading_level: str) -> str
  # Converte linguagem clínica para linguagem de paciente
  # Ex: "Insuficiência renal crônica estágio 3" →
  #     "Seu rim está funcionando a cerca de 40% do normal"
  ```
- [ ] ⚙️ Integrar no endpoint de plano de cuidado — `?simplify=true`

### 3.2.C — Motor de Eventos (EF-006)

- [ ] ⚙️ Criar `geralda/events/event_engine.py`
  ```python
  # Regras configuráveis:
  # SE tarefa vencida há > 3 dias → criar alerta para WANDA
  # SE meta não atingida em 30 dias → notificar responsável via Comunicacao
  # SE nova condição ICD-10 adicionada → gerar tarefas automáticas
  ```
- [ ] ⚙️ Integrar com Kestra — criar flow `geralda_event_check` que roda a cada hora
  ```yaml
  # kestra/flows/geralda_event_check.yml
  id: geralda_event_check
  triggers:
    - type: io.kestra.plugin.core.trigger.Schedule
      cron: "0 * * * *"  # hourly
  tasks:
    - id: check_events
      type: io.kestra.plugin.core.http.Request
      uri: http://geralda:8006/api/v1/internal/run-event-check
      method: POST
  ```

**Critérios de aceite Fases 2–3:**
- Geralda responde em linguagem acessível quando solicitado
- Motor de eventos gera alertas para tarefas vencidas
- Kestra flow rodando e disparando verificações periódicas

---

# Cronograma Sugerido

```
╔══════════════════════════════════════════════════════════════╗
║  SEMANA 1    │  SEMANA 2    │  SEMANA 3    │  SEMANA 4       ║
╠══════════════╪══════════════╪══════════════╪═════════════════╣
║ 1.1.A+B      │ 1.2.A+B+C   │ 1.3.A+B      │ 2.2.A+B         ║
║ Comunicacao  │ Geralda EF-  │ Geralda FHIR │ Portal APIs     ║
║ deps + testes│ 001 (PostgreS│ CarePlan     │ reais           ║
║              │ QL + modelos)│              │                 ║
╠══════════════╪══════════════╪══════════════╪═════════════════╣
║ 1.1.C        │ 2.1.A        │ 2.1.B+C      │ 2.2.C           ║
║ Smoke test   │ Preparar     │ Integration  │ Testes E2E      ║
║ Comunicacao  │ ambiente     │ smoke test   │ Portal          ║
╚══════════════╧══════════════╧══════════════╧═════════════════╝

SEMANA 5+:
  - Fase 3.1 (WANDA MCP) — depende de MINERVA e PIERRE implementados
  - Fase 3.2 (GERALDA Motor IA) — depende de Fase 1.2+1.3 estáveis
```

---

# Checklist de Entrega por Fase

| Fase | Entrega | Critério de Aceite |
|------|---------|-------------------|
| 1.1.A | `pyproject.toml` corrigido | `pytest --co -q` → 0 errors |
| 1.1.B | 4 testes corrigidos | `pytest -q` → 0 falhas, ≥80% cov |
| 1.1.C | Comunicacao no ar | health 200, mensagem RC enviada |
| 1.2.A | 4 modelos + migração Alembic | `alembic upgrade head` sem erro |
| 1.2.B | Serviços refatorados | dados persistem após `docker restart` |
| 1.2.C | Testes PostgreSQL | ≥80% cov, 0 falhas |
| 1.3.A | Mapper FHIR | CarePlan aparece no Grahame |
| 1.3.B | Testes mapper | 8 testes, 0 falhas, sem rede |
| 2.1.A | `.env.full` preparado | compose sobe sem erro de env var |
| 2.1.B | Smoke test 13/13 | `smoke_tests.py` → 100% healthy |
| 2.1.C | Cross-módulo OK | 3 fluxos validados manualmente |
| 2.2.A | API clients portal | TypeScript compila sem erros |
| 2.2.B | Páginas com dados reais | sem dados hardcoded |
| 2.2.C | Testes E2E | 5 testes Playwright passando |
| 3.1.A | MCP clients | `list_tools()` retorna ferramentas |
| 3.1.B | LangGraph + MCP | query → Pierre invocado |
| 3.1.C | 15 testes MCP | 0 falhas |
| 3.2.A | Ollama client | `generate()` testado com mock |
| 3.2.B | Linguagem acessível | endpoint `?simplify=true` funciona |
| 3.2.C | Motor eventos | Kestra flow ativo, alertas gerados |

---

*Documento gerado por DEV0 — IntelliCare PLANNER-ANTIGRAVITY*
*Versão: 1.0.0 — 2026-02-22*
