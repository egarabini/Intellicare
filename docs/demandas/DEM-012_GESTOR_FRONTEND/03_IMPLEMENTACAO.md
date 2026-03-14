---
dem: DEM-012
titulo: Gestor Frontend — Interface da Unidade de Saúde
tipo: IMPLEMENTACAO
status: concluido
criado: 2026-03-13
---

# DEM-012 · 03 — Relatório de Implementação

## O que foi feito

Nesta demanda, verificamos a inicialização e o empacotamento da interface web para o `TENANT_GESTOR`. Notou-se que a infraestrutura React + Vite + Mantine (definidas na revisão da técnica 02) já havia sido instanciada.

### Principais Entregas:

1. **GestorUI (`frontend/GestorUI/`)**
   - **package.json & vite.config.ts**: Estruturados e compatíveis com a documentação, usando Vite na porta 5175 e roteamento para o proxy `/gestor` e `/vector` do FastAPI.
   - **Autenticação (`src/auth/`)**: Componentes `AuthProvider` com `react-oidc-context` apontando para o Keycloak no realm `intellicare` e client `gestor-ui`.
   - **API Client (`src/api/client.ts`)**: Base `axios` provisionada com interceptadores para injeção de `oidc.access_token` do SessionStorage armazenado pelo `TokenSync`.
   - **React Query Hooks (`src/hooks/`)**: Abstrações para gerenciar o estado da API do banco de documentos RAG (`useDocuments`), upload/exclusão de itens da base de conhecimento (pgvector) e listagem de usuários (`useUsers`).
   - **Páginas (`src/pages/`)**: `DocumentUpload` (integração do Drag and Drop de PDFs) e `UsageReport` implementados sob a identidade visual em Mantine UI.

2. **Geração Física & Servidor (CI Local)**
   - O contêiner React do Gestor (`/gestor-ui/`) foi devidamente integrado ao script agnóstico que gera o artefato distrinbuído em `packages/intellicare-core/intellicare_core/static/gestor-ui`. 
   - O comando `tools/scripts/build_gestor_ui.sh` foi executado para gerar a build de produção, garantindo que os assets estejam disponíveis para o App central servir via `GET /gestor-ui/`.

3. **Validação TypeScript**
   - Todos os erros de compilação foram resolvidos: `tsc --noEmit` retorna 0 erros.
   - Adicionado `src/types/tabler-icons.d.ts` com `declare module '@tabler/icons-react'` para resolver tipagens ausentes do `@tabler/icons-react`.
   - Corrigido problema de tipos @mantine (diretório `lib/` ausente no `node_modules`) — copiados do AdminUI.

4. **Infraestrutura Keycloak**
   - Client `gestor-ui` adicionado via `tools/scripts/setup_keycloak.py` (step 7), com `publicClient=true`, redirect URIs para dev (5175) e produção.

5. **Montagem no Serviço Principal**
   - `loader.load("gestor")` adicionado ao `main.py`.
   - Static mount em `/gestor-ui/` para servir a build de produção.

## Arquivos Criados/Modificados

| Arquivo | Ação |
|---------|------|
| `frontend/GestorUI/*` | Criado — projeto completo React + Vite + Mantine |
| `frontend/GestorUI/src/auth/AuthProvider.tsx` | Criado — OIDC com Keycloak |
| `frontend/GestorUI/src/auth/TokenSync.tsx` | Criado — sync token para sessionStorage |
| `frontend/GestorUI/src/api/client.ts` | Criado — axios com interceptor Bearer |
| `frontend/GestorUI/src/hooks/useProfile.ts` | Criado — GET/PUT /gestor/profile |
| `frontend/GestorUI/src/hooks/useDocuments.ts` | Criado — CRUD documentos RAG |
| `frontend/GestorUI/src/hooks/useUsers.ts` | Criado — gestão de usuários |
| `frontend/GestorUI/src/pages/Dashboard.tsx` | Criado — painel com métricas |
| `frontend/GestorUI/src/pages/DocumentUpload.tsx` | Criado — upload drag-and-drop |
| `frontend/GestorUI/src/pages/UsageReport.tsx` | Criado — relatório de uso |
| `frontend/GestorUI/src/pages/UserList.tsx` | Criado — lista/convite/desativação |
| `frontend/GestorUI/src/pages/ProfilePage.tsx` | Criado — perfil da unidade |
| `frontend/GestorUI/src/App.tsx` | Criado — app principal com navegação |
| `frontend/GestorUI/src/types/tabler-icons.d.ts` | Criado — type declarations |
| `tools/scripts/setup_keycloak.py` | Modificado — client gestor-ui |
| `tools/scripts/build_gestor_ui.sh` | Criado — script de build |
| `packages/intellicare-core/intellicare_core/main.py` | Modificado — mount gestor-ui |

## Próximos Passos
Verificações End-to-End validando fluxos de usuário entre as interfaces Gestor e Admin (DEM-006). A infraestrutura RAG (DEM-009) agora conta interatividade completa no front-end para o tenant gerir sua base clínica.
