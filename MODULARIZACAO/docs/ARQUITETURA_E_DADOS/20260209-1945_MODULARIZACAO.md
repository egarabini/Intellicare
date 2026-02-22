# Plano de Modularizacao IntelliCare

> Documento tecnico detalhado para a transicao do monolito para arquitetura LEGO.

## 1. Diagnostico do Estado Atual

### 1.1 Estrutura do INTELLICAREREPO (Monolito)

```
INTELLICAREREPO/
├── agentes/
│   ├── oswaldo/         ← v4.0.0 | 🟢 Maduro | Engine + UI + Tests
│   ├── wanda/           ← v3.0.1 | 🟡 Funcional | Orquestrador LangGraph
│   ├── mcp_servers/     ← v2.2.0 | 🟢 Funcional | FHIR + RNDS
│   ├── subagents/       ← Careplanner, PatientIQ (skeleton)
│   ├── tools/           ← Zilda (skeleton), Brazilian Data (docs)
│   └── legacy_v2/       ← 🔴 Deprecado
├── PortalIntellicare/   ← v1.0.0 | 🟢 Sprint 1 | React 19 + Vite 7
├── backend/             ← v1.0.0 | 🟢 MVP | Fastify + Prisma
├── apps/careplanner/    ← 🟡 Django | Operacional em producao
├── libs/                ← VAZIO (nunca usado)
└── desenvolvimento/     ← Documentacao historica
```

### 1.2 Problemas Identificados

| Problema | Impacto | Severidade |
|----------|---------|:---:|
| Dependencias duplicadas entre agentes | Conflitos de versao, builds pesados | Alta |
| Sem biblioteca compartilhada (libs/ vazio) | Codigo repetido entre agentes | Alta |
| Sem containerizacao padrao | Deploy manual e fragil | Alta |
| Agentes skeleton incompletos (Florence, Zilda) | Promessa sem entrega | Media |
| Configuracao descentralizada | Cada agente inventa seu config.py | Media |
| Sem CI/CD | Sem garantia de qualidade automatica | Media |
| Legacy code presente | Confusao sobre o que e atual | Baixa |

### 1.3 Maturidade por Componente

| Componente | Versao | Tests | Docs | UI | Docker | Score |
|-----------|--------|:---:|:---:|:---:|:---:|:---:|
| Oswaldo (engine) | 4.0.0 | 14 files | SETUP.md | Streamlit | Nao | 8/10 |
| Wanda (orquestrador) | 3.0.1 | 11 files | Sim | CLI | Nao | 7/10 |
| MCP Servers (FHIR/RNDS) | 2.2.0 | Sim | Sim | N/A | Nao | 7/10 |
| Portal (React) | 1.0.0 | Sim | Sim | React | Nao | 6/10 |
| Backend (API) | 1.0.0 | Parcial | Sim | N/A | Nao | 5/10 |
| Florence/PatientIQ | 0.1 | Nao | Nao | Nao | Nao | 1/10 |
| Zilda | 0.1 | Nao | Nao | Nao | Nao | 1/10 |
| Geralda | conceito | Nao | Nao | Nao | Nao | 0/10 |
| Donabedian | conceito | Nao | Nao | Nao | Nao | 0/10 |

---

## 2. Arquitetura LEGO — Visao Tecnica

### 2.1 Camadas

```
┌──────────────────────────────────────────────────────────────┐
│                    CAMADA DE APRESENTACAO                     │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ intellicare-portal (React 19 + Vite + Tailwind)        │ │
│  │ Detecta modulos ativos via /api/v1/info                 │ │
│  └─────────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────┤
│                    CAMADA DE ORQUESTRACAO                     │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ intellicare-wanda (LangGraph) — OPCIONAL                │ │
│  │ Supervisor → Routing → Subagents → Aggregation          │ │
│  └─────────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────┤
│                    CAMADA DE AGENTES                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────┐ ┌──────┐ │
│  │ Oswaldo  │ │ Florence │ │Donabedian│ │Zilda │ │Geralda│ │
│  │ :8501    │ │ :8502    │ │ :8503    │ │:8504 │ │:8505  │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └──┬───┘ └──┬────┘ │
│       │             │            │           │        │      │
├───────┴─────────────┴────────────┴───────────┴────────┴──────┤
│                    CAMADA DE INFRAESTRUTURA                   │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ intellicare-core (biblioteca Python)                    │ │
│  │ FHIR Client | Auth | Config | Logging | Tipos Base      │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │PostgreSQL│  │  Redis   │  │FHIR Server│  │  Keycloak  │  │
│  │  :5432   │  │  :6379   │  │  :8080    │  │  :8443     │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 Contrato de Modulo

Cada modulo DEVE implementar:

```python
# GET /api/v1/info
{
    "name": "intellicare-oswaldo",
    "version": "1.0.0",
    "status": "healthy",
    "capabilities": ["chronic-disease-monitoring", "staging", "alerts"],
    "fhir_version": "R4",
    "diseases": ["ckd", "dm2", "has"]  # especifico do Oswaldo
}

