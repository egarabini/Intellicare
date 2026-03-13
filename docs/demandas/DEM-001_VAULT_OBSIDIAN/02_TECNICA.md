---
tipo: especificacao-tecnica
demanda: DEM-001
titulo: Vault Obsidian + Documentação Base
fase: 0
sprint: "0.1"
status: aprovado
planejador: Claude
criado: 2026-03-13
---

# DEM-001 — Especificação Técnica

> Todos os arquivos são criados dentro de `C:\Users\egara\INTELLICARE\`.
> Nenhum código Python. Apenas criação de arquivos `.md`.

---

## PRÉ-CONDIÇÕES

- `git status` em `C:\Users\egara\INTELLICARE` mostra branch `main` limpa
- DEM-000 concluída (v2-archive, estrutura V3 no main)

---

## BLOCO 1 — docs/.gitignore

Criar `docs/.gitignore` com o conteúdo:

```
# Obsidian — config pessoal (não commitar)
.obsidian/
.trash/

# Arquivos temporários
*.tmp
```

---

## BLOCO 2 — docs/_templates/ (6 arquivos)

Criar diretório `docs/_templates/` e os arquivos abaixo.

### tpl_01_funcional.md

```
---
tipo: especificacao-funcional
demanda: DEM-XXX
titulo: TITULO
fase: X
sprint: "X.X"
status: rascunho
planejador: Claude
criado: YYYY-MM-DD
depende_de: []
habilita: []
tags: [fase-X, modulo, p0]
---

# DEM-XXX — TITULO

## Objetivo

## Contexto

## Escopo

### O que está incluído

| Bloco | O que entrega | Por quê |
|-------|--------------|---------|

### O que NÃO está incluído

## Critérios de Aceite

1.

## Resultado Esperado
```

### tpl_02_tecnica.md

```
---
tipo: especificacao-tecnica
demanda: DEM-XXX
titulo: TITULO
fase: X
sprint: "X.X"
status: rascunho
planejador: Claude
criado: YYYY-MM-DD
---

# DEM-XXX — Especificação Técnica

## PRÉ-CONDIÇÕES

## BLOCO 1 — NOME

**Objetivo:**

**Comandos:**

**Critério de sucesso:**
```

### tpl_03_plano.md

```
---
tipo: plano-execucao
demanda: DEM-XXX
titulo: TITULO
status: pendente
dev: dev1
criado: YYYY-MM-DD
---

# DEM-XXX — Plano de Execução

## Estimativa

Tempo estimado: Xh | Complexidade: baixa/média/alta

## STEPs

### STEP-001 — NOME

**Status:** pendente

Ação:

Critério:
```

### tpl_03_1_duvidas.md

```
---
tipo: duvidas
demanda: DEM-XXX
status: aberto
criado: YYYY-MM-DD
---

# DEM-XXX — Dúvidas

## DUV-001 — PERGUNTA

**Pergunta (dev):**

**Resposta (arquiteto/planejador):**
> Pendente
```

### tpl_04_diario.md

```
---
tipo: diario-execucao
demanda: DEM-XXX
dev: dev1
iniciado: YYYY-MM-DD
---

# DEM-XXX — Diário de Execução

## STEP-001 — NOME · YYYY-MM-DD

**Status:** concluido

O que foi feito:

Observações:
```

### tpl_05_finalizacao.md

```
---
tipo: finalizacao
demanda: DEM-XXX
titulo: TITULO
dev: dev1
concluido: YYYY-MM-DD
pr: ""
---

# DEM-XXX — Finalização

## Resumo

## Diferenças do Plano

## Dívida Técnica Gerada

## Aprendizados
```

---

## BLOCO 3 — docs/index.md (MOC)

Criar `docs/index.md`:

```markdown
---
tipo: moc
titulo: IntelliCare V3 — Índice
atualizado: 2026-03-13
---

# IntelliCare V3 — Mapa de Conteúdo

> Ponto de entrada do vault. Navegue por aqui.

---

## Arquitetura e Decisões

