---
dem: DEM-012
titulo: Gestor Frontend — Interface da Unidade de Saúde
tipo: FUNCIONAL
status: aprovado
criado: 2026-03-13
dependencias: [DEM-004, DEM-011]
---

# DEM-012 · 01 — Especificação Funcional

## Contexto

Interface web para o `TENANT_GESTOR` gerenciar sua unidade: usuários, documentos RAG e relatórios.
Stack: Blazor WASM + MudBlazor (mesma do Admin Frontend — DEM-006). Servida em `/gestor-ui`.

## Telas e Rotas

| Rota | Tela | Acesso |
|---|---|---|
| `/gestor-ui/` | Dashboard (uso, docs, usuários) | TENANT_GESTOR |
| `/gestor-ui/users` | Lista de usuários do tenant | TENANT_GESTOR |
| `/gestor-ui/users/invite` | Convidar novo usuário | TENANT_GESTOR |
| `/gestor-ui/documents` | Lista de documentos RAG | TENANT_GESTOR |
| `/gestor-ui/documents/upload` | Upload de documento | TENANT_GESTOR |
| `/gestor-ui/profile` | Perfil da unidade | TENANT_GESTOR |
| `/gestor-ui/reports` | Relatório de uso do SLM | TENANT_GESTOR |

## Critérios de Aceite

| # | Critério |
|---|---|
| AC-1 | Login via Keycloak redireciona `TENANT_GESTOR` para `/gestor-ui/` |
| AC-2 | PLATFORM_ADMIN ou CLINICO → acesso negado |
| AC-3 | Dashboard exibe contadores reais (usuários, docs, queries hoje) |
| AC-4 | Convidar usuário → email, role → API → confirmação |
| AC-5 | Upload de documento → progress → confirmação com `chunk_count` |
| AC-6 | Lista de documentos: `source_path`, `chunk_count`, `last_ingested_at` |
| AC-7 | Relatório de uso: total queries últimos 30 dias |
| AC-8 | Build compilado servido em `/gestor-ui` pelo FastAPI |

## Tecnologia

Blazor WASM + MudBlazor. Projeto: `frontend/GestorUI/`.
Build: `tools/scripts/build_gestor_ui.sh` → `intellicare_core/static/gestor-ui/`.
