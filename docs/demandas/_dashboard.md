# IntelliCare V3 — Dashboard de Demandas

> Atualizado: 2026-03-15 | Branch: main | Último commit: bc796d1

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
| DEM-023 | Deploy Produção (VPS + DNS + SSL + Traefik) | Eduardo | aguardando DNS + VPS |

---

## 📋 Fila — specs prontas para distribuir

| DEM | Título | Arquivo spec | Pode paralelo com |
|-----|--------|-------------|-------------------|
| DEM-023 | Deploy Produção (VPS + DNS + SSL) | `DEM-023_DEPLOY_PRODUCAO/02_TECNICA.md` | independente |
| DEM-030 | Administrativo Completo (Servidores, Módulos, Financeiro, Usuários Admin) | `DEM-030_ADMINISTRATIVO_COMPLETO/02_TECNICA.md` | DEM-031 |
| DEM-032 | Clínico Gestão (Grupos, Profissionais, Equipe) | `DEM-032_CLINICO_GESTAO/02_TECNICA.md` | pode iniciar — migration 005 já aplicada |

---

## 🗓️ Planejadas (sem spec ainda)

| DEM | Título | Prioridade |
|-----|--------|-----------|
| DEM-026 | Notificações em tempo real (WebSocket / SSE) | Média |
| DEM-027 | Relatórios PDF exportáveis | Média |
| DEM-028 | Alertas Grafana (Alertmanager — e-mail + Slack) | Baixa |
| DEM-029 | Agendamento de consultas (ClinicoUI + PacienteUI integrado) | Alta |

---

## Distribuição sugerida para devs disponíveis

```
DEV-A      → DEM-030  Administrativo Completo (maior escopo — 4 áreas)
DEV-B      → ✅ DEM-031 entregue! Próximo: suporte a DEM-032 ou DEM-030
DEV-C      → DEM-032  Clínico Gestão (migration 005 já aplicada — pode iniciar)
Eduardo    → DEM-023  Deploy Produção (requer ação manual: VPS + DNS)
```

## Credenciais de teste (ambiente local)

| Usuário | Senha | Módulo |
|---------|-------|--------|
| `platform-admin` | `Admin@2025!` | AdminUI — `http://127.0.0.1:9000/admin-ui/` |
| `gestor.alfa` | `Demo@1234` | GestorUI — `http://127.0.0.1:9000/gestor-ui/` |
| `dr.silva` | `Demo@1234` | ClinicoUI — `http://127.0.0.1:9000/clinico-ui/` |
| `paciente.alfa` | `Demo@1234` | PacienteUI — `http://127.0.0.1:9000/paciente-ui/` |

## Ação pendente (Eduardo — DNS)

Antes de executar DEM-023, criar registros DNS:
```
A  admin.intellicare.ia.br   → IP do VPS
A  api.intellicare.ia.br     → IP do VPS
A  auth.intellicare.ia.br    → IP do VPS
```