- [[decisoes/ADR-001-schema-autonomo]] — Schema PostgreSQL autônomo por tenant
- [[decisoes/ADR-002-modulo-vs-servico]] — Módulo (código) ≠ Serviço (runtime)
- [[decisoes/ADR-003-rag-slm-pgvector]] — Tríade RAG+SLM+pgvector como core de IA

## Módulos

- [[modulos/admin]] — Administração da plataforma (porto 8010)
- [[modulos/gestor]] — Gestão do tenant (porto 8011)
- [[modulos/cuidado]] — Cuidado clínico + RAG (porto 8004)
- [[modulos/florence]] — Protocolos clínicos RAG (porto 8001)
- [[modulos/oswaldo]] — Análise clínica + FHIR (porto 8002)

## Design e Produto

- [[design-docs/PLANS]] — Roadmap e fases
- [[design-docs/DESIGN]] — Tokens de design, acessibilidade
- [[design-docs/PRODUCT_SENSE]] — Para quem construímos
- [[design-docs/QUALITY_SCORE]] — Scorecard de qualidade por módulo
- [[design-docs/RELIABILITY]] — SLOs e runbooks
- [[design-docs/SECURITY]] — Controles de segurança

## Demandas

- [[demandas/_dashboard]] — Dashboard de todas as DEMs
- [[demandas/DEM-000_MIGRACAO/01_FUNCIONAL]] — Migração V2→V3
- [[demandas/DEM-001_VAULT_OBSIDIAN/01_FUNCIONAL]] — Este vault

## Templates

Em `_templates/` — use o Templater do Obsidian para criar novas DEMs.
```

---

## BLOCO 4 — docs/decisoes/ (3 ADRs)

Criar diretório `docs/decisoes/` e os 3 arquivos.

### ADR-001-schema-autonomo.md

```markdown
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

O projeto anterior usava tabelas globais para tenants/planos/billing. Isso impedia:
- Migração de tenant para servidor dedicado sem cirurgia no código
- Encerramento de contrato limpo (backup + drop sem afetar outros)
- Independência total de dados e processos por tenant

## Operações habilitadas por esta decisão

| Operação | Como funciona |
|----------|--------------|
| Onboarding | `CREATE SCHEMA tenant_{slug}` + seed completo |
| Encerrar contrato | `pg_dump` → backup → `DROP SCHEMA CASCADE` |
| Migrar para servidor dedicado | `pg_dump` → `pg_restore` + atualizar connection |
| Observabilidade | Métricas isoladas por schema no Grafana |
| Customização exclusiva | `_admin_config` no schema do tenant |

## Consequências

- Cada módulo cria suas tabelas com prefixo no schema do tenant (`_admin_*`, `_gestor_*`, etc.)
- Alembic usa `TenantAwareSessionFactory` para saber em qual schema migrar
- Não há tabelas cross-tenant em nenhuma circunstância
```

### ADR-002-modulo-vs-servico.md

```markdown
---
tipo: adr
id: ADR-002
titulo: Módulo (código) ≠ Serviço (runtime)
status: aprovado
data: 2026-03-13
decidido_por: Eduardo (Arquiteto)
tags: [arquitetura, modulos, deploy]
---

# ADR-002 — Módulo (código) ≠ Serviço (runtime)

## Decisão

**MÓDULO** = unidade de código/desenvolvimento com responsabilidade distinta.
**SERVIÇO** = o que o tenant contratou: um conjunto de módulos empacotados rodando
juntos em 1 container `intellicare-service`.

## Contexto

O projeto V2 tinha 10+ containers (1 por agente). Isso gerava:
- Overhead operacional: gerenciar 10 health checks, 10 logs, 10 redes
- Latência extra: chamadas inter-container para funcionalidades simples
- Complexidade de deploy: orquestrar 10 serviços para rodar 1 tenant

## Arquitetura aprovada

