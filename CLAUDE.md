# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

IntelliCare . is a modular healthcare platform built as a collection of independent Python FastAPI microservices (agents) + one React portal. Each module runs standalone and communicates via REST using HL7 FHIR R4 as the data interchange format.

**Root:** `C:\DOCSHARE\INTELLICARE\`

---

## Commands

### Python Modules (each has its own virtualenv)

```bash
# From inside any module directory (e.g., intellicare-wanda/)
make install-dev        # Install with dev dependencies (pip install -e ".[dev]")
make test               # Run full test suite
make test-quick         # Run tests with -x (stop on first failure)
make lint               # ruff check
make format             # ruff format
make typecheck          # mypy
make check              # lint + typecheck + test
make coverage           # pytest with coverage report

# Run a single test
pytest tests/test_foo.py::TestClass::test_method -v

# Skip integration tests (require live infra)
pytest tests/ -m "not integration" -v

# Run module API locally
uvicorn <module>.api.app:app --reload --port 80XX
```

Most modules use **setuptools** (`pip install -e ".[dev]"`). Some (wanda, oswaldo, auth, donabedian) use **poetry** — check `pyproject.toml` build-backend.

### Frontend (intellicare-portal/frontend/)

```bash
npm run dev             # Dev server at http://localhost:5173
npm run build           # TypeScript compile + Vite build
npm run lint            # ESLint
npm run format          # Prettier
npm run test            # Vitest
npm run test:coverage   # Vitest with coverage
```

### Infrastructure & Full Stack

```bash
# Minimal infra (PostgreSQL + Redis + Prometheus)
docker compose up -d

# Full stack (all 13 backends + portal)
docker compose -f docker-compose.full.yml up -d

# Smoke test all module health endpoints
bash scripts/smoke_test.sh
python scripts/smoke_tests.py