# GET /api/v1/health
{
    "status": "healthy",
    "uptime_seconds": 3600,
    "dependencies": {
        "database": "connected",
        "fhir_server": "connected"
    }
}
```

### 2.3 Comunicacao Entre Modulos

```
Modulo A ──FHIR R4──> Modulo B     (sincrono, REST)
Modulo A ──evento──> Redis Stream   (assincrono, pub/sub)
Wanda ──subagent──> Modulo N        (orquestracao LangGraph)
Portal ──REST──> Qualquer Modulo    (API padronizada)
```

---

## 3. Plano de Execucao por Fase

### FASE 1: intellicare-core (Fundacao)
**Duracao estimada:** Sprint 1 (1-2 semanas)
**Prioridade:** CRITICA

#### O que extrair do monolito:
- `agentes/mcp_servers/config.py` → config base
- `agentes/mcp_servers/base_mcp_server.py` → patterns reutilizaveis
- `agentes/mcp_servers/fhir_mcp_server.py` → FHIR client (extrair classe client)
- `agentes/wanda/subagents/base.py` → BaseSubagent interface
- Patterns de logging do structlog
- Patterns de validacao do pydantic

#### Entregaveis:
```
intellicare-core/
├── intellicare_core/
│   ├── __init__.py
│   ├── fhir/
│   │   ├── client.py          ← FHIR R4 client HTTP
│   │   ├── models.py          ← PatientSummary, IPS, etc.
│   │   └── ips.py             ← International Patient Summary
│   ├── config/
│   │   ├── base.py            ← BaseConfig (pydantic-settings)
│   │   └── env.py             ← Environment helpers
│   ├── auth/
│   │   └── keycloak.py        ← Auth client
│   ├── logging/
│   │   └── setup.py           ← Structured logging (structlog)
│   ├── contracts/
│   │   ├── module_info.py     ← ModuleInfo schema
│   │   ├── health.py          ← HealthCheck schema
│   │   └── base_agent.py      ← BaseAgent interface
│   └── events/
│       └── publisher.py       ← Redis Stream publisher
├── tests/
├── pyproject.toml
├── README.md
└── Makefile
```

#### Criterios de Conclusao:
- [ ] Pacote instalavel via pip (`pip install intellicare-core`)
- [ ] FHIR client funcional com testes
- [ ] BaseAgent interface definida
- [ ] ModuleInfo e HealthCheck schemas
- [ ] Publicado como pacote Python local (ou git+ssh)

---

### FASE 2: intellicare-oswaldo (Primeiro Modulo Piloto)
**Duracao estimada:** Sprint 2-3 (2-3 semanas)
**Prioridade:** CRITICA
**Origem:** `agentes/oswaldo/` (8/10 maturidade)

#### O que migrar:
- `engine/` inteiro (core_logic, staging, alerts, medication, risk)
- `profiles/` inteiro (loader, registry, schema, diseases/*.yaml)
- `datastore/` (fhir_datastore.py)
- `ui/` (Streamlit dashboard)
- `tests/` inteiro (14+ arquivos)
- `subagent/` → adaptado para usar intellicare-core BaseAgent

#### O que adaptar:
- Importar FHIR client do intellicare-core (nao mais local)
- Implementar contrato /api/v1/info e /api/v1/health
- Expor API REST alem do Streamlit (FastAPI wrapper)
- Criar Dockerfile autonomo
- Criar docker-compose.yml autonomo (com Postgres local)

#### Entregaveis:
```
intellicare-oswaldo/
├── oswaldo/
│   ├── __init__.py
│   ├── config.py
│   ├── api/                   ← NOVO: FastAPI REST
│   │   ├── app.py
│   │   ├── routes/
│   │   │   ├── health.py
│   │   │   ├── info.py
│   │   │   └── analyze.py
│   │   └── dependencies.py
│   ├── engine/                ← MIGRADO de agentes/oswaldo/engine/
│   │   ├── core_logic.py
│   │   ├── models.py
│   │   ├── alerts/
│   │   ├── staging/
│   │   ├── medication/
│   │   └── risk/
│   ├── profiles/              ← MIGRADO integralmente
│   │   ├── diseases/
│   │   │   ├── ckd.yaml
│   │   │   ├── dm2.yaml
│   │   │   └── has.yaml
│   │   ├── loader.py
│   │   ├── registry.py
│   │   └── schema.py
│   ├── datastore/             ← MIGRADO
│   ├── ui/                    ← MIGRADO (Streamlit)
│   └── subagent/              ← ADAPTADO para intellicare-core
├── tests/                     ← MIGRADO (14+ arquivos)
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml             ← Depende de intellicare-core
├── README.md
├── Makefile
└── .env.example
```

#### Criterios de Conclusao:
- [ ] `docker compose up` sobe Oswaldo + Postgres em < 2 min
- [ ] Streamlit acessivel em http://localhost:8501
- [ ] API REST acessivel em http://localhost:8000
- [ ] Todos os 14+ testes passando
- [ ] Funciona SEM nenhum outro modulo instalado
- [ ] Disease profiles carregam corretamente
- [ ] Staging KDIGO, ADA, ESC/ESH funcionais

---

### FASE 3: intellicare-florence (Inteligencia Clinica)
**Duracao estimada:** Sprint 4-5 (2-3 semanas)
**Prioridade:** ALTA
**Origem:** `agentes/subagents/patient_iq/` + novo desenvolvimento

#### O que existe:
- Skeleton em `agentes/wanda/subagents/patient_iq.py`
- Conceito documentado na apresentacao e portal
- Integracao com IPS via FHIR MCP Server

#### O que desenvolver:
- Engine de analise clinica (RAG sobre protocolos)
- Interpretacao de exames laboratoriais
- Deteccao de tendencias clinicas
- API REST padronizada
- UI Streamlit propria

#### Entregaveis:
```
intellicare-florence/
├── florence/
│   ├── __init__.py
│   ├── config.py
│   ├── api/                   ← FastAPI REST
│   ├── engine/
│   │   ├── clinical_analyzer.py
│   │   ├── lab_interpreter.py
│   │   ├── trend_detector.py
│   │   └── rag/
│   │       ├── retriever.py
│   │       └── protocols/     ← Protocolos clinicos indexados
│   ├── ui/                    ← Streamlit
│   └── subagent/              ← Para integracao com Wanda
├── tests/
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