```
Repositório (código):
  modules/admin/       → MÓDULO (unidade de desenvolvimento)
  modules/gestor/      → MÓDULO
  modules/cuidado/     → MÓDULO
  ...

Runtime (servidor):
  Container: intellicare-service  → carrega módulos dinamicamente
  Container: postgresql+pgvector
  Container: redis
  Container: keycloak
  Container: ollama
```

O `intellicare-service` usa `ModuleLoader` para carregar apenas os módulos
habilitados no plano do tenant. Um tenant "Básico" carrega admin+gestor+florence.
Um tenant "Pro" carrega todos os módulos.

## Consequências

- 1 Dockerfile em `deploy/` empacota todos os módulos
- Módulos não têm porta própria — são roteados via `intellicare-service`
- `configs/plans/*.yaml` define quais módulos cada plano inclui
```

### ADR-003-rag-slm-pgvector.md

```markdown
---
tipo: adr
id: ADR-003
titulo: Tríade RAG+SLM+pgvector como core de IA clínica
status: aprovado
data: 2026-03-13
decidido_por: Eduardo (Arquiteto)
tags: [ia, rag, slm, pgvector, arquitetura]
---

# ADR-003 — Tríade RAG+SLM+pgvector

## Decisão

A inteligência clínica do IntelliCare V3 é construída sobre 3 componentes:

1. **pgvector** — extensão do PostgreSQL (`CREATE EXTENSION vector`).
   Embeddings ficam na mesma tabela dos dados clínicos do tenant.
2. **SLM local** — modelo leve via OLLAMA (Qwen2.5-7B ou similar).
   Inferência em ~100-300ms, sem hop de rede.
3. **RAG pipeline** — busca semântica (`ORDER BY embedding <=> $1 LIMIT 5`)
   + síntese via SLM. Latência alvo: <300ms total.

## Contexto

Stack anterior: WANDA → LangGraph → FLORENCE → Flowise → OLLAMA → Pinecone.
Isso criava 4-5 hops de rede para cada consulta clínica. Latência >2s.
Inaceitável para uso em consulta médica (janela de atenção: <30s).

## Por que funciona

- pgvector elimina o hop de rede para banco vetorial externo
- SLM elimina o hop de rede para API de LLM na nuvem
- Isolamento multi-tenant nativo: cada tenant tem seus embeddings no seu schema
- Backup/restore unificado: dados + vetores no mesmo `pg_dump`

## Fluxo de referência

```python
# Busca semântica: ~5ms
results = await db.execute(f"""
    SELECT title, content
    FROM {tenant_schema}.protocols
    ORDER BY embedding <=> :emb
    LIMIT 5
""", {"emb": query_embedding})

# Síntese SLM local: ~200ms
response = await ollama_generate(
    model="qwen2.5:7b",
    prompt=f"Baseado nos protocolos abaixo, responda: {query}\n\n{context}"
)
# Total: <300ms
```

## Implementação

- DEM-002: pgvector ativo + docker-compose
- DEM-002: pipeline `ingest_docs.py` (Markdown → chunks → embedding → INSERT)
- DEM-013: módulo `cuidado` com busca semântica e síntese
```

---

## BLOCO 5 — docs/modulos/ (5 notas)

Criar diretório `docs/modulos/` e os 5 arquivos.

### admin.md

```markdown
---
tipo: nota-modulo
modulo: admin
porto: 8010
fase: 1
sprint: "1.3"
status: pendente
dem_principal: DEM-005
tags: [fase-1, admin]
---

# Módulo: admin

**Responsabilidade:** Administração da plataforma — tenants, planos, billing, provisionamento.

## O que entrega

- CRUD de tenants (nome, vertical, plano, status)
- CRUD de planos (config YAML → JSONB no schema do tenant)
- Provisionamento automático: `CREATE SCHEMA tenant_{slug}` + seed + Keycloak group
- Finance básico: registro de uso mensal, billing status
- Auditoria: toda ação admin registrada em `_admin_audit`

## Tabelas (no schema do tenant)

