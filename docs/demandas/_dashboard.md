# IntelliCare V3 — Dashboard de Demandas

> Atualizado: 2026-03-26 | Branch: main | Último commit: cc62729 (feat(platform): migration 025 keycloak_user_mapping) | Sprint: 2026-06-06 ⏳ Em andamento

---

## ⚠️ Processo obrigatório por DEM

Todo dev que executa uma DEM **deve** produzir os 5 arquivos abaixo. Entregas sem esses arquivos **não são aceitas**:

| Arquivo | Quando | Conteúdo mínimo |
|---------|--------|-----------------|
| `01_FUNCIONAL.md` | Criado pelo ARQUITETO | Escopo, critério de aceite — não alterar |
| `02_TECNICA.md` | Criado pelo ARQUITETO | Spec técnica — atualizar se houver divergência do real |
| `03_PLANO.md` | **Dev cria/confirma ANTES de implementar** | Passos, gotchas, restrições — deve existir antes do primeiro commit |
| `04_DIARIO.md` | **Dev preenche DURANTE a implementação** | Decisões tomadas, problemas encontrados, adaptações ao código real |
| `05_FINALIZACAO.md` | **Dev cria ao entregar** | Commit hash, testes passando, o que mudou vs spec |

> **Regra de aceite:** o ARQUITETO só registra o hash no dashboard quando `04_DIARIO.md` e `05_FINALIZACAO.md` existirem e tiverem conteúdo real — não placeholders.

---

## ✅ Concluídas (DEMs 000–025)

