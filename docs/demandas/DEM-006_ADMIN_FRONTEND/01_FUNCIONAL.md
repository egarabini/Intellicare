---
dem: DEM-006
titulo: Admin Frontend — Interface de Gestão de Plataforma
tipo: FUNCIONAL
status: aprovado
criado: 2026-03-13
dependencias: [DEM-004, DEM-005]
---

# DEM-006 · 01 — Especificação Funcional

## Contexto e Motivação

O Admin Backend (DEM-005) expõe uma API completa para gestão de tenants. O Admin Frontend
é a interface web que o `PLATFORM_ADMIN` usa no dia a dia: visualizar tenants, criar novos,
suspender ou reativar, e inspecionar usuários.

Por decisão de arquitetura (ADR-002), o frontend é um módulo **separado do runtime**
(`modules/admin_ui/`) mas integrado ao mesmo container `intellicare-service`. Em V3 não há
servidor de frontend independente — o FastAPI serve os arquivos estáticos compilados.

## Tecnologia

| Escolha | Justificativa |
|---|---|
| **Blazor WebAssembly** (.NET 9) | Equipe usa VS 2022 / .NET como stack principal |
| **MudBlazor** | Component library madura, Material Design, suporte a tabelas e formulários |
| **OIDC via Keycloak** | `Microsoft.AspNetCore.Components.WebAssembly.Authentication` |
| Hospedagem | FastAPI serve `wwwroot/` como `StaticFiles` em `/admin-ui` |

> **Alternativa considerada**: React/Vite. Rejeitado nesta fase — evita contexto de troca
> tecnológica. React virá no frontend clínico (DEM-015, Fase 3).

## Escopo

### Incluído

- **Login via Keycloak** (OIDC Authorization Code + PKCE)
- **Dashboard**: cards com contadores (total tenants, ativos, suspensos)
- **Lista de Tenants**: tabela paginada com busca, status badge colorido
- **Detalhe de Tenant**: informações + lista de usuários
- **Criar Tenant**: formulário com validação client-side (slug, nome, email gestor)
- **Suspender / Reativar**: botão de ação com confirmação modal
- **Guarda de rota**: redireciona para login se não autenticado ou sem role `PLATFORM_ADMIN`

### Excluído

- Frontend clínico (pacientes, prontuário) → DEM-015
- Frontend do gestor → DEM-010
- Upload de documentos para RAG → DEM-011 (ingest pipeline)

## Fluxo de Autenticação

```
Browser → /admin-ui
  → Redirect para Keycloak /authorize (PKCE)
  → Login com credenciais
  → Redirect de volta com code
  → Troca code → access_token + refresh_token (armazenado em memória WASM)
  → Cada chamada à API inclui Bearer token
  → Se 401 → refresh automático
  → Se refresh expirado → volta para login
```

## Telas e Rotas

| Rota | Componente | Descrição |
|---|---|---|
| `/admin-ui/login` | `LoginPage` | Redirect automático para Keycloak |
| `/admin-ui/` | `Dashboard` | Cards de resumo |
| `/admin-ui/tenants` | `TenantList` | Tabela com busca e paginação |
| `/admin-ui/tenants/new` | `TenantForm` | Formulário de criação |
| `/admin-ui/tenants/{slug}` | `TenantDetail` | Detalhe + usuários |

## Comportamentos de UX

- Slug no formulário: automático a partir do nome (lowercase, replace spaces→`_`, strip chars inválidos)
- Badge de status: verde (active), amarelo (suspended), cinza (terminated)
- Ação de suspender/reativar: modal de confirmação com nome do tenant
- Erros da API: toast de erro com mensagem legível
- Loading states: skeleton nos cards e tabelas

## Critérios de Aceite

| # | Critério |
|---|---|
| AC-1 | Acessar `/admin-ui/` sem autenticação redireciona para Keycloak |
| AC-2 | Login com `platform-admin` / `Admin@2025!` autentica com sucesso |
| AC-3 | Login com `gestor-dev` → acesso negado (role insuficiente) |
| AC-4 | Dashboard exibe contadores corretos para os tenants criados |
| AC-5 | Criar tenant via formulário chama POST `/admin/tenants` e exibe o novo na lista |
| AC-6 | Slug gerado automaticamente a partir do nome |
| AC-7 | Slug inválido no formulário → erro client-side antes de enviar |
| AC-8 | Suspender tenant → status muda na lista sem recarregar a página |
| AC-9 | `wwwroot/` compilado é servido pelo FastAPI em `/admin-ui` |
| AC-10 | Token é renovado automaticamente (sem logout forçado dentro do `ssoSessionMaxLifespan`) |

## Não-Funcionais

- First Contentful Paint < 3s (WASM tem cold start; aceitável para admin interno)
- Sem dados sensíveis no localStorage (token apenas em memória WASM)
- Compatível com Chrome 120+, Edge 120+, Firefox 120+