```sql
tenant_{slug}._admin_contract   -- plano ativo, config JSONB
tenant_{slug}._admin_modules    -- módulos habilitados
tenant_{slug}._admin_billing    -- períodos, valores, status
tenant_{slug}._admin_audit      -- log de ações
tenant_{slug}._admin_config     -- custom rules (JSONB)
```

## Dependências

- [[decisoes/ADR-001-schema-autonomo]] — schema autônomo
- DEM-003: intellicare-core (TenantContext, auth, db)
- DEM-004: Keycloak configurado (realm, clients, roles)

## DEMs relacionadas

- [[demandas/DEM-005_ADMIN_BACKEND/01_FUNCIONAL]]
- [[demandas/DEM-006_ADMIN_FRONTEND/01_FUNCIONAL]]
- [[demandas/DEM-007_FINANCE/01_FUNCIONAL]]
```

### gestor.md

```markdown
---
tipo: nota-modulo
modulo: gestor
porto: 8011
fase: 2
sprint: "2.1"
status: pendente
dem_principal: DEM-008
tags: [fase-2, gestor]
---

# Módulo: gestor

**Responsabilidade:** Gestão do tenant — unidades, setores, profissionais, alocações.

## O que entrega

- CRUD de unidades de saúde (UBS, hospital, clínica)
- CRUD de setores por unidade
- CRUD de profissionais (vinculados ao Keycloak)
- Alocações: profissional × setor × turno

## Tabelas (no schema do tenant)

```sql
tenant_{slug}._gestor_units          -- unidades de saúde
tenant_{slug}._gestor_sectors        -- setores por unidade
tenant_{slug}._gestor_professionals  -- profissionais
tenant_{slug}._gestor_allocations    -- alocações
```

## Dependências

- Módulo admin provisionado e funcional (DEM-005)
- intellicare-core (TenantContext, auth)

## DEMs relacionadas

- [[demandas/DEM-008_GESTOR_BACKEND/01_FUNCIONAL]]
- [[demandas/DEM-009_GESTOR_FRONTEND/01_FUNCIONAL]]
```

### cuidado.md

```markdown
---
tipo: nota-modulo
modulo: cuidado
porto: 8004
fase: 3
sprint: "3.3"
status: pendente
dem_principal: DEM-013
tags: [fase-3, cuidado, rag, slm]
---

# Módulo: cuidado

**Responsabilidade:** Cuidado clínico base com busca semântica de protocolos (RAG+SLM).

## O que entrega

- Consulta de protocolos clínicos via busca semântica (pgvector)
- Síntese de resposta via SLM local (OLLAMA)
- Programas de saúde: DRC, Diabetes, HAS, Câncer
- Latência alvo: <300ms por consulta

## Tabelas (no schema do tenant)

```sql
tenant_{slug}.protocols (
    id SERIAL PRIMARY KEY,
    title TEXT,
    content TEXT,
    program TEXT,           -- 'drc', 'diabetes', 'has', 'cancer'
    source TEXT,
    embedding vector(384),  -- pgvector
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
)

CREATE INDEX ON tenant_{slug}.protocols
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);
```

## Dependências

- [[decisoes/ADR-003-rag-slm-pgvector]]
- pgvector ativo (DEM-002)
- SLM OLLAMA configurado (DEM-002)

## DEMs relacionadas

- [[demandas/DEM-013_CUIDADO_BACKEND/01_FUNCIONAL]]
- [[demandas/DEM-014_PROGRAMAS_SAUDE/01_FUNCIONAL]]
```

### florence.md

```markdown
---
tipo: nota-modulo
modulo: florence
porto: 8001
fase: 3
sprint: "3.x"
status: pendente
dem_principal: TBD
tags: [fase-3, florence, rag]
---

# Módulo: florence

**Responsabilidade:** Protocolos clínicos especializados via RAG.
Versão anterior: score 1/10. Reconstruído do zero em V3.

## O que entrega

- Base de protocolos clínicos indexados (SBEM, MS, CFM)
- Busca semântica especializada por programa/vertical
- Referências rastreáveis (fonte + data de publicação)

## Nota

