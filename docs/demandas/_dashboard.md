# IntelliCare V3 — Dashboard de Demandas

> Atualizado: 2026-03-18 | Branch: main | Último commit: 9ff6a05 (DEM-INF Staging) | Próxima: DEM-047

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

¹ DEM-044 e DEM-045 compartilham o commit `d7a61dd` — arquivos de ambas as DEMs entraram agrupados na mesma entrega. Código verificado e funcional em ambas.

### Fixes colaterais aplicados no DEM-024

| Fix | Arquivo | Impacto |
|-----|---------|---------|
| `VITE_KEYCLOAK_URL` ausente | `frontend/PacienteUI/.env` | OIDC authority `undefined` → login quebrado |
| `redirect_uri` errado | `frontend/ClinicoUI` (OIDC config) | `/clinico-ui/callback` → `/clinico-ui/` — SPA não tem fallback de subrota |
| Rebuild ClinicoUI + PacienteUI | `static/clinico-ui/`, `static/paciente-ui/` | Builds atualizados no container |

---

## 🔄 Em execução

| DEM | Título | Dev | Status |
|-----|--------|-----|--------|
| DEM-044 | Criar Videoconsulta GestorUI | DEV-1 | ✅ Commitado `d7a61dd` (agrupado com DEM-045) |
| DEM-045 | CarePlanner ClinicoUI | DEV-2 | ✅ Commitado `d7a61dd` |
| DEM-046 | CI/CD Pipeline GitHub Actions | CODEX | ✅ Commitado `0c88a9d` |
| DEM-INF | Staging Script | DEV-3/4 | ✅ Commitado `9ff6a05` |
| **DEM-047** | **WhatsApp via Evolution API** | **DEV-1** | ⏳ Spec pronta — aguardando execução |

---

## 📋 Fila — specs prontas para distribuir

| DEM | Título | Dev | Spec |
|-----|--------|-----|------|
| DEM-044 | Criar Videoconsulta — hook useCreateVideoSession, modal patient_url + CopyButton | DEV-1 | ✅ `docs/demandas/DEM-044_VIDEO_SESSION_UI/` |
| DEM-045 | CarePlanner ClinicoUI — useCareplanner.ts, CareplannerPage, CareplannerDetail, NavLink badge REPLIED | DEV-2 | ✅ `docs/demandas/DEM-045_CAREPLANNER_CLINICO/` |
| DEM-046 | CI/CD GitHub Actions — pytest + build GestorUI + ClinicoUI, badge README | CODEX | ✅ `docs/demandas/DEM-046_CI_CD_PIPELINE/` |
| DEM-INF | Staging Script — staging_update.sh, .env.staging.example, deploy/README.md | DEV-3/4 | ✅ `docs/demandas/DEM-INF_STAGING_SCRIPT/` |
| **DEM-047** | **WhatsApp via Evolution API — WhatsAppAdapter, webhook, TriggerModal canal, Kestra flow** | **DEV-1** | ✅ `docs/demandas/DEM-047_WHATSAPP_EVOLUTION/` |

> **Próximas na esteira (a especificar):**
> DEM-048 — E-mail via Listmonk (canal 3 do CarePlanner)
> DEM-049 — SMS via Jasmin (canal 4 do CarePlanner)

---

## Distribuição sugerida para devs disponíveis

```
DEV-1      → DEM-047 (WhatsApp Evolution API — ~3.5h)
DEV-2      → aguardando nova DEM
CODEX      → aguardando nova DEM
DEV-3/4    → aguardando nova DEM
```

## Credenciais de teste (ambiente local)

| Usuário | Senha | Módulo |
|---------|-------|--------|
| `platform-admin` | `Admin@2025!` | AdminUI — `http://127.0.0.1:9000/admin-ui/` |
| `gestor.alfa` | `Demo@1234` | GestorUI — `http://127.0.0.1:9000/gestor-ui/` |
| `dr.silva` | `Demo@1234` | ClinicoUI — `http://127.0.0.1:9000/clinico-ui/` |
| `paciente.alfa` | `Demo@1234` | PacienteUI — `http://127.0.0.1:9000/paciente-ui/` |

## Ações pendentes

**Staging — aplicar DEM-030 a DEM-036 (statics novos incluídos no build):**
```bash
cd /opt/intellicare && git pull origin main
docker compose --env-file infra/.env.staging -f infra/docker-compose.yml \
  build --no-cache intellicare-service
docker compose --env-file infra/.env.staging -f infra/docker-compose.yml \
  up -d intellicare-service
```

**⚠️ Gitignore — artefatos de build entraram nos commits DEM-035/036:**
Adicionar ao `.gitignore` (ou ao `frontend/.gitignore`):
```
frontend/AdminUI/build_admin.txt
frontend/AdminUI/build_out.txt
tests/e2e/report/
```

**Produção — DNS subdomínios (Eduardo):**
```
A  admin.intellicare.ia.br   → IP do VPS de produção
A  api.intellicare.ia.br     → IP do VPS de produção
A  auth.intellicare.ia.br    → IP do VPS de produção
```
