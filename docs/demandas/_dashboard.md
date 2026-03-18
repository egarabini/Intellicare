# IntelliCare V3 — Dashboard de Demandas

> Atualizado: 2026-03-18 | Branch: main | Último commit: e572dba

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
| — | Fila vazia — aguardando próxima spec | — | — |

---

## 📋 Fila — specs prontas para distribuir

| DEM | Título | Spec |
|-----|--------|------|
| DEM-040 | CarePlanner UI Completo — lista paginada, detalhe+timeline, modal Nova Jornada, encerrar, link vídeo | ✅ pronta em `docs/demandas/DEM-040_CAREPLANNER_UI/` |
| DEM-041 | Templates CarePlanner — CRUD backend (4 endpoints), seed 4 defaults, página GestorUI, TriggerModal Select | ✅ pronta em `docs/demandas/DEM-041_TEMPLATES_CAREPLANNER/` |

---

## Distribuição sugerida para devs disponíveis

```
DEV-A      → DEM-040 — em execução (Codex)
DEV-B      → DEM-041 — spec pronta, pode iniciar em paralelo
DEV-C      → livre
Eduardo    → Deploy staging (DEM-038 completa após Fase D):
             ⚠ Pendentes antes do deploy staging:
             [ ] Firewall VPS: abrir UDP 10000 (Jitsi JVB)
             [ ] PostgreSQL staging: CREATE DATABASE kestra;
             [ ] Gerar segredos reais no .env.staging:
                 ROCKETCHAT_WEBHOOK_TOKEN, JITSI_APP_SECRET,
                 JICOFO_AUTH_PASSWORD, JVB_AUTH_PASSWORD
             DNS staging: ✅ chat / meet / kestra.intellicare.ia.br configurados
             Após Fase D commitada:
               git pull + docker compose --env-file infra/.env.staging up -d --build
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
