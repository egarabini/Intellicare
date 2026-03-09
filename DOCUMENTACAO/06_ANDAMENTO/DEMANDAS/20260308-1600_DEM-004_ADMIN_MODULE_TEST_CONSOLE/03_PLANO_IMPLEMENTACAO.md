# DEM-004 — Module Test Console: Plano de Implementação

**Demanda:** DEM-004
**Dev:** dev2
**Branch:** `feature/admin-module-test-console`
**Base:** branch `fix/admin-gestor-auth` (DEM-002) — já contém auth funcionando

---

## Antes de começar

### 1. Criar a branch corretamente

```bash
# A partir da branch do DEM-002 que já tem auth
git checkout fix/admin-gestor-auth
git pull
git checkout -b feature/admin-module-test-console
```

### 2. Entender o que já existe

Ler antes de codificar:
- `intellicare-admin/admin/api/app.py` — como as rotas são registradas
- `intellicare-admin/admin/api/deps.py` — `require_platform_admin` e `get_db`
- `intellicare-admin/admin/db/session.py` — `TenantAwareSessionFactory`
- `intellicare-admin/admin/api/plan_routes.py` — exemplo de rota com session e deps

### 3. Verificar dependências

```bash
cd intellicare-admin
poetry show | grep httpx   # deve aparecer httpx 0.27.x
```

`httpx` já está no `pyproject.toml` — não instalar nada adicional para o backend.

---

## Sprint 1 — Probe Dashboard (2 dias)

**Objetivo:** Grid de cards funcionando com probe real.

### Passo 1 — Modelo e migração

Criar `intellicare-admin/admin/models/module_test_log.py`
(código completo na `ESPECIFICACAO_TECNICA.md`).

```bash
cd intellicare-admin
alembic revision --autogenerate -m "add_module_test_log"
# Revisar o arquivo gerado em migrations/versions/
alembic upgrade head
```

### Passo 2 — Service e config

Criar em ordem:
1. `admin/services/module_proxy.py` — `ModuleProxyClient.probe()` e `probe_all()`
2. `admin/config/test_payloads.py` — payloads por módulo (copiar da spec técnica)

### Passo 3 — Rotas backend

Criar `admin/api/module_probe_routes.py` com:
- `GET /api/v1/admin/modules` — probe all
- `GET /api/v1/admin/modules/{name}/probe` — probe individual

Registrar em `admin/api/app.py`:
```python
from admin.api.module_probe_routes import router as probe_router
app.include_router(probe_router, prefix="/api/v1")
```

### Passo 4 — Testar backend localmente

```bash
cd intellicare-admin
uvicorn admin.api.app:app --reload --port 8010

# Em outro terminal — probe de todos (com token válido no header):
curl -H "Authorization: Bearer <token>" \
     http://localhost:8010/api/v1/admin/modules
```

Resultado esperado: lista JSON com 11 módulos. Os que não estiverem rodando
retornam `"health": "unreachable"` — isso é correto, não é erro.

### Passo 5 — Frontend: ModuleGrid

No projeto `intellicare-admin-frontend`:

```bash
npm install @uiw/react-codemirror @codemirror/lang-json
```

Criar `src/pages/Diagnostico/`:
- `index.tsx` — página com rota `/diagnostico`, chama `GET /api/v1/admin/modules`
- `ModuleCard.tsx` — card individual com badge de status, latência, versão
- `ModuleGrid.tsx` — grid responsivo com os cards + botão "Atualizar tudo"

**Cores dos badges (Tailwind):**

```tsx
const STATUS_COLORS = {
  healthy:     'bg-green-100 text-green-800 border-green-300',
  degraded:    'bg-yellow-100 text-yellow-800 border-yellow-300',
  unhealthy:   'bg-red-100 text-red-800 border-red-300',
  unreachable: 'bg-gray-100 text-gray-600 border-gray-300',
}
```

**Auto-refresh** com `useEffect` e `setInterval` — opções: off / 30s / 60s / 5min.

### Entrega do Sprint 1

