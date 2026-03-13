# DEM-006 — Admin Frontend: Especificação Técnica (REVISADA)

> **Revisão 2026-03-13**: Stack alterada de Blazor WASM → React + Vite + Mantine UI
> para consistência com DEM-015 (ClinicoUI) e alinhamento com a stack Python do projeto.

---

## 1. Estrutura de Arquivos

```
frontend/AdminUI/
├── package.json
├── tsconfig.json
├── vite.config.ts
├── index.html
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── auth/
│   │   ├── AuthProvider.tsx
│   │   └── TokenSync.tsx
│   ├── api/
│   │   └── client.ts
│   ├── hooks/
│   │   └── useTenants.ts
│   ├── components/
│   │   └── StatusBadge.tsx
│   └── pages/
│       ├── TenantList.tsx
│       └── TenantForm.tsx
tools/scripts/
└── build_admin_ui.sh
```

---

## 2. package.json

```json
{
  "name": "admin-ui",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev":     "vite",
    "build":   "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "@mantine/core":           "^7.10.0",
    "@mantine/hooks":          "^7.10.0",
    "@mantine/notifications":  "^7.10.0",
    "@mantine/dates":          "^7.10.0",
    "@tabler/icons-react":     "^3.5.0",
    "@tanstack/react-query":   "^5.40.0",
    "axios":                   "^1.7.0",
    "oidc-client-ts":          "^3.0.1",
    "react":                   "^18.3.0",
    "react-dom":               "^18.3.0",
    "react-oidc-context":      "^3.1.0",
    "react-router-dom":        "^6.23.0"
  },
  "devDependencies": {
    "@types/react":            "^18.3.0",
    "@types/react-dom":        "^18.3.0",
    "@vitejs/plugin-react":    "^4.3.0",
    "typescript":              "^5.4.0",
    "vite":                    "^5.3.0"
  }
}
```

---

## 3. vite.config.ts

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/admin-ui/',
  build: {
    outDir: '../../intellicare_core/static/admin-ui',
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '/admin':  'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
})
```

---

## 4. Auth Provider

**`src/auth/AuthProvider.tsx`** — idêntico ao ClinicoUI, client_id diferente:

```tsx
import React from 'react'
import { AuthProvider as OidcAuthProvider, AuthProviderProps } from 'react-oidc-context'

const oidcConfig: AuthProviderProps = {
  authority:    import.meta.env.VITE_KEYCLOAK_URL + '/realms/intellicare',
  client_id:    'admin-ui',
  redirect_uri: window.location.origin + '/admin-ui/callback',
  post_logout_redirect_uri: window.location.origin + '/admin-ui/',
  scope:        'openid profile email',
  userStore:    undefined,    // tokens apenas em memória
  onSigninCallback: () => {
    window.history.replaceState({}, document.title, window.location.pathname)
  },
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  return <OidcAuthProvider {...oidcConfig}>{children}</OidcAuthProvider>
}
```

**`src/auth/TokenSync.tsx`**

```tsx
import { useEffect } from 'react'
import { useAuth } from 'react-oidc-context'

export function TokenSync() {
  const auth = useAuth()
  useEffect(() => {
    if (auth.user?.access_token) {
      sessionStorage.setItem('oidc.access_token', auth.user.access_token)
    } else {
      sessionStorage.removeItem('oidc.access_token')
    }
  }, [auth.user?.access_token])
  return null
}
```

---

## 5. Axios Client

**`src/api/client.ts`**

```typescript
import axios, { InternalAxiosRequestConfig } from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '',
  timeout: 30_000,
})

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = sessionStorage.getItem('oidc.access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export default apiClient
```

---

## 6. Types e Hook

**`src/hooks/useTenants.ts`**

```typescript
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import apiClient from '../api/client'

export interface Tenant {
  id: string
  name: string
  slug: string
  status: 'active' | 'suspended' | 'trial'
  plan: string
  created_at: string
}

export interface TenantCreateRequest {
  name: string
  slug: string
  plan: string
}

export interface PagedResult<T> {
  items: T[]
  total: number
  page: number
  size: number
}

export function useTenants(page = 1, size = 20) {
  return useQuery<PagedResult<Tenant>>({
    queryKey: ['tenants', page, size],
    queryFn: async () => {
      const { data } = await apiClient.get('/admin/tenants', {
        params: { page, size },
      })
      return data
    },
  })
}

export function useCreateTenant() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: TenantCreateRequest) =>
      apiClient.post('/admin/tenants', body).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tenants'] }),
  })
}

