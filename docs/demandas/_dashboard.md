# IntelliCare V3 — Dashboard de Demandas

> Atualizado: 2026-03-14 | Branch: main | Último commit: 6d9a5c4

## ✅ Concluídas (DEMs 000–022)

| DEM | Título | Commit |
|-----|--------|--------|
| DEM-000 a DEM-017 | Infraestrutura, backend, frontends base, seed | vários |
| DEM-018 | Admin Módulo Completo + Traefik SSL | `51465d0` |
| DEM-019 | Gestor Módulo Completo | `c01d007` |
| DEM-020 | Clínico Frontend Completo (AppShell, RoleGuard, Dashboard, Agenda, PatientProfile, EncounterView+CID10, AIAssistant) | `6d9a5c4` |
| DEM-021 | Fix Frontends — token síncrono GestorUI + rebuild Docker | `1911a3a` |
| DEM-022 | Portal do Paciente — 6 páginas + backend + Keycloak client | `3f5a615` |

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
| DEM-024 | Testes E2E (Playwright) | `DEM-024_TESTES_E2E/02_TECNICA.md` | DEM-025 |
| DEM-025 | Observabilidade (Prometheus + Grafana) | `DEM-025_OBSERVABILIDADE/02_TECNICA.md` | DEM-024 |

---

## 🗓️ Planejadas (sem spec ainda)

| DEM | Título | Prioridade |
|-----|--------|-----------|
| DEM-026 | Notificações em tempo real (WebSocket / SSE) | Média |
| DEM-027 | Relatórios PDF exportáveis | Baixa |

---

## Distribuição sugerida para devs disponíveis

```
DEV-A → DEM-024  Testes E2E Playwright (spec em criação)
DEV-B → DEM-025  Observabilidade Prometheus + Grafana (spec em criação)
Eduardo → DEM-023  Deploy Produção (requer ação manual: VPS + DNS)
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
