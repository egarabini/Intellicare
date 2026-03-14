# DEM-016 — Portal de Entrada: Especificação Técnica

## 1. Estrutura de Arquivos

```
frontend/Portal/
├── package.json
├── tsconfig.json
├── vite.config.ts
├── index.html
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── auth/
    │   └── AuthProvider.tsx
    └── pages/
        ├── Redirecting.tsx
        └── Unauthorized.tsx
tools/scripts/
└── build_portal.sh
```

---

## 2. package.json

```json
{
  "name": "intellicare-portal",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev":     "vite",
    "build":   "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "@mantine/core":        "^7.10.0",
    "@mantine/hooks":       "^7.10.0",
    "oidc-client-ts":       "^3.0.1",
    "react":                "^18.3.0",
    "react-dom":            "^18.3.0",
    "react-oidc-context":   "^3.1.0"
  },
  "devDependencies": {
    "@types/react":         "^18.3.0",
    "@types/react-dom":     "^18.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "typescript":           "^5.4.0",
    "vite":                 "^5.3.0"
  }
}
```

> Bundle mínimo — sem react-router-dom, sem TanStack Query, sem Axios.
> O portal só precisa de OIDC + Mantine para a tela de erro.

---

## 3. vite.config.ts

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/',
  build: {
    outDir: '../../intellicare_core/static/portal',
    emptyOutDir: true,
  },
  server: {
    port: 5176,
    proxy: {
      '/health': 'http://localhost:8000',
    },
  },
})
```

---

## 4. Auth Provider

**`src/auth/AuthProvider.tsx`**

```tsx
import React from 'react'
import { AuthProvider as OidcAuthProvider, AuthProviderProps } from 'react-oidc-context'

const oidcConfig: AuthProviderProps = {
  authority:    import.meta.env.VITE_KEYCLOAK_URL + '/realms/intellicare',
  client_id:    'portal',
  redirect_uri: window.location.origin + '/',
  post_logout_redirect_uri: window.location.origin + '/',
  scope:        'openid profile email',
  userStore:    undefined,   // tokens apenas em memória
  onSigninCallback: () => {
    // limpa os parâmetros OIDC da URL após callback
    window.history.replaceState({}, document.title, '/')
  },
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  return <OidcAuthProvider {...oidcConfig}>{children}</OidcAuthProvider>
}
```

---

## 5. Lógica de Redirecionamento

**`src/App.tsx`**

```tsx
import { useEffect } from 'react'
import { useAuth } from 'react-oidc-context'
import { MantineProvider, Center, Loader, Text, Stack } from '@mantine/core'
import { AuthProvider } from './auth/AuthProvider'
import { Unauthorized } from './pages/Unauthorized'
import '@mantine/core/styles.css'

// Mapeamento role → URL de destino
const ROLE_ROUTES: Record<string, string> = {
  PLATFORM_ADMIN: '/admin-ui/',
  TENANT_GESTOR:  '/gestor-ui/',
  CLINICO:        '/clinico-ui/',
}

function extractRoles(user: { profile: Record<string, unknown> } | null | undefined): string[] {
  if (!user) return []
  // Keycloak emite roles em realm_access.roles
  const realmAccess = user.profile['realm_access'] as { roles?: string[] } | undefined
  return realmAccess?.roles ?? []
}

function Router() {
  const auth = useAuth()

  useEffect(() => {
    // Não autenticado → inicia login imediatamente
    if (!auth.isLoading && !auth.isAuthenticated) {
      auth.signinRedirect()
    }
  }, [auth.isLoading, auth.isAuthenticated])

  // Carregando / aguardando redirecionamento para Keycloak
  if (auth.isLoading || !auth.isAuthenticated) {
    return (
      <Center h="100vh">
        <Stack align="center" gap="sm">
          <Loader size="lg" />
          <Text c="dimmed">Autenticando...</Text>
        </Stack>
      </Center>
    )
  }

  // Autenticado — determinar destino pelo role
  const roles = extractRoles(auth.user)
  const destination = Object.entries(ROLE_ROUTES).find(
    ([role]) => roles.includes(role)
  )?.[1]

  if (destination) {
    // Redireciona para a UI correta
    window.location.replace(destination)
    return (
      <Center h="100vh">
        <Stack align="center" gap="sm">
          <Loader size="lg" />
          <Text c="dimmed">Redirecionando...</Text>
        </Stack>
      </Center>
    )
  }

  // Nenhum role reconhecido
  return <Unauthorized onLogout={() => auth.signoutRedirect()} email={auth.user?.profile.email as string} />
}