Florence em V3 é um módulo especializado de florence, não um agente separado.
Usa a mesma infraestrutura pgvector+SLM do módulo `cuidado`.
A distinção: `cuidado` é o fluxo clínico; `florence` é a biblioteca especializada.

## Dependências

- Módulo cuidado funcional (DEM-013)
- Pipeline ingest_docs.py (DEM-002)
```

### oswaldo.md

```markdown
---
tipo: nota-modulo
modulo: oswaldo
porto: 8002
fase: 3
sprint: "3.x"
status: existente-v2
score_v2: 8/10
dem_principal: TBD
tags: [fase-3, oswaldo, fhir]
---

# Módulo: oswaldo

**Responsabilidade:** Análise clínica + FHIR R4.
Único módulo com score alto no V2 (8/10). Será incorporado em Fase 3.

## O que entrega (V2, a preservar)

- Análise de prontuários via LLM
- Exportação FHIR R4 (Patient, Observation, Condition, MedicationStatement)
- Score de qualidade de dados clínicos

## Estratégia de incorporação em V3

1. Preservar lógica de análise e exports FHIR do V2
2. Adaptar para usar `TenantAwareSessionFactory` do intellicare-core
3. Substituir chamadas LLM externas por SLM local (OLLAMA)
4. Integrar com pgvector para busca semântica de histórico clínico

## Referências FHIR usadas

Ver [[references/fhir-r4-recursos-usados]]
```

---

## BLOCO 6 — docs/demandas/_dashboard.md

```markdown
---
tipo: dashboard
titulo: Dashboard de Demandas
atualizado: 2026-03-13
---

# Dashboard de Demandas — IntelliCare V3

> Gerado automaticamente pelo Dataview. Abra no Obsidian para ver os dados.

---

## Em Execução

\`\`\`dataview
TABLE fase, modulo, dev, criado AS "Criado"
FROM "demandas"
WHERE tipo = "especificacao-funcional" AND status = "em-execucao"
SORT fase ASC
\`\`\`

## Aprovadas (aguardando execução)

\`\`\`dataview
TABLE fase, modulo, sprint
FROM "demandas"
WHERE tipo = "especificacao-funcional" AND status = "aprovado"
SORT fase ASC
\`\`\`

## Concluídas

\`\`\`dataview
TABLE fase, modulo, concluido AS "Concluído"
FROM "demandas"
WHERE tipo = "finalizacao"
SORT concluido DESC
\`\`\`

## Todas as DEMs (visão geral)

\`\`\`dataview
TABLE fase, sprint, status, modulo
FROM "demandas"
WHERE tipo = "especificacao-funcional"
SORT fase ASC, sprint ASC
\`\`\`
```

---

## BLOCO 7 — docs/design-docs/ (6 arquivos)

Criar `docs/design-docs/PLANS.md`, `DESIGN.md`, `PRODUCT_SENSE.md`,
`QUALITY_SCORE.md`, `RELIABILITY.md`, `SECURITY.md`.

### PLANS.md — Roadmap