- [ ] Migração criada e aplicada
- [ ] `GET /api/v1/admin/modules` retornando probe real dos módulos
- [ ] `GET /api/v1/admin/modules/{name}/probe` funcionando
- [ ] Grid de cards renderizando no frontend com status correto
- [ ] Auto-refresh funcionando

---

## Sprint 2 — Teste Funcional (3 dias)

**Objetivo:** Cada módulo pode ser testado individualmente com payload.

### Passo 1 — Completar o proxy

Adicionar `test_analyze()` em `admin/services/module_proxy.py`
(código completo na spec técnica).

### Passo 2 — Rotas de teste

Criar `admin/api/module_test_routes.py` com:
- `POST /api/v1/admin/modules/{name}/test` — executa e persiste no log
- `GET  /api/v1/admin/modules/{name}/test/history` — histórico paginado
- `GET  /api/v1/admin/modules/{name}/test/payloads` — lista payloads disponíveis

Registrar em `app.py`.

### Passo 3 — Frontend: painel de teste

Adicionar aba "Teste Funcional" ao `ModuleCard` expandido:

- `ModuleTestPanel.tsx`:
  - Dropdown com payloads disponíveis (chama `/payloads`)
  - Botão "Executar Teste"
  - Ao executar: spinner → resultado

- `PayloadEditor.tsx`:
  - Editor JSON com `@uiw/react-codemirror` + extensão `lang-json`
  - Exibe o payload selecionado e permite edição antes de enviar

- `ResponseViewer.tsx`:
  - Exibe status HTTP, latência, badge success/fail
  - JSON formatado com syntax highlight (usar o mesmo CodeMirror em modo read-only)

- `TestHistory.tsx`:
  - Tabela com histórico: data, payload usado, status, latência, success
  - Paginação simples (limit/offset)

### Entrega do Sprint 2

- [ ] `POST /api/v1/admin/modules/{name}/test` funcionando e persistindo no log
- [ ] Histórico acessível via API e no frontend
- [ ] Editor de payload funcional com CodeMirror
- [ ] Resultado exibido com latência e status corretos
- [ ] Todos os 11 módulos têm ao menos o payload "default" configurado

---

## Sprint 3 — Testes de Integração (3 dias)

**Objetivo:** Flows multi-módulo pré-definidos com visualização step-by-step.

### Passo 1 — Config dos flows

Criar `admin/config/integration_tests.py`:

```python
INTEGRATION_TESTS = {
    "basic_patient_flow": {
        "display": "Fluxo Básico do Paciente",
        "description": "WANDA orquestra análise clínica completa com OSWALDO e DONABEDIAN",
        "steps": [
            {
                "id": "wanda",
                "module": "wanda",
                "payload_key": "orchestration",
                "depends_on": None,
            },
            {
                "id": "oswaldo",
                "module": "oswaldo",
                "payload_key": "default",
                "depends_on": None,  # paralelo com wanda
            },
            {
                "id": "donabedian",
                "module": "donabedian",
                "payload_key": "default",
                "depends_on": ["wanda", "oswaldo"],  # aguarda os anteriores
            },
        ],
    },
    "rag_protocol_search": {
        "display": "Busca de Protocolo Clínico",
        "description": "FLORENCE (RAG local) + PIERRE (PubMed) em paralelo",
        "steps": [
            {"id": "florence", "module": "florence", "payload_key": "default", "depends_on": None},
            {"id": "pierre",   "module": "pierre",   "payload_key": "default", "depends_on": None},
        ],
    },
    "full_health_sweep": {
        "display": "Varredura Completa de Saúde",
        "description": "Probe de todos os módulos em paralelo",
        "steps": [
            {"id": name, "module": name, "payload_key": None, "depends_on": None}
            for name in ["florence","oswaldo","donabedian","wanda","comunicacao",
                         "geralda","zilda","minerva","pierre","grahame","nise"]
        ],
    },
}
```

### Passo 2 — Rotas de integração

Criar `admin/api/integration_test_routes.py`:
- `GET  /api/v1/admin/integration-tests` — lista flows disponíveis
- `POST /api/v1/admin/integration-tests/run` — executa um flow, retorna resultado step-by-step
- `GET  /api/v1/admin/integration-tests/history` — últimas execuções