export function useUpdateTenantStatus() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      apiClient.patch(`/admin/tenants/${id}/status`, { status }).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tenants'] }),
  })
}

export function useTenantUsers(tenantId: string) {
  return useQuery({
    queryKey: ['tenant-users', tenantId],
    queryFn: async () => {
      const { data } = await apiClient.get(`/admin/tenants/${tenantId}/users`)
      return data
    },
    enabled: !!tenantId,
  })
}
```

---

## 7. Componente StatusBadge

**`src/components/StatusBadge.tsx`**

```tsx
import { Badge } from '@mantine/core'

const colorMap: Record<string, string> = {
  active:    'green',
  suspended: 'red',
  trial:     'yellow',
}

export function StatusBadge({ status }: { status: string }) {
  return (
    <Badge color={colorMap[status] ?? 'gray'} variant="light">
      {status}
    </Badge>
  )
}
```

---

## 8. Página TenantList

**`src/pages/TenantList.tsx`**

```tsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Title, Button, Group, Table, Text, Loader, Center,
  ActionIcon, Tooltip, Stack, Pagination,
} from '@mantine/core'
import { IconPlus, IconEye, IconPlayerPause, IconPlayerPlay } from '@tabler/icons-react'
import { useTenants, useUpdateTenantStatus } from '../hooks/useTenants'
import { StatusBadge } from '../components/StatusBadge'
import { notifications } from '@mantine/notifications'

