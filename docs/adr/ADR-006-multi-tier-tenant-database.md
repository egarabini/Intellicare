# ADR-006 - Arquitetura Multi-Tier de Banco de Dados por Porte de Tenant

## Status
Proposed

## Contexto

O IntelliCare V3 adota multi-tenancy por schema PostgreSQL (um schema por tenant,
ex: `tenant_clinica_alfa`). Essa estrategia funciona bem para clinicas de pequeno e
medio porte compartilhando o mesmo servidor de banco de dados.

Porem, ao crescer o portfolio de clientes, surgem dois perfis com necessidades opostas:

**Perfil A — Clinicas e consultórios pequenos/medios**
- Volume de dados moderado (centenas a poucos milhares de pacientes)
- Sem SLA rigido de performance
- Custo operacional precisa ser baixo
- Schema-per-tenant no servidor compartilhado e adequado

**Perfil B — Redes hospitalares e grandes estabelecimentos**
- Volume de dados massivo (dezenas a centenas de milhares de pacientes)
- SLA rigido de performance e disponibilidade
- Dados sensiveis com requisitos de isolamento contratual e regulatorio
- Podem demandar instancia PostgreSQL exclusiva (nuvem propria, VPS dedicado, on-premise)

A arquitetura atual nao suporta o Perfil B sem customizacao manual. O modulo de
administracao precisa evoluir para configurar dinamicamente a conexao de banco por tenant.

## Decisao

Implementar arquitetura multi-tier de banco de dados com dois niveis:

### Tier 1 — Shared (padrao)
- Tenant reside no servidor PostgreSQL compartilhado (VPS-DATA)
- Isolamento via schema: `tenant_<slug>`
- Gerenciado automaticamente pela plataforma
- Sem custo adicional de infraestrutura para o cliente

### Tier 2 — Dedicated
- Tenant possui instancia PostgreSQL exclusiva
- Host, porta, nome do banco e credenciais configurados no modulo Admin
- A plataforma cria o schema e executa as migrations no banco remoto
- O connection pool e criado dinamicamente e cacheado

### Evolucao do modelo de dados

```sql
-- Evolucao da tabela public.tenants
ALTER TABLE public.tenants
  ADD COLUMN db_tier       VARCHAR(10)  NOT NULL DEFAULT 'shared',
  -- 'shared' = usa VPS-DATA compartilhado
  -- 'dedicated' = instancia exclusiva configurada abaixo
  ADD COLUMN db_host       VARCHAR(255),  -- NULL = shared
  ADD COLUMN db_port       INTEGER        DEFAULT 5432,
  ADD COLUMN db_name       VARCHAR(100),
  ADD COLUMN db_secret_ref VARCHAR(255);
  -- referencia ao secret manager (ex: nome da env var ou chave no Vault)
  -- as credenciais nunca ficam em plain text na tabela
```

### Roteamento de conexao

O servico FastAPI mantem um `ConnectionRouter` que:
1. Ao receber uma requisicao com header `X-Tenant-Schema`, busca o registro do tenant
2. Se `db_tier = 'shared'` → usa o pool padrao
3. Se `db_tier = 'dedicated'` → resolve credenciais via `db_secret_ref`,
   cria pool dedicado se nao existir, retorna conexao isolada

```python
# Pseudocodigo do router
async def get_tenant_session(tenant_slug: str) -> AsyncSession:
    tenant = await get_tenant_config(tenant_slug)
    if tenant.db_tier == 'shared':
        return shared_pool.get_session(schema=tenant.schema_name)
    else:
        pool = await dedicated_pool_registry.get_or_create(
            host=tenant.db_host,
            port=tenant.db_port,
            dbname=tenant.db_name,
            secret_ref=tenant.db_secret_ref,
        )
        return pool.get_session(schema=tenant.schema_name)
```

### Interface no modulo Admin

O AdminUI expoe, na tela de detalhe do tenant, uma secao "Configuracao de Banco":
- Campo: Tier (Shared / Dedicated)
- Se Dedicated: host, porta, nome do banco, referencia ao secret
- Botao "Testar Conexao" — valida conectividade antes de salvar
- Botao "Provisionar" — executa migrations no banco remoto e ativa o tenant

## Conexao com ADR-005

A ADR-005 estabelece o VPS-DATA como servidor PostgreSQL compartilhado (Tier 1).
O modelo desta ADR e compativel: Tier 1 aponta para VPS-DATA; Tier 2 aponta para
qualquer PostgreSQL externo configurado pelo operador do tenant.

A separacao de infraestrutura da ADR-005 ja exercita o mecanismo de conexao remota
que sera generalizado nesta ADR, servindo como prova de conceito.

## Consequências

**Positivas:**
- Plataforma serve pequenas clinicas e grandes redes hospitalares com a mesma codebase
- Isolamento contratual e regulatorio para clientes premium sem bifurcar o produto
- Flexibilidade de deployment: banco em nuvem propria do cliente, VPS dedicado ou on-premise
- Arquitetura de desenvolvimento (ADR-005) reflete e valida a arquitetura de producao

**Negativas / riscos:**
- Complexidade adicional no connection pool manager
- Migrations precisam ser executadas remotamente com tratamento de erro robusto
- Monitoramento precisa cobrir multiplas instancias de banco
- Secret management para credenciais de bancos dedicados precisa de estrategia formal

## Status de implementacao

Esta ADR esta em status **Proposed**. Nao ha DEM aberta ainda.
A implementacao sera planejada quando o portfolio do IntelliCare atingir o primeiro
cliente de Perfil B (rede hospitalar / grande estabelecimento).

A tabela `public.tenants` ainda nao possui as colunas de db_tier — a migration
sera criada na DEM correspondente.

## Data
2026-03-28

## Autor
ARQUITETO (Eduardo Garabini)