```markdown
---
tipo: roadmap
atualizado: 2026-03-13
---

# IntelliCare V3 — Roadmap

## Visão

1 serviço Python, módulos dinâmicos, RAG/SLM/pgvector.
De 10+ containers caóticos para 1 container inteligente.

---

## Fase 0 — Fundação (concluída)

| DEM | Sprint | Entrega |
|-----|--------|---------|
| DEM-000 | 0.0 | Migração V2→V3, estrutura skeleton, git limpo |
| DEM-001 | 0.1 | Vault Obsidian, ADRs, templates, docs base |

## Fase 1 — Admin (Semanas 1-3)

| DEM | Sprint | Entrega |
|-----|--------|---------|
| DEM-002 | 1.0 | Infra Docker: PG+pgvector, Redis, Keycloak, OLLAMA, Traefik |
| DEM-003 | 1.1 | intellicare-core: TenantContext, auth, db, vector, module_loader |
| DEM-004 | 1.2 | Keycloak: realm, clients, roles, mappers |
| DEM-005 | 1.3 | Admin backend: CRUD tenants, planos, provisionamento |
| DEM-006 | 1.4 | Admin frontend: HTMX/Jinja2, dashboard |
| DEM-007 | 1.5 | Finance básico: billing, uso mensal |

**Resultado:** Tenant pode ser criado, configurado e faturado.

## Fase 2 — Gestor (Semanas 4-6)

| DEM | Sprint | Entrega |
|-----|--------|---------|
| DEM-008 | 2.1 | Gestor backend: unidades, setores, profissionais |
| DEM-009 | 2.2 | Gestor frontend |
| DEM-010 | 2.3 | Integração admin↔gestor E2E |

**Resultado:** Gestor do tenant pode organizar sua equipe e estrutura.

## Fase 3 — Cuidado + RAG (Semanas 7-12)

| DEM | Sprint | Entrega |
|-----|--------|---------|
| DEM-011 | 3.1 | pgvector + pipeline ingestão |
| DEM-012 | 3.2 | SLM local OLLAMA configurado |
| DEM-013 | 3.3 | Cuidado backend: busca semântica, protocolos |
| DEM-014 | 3.4 | Programas de saúde: DRC, Diabetes, HAS, Câncer |
| DEM-015 | 3.5 | Frontend clínico MVP |

**Resultado:** Profissional de saúde consulta protocolos em <300ms.

---

## O que NÃO fazer agora

- Não criar 10 containers separados por módulo
- Não usar LangGraph/Flowise/LangChain nas Fases 1-2
- Não construir WANDA até ter 2+ módulos clínicos funcionais
- Não criar schema global — cada tenant é autônomo
```

### PRODUCT_SENSE.md

```markdown
---
tipo: product-sense
atualizado: 2026-03-13
---

# Para quem construímos

## Usuário primário: o profissional de saúde

Tempo médio de consulta: 12-15 minutos.
Janela de atenção para o sistema: <30 segundos.

O sistema deve ser invisível quando funciona.
O sistema deve ser imediato quando consultado.
O sistema deve ser preciso quando responde.

## Personas

**Médico de família (UBS):** alta demanda, poucos recursos,
precisa de protocolos rápidos e referências confiáveis.

**Gestor da UBS:** precisa de números, não de narrativas.
Dashboard limpo, alertas claros.

**Administrador da plataforma:** técnico, confia em logs.
Não precisa de interface bonita — precisa de interface eficaz.

## Proposta de valor

"A documentação clínica certa, na hora certa, sem sair do fluxo de trabalho."

## O que nunca fazemos

- Não adicionamos funcionalidade sem usuário confirmado
- Não priorizamos estética sobre velocidade em contexto clínico
- Não exigimos treinamento para tarefas básicas
```

### DESIGN.md

```markdown
---
tipo: design-system
atualizado: 2026-03-13
---

# Sistema de Design

## Paleta Clínica de Severidade

| Token | Hex | Uso |
|-------|-----|-----|
| `--severity-critical` | #DC2626 | Alertas críticos, dados faltantes urgentes |
| `--severity-warning` | #D97706 | Avisos, prazo vencendo |
| `--severity-info` | #2563EB | Informação neutra |
| `--severity-success` | #16A34A | Confirmações, dados completos |
| `--severity-neutral` | #6B7280 | Texto secundário |

## Princípios de Interface

1. **Densidade informacional** — painéis clínicos mostram mais dados em menos espaço
2. **Contraste alto** — acessível em monitores ruins e com iluminação adversa
3. **Ação principal sempre visível** — sem caça a botões em tela cheia
4. **Estado do sistema explícito** — loading, erro, vazio, sucesso: sempre indicado

## Stack Frontend

- Admin/Gestor: FastAPI + Jinja2 + HTMX (sem build step, sem Node)
- Clínico (Fase 3): React 19 + TailwindCSS (SPA para fluidez em consulta)
- Design tokens: CSS custom properties, sem framework de UI externo
```

### QUALITY_SCORE.md