---

### FASE 4: intellicare-donabedian (Qualidade)
**Duracao estimada:** Sprint 6-7 (2-3 semanas)
**Prioridade:** ALTA
**Origem:** Novo desenvolvimento (conceito existe)

#### O que desenvolver:
- Engine de avaliacao baseada nos 7 pilares
- Indicadores IQASUS, PMAQ, ONA
- Triade Estrutura-Processo-Resultado
- Dashboard de qualidade
- Benchmarking

#### Entregaveis:
```
intellicare-donabedian/
├── donabedian/
│   ├── engine/
│   │   ├── quality_engine.py
│   │   ├── pillars/           ← 7 pilares
│   │   │   ├── efficacy.py
│   │   │   ├── effectiveness.py
│   │   │   ├── efficiency.py
│   │   │   ├── optimality.py
│   │   │   ├── acceptability.py
│   │   │   ├── legitimacy.py
│   │   │   └── equity.py
│   │   ├── indicators/
│   │   │   ├── iqasus.py
│   │   │   └── pmaq.py
│   │   └── triad/
│   │       ├── structure.py
│   │       ├── process.py
│   │       └── outcome.py
│   ├── api/
│   ├── ui/
│   └── subagent/
├── tests/
├── Dockerfile
└── docker-compose.yml
```

---

### FASE 5: intellicare-zilda (Dados Brasileiros)
**Duracao estimada:** Sprint 8-9 (2-3 semanas)
**Prioridade:** MEDIA
**Origem:** `agentes/tools/zilda_health_data_agent.py` + `brazilian_public_data_agent.py`

#### O que migrar/desenvolver:
- Integracao CNES (ja documentada, 23k linhas de spec)
- Integracao DATASUS
- Contexto territorial
- Cache de dados publicos

#### Entregaveis:
```
intellicare-zilda/
├── zilda/
│   ├── engine/
│   │   ├── cnes_client.py
│   │   ├── datasus_client.py
│   │   ├── territorial.py
│   │   └── cache.py
│   ├── api/
│   ├── ui/
│   └── subagent/
├── tests/
├── Dockerfile
└── docker-compose.yml
```

---

### FASE 6: intellicare-geralda (Acompanhamento)
**Duracao estimada:** Sprint 10-11 (2-3 semanas)
**Prioridade:** MEDIA
**Origem:** Novo desenvolvimento

#### O que desenvolver:
- Engine de acompanhamento do paciente
- Sistema de lembretes e notificacoes
- Educacao em saude personalizada
- Integracao com CarePlan FHIR

---

### FASE 7: intellicare-wanda (Orquestracao)
**Duracao estimada:** Sprint 12-13 (2-3 semanas)
**Prioridade:** MEDIA (depende de 2+ modulos prontos)
**Origem:** `agentes/wanda/` (7/10 maturidade)