export function TenantList() {
  const [page, setPage] = useState(1)
  const { data, isLoading } = useTenants(page)
  const updateStatus = useUpdateTenantStatus()
  const navigate = useNavigate()

  const handleToggle = async (id: string, current: string) => {
    const next = current === 'active' ? 'suspended' : 'active'
    try {
      await updateStatus.mutateAsync({ id, status: next })
      notifications.show({
        title: 'Status atualizado',
        message: `Tenant ${next === 'active' ? 'reativado' : 'suspenso'} com sucesso.`,
        color: next === 'active' ? 'green' : 'orange',
      })
    } catch {
      notifications.show({ title: 'Erro', message: 'Falha ao atualizar status.', color: 'red' })
    }
  }

  if (isLoading) return <Center><Loader /></Center>

  const totalPages = data ? Math.ceil(data.total / 20) : 1

  return (
    <Stack>
      <Group justify="space-between">
        <Title order={2}>Tenants</Title>
        <Button leftSection={<IconPlus size={16} />} onClick={() => navigate('/tenants/new')}>
          Novo Tenant
        </Button>
      </Group>

      <Table highlightOnHover striped withTableBorder>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Nome</Table.Th>
            <Table.Th>Slug</Table.Th>
            <Table.Th>Plano</Table.Th>
            <Table.Th>Status</Table.Th>
            <Table.Th>Criado em</Table.Th>
            <Table.Th>Ações</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {data?.items.map(t => (
            <Table.Tr key={t.id}>
              <Table.Td>{t.name}</Table.Td>
              <Table.Td><Text size="sm" c="dimmed" ff="monospace">{t.slug}</Text></Table.Td>
              <Table.Td>{t.plan}</Table.Td>
              <Table.Td><StatusBadge status={t.status} /></Table.Td>
              <Table.Td>{new Date(t.created_at).toLocaleDateString('pt-BR')}</Table.Td>
              <Table.Td>
                <Group gap="xs">
                  <Tooltip label="Ver usuários">
                    <ActionIcon variant="subtle" onClick={() => navigate(`/tenants/${t.id}/users`)}>
                      <IconEye size={16} />
                    </ActionIcon>
                  </Tooltip>
                  <Tooltip label={t.status === 'active' ? 'Suspender' : 'Reativar'}>
                    <ActionIcon
                      variant="subtle"
                      color={t.status === 'active' ? 'orange' : 'green'}
                      onClick={() => handleToggle(t.id, t.status)}
                      loading={updateStatus.isPending}
                    >
                      {t.status === 'active'
                        ? <IconPlayerPause size={16} />
                        : <IconPlayerPlay size={16} />}
                    </ActionIcon>
                  </Tooltip>
                </Group>
              </Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>

      {totalPages > 1 && (
        <Pagination total={totalPages} value={page} onChange={setPage} />
      )}
    </Stack>
  )
}
```

---

## 9. Página TenantForm

**`src/pages/TenantForm.tsx`**

```tsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Title, TextInput, Select, Button, Stack, Group, Paper, Text,
} from '@mantine/core'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { useCreateTenant } from '../hooks/useTenants'

export function TenantForm() {
  const navigate = useNavigate()
  const createTenant = useCreateTenant()

  const form = useForm({
    initialValues: { name: '', slug: '', plan: 'basic' },
    validate: {
      name: v => v.length < 3 ? 'Nome deve ter ao menos 3 caracteres' : null,
      slug: v => /^[a-z0-9-]+$/.test(v) ? null : 'Slug: apenas letras minúsculas, números e hífens',
      plan: v => v ? null : 'Selecione um plano',
    },
  })

  // auto-gera slug a partir do nome
  const handleNameChange = (name: string) => {
    form.setFieldValue('name', name)
    const slug = name
      .toLowerCase()
      .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '')
    form.setFieldValue('slug', slug)
  }

  const handleSubmit = async (values: typeof form.values) => {
    try {
      await createTenant.mutateAsync(values)
      notifications.show({
        title: 'Tenant criado',
        message: `${values.name} criado com sucesso.`,
        color: 'green',
      })
      navigate('/')
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail ?? 'Erro ao criar tenant.'
      notifications.show({ title: 'Erro', message: msg, color: 'red' })
    }
  }

  return (
    <Stack maw={480}>
      <Title order={2}>Novo Tenant</Title>
      <Paper withBorder p="lg" radius="md">
        <form onSubmit={form.onSubmit(handleSubmit)}>
          <Stack>
            <TextInput
              label="Nome"
              placeholder="Clínica São Lucas"
              required
              {...form.getInputProps('name')}
              onChange={e => handleNameChange(e.currentTarget.value)}
            />
            <TextInput
              label="Slug"
              placeholder="clinica-sao-lucas"
              description="Gerado automaticamente. Identificador único e imutável."
              required
              {...form.getInputProps('slug')}
            />
            <Select
              label="Plano"
              data={[
                { value: 'basic',      label: 'Basic' },
                { value: 'pro',        label: 'Pro' },
                { value: 'enterprise', label: 'Enterprise' },
              ]}
              required
              {...form.getInputProps('plan')}
            />
            <Group justify="flex-end">
              <Button variant="subtle" onClick={() => navigate('/')}>Cancelar</Button>
              <Button type="submit" loading={createTenant.isPending}>Criar Tenant</Button>
            </Group>
          </Stack>
        </form>
      </Paper>
    </Stack>
  )
}
```

---

## 10. App.tsx e main.tsx

**`src/App.tsx`**

```tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { MantineProvider, AppShell, Title, Group, Button, Text } from '@mantine/core'
import { Notifications } from '@mantine/notifications'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAuth } from 'react-oidc-context'
import { AuthProvider } from './auth/AuthProvider'
import { TokenSync } from './auth/TokenSync'
import { TenantList } from './pages/TenantList'
import { TenantForm } from './pages/TenantForm'
import '@mantine/core/styles.css'
import '@mantine/notifications/styles.css'

