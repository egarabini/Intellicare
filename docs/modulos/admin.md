---
tipo: nota-modulo
modulo: admin
porto: 8010
fase: 1
sprint: "1.3"
status: pendente
dem_principal: DEM-005
tags: [fase-1, admin, p0]
---

# Módulo: admin

**Responsabilidade:** Administração da plataforma — tenants, planos, billing, provisionamento.

---

## O que entrega

- CRUD de tenants (nome, vertical, plano, status)
- CRUD de planos (lê `configs/plans/*.yaml` → armazena JSONB no schema do tenant)
- Provisionamento automático: `CREATE SCHEMA tenant_{slug}` + seed + grupo Keycloak + admin user
- Finance básico: registro de uso mensal, billing status, plano ativo
- Auditoria: toda ação admin registrada em `_admin_audit`

## Tabelas (dentro do schema autônomo do tenant)

```sql
tenant_{slug}._admin_contract   -- plano ativo, config JSONB, vertical, status
tenant_{slug}._admin_modules    -- módulos habilitados e data de ativação
tenant_{slug}._admin_billing    -- período, valor, status, data de pagamento
tenant_{slug}._admin_audit      -- ator, ação, alvo, detalhes, timestamp
tenant_{slug}._admin_config     -- custom rules (JSONB) por tenant
```

## Stack

- FastAPI + Jinja2 + HTMX (sem build step)
- SQLAlchemy async com `TenantAwareSessionFactory`
- Keycloak: role `PLATFORM_ADMIN` para acesso total

## Tipos de vertical suportados

```sql
CREATE TYPE tenant_vertical AS ENUM (
    'estabelecimento_saude',  -- UBS, hospital, clínica
    'secretaria_saude',       -- secretarias municipais/estaduais
    'odontologico',           -- FUTURO
    'veterinario'             -- FUTURO
);
```

## Dependências

- [[decisoes/ADR-001-schema-autonomo]]
- [[decisoes/ADR-002-modulo-vs-servico]]
- DEM-003: intellicare-core (TenantContext, auth, db)
- DEM-004: Keycloak configurado (realm, clients, roles)

## DEMs relacionadas

- DEM-005: Admin backend (CRUD + provisionamento)
- DEM-006: Admin frontend (HTMX/Jinja2 dashboard)
- DEM-007: Finance básico (billing, uso mensal)