```markdown
---
tipo: quality-scorecard
atualizado: 2026-03-13
---

# Quality Scorecard

> ⚪ = não avaliado | 🟢 = OK | 🟡 = atenção | 🔴 = crítico

| Módulo | Tests | API Docs | Error Handling | Auth | DB Migrations | Health Check |
|--------|-------|----------|----------------|------|---------------|--------------|
| core | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ |
| admin | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ |
| gestor | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ |
| cuidado | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ |
| florence | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ |
| oswaldo | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ |

*Atualizar após cada DEM concluída.*
```

### RELIABILITY.md

```markdown
---
tipo: reliability
atualizado: 2026-03-13
---

# Confiabilidade e SLOs

## SLOs por categoria

| Serviço | Disponibilidade | Latência p95 | Latência p99 |
|---------|----------------|--------------|--------------|
| Admin | 99.5% | 500ms | 2s |
| Gestor | 99.5% | 500ms | 2s |
| Cuidado (RAG) | 99.9% | 300ms | 1s |
| Health check | 99.99% | 50ms | 100ms |

## Health check padrão

Todo módulo expõe `GET /health` com resposta:

```json
{
  "status": "healthy",
  "module": "admin",
  "version": "0.1.0",
  "db": "connected",
  "uptime_seconds": 3600
}
```

## Runbook: módulo não responde

1. Verificar `docker logs intellicare-service`
2. Verificar `GET /health` de cada módulo
3. Verificar conexão PostgreSQL: `docker exec postgres pg_isready`
4. Verificar Redis: `docker exec redis redis-cli ping`
5. Se persistir: reiniciar container com `docker compose restart intellicare-service`
```

### SECURITY.md

```markdown
---
tipo: security
atualizado: 2026-03-13
---

# Controles de Segurança

## Autenticação

- Keycloak como IdP único
- JWT com claims: `tenant_id`, `user_id`, `roles`
- Roles: `PLATFORM_ADMIN`, `TENANT_GESTOR`, `CLINICO`, `PACIENTE`
- Token válido por 15 minutos (refresh por 8h)

## Multi-tenancy

- Cada request tem `tenant_id` extraído do JWT
- `TenantAwareSessionFactory` direciona para `tenant_{slug}` no PostgreSQL
- Zero possibilidade de acesso cross-tenant via query (schema isolation)

## Segredos

- NUNCA no código ou no git
- `.env` local para desenvolvimento
- Variáveis de ambiente no container em produção
- `keycloak_client_secrets.json` está no `.gitignore`

## Checklist por DEM

Antes de marcar DEM como concluída, verificar:
- [ ] Nenhum secret hardcoded
- [ ] Todos os endpoints autenticados (exceto /health)
- [ ] `tenant_id` validado em toda operação de dados
- [ ] Inputs validados com Pydantic
- [ ] Logs não expõem dados clínicos
```

---

## BLOCO 8 — Commit

Após criar todos os arquivos acima:

```bash
cd C:\Users\egara\INTELLICARE
git add docs/
git commit -m "docs: vault Obsidian base - ADRs, templates, modulos, dashboard"
git push origin main
```

Verificação final:
```bash
git log --oneline -5
git diff HEAD~1 --stat
```

---

## Resultado esperado

```
docs/
├── .gitignore
├── index.md
├── _templates/           (6 templates)
├── decisoes/             (3 ADRs)
├── modulos/              (5 notas)
├── demandas/
│   ├── _dashboard.md
│   ├── DEM-000_MIGRACAO/ (já existia)
│   └── DEM-001_VAULT_OBSIDIAN/ (esta DEM)
├── design-docs/
│   ├── PLANS.md
│   ├── DESIGN.md
│   ├── PRODUCT_SENSE.md
│   ├── QUALITY_SCORE.md
│   ├── RELIABILITY.md
│   └── SECURITY.md
└── references/           (placeholder existente)
```

Após commit, abrir `C:\Users\egara\INTELLICARE\docs` como vault no Obsidian
para confirmar que os wiki-links resolvem corretamente.