| DEM | Título | Commit |
|-----|--------|--------|
| DEM-000 a DEM-017 | Infraestrutura, backend, frontends base, seed | vários |
| DEM-018 | Admin Módulo Completo + Traefik SSL | `51465d0` |
| DEM-019 | Gestor Módulo Completo | `c01d007` |
| DEM-020 | Clínico Frontend Completo (AppShell, RoleGuard, Dashboard, Agenda, PatientProfile, EncounterView+CID10, AIAssistant) | `6d9a5c4` |
| DEM-021 | Fix Frontends — token síncrono GestorUI + rebuild Docker | `1911a3a` |
| DEM-022 | Portal do Paciente — 6 páginas + backend + Keycloak client | `3f5a615` |
| DEM-024 | Testes E2E Playwright — 13/13 passando em 1.2min, 4 workers (Admin 4, Clínico 3, Gestor 3, Paciente 3) | `0418bc4` |
| DEM-025 | Observabilidade — Prometheus v2.51 + Grafana v10.4, 5 targets UP, 10 panels | `45c0d0b` |
| DEM-031 | Gestão Completa — 4 tabelas, 11 endpoints, 3 páginas (Units, UnitDetail, TenantUsers) | `bc796d1` |
| DEM-033 | Portal — EnvironmentSelector modal (4 ambientes) + Fix Traefik HTTP `intellicare.ia.br` | `2f49d54` |
| DEM-INF | Infra — Dockerfile multi-stage Node+Python, docker-compose.dev.yml, fix static files staging | `a94cfcd` |
| DEM-INF | Fix .dockerignore excluía frontend/ do contexto Docker | `a2390eb` |
| DEM-INF | Fix Dockerfile: npm ci → npm install (sem package-lock.json em 3 frontends) | `9639e61` |
| DEM-INF | Fix Traefik: downgrade v3.2 → v2.11.31 (API Docker 1.24 incompatível com v3.x no VPS) | `59fd4c1` |
| DEM-INF | Fix Traefik: routers explicitam service (admin/api/portal) | `41f159a` |
| DEM-023 | Deploy Staging — HTTPS ativo, Let's Encrypt emitido, 5 endpoints validados ✅ | `41f159a` |
| DEM-032 | Clínico Gestão — migration 006, 16 endpoints, 4 páginas (Groups, GroupDetail, Professionals, ClinicalUsers) | `04c5d37` |
| DEM-034 | Fix Traefik: redirectregex admin.intellicare.ia.br/ → /admin-ui/ | `0ce31e0` |
| DEM-030 | Administrativo Completo — migration 004, 31 endpoints, 4 páginas (Servers, Modules, Financeiro, AdminUsers) | `4bc75ce` |
| DEM-029 | Integração Agendamento ClinicoUI+PacienteUI — fallbacks backend, polling, filtros, 3 testes | `695a236` |
| DEM-026 | Notificações Realtime — 12 endpoints, SSE+WS, Redis Pub/Sub, 39 testes, migration 007 | `ceaffff` |
| DEM-028 | Alertas Grafana — 9 regras provisionadas, SMTP, Keycloak scrape, Slack pronto p/ ativar | `bd30de8` |
| DEM-027 | Relatórios PDF — WeasyPrint, 6 templates, 6 endpoints, hook useDownloadPdf nos 3 módulos | `323182b` |
| DEM-035 | Notificações Frontend — sino (NotificationBell) nos 4 módulos, SSE, badge unread, popover | `48e5ea8` |
| DEM-036 | E2E Atualizado — 14 pytest novos + 11 Playwright novos (24 total), cobertura DEM-026 a DEM-035 | `627fee2` |
| DEM-037 | AdminUI Fixes — migration gestor_email, PUT /admin/tenants/{slug}, senha admin, role badge, statics rebuilt | `b0c6f51` |
| DEM-038 Fase A | CarePlanner — contracts, config, migrations (5 tabelas), repository, 3 testes (estados, idempotência, BIGINT) | `b6a3966` |
| DEM-038 Fase B | CarePlanner — adapters RC/Jitsi/Kestra + services + routes + docker-compose (Kestra/RC/Jitsi/Mongo) + 10 testes | `a646bc2` |
| DEM-038 Fase C | CarePlanner — metrics.py (6 métricas), integrations.py (notify+trigger), dashboard/stats, CareplannerDashboard.tsx + 7 testes | `c818cc1` |
| DEM-038 Fase D | CarePlanner — dispatcher Redis+retry+dead-letter+FAILED, expiry_worker (DISPATCHED>24h/SENT>72h→EXPIRED), security.py (mask_phone/content/jwt), hardening HMAC/Jitsi, Playwright 4 E2E + 10 testes Python | `fef17db` |
| DEM-039 | Kestra Workflow CarePlanner — flows YAML (jornada_basica+video), seed_flows.py (POST Kestra 0.20), trigger_flow(), POST /journeys/trigger, smoke test JWT end-to-end | `415643e` |
| DEM-040 | CarePlanner UI Completo — lista paginada+filtro, CareplannerJourneyDetail+timeline, TriggerJourneyModal, 6 hooks TypeScript, 7 testes Playwright, OOM fix Dockerfile | `88614ac` |
| DEM-041 | Templates CarePlanner — CRUD backend (get_template, update_template, active_only), seed 4 defaults no startup, CareplannerTemplates.tsx, TriggerModal Select dinâmico, sub-nav expansível | `3fd71c3` |
| DEM-042 | Notificações CarePlanner — notify_clinico_replied persiste no banco, notify_task_expired, careplannerUnread em useNotifications, badge NavLink, navegação NotificationBell → jornada, 2 testes Python + 11 Playwright | `a6eb346` |
| DEM-INF | Fix WeasyPrint — lazy import em renderer.py, conftest skip condicional — pytest global: 59 passed, 0 collection errors | `a6eb346` |
| DEM-043 | Grafana CarePlanner Overview — 8 panels (disparos, REPLIED/h, EXPIRED/h, videoconsultas, órfãos, eventos, p95 DISPATCHED→SENT, p95 REPLIED→CLOSED), UID careplanner-overview | `a6eb346` |
| DEM-044 | Criar Videoconsulta GestorUI — useCreateVideoSession hook, botão btn-criar-video, modal patient_url + CopyButton + btn Entrar como Clínico, 1 teste Playwright | `d7a61dd` ¹ |
| DEM-045 | CarePlanner ClinicoUI — fix role CLINICO nos GETs, useCareplanner.ts, CareplannerPage (filtro Minhas), CareplannerDetail read-only, NavLink badge REPLIED, 2 testes Playwright | `d7a61dd` |
| DEM-046 | CI/CD Pipeline — GitHub Actions (pytest backend + build GestorUI + ClinicoUI), badge README, repo egarabini/Intellicare | `0c88a9d` |
| DEM-INF | Staging Script — staging_update.sh (6 etapas), .env.staging.example (todos os segredos), deploy/README.md, .gitignore protege .env.staging | `9ff6a05` |
| DEM-047 | WhatsApp via Evolution API — `WhatsAppAdapter`, webhook inbound, dispatcher multi-canal, `TriggerJourneyModal` seletor canal, Kestra flow WhatsApp, init DB `evolution`, 4 testes Phase H | `da98ce2` |
| DEM-048 | E-mail via Listmonk — `EmailAdapter`, serviço listmonk Docker, init DB `03_listmonk.sql`, Kestra flow email, seed 4 templates, opção E-mail no TriggerModal, 4 testes Phase I | `18325b3` |
| DEM-049 | SMS via Jasmin — `SMSAdapter` (truncamento 160 chars, retry), webhook /sms/{token}, Kestra flow SMS, opção SMS no TriggerModal, seed 4 templates, 4 testes Phase J | `375253a` ² |
| DEM-050 | E2E Multi-Canal — mock Evolution, 4 pytest integração WA, Playwright seletor canal, fix regressões Phases B/C/D/E (fixtures CareplannerService + dispatcher multi-canal + seed_flows) — **53 passed** | `55c820c` |
| DEM-INF | Fix Staging — `DATABASE_CONNECTION_URI` Evolution URL-safe, path seed_flows corrigido, evolution-api HTTP 200 no staging | `fbc7996` |
| DEM-INF | Memória Operacional — `docs/patterns/` (backend, frontend, workers), `docs/gotchas/` (careplanner, staging, keycloak), `_templates/HANDOFF.yml` | `7f708fb` |
| DEM-051 | Observabilidade Multicanal — `GET /health/adapters` (RC+Evolution+Listmonk+Jasmin), label `channel` em `careplanner_dispatch_total`, 4 painéis Grafana por canal | `2fa8949` |
| DEM-INF | Staging follow-up — banco `listmonk` criado, 5 vars Jasmin adicionadas ao `.env.staging`, rede Evolution OK (HTTP 200), instância `intellicare` em `close` aguarda QR | `4374f11` |
| DEM-052 | Relatórios PDF Jornadas — `get_journey_full()`, `generate_journey_report()`, `GET /journeys/{id}/report.pdf`, `journey_report.html` Jinja2, botão `IconFileTypePdf` GestorUI, 2 testes | `9ab4623` |
| DEM-053 | Staging WA Smoke — Evolution `evoapicloud/v2.3.7` (QR fix), `state: open`, Hello World entregue, secrets deletados, smoke E2E WhatsApp ✅ | `06a0b1e` |
| DEM-054 | CarePlanner × Agendamento — migration 012 `appointment_id`, `link_task_to_appointment()`, `GET /appointments/{id}/journey`, TriggerModal + JourneyDetail + AppointmentCalendar, 5 testes Phase K + 10 regressão | `945f08a` |
| DEM-055 | Florence Módulo Base — migration 013 `clinical_notes`, endpoints SOAP/FREE, `FlorenceNoteEditor`, aba "Notas Florence" em `EncounterView`, 3 testes | `e50a2c2` |
| DEM-056 | Executor Matrix ADR — `docs/adr/ADR-001-executor-matrix.md`, 24 componentes reais classificados (Worker/Agent/Hybrid/Human), referência IA-FRAMEWORK | `c571823` |
| DEM-057 | Florence IA — `suggest_soap()`, `_call_llm()` OpenAI-compatible + fallback rule-based, `POST /florence/notes/suggest`, botão Hybrid ClinicoUI, 5 testes | `29df484` |
| DEM-058 | Oswaldo Módulo Base — migration 014 UUID, `prescriptions`, busca CID-10, `OswaldoPrescriptionEditor`, aba ClinicoUI, 3 testes | `19799a2` |
| DEM-059 | Portal Paciente — `GET /cuidado/paciente/me/journeys` + `/me/clinical-notes`, `JornadasPage.tsx`, `HistoricoPage.tsx`, privacidade `soap_a`, 6 testes | `d714194` |
| DEM-061 | Oswaldo IA — `POST /oswaldo/suggest`, `shared/llm` wrapper, fallback rule-based, botão Hybrid `OswaldoPrescriptionEditor`, 5 testes (422, 403, success, fallback, LLM mock) | `9d14751` |
| DEM-062 | PDF Clínico — `get_encounter_full()`, `generate_clinical_report()`, template Florence+Oswaldo, `GET /encontros/{id}/report.pdf`, botão `IconFileTypePdf` EncounterView, 2 testes | `d4552c6` |
| DEM-063 | E2E Clinical Squad — 8 pytest (Florence, Oswaldo, Portal) + 5 Playwright (florence, oswaldo, paciente) = 13 testes E2E | `6708521` |
| DEM-INF | Fix Redis pubsub — `redis_pubsub.py` usa `REDIS_PASSWORD_URLENC` em vez de senha bruta (fix `Port could not be cast` no staging) | `c7fabecc` |
| DEM-INF | Fix ClinicoUI Docker build — `optimizeDeps.include: ['@tanstack/react-query']` em `vite.config.ts` (Vite SSR/Docker não pré-bundlava dependência) | `055e883` |
| DEM-INF | Fix Portal Agentes — rename imagens `*_ia.png` → sem sufixo em `public/agents/`, referências atualizadas em `Agents.tsx` | `0807431` |
| DEM-INF | Fix DEM-068 staging — Dockerfile copia `db/`+`tools/`, push_subscriptions criada, Kestra aceita `multipart/form-data` | `d7cc7cc8` |

