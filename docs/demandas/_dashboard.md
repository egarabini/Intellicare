# IntelliCare V3 — Dashboard de Demandas

> Atualizado: 2026-03-14 | Branch: main | Último commit: 51465d0

## Status Geral

| DEM | Título | Status | Commit |
|-----|--------|--------|--------|
| DEM-000 | Limpeza e bootstrap do repo V3 | ✅ Concluído | — |
| DEM-001 | Estrutura de pacotes Python | ✅ Concluído | — |
| DEM-002 | Infraestrutura Docker (postgres/redis/keycloak/ollama/traefik) | ✅ Concluído | `a3e4184` |
| DEM-003 | Core: settings, DB, middleware, ModuleLoader | ✅ Concluído | — |
| DEM-004 | Módulo Admin (backend) | ✅ Concluído | — |
| DEM-005 | Módulo Gestor (backend) | ✅ Concluído | — |
| DEM-006 | Admin Frontend (React + Vite + Mantine) | ✅ Concluído | `3683878` |
| DEM-007 | Módulo Cuidado/Clínico (backend) | ✅ Concluído | — |
| DEM-008 | Módulo SLM / OLLAMA | ✅ Concluído | `bdd94f6` |
| DEM-009 | Módulo Financeiro | ✅ Concluído | — |
| DEM-010 | Módulo RAG | ✅ Concluído | — |
| DEM-011 | Módulo Programas de Saúde (backend) | ✅ Concluído | — |
| DEM-012 | Gestor Frontend (React + Vite + Mantine) | ✅ Concluído | `3683878` |
| DEM-013 | Clínico Frontend (React + Vite + Mantine) | ✅ Concluído | — |
| DEM-014 | Programas de Saúde — spec técnica completa | ✅ Concluído | — |
| DEM-015 | Frontend Clínico — spec técnica completa | ✅ Concluído | — |
| DEM-016 | Portal (landing page institucional) | ✅ Concluído | `eb7e082` |
| DEM-017 | Seed de homologação (50 pacientes × 3 tenants) | ✅ Concluído | `1a26523` |
| DEM-018 | Admin Módulo Completo + Traefik SSL | ✅ Concluído | `51465d0` |
| DEM-019 | Gestor Módulo Completo | 🔄 Spec pronta — aguardando execução | `5b66208` |

## Próximos passos

### 🔥 DEM-019 — Gestor Módulo Completo (PRIORIDADE ALTA)

**Arquivo:** `docs/demandas/DEM-019_GESTOR_COMPLETO/02_TECNICA.md`

Entregáveis:
- 8 grupos de endpoints gestor (dashboard, pacientes, agendamentos, faturas, RAG, equipe, programas, configurações)
- 8 páginas GestorUI (Dashboard, PatientList, PatientProfile, AppointmentCalendar, InvoiceList, RagDocuments, ProgramList, TenantSettings)
- Migrations SQL, SSE progresso RAG, export CSV, validação CPF + conflito de horário

---

### ⚠️ Ação manual necessária — DNS + SSL Admin

Para que `admin.intellicare.ia.br` funcione em produção:
1. Configurar registro A: `admin.intellicare.ia.br` → IP do servidor
2. Aguardar propagação DNS (até 24h)
3. Traefik ACME (Let's Encrypt) emite o certificado automaticamente na primeira requisição

---

## Fila futura

| DEM | Título | Prioridade |
|-----|--------|-----------|
| DEM-020 | Deploy produção (VPS + DNS + SSL end-to-end) | Alta |
| DEM-021 | Testes E2E (Playwright) | Média |
| DEM-022 | Observabilidade (Prometheus + Grafana) | Média |
