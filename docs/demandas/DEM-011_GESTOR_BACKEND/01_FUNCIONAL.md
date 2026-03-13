---
dem: DEM-011
titulo: Gestor Backend — Módulo de Gestão da Unidade de Saúde
tipo: FUNCIONAL
status: aprovado
criado: 2026-03-13
dependencias: [DEM-003, DEM-004, DEM-009, DEM-010]
---

# DEM-011 · 01 — Especificação Funcional

## Contexto

O `TENANT_GESTOR` administra uma unidade de saúde. Este módulo oferece APIs para gerenciar
usuários clínicos, documentos da base de conhecimento e relatórios de uso do próprio tenant.

## Escopo

### Incluído

- **Gestão de usuários do tenant**: listar, convidar (via Keycloak), desativar
- **Documentos RAG**: upload, listagem, remoção da `knowledge_base` do tenant
- **Relatório de uso do SLM**: queries por dia, usuário mais ativo, top queries
- **Perfil da unidade**: nome, endereço, tipo (UBS, clínica, hospital)

### Excluído

- Dados clínicos de pacientes → DEM-013
- Interface web → DEM-012
- Financeiro → DEM-007

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| GET | `/gestor/health` | Health check |
| GET/PUT | `/gestor/profile` | Perfil da unidade |
| GET | `/gestor/users` | Listar usuários do tenant |
| POST | `/gestor/users/invite` | Convidar novo usuário |
| PATCH | `/gestor/users/{id}/deactivate` | Desativar usuário |
| GET | `/gestor/documents` | Listar documentos RAG |
| POST | `/gestor/documents/upload` | Upload de documento |
| DELETE | `/gestor/documents/{path}` | Remover documento |
| GET | `/gestor/reports/usage` | Relatório de uso SLM |

## Critérios de Aceite

| # | Critério |
|---|---|
| AC-1 | GET `/gestor/profile` → dados da unidade do tenant autenticado |
| AC-2 | PUT `/gestor/profile` → atualiza apenas campos permitidos |
| AC-3 | POST `/gestor/users/invite` → cria usuário no Keycloak no grupo do tenant |
| AC-4 | GET `/gestor/documents` → apenas documentos do schema do tenant |
| AC-5 | POST `/gestor/documents/upload` → ingerido na `knowledge_base` do tenant |
| AC-6 | Token CLINICO em `/gestor/users/invite` → 403 |
| AC-7 | GET `/gestor/reports/usage` → total queries SLM no período |
