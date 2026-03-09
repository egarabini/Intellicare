# Estudo Completo do Projeto IntelliCare .

**Data:** 2026-02-19  
**Autor:** PLANEJADOR (Cursor AI)  
**Revisão:** ARQUITETO

---

## 1. Propósito e Contexto

### 1.1 O que é o IntelliCare

O **IntelliCare** é uma plataforma modular de saúde digital que integra múltiplos módulos especializados em um portal unificado. O diretório `.` concentra a arquitetura modular, com microserviços Python (FastAPI) e um frontend React.

### 1.2 Objetivo Principal

Demonstrar e integrar módulos de:

- **Cuidado crônico** (diabetes, HAS, DRC)
- **Análise laboratorial** (validação de resultados)
- **Atenção primária** (planos de cuidado, acompanhamento longitudinal)
- **Orquestração** (workflows, chatbot)
- **Saúde pública** (CNES/DATASUS)
- **Interoperabilidade FHIR** (HL7)

---

## 2. Estrutura de Diretórios

```
./
├── docs/                          # Documentação central
│   ├── PLANO_UNIFICACAO_OPENAPI.md
│   ├── API_CATALOG.md
│   ├── LEVANTAMENTO_APIS_INTERNAS.md
│   └── PLANNER-CURSOR/            # Planejamento e interações
├── migrations/
│   └── init-db.sql                # Inicialização PostgreSQL
├── docker-compose.yml             # Infra: Postgres, Redis, Prometheus, Grafana
├── prometheus.yml / alerts.yml
├── grafana-datasources.yml / grafana-dashboards.yml
├── start_demo.bat                 # Launcher da demo (7 serviços)
├── kill_demo.bat
│
├── intellicare-apresentacao/      # Apresentação (Streamlit?)
├── intellicare-auth/              # Autenticação/Keycloak
├── intellicare-comunicacao/       # Comunicação (92 rotas)
├── intellicare-conhecimento/      # Base de conhecimento clínico
├── intellicare-core/              # SDK compartilhado
├── intellicare-donabedian/        # Qualidade assistencial
├── intellicare-florence/          # Análise laboratorial
├── intellicare-geralda/           # Atenção primária / planos de cuidado
├── intellicare-grahame/           # FHIR / interoperabilidade
├── intellicare-nise/              # Orquestração e chatbot
├── intellicare-minerva/               # MINERVA (MINERVA)
├── intellicare-oswaldo/           # Cuidado crônico
├── intellicare-portal/            # Portal unificado (backend + frontend)
├── intellicare-superz/            # MCP / busca externa
├── intellicare-wanda/             # Orquestrador inteligente
└── intellicare-zilda/             # Saúde pública (CNES/DATASUS)
```

---

## 3. Inventário de Módulos

| Módulo | Nome Ref. | Foco | Porta Demo | Rotas API |
|--------|-----------|------|------------|-----------|
| **intellicare-oswaldo** | OSWALDO | Cuidado crônico (diabetes, HAS, DRC) | 8002 | 10 |
| **intellicare-florence** | FLORENCE | Validação de resultados laboratoriais | 8001 | 12 |
| **intellicare-geralda** | GERALDA | Planos de cuidado, acompanhamento longitudinal | 8006 | 21 |
| **intellicare-nise** | NISE | Orquestração, chatbot, workflows | 8000 | 17 |
| **intellicare-zilda** | ZILDA | Dados de saúde pública (CNES/DATASUS) | 8003 | 12 |
| **intellicare-grahame** | GRAHAME | Interoperabilidade FHIR | 8004 | 4 |
| **intellicare-comunicacao** | — | Comunicação (Rocket.Chat, Jitsi, WhatsApp, etc.) | 8005 | 92 |
| **intellicare-conhecimento** | — | Base de conhecimento clínico (protocolos, terminologias, RAG) | — | 14 |
| **intellicare-donabedian** | — | Qualidade assistencial (framework Donabedian) | — | 31 |
| **intellicare-wanda** | — | Orquestrador de agentes (LangGraph) | — | 59 |
| **intellicare-minerva** | MINERVA | MINERVA e extração de documentos | — | 5 |
| **intellicare-superz** | — | MCP, busca web, literatura médica | — | 5 |
| **intellicare-auth** | — | SSO/RBAC com Keycloak | — | 0* |
| **intellicare-core** | — | SDK compartilhado | — | 0* |
| **intellicare-portal** | — | Portal unificado (frontend + backend) | 5173 | 0* |

\* Módulos sem endpoints mapeados no catálogo atual.

**Total de rotas únicas:** 282

---

## 4. Stack Tecnológica

### 4.1 Backend (Python)

| Tecnologia | Uso |
|------------|-----|
| **FastAPI** | Framework de API REST |
| **Uvicorn** | Servidor ASGI |
| **SQLAlchemy 2.x** | ORM |
| **Pydantic 2.x** | Validação e serialização |
| **PostgreSQL 15** | Banco principal (asyncpg) |
| **Redis 7** | Cache e eventos |
| **Prometheus** | Métricas |
| **Alembic** | Migrações |
| **Poetry / setuptools** | Gerenciamento de dependências |

### 4.2 Frontend (Portal)