export default function App() {
  return (
    <AuthProvider>
      <MantineProvider>
        <Router />
      </MantineProvider>
    </AuthProvider>
  )
}
```

---

## 6. Tela de Acesso Não Autorizado

**`src/pages/Unauthorized.tsx`**

```tsx
import { Center, Stack, Title, Text, Button, ThemeIcon, Paper } from '@mantine/core'
import { IconShieldOff } from '@tabler/icons-react'

interface Props {
  email?: string
  onLogout: () => void
}

export function Unauthorized({ email, onLogout }: Props) {
  return (
    <Center h="100vh" bg="gray.0">
      <Paper withBorder shadow="md" p="xl" radius="md" maw={420} w="100%">
        <Stack align="center" gap="md">
          <ThemeIcon size={64} radius="xl" color="red" variant="light">
            <IconShieldOff size={36} />
          </ThemeIcon>
          <Title order={3} ta="center">Acesso não autorizado</Title>
          <Text c="dimmed" ta="center" size="sm">
            O usuário <strong>{email ?? 'desconhecido'}</strong> não possui
            um perfil de acesso configurado nesta plataforma.
          </Text>
          <Text c="dimmed" ta="center" size="xs">
            Entre em contato com o administrador do sistema.
          </Text>
          <Button fullWidth color="red" variant="light" onClick={onLogout}>
            Sair
          </Button>
        </Stack>
      </Paper>
    </Center>
  )
}
```

---

## 7. main.tsx e index.html

**`src/main.tsx`**

```tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
```

**`index.html`**

```html
<!DOCTYPE html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>IntelliCare</title>
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

---

## 8. Script de Build

**`tools/scripts/build_portal.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail

UI_DIR="$(git rev-parse --show-toplevel)/frontend/Portal"
OUT_DIR="$(git rev-parse --show-toplevel)/intellicare_core/static/portal"

echo "==> Instalando dependências..."
cd "$UI_DIR"
npm ci

echo "==> Gerando build de produção..."
npm run build

echo "==> Bundle size:"
du -sh "$OUT_DIR"
```

---

## 9. Keycloak — Client `portal`

Adicionar em `tools/scripts/setup_keycloak.py`:

```python
ensure_client(admin, realm="intellicare", client_id="portal", config={
    "publicClient": True,
    "redirectUris": [
        "http://localhost:5176/*",
        "http://localhost:8000/*"
    ],
    "webOrigins": ["http://localhost:5176", "http://localhost:8000"],
    "standardFlowEnabled": True,
    "directAccessGrantsEnabled": False,
})
```

---

## 10. Mount no FastAPI

Em `intellicare_core/main.py`, o portal deve ser o **último** mount e servir `/`:

```python
# Mounts específicos primeiro
app.mount("/admin-ui",   StaticFiles(directory=str(STATIC_ROOT / "admin-ui"),   html=True), name="admin-ui")
app.mount("/gestor-ui",  StaticFiles(directory=str(STATIC_ROOT / "gestor-ui"),  html=True), name="gestor-ui")
app.mount("/clinico-ui", StaticFiles(directory=str(STATIC_ROOT / "clinico-ui"), html=True), name="clinico-ui")

# Portal por último — captura /
app.mount("/",           StaticFiles(directory=str(STATIC_ROOT / "portal"),     html=True), name="portal")
```

> ⚠️ A ordem dos mounts importa no FastAPI — o `/` deve ser o último para não
> interceptar as rotas da API.

---

## 11. Variáveis de Ambiente (`.env.local`)

```
VITE_KEYCLOAK_URL=http://localhost:8080
```

> Portal não precisa de `VITE_API_BASE_URL` — não faz chamadas à API.

---

## 12. Portas de desenvolvimento (todas as UIs)

| UI | Porta dev | Base path | Client ID |
|---|---|---|---|
| Portal | 5176 | `/` | `portal` |
| AdminUI | 5174 | `/admin-ui/` | `admin-ui` |
| GestorUI | 5175 | `/gestor-ui/` | `gestor-ui` |
| ClinicoUI | 5173 | `/clinico-ui/` | `clinico-ui` |

---

## 13. Checklist de Aceite Técnico

- [ ] `npm run build` sem erros TypeScript
- [ ] Bundle gzip < 100 KB (`du -sh static/portal`)
- [ ] Acessar `http://localhost:8000/` sem sessão → redireciona para Keycloak
- [ ] Login `platform-admin` → redireciona para `/admin-ui/`
- [ ] Login `gestor-dev` → redireciona para `/gestor-ui/`
- [ ] Login `clinico-dev` → redireciona para `/clinico-ui/`
- [ ] Usuário sem role → tela "Acesso não autorizado" com email exibido
- [ ] Botão "Sair" encerra sessão Keycloak e retorna ao portal
- [ ] `GET /` via FastAPI → 200
- [ ] Rotas `/admin/`, `/slm/`, `/gestor/` ainda respondem corretamente (mount `/` não interfere)
