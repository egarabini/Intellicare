# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Added
- (mudanças ainda não lançadas)

### Changed
- (mudanças ainda não lançadas)

### Fixed
- (mudanças ainda não lançadas)

## [0.2.0-onda2] - 2026-03-04

### ONDA 2 — Core Clínico (MINERVA + GRAHAME + GERALDA)

#### MINERVA v2.0 — Extração de Documentos (port 8008)

##### Added
- **Lab Extractor v2**: Motor de extração laboratorial expandido de 7 para 100+ analitos
  - Mapeamento PT→EN completo (hemograma, bioquímica, lipídeos, hepático, tireoide, urinálise, coagulação, eletrólitos, marcadores cardíacos/inflamatórios/tumorais)
  - Faixas de referência padrão para 35 analitos
  - Limiares críticos para 12 analitos (hemoglobina <7, creatinina >10, potássio <2.5/>6.5, etc.)
  - Dataclasses `LabResult` e `LabReport` com serialização `to_dict()`
  - Detecção de status: normal, alto, baixo, crítico
  - Suporte a formato numérico brasileiro (250.000 = 250000, 8.500 = 8500)
- **POST /api/v1/analyze**: Endpoint de análise padrão (BaseAgent contract)
  - Aceita texto bruto via `parameters.text`
  - Retorna resultados lab estruturados, alertas para valores críticos, recomendações para anormais
  - Compatível com `AnalysisResponse` do intellicare-core
- **Contratos HealthCheck/ModuleInfo**: Integração com intellicare-core quando disponível, fallback para formato legado
- **Testes**: 50 testes (11 lab extractor, 4 analyze, 35 existentes) — 100% passando

##### Fixed
- Imports de teste corrigidos: `ocr.*` → `minerva.*` em test_mcp_tools.py
- Regex de valor numérico: tratamento de separador de milhar brasileiro (ponto + 3 dígitos = milhares)
- Busca de valor após posição do nome do exame: evita capturar números do nome (ex: "T4 Livre: 0.6" não captura "4")
- Health endpoint sempre retorna "healthy" (engines OCR são opcionais, não bloqueiam status)

#### GRAHAME v1.0 — FHIR R4 Interoperability Hub (port 8012)

##### Status
- **Módulo maduro**: 371 testes core passando, 40+ endpoints
- FHIR CRUD completo (Patient, Observation, Condition, MedicationRequest, Encounter, etc.)
- CDS Hooks 2.0 (patient-view, order-sign) funcionais
- HL7v2 parsing + CCDA generation operacionais
- Terminology (ValueSet, CodeSystem) com validação
- Bulk Export, Subscriptions, Bots, SMART-on-FHIR
- 20 falhas periféricas (Excalidraw import, HL7v2 Redis events, TestClient API change) — não impactam core

#### GERALDA v2.0 — Acompanhamento do Paciente (port 8006)

##### Added
- **Migração para PostgreSQL**: Dockerfile agora executa `app_db:app` (DB-backed) ao invés de `app:app` (in-memory)
- **POST /api/v1/analyze**: Análise longitudinal do paciente
  - Agrega planos, tarefas pendentes/vencidas, aderência ao tratamento
  - Gera alertas para baixa aderência (<50%) e tarefas vencidas
  - Gera recomendações de intervenção
- **Rotas de Chat montadas** (`/api/v1/chat`): Conversação com IA (LangChain/Ollama), criação assistida de planos
- **Rotas de Eventos montadas** (`/api/v1/events`): Pipeline de 7 estágios (normalização, dedup, enriquecimento, interpretação, execução, evidência, persistência)
- **Endpoints de educação** portados para app_db: conditions, search, material/{id}, {condition_code}
- **Endpoints de lembretes** portados para app_db: list, due, schedule, pause/resume/cancel (in-memory engine)
- **Migração Alembic inicial**: 4 tabelas (care_plans, care_tasks, reminders, educational_materials) com índices
- **Config v2.0**: Campos `llm_provider`, `ollama_url`, `ollama_model` para integração AI
- **Testes app_db**: 12 novos testes async (AsyncClient + SQLite in-memory)
- **Total**: 399 testes (387 passando + 12 novos; 6 skips por deps opcionais langchain_ollama/openai)

##### Changed
- `pyproject.toml`: packages de `src/geralda` → `geralda/` (corrige resolução de imports)
- `pyproject.toml`: coverage source de `src` → `geralda` (mede código real)
- Modelos SQLAlchemy: `JSONB` → `JSON` (compatível com SQLite em testes, funciona como JSON no PostgreSQL)
- `migrations/env.py`: lê `DATABASE_URL` de variáveis de ambiente (não mais hardcoded)
- Versão bumped: 1.0.0 → 2.0.0