| Tecnologia | Versão |
|------------|--------|
| **React** | 19.2 |
| **Vite** | 7.2 |
| **TypeScript** | 5.9 |
| **TailwindCSS** | 4.x |
| **React Router** | 7.13 |
| **Zustand** | 5.x |
| **React Hook Form + Zod** | — |
| **Framer Motion** | 12.x |
| **Recharts** | 3.7 |
| **Lucide React** | Ícones |

### 4.3 Infraestrutura

- **Docker Compose:** PostgreSQL 15, Redis 7, Prometheus, Grafana
- **Schemas DB:** `intellicare_operacional`, `intellicare_analitico`
- **Schemas por módulo:** `oswaldo_operacional`, `florence_operacional`, etc.
- **RLS (Row-Level Security)** habilitado
- **Roles:** `operacional_user`, `analytics_user`, `intellicare_admin`

---

## 5. Padrões de Código

### 5.1 Backend

- Prefixo de API: `/api/v1`
- Endpoints de saúde: `/api/v1/health`, `/health`, `/api/v1/info`
- App factory: `create_app()` em vários módulos
- Lint: Ruff (pycodestyle, pyflakes, isort, bugbear)
- Tipagem: mypy strict em vários módulos
- Testes: pytest, pytest-asyncio, pytest-cov

### 5.2 Frontend

- Aliases: `@/`, `@components`, `@pages`, `@hooks`, `@services`, `@store`, `@types`, `@utils`, `@config`, `@styles`
- Code splitting: lazy loading de páginas de módulos
- Chunks: react-vendor, ui-vendor, form-vendor, chart-vendor

### 5.3 Bibliotecas Específicas por Módulo

- **intellicare-florence:** LangChain, ChromaDB, sentence-transformers (RAG)
- **intellicare-conhecimento:** pgvector, sentence-transformers
- **intellicare-wanda:** LangGraph
- **intellicare-superz:** MCP, Tavily, BeautifulSoup
- **intellicare-core:** fhir.resources, structlog, httpx

---

## 6. Documentação Existente

| Arquivo | Conteúdo |
|---------|----------|
| `README_DEMO.md` | Guia rápido da demo |
| `docs/PLANO_UNIFICACAO_OPENAPI.md` | Plano de unificação OpenAPI |
| `docs/API_CATALOG.md` | Catálogo de 282 rotas por módulo |
| `docs/LEVANTAMENTO_APIS_INTERNAS.md` | Levantamento de APIs |
| `intellicare-conhecimento/README.md` | BCCO – Base de Conhecimento |
| `intellicare-comunicacao/README.md` | Módulo de comunicação |
| `intellicare-auth/docs/PLANO_EXECUCAO.md` | Integração Keycloak |
| `intellicare-comunicacao/docs/` | Especificações (engine roteamento, teleconsulta, LGPD) |

---

## 7. Pontos de Entrada (Entry Points)

| Módulo | Comando |
|--------|---------|
| Oswaldo | `python -m src.oswaldo.api.main` |
| Florence | `python run_api_8001.py` |
| Geralda | `python run_api_8006.py` |
| Nise | `python run_api_lite.py` |
| Zilda | `python run_api_lite.py` |
| Grahame | `python run_api_lite.py` |
| Portal | `npm run dev` (intellicare-portal/frontend) |

---

## 8. Observações Importantes

1. **intellicare-auth:** biblioteca Keycloak planejada; infraestrutura pronta, implementação Python pendente.
2. **intellicare-core:** SDK compartilhado com `BaseModuleConfig`, `HealthCheck`, `ModuleInfo`, `BaseAgent`.
3. **Padrão LEGO:** módulos independentes, APIs REST bem definidas, testes e documentação.
4. **Dados clínicos:** YAML para protocolos (DRC/KDIGO, IC, oncologia), terminologias (CID-10, LOINC, SNOMED) e painéis de referência laboratorial.
5. **Workflows:** Kestra em intellicare-nise (ex.: avaliação de risco cardiovascular, alertas).
6. **Inconsistência de entry points:** alguns módulos usam `run_api_lite.py`, outros `run_api_800X.py` ou `src.*.api.main`.

---

## 9. Variáveis de Ambiente Relevantes

- `INTELLICARE_DATABASE_URL` — conexão PostgreSQL
- `REDIS_URL` — Redis
- `VITE_OSWALDO_URL`, `VITE_FLORENCE_URL`, etc. — URLs dos backends no frontend

---

## 10. Controle de Versão e Deploy

| Aspecto | Status atual |
|---------|--------------|
| **Repositório Git** | `eduardo/intellicare` |
| **Deploy** | Nenhum deploy realizado até o momento |
| **Controle de atualizações Git** | Não implementado |

> **Importante:** O projeto está versionado no Git (eduardo/intellicare), porém ainda não há processo de deploy nem controle formal de atualizações/ releases.

---

## 11. Resumo Executivo

O projeto IntelliCare . é uma plataforma de saúde digital madura em termos de arquitetura modular, com 15+ módulos especializados, 282 rotas de API documentadas, stack moderna (FastAPI, React 19, Vite 7) e infraestrutura observável (Prometheus, Grafana). A demo unifica 6 módulos clínicos + portal em um fluxo one-click. O repositório está em `eduardo/intellicare`, sem deploy nem controle de atualizações Git implementados. Há espaço para padronização (entry points, OpenAPI unificado, auth), governança de releases e evolução governada.