¹ DEM-044 e DEM-045 compartilham o commit `d7a61dd` — arquivos de ambas as DEMs entraram agrupados na mesma entrega. Código verificado e funcional em ambas.
² DEM-049 incluiu antecipadamente `Channel.EMAIL` em `contracts.py` — DEV-1 (DEM-048) deve fazer `git pull --rebase` antes de commitar para evitar conflito nessa linha.

### Fixes colaterais aplicados no DEM-024

| Fix | Arquivo | Impacto |
|-----|---------|---------|
| `VITE_KEYCLOAK_URL` ausente | `frontend/PacienteUI/.env` | OIDC authority `undefined` → login quebrado |
| `redirect_uri` errado | `frontend/ClinicoUI` (OIDC config) | `/clinico-ui/callback` → `/clinico-ui/` — SPA não tem fallback de subrota |
| Rebuild ClinicoUI + PacienteUI | `static/clinico-ui/`, `static/paciente-ui/` | Builds atualizados no container |

---

## ✅ Sprint 2026-03-21 — Concluída

| DEM | Título | Dev | Commit |
|-----|--------|-----|--------|
| DEM-INF | Staging follow-up — listmonk DB, Jasmin vars, rede Evolution OK | DEV-3/4 | `4374f11` |
| DEM-INF | Memória Operacional — patterns, gotchas, HANDOFF template | CODEX | `7f708fb` |
| DEM-051 | Observabilidade Multicanal — healthcheck + Grafana por canal | DEV-2 | `2fa8949` |
| DEM-052 | Relatórios PDF Jornadas — WeasyPrint + botão GestorUI | DEV-1 | `9ab4623` |

