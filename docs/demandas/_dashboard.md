# IntelliCare V3 — Dashboard de Demandas

> Atualizado: 2026-03-16 | Branch: main | Último commit: 627fee2

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
| — | Nenhuma demanda técnica em aberto | — | — |

---

## 📋 Fila — specs prontas para distribuir

Nenhuma demanda com spec pronta aguardando. Todos os devs disponíveis.

---

## Distribuição sugerida para devs disponíveis

```
DEV-A      → ✅ DEM-035 entregue! Disponível — aguardando próxima spec
DEV-B      → ✅ DEM-036 entregue! Disponível — aguardando próxima spec
DEV-C      → Disponível — aguardando próxima spec
Eduardo    → Deploy staging pendente (DEM-035 + DEM-036 + statics)
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
