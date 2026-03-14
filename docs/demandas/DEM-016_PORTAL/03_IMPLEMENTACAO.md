# DEM-016 — Portal de Entrada: Implementação

## Resumo

Portal mínimo de entrada OIDC que autentica via Keycloak e redireciona o
usuário para a UI correspondente ao seu role (PLATFORM_ADMIN → /admin-ui/,
TENANT_GESTOR → /gestor-ui/, CLINICO → /clinico-ui/). Sem react-router,
sem TanStack Query, sem Axios — apenas OIDC + Mantine para tela de erro.

---

## Arquivos Criados / Modificados

### Novos (frontend/Portal/)

| Arquivo | Papel |
|---|---|
| `package.json` | Deps mínimas: react, react-dom, oidc-client-ts, react-oidc-context, @mantine/core+hooks |
| `tsconfig.json` | TypeScript strict, ES2020, ESNext modules |
| `vite.config.ts` | Build output → `intellicare_core/static/portal/`, dev port 5176 |
| `index.html` | Entry point HTML |
| `src/vite-env.d.ts` | Referência vite/client para import.meta.env |
| `src/main.tsx` | ReactDOM.createRoot |
| `src/App.tsx` | Lógica principal: OIDC auth → extractRoles → redirect por ROLE_ROUTES ou Unauthorized |
| `src/auth/AuthProvider.tsx` | OIDC config (authority, client_id=portal, tokens em memória) |
| `src/pages/Unauthorized.tsx` | Tela "Acesso não autorizado" com botão Sair |
| `src/pages/Redirecting.tsx` | Componente de loading reutilizável |
| `.env.local` | VITE_KEYCLOAK_URL=http://localhost:8080 |

### Novos (tools/scripts/)

| Arquivo | Papel |
|---|---|
| `build_portal.sh` | npm ci + npm run build → static/portal/ |

### Modificados

| Arquivo | Alteração |
|---|---|
| `tools/scripts/setup_keycloak.py` | Step 9: client `portal` (public, redirectUris localhost:5176 + :8000). Steps renumerados (users → step 10) |
| `packages/intellicare-core/intellicare_core/main.py` | Mount `/` (portal) como último — após /admin-ui/, /gestor-ui/, /clinico-ui/ |

---

## Decisões Técnicas

1. **Sem react-router** — Portal tem uma única "rota". A lógica está em `App.tsx` com `useAuth()`.
2. **Sem TanStack Query / Axios** — Portal não faz chamadas à API. Apenas lê o JWT e redireciona.
3. **`window.location.replace()`** — Redirecionamento hard para a UI correta (não SPA navigation).
4. **Tokens em memória** — `userStore: undefined` no AuthProvider. Sem localStorage.
5. **Mount `/` por último** — No FastAPI, mounts são avaliados em ordem. O `/` capturaria tudo se fosse primeiro.
6. **Removed @tabler/icons-react** — Spec usava IconShieldOff, mas para manter o bundle mínimo (< 100KB gzip) a tela Unauthorized usa apenas Mantine components.

---

## Validação

- TypeScript: **0 erros** (`tsc --noEmit`)
- Estrutura segue spec `02_TECNICA.md` fielmente
- Bundle estimado < 100 KB gzip (react + react-dom + oidc-client-ts + mantine core mínimo)

---

## Fluxo Implementado

```
GET / → Portal (static)
  → useAuth() verifica sessão OIDC
    → Não autenticado: signinRedirect() → Keycloak login
    → Autenticado: extractRoles(user)
      → PLATFORM_ADMIN  → window.location.replace('/admin-ui/')
      → TENANT_GESTOR   → window.location.replace('/gestor-ui/')
      → CLINICO          → window.location.replace('/clinico-ui/')
      → Sem role         → <Unauthorized /> com botão Sair
```