---

## ✅ Sprint 2026-03-28 — Concluída

| DEM | Título | Dev | Commit |
|-----|--------|-----|--------|
| DEM-053 | Staging WA Smoke — Evolution `evoapicloud/v2.3.7`, QR + Hello World | DEV-3/4 + Eduardo | `06a0b1e` |
| DEM-054 | CarePlanner × Agendamento — link bidirecional, 5+10 testes | DEV-1 | `945f08a` |
| DEM-055 | Florence Módulo Base — notas SOAP/FREE, aba ClinicoUI | DEV-2 | `e50a2c2` |
| DEM-056 | Executor Matrix ADR — 24 componentes, Camada 2 IA-FRAMEWORK | CODEX | `c571823` |

---

## ✅ Sprint 2026-04-04 — Concluída

| DEM | Título | Dev | Commit |
|-----|--------|-----|--------|
| DEM-057 | Florence IA — suggest SOAP, LLM + fallback, 5 testes | DEV-2 | `29df484` |
| DEM-058 | Oswaldo Módulo Base — migration 014, CID-10, prescrições, 3 testes | DEV-1 | `19799a2` |
| DEM-059 | Portal Paciente — jornadas + histórico, privacidade soap_a, 6 testes | CODEX | `d714194` |
| DEM-060 | Staging Full Sync — migrations 012–014, Florence+Oswaldo UP, Clinical Squad smoke ✅ | DEV-3/4 | `af3e66bb` |