const queryClient = new QueryClient()

function AppRoutes() {
  const auth = useAuth()

  if (auth.isLoading) return <Text p="md">Autenticando...</Text>
  if (!auth.isAuthenticated) {
    auth.signinRedirect()
    return null
  }

  return (
    <>
      <TokenSync />
      <AppShell header={{ height: 56 }} padding="md">
        <AppShell.Header>
          <Group h="100%" px="md" justify="space-between">
            <Title order={4}>IntelliCare — Admin</Title>
            <Group>
              <Text size="sm" c="dimmed">{auth.user?.profile.email}</Text>
              <Button size="xs" variant="subtle" onClick={() => auth.signoutRedirect()}>
                Sair
              </Button>
            </Group>
          </Group>
        </AppShell.Header>
        <AppShell.Main>
          <Routes>
            <Route path="/"                element={<TenantList />} />
            <Route path="/tenants/new"     element={<TenantForm />} />
            <Route path="*"                element={<Navigate to="/" />} />
          </Routes>
        </AppShell.Main>
      </AppShell>
    </>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <QueryClientProvider client={queryClient}>
        <MantineProvider>
          <Notifications />
          <BrowserRouter basename="/admin-ui">
            <AppRoutes />
          </BrowserRouter>
        </MantineProvider>
      </QueryClientProvider>
    </AuthProvider>
  )
}
```

---

## 11. Script de Build

**`tools/scripts/build_admin_ui.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail

UI_DIR="$(git rev-parse --show-toplevel)/frontend/AdminUI"
OUT_DIR="$(git rev-parse --show-toplevel)/intellicare_core/static/admin-ui"

echo "==> Instalando dependências..."
cd "$UI_DIR"
npm ci

echo "==> Gerando build de produção..."
npm run build

echo "==> Artefato em: $OUT_DIR"
ls -lh "$OUT_DIR"
```

---

## 12. Keycloak — Client `admin-ui`

Adicionar em `tools/scripts/setup_keycloak.py`:

```python
ensure_client(admin, realm="intellicare", client_id="admin-ui", config={
    "publicClient": True,
    "redirectUris": [
        "http://localhost:5174/*",
        "http://localhost:8000/admin-ui/*"
    ],
    "webOrigins": ["http://localhost:5174", "http://localhost:8000"],
    "standardFlowEnabled": True,
    "directAccessGrantsEnabled": False,
})
```

---

## 13. Mount no FastAPI

Em `intellicare_core/main.py`:

```python
app.mount(
    "/admin-ui",
    StaticFiles(directory=str(STATIC_ROOT / "admin-ui"), html=True),
    name="admin-ui",
)
```

---

## 14. Variáveis de Ambiente (`.env.local`)

```
VITE_KEYCLOAK_URL=http://localhost:8080
VITE_API_BASE_URL=http://localhost:8000
```

> Usar porta `5174` no dev para não conflitar com ClinicoUI (`5173`).

---

## 15. Checklist de Aceite Técnico

- [ ] `npm run build` sem erros TypeScript
- [ ] Login OIDC redireciona para Keycloak com `client_id=admin-ui`
- [ ] Apenas usuários com role `PLATFORM_ADMIN` conseguem acessar (`403` para outros roles)
- [ ] Lista de tenants carrega com paginação
- [ ] Formulário gera slug automaticamente a partir do nome
- [ ] Suspender/reativar tenant atualiza badge sem reload da página
- [ ] `sessionStorage` tem token; `localStorage` vazio
- [ ] Build copiado para `intellicare_core/static/admin-ui/`
- [ ] FastAPI serve `GET /admin-ui/` com status 200
