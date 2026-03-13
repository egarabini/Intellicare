---
tipo: nota-modulo
modulo: gestor
porto: 8011
fase: 2
sprint: "2.1"
status: pendente
dem_principal: DEM-011
tags: [fase-2, gestor]
---

# Módulo: gestor

**Responsabilidade:** Gestão do tenant — perfil da unidade de saúde, usuários Keycloak, documentos RAG e relatórios de uso do SLM.

---

## Propósito

Módulo do `TENANT_GESTOR`. Permite configurar a unidade de saúde, gerenciar usuários do tenant via Keycloak, fazer upload/remoção de documentos na base de conhecimento (RAG) e consultar relatórios de uso das queries SLM.

---

## Endpoints Principais

| Método | Rota | Descrição | Role |
|--------|------|-----------|------|
| GET | `/gestor/health` | Health check | any |
| GET | `/gestor/profile` | Perfil da unidade de saúde | any autenticado |
| PUT | `/gestor/profile` | Criar/atualizar perfil da unidade | `TENANT_GESTOR` |
| GET | `/gestor/users` | Lista usuários do tenant (via Keycloak) | `TENANT_GESTOR` |
| GET | `/gestor/documents` | Lista documentos indexados na knowledge_base | `TENANT_GESTOR` |
| POST | `/gestor/documents/upload` | Upload de documento para ingestão RAG | `TENANT_GESTOR` |
| DELETE | `/gestor/documents/{source_path}` | Remove documento da knowledge_base | `TENANT_GESTOR` |
| GET | `/gestor/reports/usage` | Relatório de uso do SLM (queries, latência) | `TENANT_GESTOR` |

---

## Tabelas (schema `tenant_{slug}`)

| Tabela | Descrição |
|--------|-----------|
| `unit_profile` | Perfil da unidade (`name`, `address`, `city`, `state`, `unit_type`, `phone`, `email`) |
| `slm_query_log` | Log de queries SLM (`user_id`, `query_text`, `latency_ms`, `chunk_count`) |
| `knowledge_base` | Base RAG (gerida via upload/delete deste módulo) |

### Tipos de unidade suportados

`ubs`, `clinic`, `hospital`, `specialty`

---

## Roles Autorizados

- **`TENANT_GESTOR`** — acesso a todos os endpoints de gestão
- **Qualquer autenticado** — leitura do perfil (`GET /gestor/profile`)

---

## Stack e Dependências

- FastAPI (APIRouter com prefix `/gestor`)
- SQLAlchemy async via `tenant_session(ctx)` (queries dentro do schema do tenant)
- Keycloak Admin API via `KeycloakAdminClient` (listagem de usuários do grupo)
- `IngestService` do módulo vector (ingestão/remoção de documentos)
- [[decisoes/ADR-001-schema-autonomo]]
- Módulo admin funcional (DEM-005) — tenant já provisionado
- intellicare-core (DEM-003)

---

## DEMs relacionadas

- **DEM-011**: Gestor backend (perfil unidade, usuários Keycloak, documentos RAG, relatório)
- **DEM-012**: Gestor frontend