#### O que migrar:
- `graph/` (main_graph, supervisor, aggregator)
- `adapters/` (mcp_adapter)
- `rules/` (safety_rules)
- `prompts/` (system_prompt)

#### O que adaptar:
- Descoberta dinamica de modulos ativos (via /api/v1/info)
- Routing baseado em capabilities declaradas
- Nao depender de import direto dos agentes

---

### FASE 8: intellicare-portal (Interface Unificada)
**Duracao estimada:** Sprint 14-15 (2-3 semanas)
**Prioridade:** BAIXA (funciona sem portal)
**Origem:** `PortalIntellicare/` + `backend/`

#### O que adaptar:
- Deteccao automatica de modulos ativos
- Dashboard dinamico baseado em capabilities
- Remocao de dados hardcoded de agentes
- Cada modulo registra seus componentes de UI

---

## 4. Dependencias Entre Fases

```
Fase 1 (core) ──────┬──> Fase 2 (oswaldo)
                     ├──> Fase 3 (florence)
                     ├──> Fase 4 (donabedian)
                     ├──> Fase 5 (zilda)
                     └──> Fase 6 (geralda)

Fase 2 + Fase 3 ────┬──> Fase 7 (wanda) ← precisa de 2+ modulos
                     └──> Fase 8 (portal) ← precisa de 1+ modulos
```

**Regra:** Fases 2-6 sao INDEPENDENTES entre si. Podem ser executadas em paralelo ou em qualquer ordem apos a Fase 1.

---

## 5. Estrategia de Migracao

### 5.1 Abordagem: Strangler Fig Pattern

Nao vamos "desligar" o monolito de uma vez. A estrategia:

1. Criar o modulo novo no diretorio MODULARIZACAO
2. Migrar o codigo do INTELLICAREREPO
3. Validar que funciona isolado (testes + docker)
4. Quando todos os modulos estiverem prontos, o INTELLICAREREPO vira "legacy"

### 5.2 Regras de Migracao

- NUNCA copiar codigo — sempre mover e adaptar
- SEMPRE manter testes passando durante a migracao
- CADA modulo tem seu proprio repositorio Git (dentro de MODULARIZACAO inicialmente, depois repos separados)
- CADA modulo tem seu proprio CHANGELOG.md

### 5.3 Versionamento

Todos os modulos seguem SemVer (Semantic Versioning):
- `MAJOR.MINOR.PATCH`
- MAJOR: quebra de contrato de API
- MINOR: nova funcionalidade compativel
- PATCH: bug fix

Versao inicial de todos: `1.0.0` (pos-migracao e validacao)

---

## 6. Stack Tecnica por Modulo

### Agentes (Python)
```
Runtime:        Python 3.11+
Framework API:  FastAPI
Framework UI:   Streamlit
ORM:            SQLAlchemy 2.0
Validacao:      Pydantic 2.x
FHIR:           fhir.resources 7.x
IA:             LangChain + LangGraph
Testes:         pytest + pytest-cov + pytest-asyncio
Linting:        ruff
Formatting:     black + isort
Types:          mypy
Container:      Docker (python:3.11-slim)
```

### Portal (TypeScript)
```
Runtime:        Node.js 22
Framework:      React 19
Build:          Vite 7
CSS:            Tailwind CSS 4
State:          Zustand
Forms:          React Hook Form + Zod
Charts:         Recharts
Testes:         Vitest + Testing Library
Container:      Docker (node:22-alpine)
```

### Infraestrutura
```
Database:       PostgreSQL 16
Cache:          Redis 7
FHIR Server:   HAPI FHIR (existente em fhir.gsi.srv.br)
Auth:           Keycloak (futuro)
Container:      Docker Compose (dev) / Kubernetes (prod futuro)
```

---

## 7. Governanca

### 7.1 Documentacao por Modulo

Cada modulo DEVE ter:
```
docs/
├── ESPECIFICACAO_FUNCIONAL.md   ← O que faz (linguagem de negocio)
└── ESPECIFICACAO_TECNICA.md     ← Como faz (linguagem tecnica)

steps/
├── STEP-001.md                  ← Registro de cada etapa
├── STEP-002.md
└── ...

desenvolvimento/
└── VERSIONAMENTO.md             ← Historico de versoes e decisoes
```

### 7.2 Checklist de Qualidade por Modulo

Antes de considerar um modulo "pronto":
- [ ] Roda sozinho com `docker compose up`
- [ ] Testes >= 80% cobertura
- [ ] API /health e /info implementadas
- [ ] Docs funcional e tecnica completas
- [ ] README com instrucoes de setup em 15 min
- [ ] .env.example com todas as variaveis
- [ ] Sem dependencia direta de outro modulo de agente
- [ ] Sem secrets hardcoded