---

## ✅ Sprint 2026-04-11 — Concluída

| DEM | Título | Dev | Commit |
|-----|--------|-----|--------|
| DEM-061 | Oswaldo IA — sugestão CID-10 + prescrição via LLM, 5 testes | DEV-2 | `9d14751` |
| DEM-062 | PDF Clínico — WeasyPrint Florence+Oswaldo, EncounterView | DEV-1 | `d4552c6` |
| DEM-063 | E2E Clinical Squad — 8 pytest + 5 Playwright, 13 testes | CODEX | `6708521` |
| DEM-064 | Staging Clinical Squad Validation — Florence ✅ Oswaldo ✅ PDF ✅ Evolution open ✅ Adapters ✅ | DEV-3/4 | `af3e66bb` |

---

## ✅ Sprint 2026-04-18 — Concluída

| DEM | Título | Dev | Commit |
|-----|--------|-----|--------|
| DEM-065 | Multi-tenant Avançado — `tenant_provisioner`, migration 015, TenantsManager + TenantConfigPage, suspend/reactivate, 16 testes | DEV-1 | `683c0f9` |
| DEM-066 | Notificações Push PWA — migration 016, `push_sender.py`, endpoints subscribe/unsubscribe/vapid, `sw.js`+`manifest.json` ClinicoUI+GestorUI, toggle NotificationBell | DEV-2 | `98d0310f` |
| DEM-067 | Kestra Flows Condicionais — 4 flows (fallback canal, branching resposta, retry backoff, urgência clínica), normalize_confirmation, 24 testes | CODEX | `5b7e1a42` |
| DEM-068 | Staging Full Sync 2026-04-18 — provision ✅ push/subscribe ✅ Kestra trigger ✅ adapters ✅ Evolution open ✅ Florence ✅ | DEV-3/4 | `772a1dd` |

---

## ✅ Sprint 2026-04-25 — Concluída

| DEM | Título | Dev | Commit |
|-----|--------|-----|--------|
| DEM-071 | Linha do Tempo Clínica — timeline unificada encounters+notes+prescriptions+journeys, UNION ALL query, ClinicalTimeline.tsx | DEV-2 | `ef40df8` |
| DEM-072 | Receituário Digital — template Jinja2 CFM/ANVISA, posologia formal, simple/special_control, WeasyPrint | DEV-1 | `7d1c6a9` |
| DEM-073 | Prompt Versioning — migration 017 `prompt_templates`, `get_active_prompt()`, AdminUI PromptsPage, versionamento + rollback | CODEX | `60f2619` |
| DEM-074 | Staging Sync 2026-04-25 — migration 017 ✅ timeline ✅ receituário ✅ prompts ✅ AdminUI ✅ 22/22 testes | DEV-1 | `33b7435` |

---

## ✅ Sprint 2026-05-02 — Concluída

| DEM | Título | Dev | Commit |
|-----|--------|-----|--------|
| DEM-075 | Marie Bootstrap — Dify stack, `marie_client.py`, `MARIE_ENABLED`, `cid10_rag` proof-of-concept | CODEX | `6ed6281` |
| DEM-076 | Portal Paciente Avançado — timeline + receituário PacienteUI, filtro privacidade SOAP | DEV-2 | `8e5fa8a` |
| DEM-077 | Oswaldo Interação Medicamentosa — checker estático + LLM fallback, `InteractionWarningBanner` | DEV-1 | `3105284` |
| DEM-078 | Staging Sync 2026-05-02 — Marie UP ✅ interações ✅ portal ✅ 018 migration ✅ suite testes ✅ | DEV-1 | `a4b2b94` |

---

## ✅ Sprint 2026-05-09 — Concluída