### Passo 3 — Frontend: runner step-by-step

- `IntegrationTests.tsx` — lista de flows com botão "Executar"
- `IntegrationTestRunner.tsx` — visualização em tempo real:
  - Lista de steps com status (⏳ aguardando / 🔄 executando / ✅ ok / ❌ erro)
  - Latência por step
  - Detalhes colapsáveis de cada resposta
  - Timeline horizontal simplificada mostrando execução paralela vs. sequencial

### Entrega do Sprint 3

- [ ] 3 flows de integração funcionando
- [ ] Execução paralela dos steps independentes via `asyncio.gather()`
- [ ] Runner step-by-step funcionando no frontend
- [ ] Histórico de execuções de integração

---

## Dúvidas frequentes (FAQ para o dev2)

**P: O admin precisa de token para chamar os módulos?**
R: Não neste MVP. As chamadas são feitas pelo backend do admin dentro da rede
Docker com o header `X-Internal-Call: intellicare-admin`. Os módulos estão
na mesma rede e aceitam chamadas internas. Se isso mudar no futuro (DEM-005
prepara isso), o `module_proxy.py` já está estruturado para receber um token.

**P: E se um módulo não estiver rodando?**
R: O `probe()` captura o `httpx.TimeoutException` e retorna `"health": "unreachable"`.
O grid mostra o card em cinza. Isso é comportamento esperado — não é erro do admin.

**P: Os payloads de teste podem afetar dados reais?**
R: Não. Os módulos têm lógica de análise, não de escrita direta. O `analyze`
é uma operação de leitura/processamento. Para módulo de comunicação, o payload
usa `"dry_run": true` explicitamente.

**P: Onde fica a página no menu do admin?**
R: Criar item "Diagnóstico" no menu lateral do frontend, com ícone de
checkmark/pulse. Abaixo de "Dashboard" e acima de "Tenants".

**P: A Fase 3 (integração) pode ser entregue separada?**
R: Sim. Entregas aceitas em ordem: Sprint 1 → Sprint 2 → Sprint 3.
Cada sprint é funcional e útil por si só.

---

## Checklist de entrega final

### Backend
- [ ] `admin/services/module_proxy.py` — probe + test_analyze
- [ ] `admin/config/test_payloads.py` — 11 módulos com payload default
- [ ] `admin/config/integration_tests.py` — 3 flows
- [ ] `admin/models/module_test_log.py` + migração Alembic
- [ ] `admin/api/module_probe_routes.py` — GET /modules + GET /modules/{name}/probe
- [ ] `admin/api/module_test_routes.py` — POST /test + GET /history + GET /payloads
- [ ] `admin/api/integration_test_routes.py` — GET /integration-tests + POST /run + GET /history
- [ ] Rotas registradas em `app.py`
- [ ] Testes: pelo menos 1 teste por rota nova (pytest)

### Frontend
- [ ] Página `/diagnostico` no menu lateral
- [ ] `ModuleGrid.tsx` com auto-refresh
- [ ] `ModuleCard.tsx` com badge de status e latência
- [ ] `ModuleTestPanel.tsx` com dropdown de payloads
- [ ] `PayloadEditor.tsx` com CodeMirror JSON
- [ ] `ResponseViewer.tsx` com syntax highlight
- [ ] `TestHistory.tsx` com paginação
- [ ] `IntegrationTests.tsx` com lista de flows
- [ ] `IntegrationTestRunner.tsx` com step-by-step

### Qualidade
- [ ] `make lint` passando (ruff)
- [ ] `make typecheck` passando (mypy)
- [ ] `npm run lint` passando (ESLint)
- [ ] `npm run build` sem erros TypeScript

---

## Ao terminar

1. Preencher a seção **"Log de execução"** no `DEM-004_*.md` em `DOCUMENTACAO/06_ANDAMENTO/DEMANDAS/`
2. Abrir PR apontando para `fix/admin-gestor-auth` (base) ou `main` conforme orientação do Eduardo
3. Avisar Eduardo que o DEM-004 está concluído para revisão