# Demo (Windows)
.\start_demo.bat        # Start all services
.\kill_demo.bat         # Stop all services
.\check_demo_health.ps1 # Health check
```

---

## Architecture

### Module Map

| Port | Module directory | Agent name | Role | Port Mapping |
|------|-----------------|------------|------|--------------|
| 8001 | `intellicare-florence/` | FLORENCE | RAG + Protocolos Clínicos | 8001:8000 |
| 8002 | `intellicare-oswaldo/` | OSWALDO | Análise Clínica + FHIR | 8002:8000 |
| 8003 | `intellicare-donabedian/` | DONABEDIAN | Qualidade + Indicadores | 8003:8000 |
| 8004 | `intellicare-wanda/` | WANDA | **Orquestrador IA** — routes, aggregates, AlertHub | 8004:8000 |
| 8005 | `intellicare-comunicacao/` | — | WhatsApp + Email + SMS | 8005:8000 |
| 8006 | `intellicare-geralda/` | GERALDA | Gestão + Administrativo | 8006:8000 |
| 8007 | `intellicare-zilda/` | ZILDA | CNES + DATASUS | 8007:8000 |
| 8008 | `intellicare-minerva/` | MINERVA | Extração Documentos (MCP Server) | 8008:8008 |
| 8009 | `intellicare-pierre/` | PIERRE | Scientific Search PubMed+Tavily (MCP Server) | 8009:8009 |
| 8010 | `intellicare-admin/` | — | Administração do Sistema | 8010:8010 |
| 8011 | `intellicare-gestor/` | — | Gestão de Módulos Clínicos | 8011:8011 |
| 8012 | `intellicare-grahame/` | GRAHAME | FHIR R4 + CDS Hooks 2.0 + Terminology + HL7v2 + CCDA + Excalidraw | 8012:8000 |
| 8013 | `intellicare-nise/` | NISE | Chatbot + Treinamento (Flowise/Kestra) | 8013:8000 |
| 3001 | `intellicare-portal/frontend/` | — | React 19 + Vite Portal | 3001:80 |
| 5432 | PostgreSQL | — | Database Principal | 5432:5432 |
| 6379 | Redis | — | Cache + Pub/Sub + Rate Limiting | 6379:6379 |
| 3000 | Grafana | — | Dashboards de Monitoramento | 3000:3000 |
| 9090 | Prometheus | — | Métricas do Sistema | 9090:9090 |

Additional libraries (not services): `intellicare-core/` (shared SDK), `intellicare-auth/` (Keycloak/SMART-on-FHIR), `intellicare-conhecimento/` (FHIR protocols, RAG, terminology).

### Shared SDK — `intellicare-core/`

All Python modules depend on `intellicare-core` installed via path reference (`pip install -e ../intellicare-core`). Key packages:

- `intellicare_core.contracts` — `BaseAgent`, `HealthCheck`, `ModuleInfo`, `AnalysisRequest/Response` (the mandatory API contract every module must implement)
- `intellicare_core.fhir` — `FHIRClient`, `PatientSummary`, `ConditionSummary`, `ObservationValue`
- `intellicare_core.tenant` — Multi-tenancy: `TenantContext`, `TenantResolver` (reads JWT/header/subdomain/path), `TenantAwareSessionFactory`, `TenantRedisClient`
- `intellicare_core.monitoring` — Prometheus metrics via `setup_metrics(app, module_name=...)`
- `intellicare_core.events`, `intellicare_core.logging`, `intellicare_core.config`

### Module Contract

Every agent module **must** expose:
- `GET /api/v1/health` → `HealthCheck` schema
- `GET /api/v1/info` → `ModuleInfo` schema
- `POST /api/v1/analyze` → `AnalysisResponse` schema

Implement by inheriting from `intellicare_core.contracts.BaseAgent`.

### Authentication — `intellicare-auth/`

Provides Keycloak + SMART-on-FHIR 2.0 integration. Modules optionally enable it:
```python
from intellicare_auth.fastapi import configure_auth
configure_auth(app, secrets_path="keycloak_client_secrets.json")
```

### Wanda Orchestrator (`intellicare-wanda/`)

Wanda is the central hub. Architecture layers:
- **v2.0:** Module registry + discovery, IPS-First (patient summary), MCP client (MINERVA/PIERRE tools)
- **v2.1:** LLM intent routing, intelligent aggregation, circuit breaker, tracing, metrics
- **v3.0:** LangGraph workflows, AlertHub, Redis event streams, Rocket.Chat bot, Dr. Nise (Flowise)

All subsystems are initialized in `wanda/api/app.py:lifespan()` and accessed via `app.state.*`.

### Multi-Tenancy Pattern

Each module calls `init_tenant_resolver()` at startup. DB isolation uses PostgreSQL schemas per tenant via `TenantAwareSessionFactory`. Redis uses key prefixing via `TenantRedisClient`.

### Infrastructure

- **PostgreSQL 15** — primary store, one schema per module per tenant
- **Redis 7** — event streams (Redis Streams + consumer groups), cache, Wanda events
- **Prometheus + Grafana** — metrics from all modules (`/metrics` endpoint added by `setup_metrics`)
- **Traefik** — reverse proxy for production (`docker-compose.traefik.yml`)
- **Kestra** — workflow automation/orchestration (deployed separately; N8N is NOT used)
- **Flowise** — LLM workflow + RAG pipelines (used by NISE/Dr. Nise)
- **OLLAMA** — local AI (Llama4 Scout, Qwen2.5-72B)
- **Rocket.Chat + Jitsi** — messaging and video (deployed separately)

### Frontend — `intellicare-portal/frontend/`

React 19 + TypeScript + Vite 7 + Tailwind CSS 4. Path aliases configured in `vite.config.ts`: `@components`, `@pages`, `@hooks`, `@services`, `@store`, `@types`, `@utils`, `@config`.

Key patterns:
- **Multi-tenancy:** `TenantProvider` decodes JWT, resolves tenant, handles white-label subdomains
- **White-label:** `whiteLabelResolver.ts` reads hostname to apply per-tenant branding via CSS
- **State:** Zustand stores + React Query
- **Routing:** React Router v7, lazy-loaded page components

### Database Migrations

Each module with a DB has Alembic migrations in its `migrations/` directory:
```bash
alembic upgrade head     # Apply migrations
alembic revision --autogenerate -m "description"  # Generate new migration
```

### Code Quality Tools

| Tool | Config | Purpose |
|------|--------|---------|
| `ruff` | `pyproject.toml [tool.ruff]` | Linting + formatting (line-length: 100, target: py311) |
| `mypy` | `pyproject.toml [tool.mypy]` | Strict type checking |
| `pytest` | `pyproject.toml [tool.pytest]` | Tests, `asyncio_mode = "auto"` |
| `ESLint` + `Prettier` | `eslint.config.js` | Frontend linting + formatting |
| `vitest` | `vite.config.ts` | Frontend tests (jsdom environment) |

### Adding a New Module

1. Create `intellicare-<name>/` with the standard layout: `<name>/api/app.py`, `<name>/config.py`, `tests/`, `pyproject.toml`, `Dockerfile`, `docker-compose.yml`
2. Add `intellicare-core` and `intellicare-auth` as path dependencies in `pyproject.toml`
3. Call `init_tenant_resolver()` in the FastAPI `lifespan` handler
4. Implement `BaseAgent` and expose the three mandatory endpoints
5. Call `setup_metrics(app, module_name="<name>")` for Prometheus
6. Add the service to `docker-compose.full.yml` and `scripts/smoke_test.sh`
