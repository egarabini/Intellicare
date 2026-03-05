# V2.0.2 - ADMIN + GESTOR + Portal Auth

> **Versão:** 2.0.2 | **Data Início:** 2026-03-05 | **Status:** 📋 Planejamento
> **Prioridade:** P0 (Crítica) | **Complexidade:** Alta | **Estimativa:** ~15 dias-dev

---

## 🎯 Objetivo

Implementar a **camada administrativa completa** do IntelliCare, cobrindo:

✅ **intellicare-admin** — Painel PLATFORM_ADMIN: gestão de tenants, planos, contratos e módulos
✅ **intellicare-gestor** — Painel TENANT_GESTOR: gestão de unidades e usuários por tenant
✅ **Portal Auth** — Login unificado com redirecionamento automático por role via Keycloak

---

## 📁 Documentos desta versão

| Arquivo | Conteúdo | Público-alvo |
|---------|----------|--------------|
| [`01_ESPECIFICACAO_FUNCIONAL.md`](./01_ESPECIFICACAO_FUNCIONAL.md) | Atores, casos de uso, telas, regras de negócio | PO, stakeholders, designers |
| [`02_ESPECIFICACAO_TECNICA.md`](./02_ESPECIFICACAO_TECNICA.md) | APIs, schemas, código, Keycloak, frontend | Desenvolvedores, arquitetos |
| [`03_PLANO_IMPLEMENTACAO.md`](./03_PLANO_IMPLEMENTACAO.md) | Sprints, tarefas, deploy, Docker, Traefik, CI/CD | Tech lead, DevOps, PMs |

---

## 🗺️ Arquitetura Resumida

```
┌─────────────────────────────────────────────────────────────────┐
│                    PORTAL REACT (porta 3001)                     │
│                                                                  │
│   /login ──► Keycloak OIDC/PKCE ──► RoleRouter                 │
│                                         │                        │
│              ┌──────────────────────────┼────────────────────┐  │
│              │                          │                     │  │
│           /admin                    /gestor              /dashboard│
│      (PLATFORM_ADMIN)          (TENANT_GESTOR)        (CLINICO)  │
│              │                          │                         │
└──────────────┼──────────────────────────┼─────────────────────────┘
               │                          │
               ▼                          ▼
      intellicare-admin           intellicare-gestor
         (porta 8010)               (porta 8011)
         schema: platform           schema: {tenant_id}
```

---

## 🔑 Roles Keycloak

| Role | Destino | Descrição |
|------|---------|-----------|
| `PLATFORM_ADMIN` | `/admin` | Superadmin IntelliCare — gerencia toda a plataforma |
| `TENANT_GESTOR` | `/gestor` | Admin local do cliente — gerencia seu tenant |
| `CLINICO/MEDICO/ENFERMEIRO` | `/dashboard` | Profissional de saúde |
| `PACIENTE` | `/paciente` | Área do paciente (escopo futuro) |

---

## 📊 Status de Implementação

| Sprint | Entregável | Status |
|--------|------------|--------|
| 1 | Keycloak: realm, roles, clients, mappers | ⬜ Pendente |
| 2 | Portal: Login + auth flow PKCE + RoleRouter | ⬜ Pendente |
| 3 | intellicare-admin Backend (auth + endpoints novos + migrations) | ⬜ Pendente |
| 4 | intellicare-admin Frontend (5 abas no detalhe de tenant) | ⬜ Pendente |
| 5 | intellicare-gestor Backend (auth + módulos + dashboard) | ⬜ Pendente |
| 6 | intellicare-gestor Frontend (tree unidades + alertas usuários) | ⬜ Pendente |
| 7 | QA + Smoke Tests + Deploy | ⬜ Pendente |

---

## 🔗 Relacionamentos

- **Depende de:** `V2.0.1 - ADMIN` (estrutura base do intellicare-admin existente)
- **Desbloqueia:** Portal clínico multi-tenant completo
- **Integra com:** `intellicare-auth`, `intellicare-core`, Keycloak 24.x, Redis 7

---

*Gerado em: 2026-03-05 | Responsável: Eduardo Garabini*