### Infrastructure

#### Fixed
- Portal healthcheck corrigido: usa `127.0.0.1:80/health` ao invés de `localhost`
- Deploy script (`deploy_staging.ps1`): inclui overlay `-f docker-compose.traefik.yml`
- Traefik: `ping: {}` habilitado para healthcheck
- Rotas Traefik: health path do portal `/` → `/health`

## [0.1.0-demo] - 2026-02-20

### Added
- Estrutura modular com 15 módulos (core, wanda, florence, oswaldo, nise, geralda, grahame, zilda, donabedian, pierre, ocr, conhecimento, comunicacao, auth, portal)
- Demo local funcional com 6 backends Python + portal React
- Ambientes virtuais Python por módulo (.venv ou venv)
- Scripts de automação:
  - `start_demo.bat` - Iniciar demo completa
  - `kill_demo.bat` - Encerrar todos os serviços
  - `check_demo_health.ps1` - Smoke test de health checks
  - `setup_demo_venvs.ps1` - Configurar ambientes virtuais
- Infraestrutura Docker:
  - PostgreSQL (porta 5432)
  - Redis (porta 6379)
  - Prometheus (porta 9090)
  - Grafana (porta 3000)
- Módulo intellicare-comunicacao:
  - D1 - Engine de Roteamento (35+ arquivos, 100+ testes, 21 endpoints)
  - D2 - Integração Rocket.Chat (20 arquivos, 30+ testes, 6 endpoints)
  - D3 - Teleconsulta/Vídeo com Jitsi (15 arquivos, 50+ testes, 11 endpoints)
  - D4 - Notificações Externas (65 arquivos, 71 testes, 16 endpoints)
    - Push Notifications (VAPID/FCM)
    - WhatsApp Business API (Meta Graph API)
    - SMS (Twilio/Zenvia/SNS)
    - Email (SMTP com templates Jinja2)
  - D6 - LGPD/Auditoria (22 arquivos, 39 testes, 15 endpoints)
  - D7 - Dashboard/Monitoramento (20 arquivos, 8 dashboards Grafana, 14 alertas)
- Documentação técnica:
  - README_DEMO.md - Guia completo da demo
  - docs/PLANNER-CURSOR/ - Governança e especificações
  - Fase 1 (Estabilização) - Especificações e relatórios
  - Fase 2 (Organização Git) - Especificações técnicas e plano
- Controle de versão:
  - .gitignore completo (Python, venv, .env, Node.js, IDEs)
  - Estratégia de branches documentada
  - Processo de release documentado

### Changed
- Migração de Matrix/Synapse (legacy) para Rocket.Chat + Jitsi (V5 oficial)
- Padronização de health checks em todos os módulos
- Isolamento de dependências Python por módulo

### Fixed
- Estabilização da demo local (Fase 1)
- Correção de scripts de inicialização e encerramento
- Ajustes em endpoints de health check

### Security
- Proteção de credenciais via .env (não versionado)
- .gitignore configurado para evitar vazamento de dados sensíveis
- LGPD compliance no módulo comunicacao (hash chain audit trail)

---

## Notas de Release

### v0.1.0-demo (2026-02-20)

Esta é a primeira release oficial da demo do IntelliCare .. O projeto está funcional em ambiente local e pronto para evolução governada através do fluxo ARQUITETO → PLANEJADOR → Agentes Desenvolvedores.

**Pré-requisitos para executar a demo:**
- Docker Desktop instalado e rodando
- Python 3.11+ instalado
- Node.js 18+ instalado (para o portal)
- Git instalado

**Como executar:**
1. Iniciar infraestrutura: `.\start-infrastructure.ps1`
2. Aguardar serviços subirem (~30 segundos)
3. Iniciar demo: `.\start_demo.bat`
4. Verificar saúde: `.\check_demo_health.ps1`

**Endpoints principais:**
- Portal: http://localhost:3000
- Wanda (Triagem): http://localhost:8001
- Florence (Exames): http://localhost:8002
- Oswaldo (Condições Crônicas): http://localhost:8003
- Nise (Medicamentos): http://localhost:8004
- Comunicacao: http://localhost:8005
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

**Próximos passos:**
- Fase 3: Deploy Mínimo (CI/CD, ambientes)
- Fase 4: Monitoramento (alertas avançados)
- Fase 5: Produção Ready (auth Keycloak, hardening)