| DEM | Título | Dev | Commit |
|-----|--------|-----|--------|
| DEM-079 | Florence via Marie RAG — workflow `florence_soap_rag`, SOAP contextualizado com timeline, `MARIE_ENABLED` ativo | CODEX | `868cf09` |
| DEM-080 | Assinatura Digital Receituário — ICP-Brasil A1 (.pfx), `pyhanko`, endpoint upload certificado, PDF assinado | DEV-1 | `b9f9749` |
| DEM-081 | GestorUI KPIs Clínicos — dashboard prescrições/médico, interações detectadas, notas Florence, jornadas CarePlanner | DEV-2 | `bd33879` |
| DEM-082 | Staging Sync 2026-05-09 — Marie ativo, PDF assinado, KPIs, migrations 019/020, 7/7 testes | DEV-1 | `edfd613` |

---

## ✅ Sprint 2026-05-16 — Concluída

| DEM | Título | Dev | Commit |
|-----|--------|-----|--------|
| DEM-083 | ADR-004 + Identity Foundation — `platform.pessoa*`, migration 021, identity service, find-or-create CPF | CODEX | `e19230a` |
| DEM-084 | Patient Identity Integration — `paciente.pessoa_id`, find-or-create no cadastro, vínculo LGPD | DEV-2 | `76d19de` |
| DEM-085 | Saneamento Técnico — git audit CODEX, Redis auth CarePlanner, clinical_notes UUID, test fix | DEV-1 | `362e682` |
| DEM-086 | Staging Sync 2026-05-16 — migrations 021/022/023, identity smoke, patient pessoa_id confirmado | DEV-1 | `57520f2` |

---

## ✅ Sprint 2026-05-23 — Concluída

| DEM | Título | Dev | Commit |
|-----|--------|-----|--------|
| DEM-087 | Infra Identity Fix — JWT issuer alignment + Traefik `/api/identity/*` | DEV-1 | `6abf345` ✅ |
| DEM-088 | Professional Identity Integration — `professionals.pessoa_id`, migration 024 | DEV-2 | `159bfe4` ✅ |
| DEM-089 | Identity Reconciliation + Admin View — backfill pacientes legados + IdentityPage AdminUI | CODEX | `3a9f386` ✅ |
| DEM-090 | Staging Sync 2026-05-23 — migration 024, intellicare-service healthy, 2/6 smokes (4 skip Keycloak) | DEV-1 | `30b30ec` ✅ |
| hotfix | DEM-089 list_tenants: `deleted_at` → `status = 'active'` — reconcile 200, 100/100 pacientes vinculados | CODEX | `0eae002` ✅ |

---

## ✅ Sprint 2026-05-30 — Concluída

| DEM | Título | Dev | Commit |
|-----|--------|-----|--------|
| DEM-091 | VPS Deploy 2026-05-30 — reset hard origin/main, 6/6 smokes, worktrees limpos | DEV-1 | `a40dce8` ✅ |
| DEM-092 | pgAdmin + Keycloak Admin Access — pgAdmin no stack, URL/credenciais KC documentadas | DEV-1 | `8e0f897` ✅ |

---

## ⏳ Sprint 2026-06-06 — Em andamento

| DEM | Título | Dev | Status |
|-----|--------|-----|--------|
| DEM-093 | DB Migration Sync Staging — migrations 005/006/017/019/020/022/023/024 + 025(keycloak_user_mapping) aplicadas; rerun 1.2/1.2b/1.3 ✅ concluído | CODEX + Eduardo | ✅ `cc62729` |
| DEM-INF | Fix Keycloak proxy headers — `KC_HOSTNAME_URL` + `KC_HOSTNAME_ADMIN_URL` no compose (issuer retornava `http://`) | Eduardo | ✅ `1fa8b8d` — issuer `https://` confirmado no VPS ✅ |
| DEM-094 | Portal: Identidade Visual IntelliCare — tema Mantine compartilhado, Header/Navbar, tokens, refatoração componentes, Guia Visual | GEMINI | ⏳ Spec pronta — aguarda 03_PLANO |

---

## 🔬 Backlog Estratégico — aguarda gatilho

