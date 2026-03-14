# IntelliCare V3 — Dashboard de Demandas

> Atualizado: 2026-03-14 | Branch: main | Último commit: c8a1123

## ✅ Concluídas (DEMs 000–019)

| DEM | Título | Commit |
|-----|--------|--------|
| DEM-000 a DEM-017 | Infraestrutura, backend, frontends base, seed | vários |
| DEM-018 | Admin Módulo Completo + Traefik SSL | `51465d0` |
| DEM-019 | Gestor Módulo Completo | `c01d007` |

---

## 🔄 Em execução

| DEM | Título | Dev | Status |
|-----|--------|-----|--------|
| DEM-020 | Clínico Frontend Completo | dev em andamento | em desenvolvimento |
| DEM-021 | Fix Frontends (GestorUI token + rebuild Docker) | — | **spec pronta** |

---

## 📋 Fila — specs prontas para distribuir

| DEM | Título | Arquivo spec | Pode paralelo com |
|-----|--------|-------------|-------------------|
| DEM-021 | Fix GestorUI token + rebuild Docker | `DEM-021_FIX_FRONTENDS/02_TECNICA.md` | DEM-020, DEM-022 |
| DEM-022 | Portal do Paciente (novo frontend) | `DEM-022_PACIENTE_PORTAL/02_TECNICA.md` | DEM-020, DEM-021 |
| DEM-023 | Deploy Produção (VPS + DNS + SSL) | `DEM-023_DEPLOY_PRODUCAO/02_TECNICA.md` | após DEM-021 estável |

---

## 🗓️ Planejadas (sem spec ainda)

| DEM | Título | Prioridade |
|-----|--------|-----------|
| DEM-024 | Testes E2E (Playwright) | Média |
| DEM-025 | Observabilidade (Prometheus + Grafana) | Média |

---

## Distribuição sugerida para devs parados

```
DEV-A → DEM-021  Fix GestorUI token + rebuild Docker (< 2h)
DEV-B → DEM-022  Portal do Paciente (novo projeto frontend, ~1 dia)
DEV-C → DEM-020  Clínico Frontend (já em andamento)
Eduardo → DEM-023  Deploy Produção (requer ação manual: VPS + DNS)
```

## Credenciais de teste (ambiente local)

| Usuário | Senha | Módulo |
|---------|-------|--------|
| `platform-admin` | `Admin@2025!` | AdminUI — `http://127.0.0.1:9000/admin-ui/` |
| `gestor.alfa` | `Demo@1234` | GestorUI — `http://127.0.0.1:9000/gestor-ui/` |
| `dr.silva` | `Demo@1234` | ClinicoUI — `http://127.0.0.1:9000/clinico-ui/` |
| `paciente.alfa` | `Demo@1234` | PacienteUI — após DEM-022 |

## Ação pendente (Eduardo — DNS)

Antes de executar DEM-023, criar registros DNS:
```
A  admin.intellicare.ia.br   → IP do VPS
A  api.intellicare.ia.br     → IP do VPS
A  auth.intellicare.ia.br    → IP do VPS
```
