---
tipo: adr
id: ADR-001
titulo: Schema PostgreSQL Autônomo por Tenant
status: aprovado
data: 2026-03-13
decidido_por: Eduardo (Arquiteto)
tags: [database, multi-tenancy, arquitetura]
---

# ADR-001 — Schema PostgreSQL Autônomo por Tenant

## Decisão

Cada tenant possui um schema PostgreSQL completamente autônomo (`tenant_{slug}`).
Não existe schema `platform` global. O catálogo de planos é config YAML versionada
no repositório, copiada para o schema do tenant no provisionamento.

## Contexto

O projeto V2 usava tabelas globais para tenants/planos/billing. Isso impedia:
- Migração de tenant para servidor dedicado sem cirurgia no código
- Encerramento de contrato limpo (backup + drop sem afetar outros)
- Independência total de dados e processos por tenant

## Operações habilitadas por esta decisão

| Operação | Como funciona |
|----------|--------------|
| Onboarding | `CREATE SCHEMA tenant_{slug}` + seed completo |
| Encerrar contrato | `pg_dump` → backup → `DROP SCHEMA CASCADE` |
| Migrar para servidor dedicado | `pg_dump` → `pg_restore` + atualizar connection string |
| Observabilidade por tenant | Métricas isoladas por schema no Grafana |
| Customização exclusiva | `_admin_config` JSONB no schema do próprio tenant |

## Estrutura de tabelas por módulo

Cada módulo cria suas tabelas com prefixo no schema do tenant:

```sql
-- Módulo admin
tenant_{slug}._admin_contract   -- plano ativo, config JSONB
tenant_{slug}._admin_modules    -- módulos habilitados
tenant_{slug}._admin_billing    -- períodos, valores, status
tenant_{slug}._admin_audit      -- log de todas as ações
tenant_{slug}._admin_config     -- custom rules (JSONB)

-- Módulo gestor
tenant_{slug}._gestor_units
tenant_{slug}._gestor_sectors
tenant_{slug}._gestor_professionals
tenant_{slug}._gestor_allocations

-- Módulo cuidado (RAG)
tenant_{slug}.protocols         -- content + embedding vector(384)
```

## Consequências

- Alembic usa `TenantAwareSessionFactory` para saber em qual schema migrar
- Não há tabelas cross-tenant em nenhuma circunstância
- Catálogo de planos = YAML no repo (`configs/plans/*.yaml`), não tabela global
- Provisionamento = operação simples e reversível

## Alternativas rejeitadas

| Alternativa | Por que foi descartada |
|-------------|----------------------|
| **Schema único com coluna `tenant_id`** | Risco de vazamento de dados entre tenants por query sem filtro. Impossibilita `DROP SCHEMA CASCADE` para encerramento limpo. Backup/restore exige filtragem por tenant_id — lento e propenso a erro. |
| **Banco de dados separado por tenant** | Overhead operacional: 1 connection pool por tenant, N bancos para migrar no Alembic. Inviável com >50 tenants em servidor compartilhado. |
| **NoSQL (MongoDB/DynamoDB)** | Perde joins relacionais necessários para relatórios clínicos. pgvector não tem equivalente nativo em NoSQL. Equipe tem expertise em PostgreSQL. |

## Implementação

- `packages/intellicare-core/tenant/` — `TenantContext`, `TenantResolver`
- `packages/intellicare-core/db/` — `TenantAwareSessionFactory`
- DEM-003 — intellicare-core com estas abstrações