| DEM | Módulo | Descrição | Gatilho |
|-----|--------|-----------|---------|
| DEM-069 | **Marie** (Orquestradora IA) | Bootstrap Dify como microsserviço parceiro — `marie_client.py`, flag `MARIE_ENABLED`, migração do primeiro flow Oswaldo prescrição → Marie RAG | ✅ **Gatilho atingido** — DEM-075 em execução |
| DEM-070 | **MinIO** (Storage Médico) | Object storage S3-compatible self-hosted — `storage.py`, buckets por tenant, presigned URLs, isolamento LGPD | Primeira demanda de upload de exame real (DICOM/laudo/ECG) **ou** PDFs clínicos precisarem ser persistidos **ou** pressão de anexos WhatsApp no PostgreSQL |

> **ADR Marie:** `docs/adr/ADR-002-marie-dify-orchestrator.md` — Marie Curie: cria os instrumentos para medir o invisível. Processa históricos complexos e RAG antes de entregar resposta validada ao Oswaldo/Florence. Não substitui — **amplifica**.
>
> **ADR MinIO:** `docs/adr/ADR-003-minio-medical-storage.md` — Storage S3-compatible self-hosted para exames, anexos e laudos. Zero vendor lock-in, LGPD-compliant, um container Docker. Complementa Marie: exames no MinIO → indexados por Marie → contexto RAG enriquecido.

## Credenciais de teste (ambiente local)

| Usuário | Senha | Módulo |
|---------|-------|--------|
| `platform-admin` | `Admin@2025!` | AdminUI — `http://127.0.0.1:9000/admin-ui/` |
| `gestor.alfa` | `Demo@1234` | GestorUI — `http://127.0.0.1:9000/gestor-ui/` |
| `dr.silva` | `Demo@1234` | ClinicoUI — `http://127.0.0.1:9000/clinico-ui/` |
| `paciente.alfa` | `Demo@1234` | PacienteUI — `http://127.0.0.1:9000/paciente-ui/` |

## Ações pendentes

### ✅ PostgreSQL staging — banco 100% sincronizado (`cc62729`)

Concluído em 2026-03-26. Todas as migrations aplicadas (DEM-093 + 025). Rerun formal das seções 1.2, 1.2b e 1.3 do `PLANO_VALIDACAO_STAGING_2026_03_25.md` fechado — todos os itens `[x]`. Divergências registradas em `DEM-093/04_DIARIO.md` e corrigidas no código (`021` + `03_PLANO` + `02_TECNICA`).

### ✅ Fix Keycloak issuer HTTPS — concluído (`1fa8b8d`)

`KC_HOSTNAME_URL=https://auth.intellicare.ia.br` no compose e no `.env.staging`. Issuer retorna `https://` ✅.

### 🟡 .tmp_staging_fix — remoção final (requer admin)

Diretório físico persiste com ~28 junction points de pytest-cache. Requer PowerShell elevado:

```powershell
Remove-Item -Path "C:\Users\egara\INTELLICARE\.tmp_staging_fix" -Recurse -Force
```

`git worktree list` já está limpo — isso é apenas housekeeping do filesystem.

### ✅ DEV-4 catch-up

~~Aplicar `DOCUMENTACAO/SPRINTS/CATCHUP_DEV4_CONSOLIDADO.md` — 5 blocos, 12 ações.~~
Concluído em 2026-03-25. Blocos 1–4 já estavam aplicados; Bloco 5 (sprint 2026-05-23) aplicado agora.
Todos os DELTAs marcados como `✅ Aplicado` em `DOCUMENTACAO/SPRINTS/README.md`.

### ✅ Concluído nesta sessão (2026-03-25)

- Keycloak restart loop resolvido — causa raiz: `intellicare-service` usando `infra/.env` em vez de `infra/.env.staging`
- `POST /identity/pessoas → 201` validado localmente
- DEM-089 hotfix: `WHERE deleted_at IS NULL` → `WHERE status = 'active'` (`0eae002`) — reconcile 200, 100/100 pacientes
- Migration 024 aplicada manualmente em staging
- 405 em `https://api.intellicare.ia.br` → confirmado ser VPS desatualizado, não código local
