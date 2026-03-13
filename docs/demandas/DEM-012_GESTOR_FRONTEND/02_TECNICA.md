# DEM-012 — Gestor Frontend: Especificação Técnica (REVISADA)

> **Revisão 2026-03-13**: Stack alterada de Blazor WASM → React + Vite + Mantine UI
> para consistência com DEM-006 (AdminUI) e DEM-015 (ClinicoUI).

---

## 1. Estrutura de Arquivos

```
frontend/GestorUI/
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
│   │   ├── useProfile.ts
│   │   ├── useDocuments.ts
│   │   └── useUsers.ts
│   └── pages/
│       ├── Dashboard.tsx
│       ├── DocumentUpload.tsx
│       └── UsageReport.tsx
tools/scripts/
└── build_gestor_ui.sh
```

---

## 2. package.json

```json
{
  "name": "gestor-ui",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev":   "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "@mantine/core":           "^7.10.0",
    "@mantine/hooks":          "^7.10.0",
    "@mantine/notifications":  "^7.10.0",
    "@mantine/dropzone":       "^7.10.0",
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
  base: '/gestor-ui/',
  build: {
    outDir: '../../intellicare_core/static/gestor-ui',
    emptyOutDir: true,
  },
  server: {
    port: 5175,
    proxy: {
      '/gestor':  'http://localhost:8000',
      '/vector':  'http://localhost:8000',
    },
  },
})
```

---

## 4. Auth (igual AdminUI e ClinicoUI)

**`src/auth/AuthProvider.tsx`**

```tsx
import React from 'react'
import { AuthProvider as OidcAuthProvider, AuthProviderProps } from 'react-oidc-context'

const oidcConfig: AuthProviderProps = {
  authority:    import.meta.env.VITE_KEYCLOAK_URL + '/realms/intellicare',
  client_id:    'gestor-ui',
  redirect_uri: window.location.origin + '/gestor-ui/callback',
  post_logout_redirect_uri: window.location.origin + '/gestor-ui/',
  scope:        'openid profile email',
  userStore:    undefined,
  onSigninCallback: () => {
    window.history.replaceState({}, document.title, window.location.pathname)
  },
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  return <OidcAuthProvider {...oidcConfig}>{children}</OidcAuthProvider>
}
```

**`src/auth/TokenSync.tsx`** — idêntico ao AdminUI e ClinicoUI.

---

## 5. Hooks

**`src/hooks/useDocuments.ts`**

```typescript
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import apiClient from '../api/client'

export interface DocumentStat {
  source_path: string
  chunk_count: number
  last_updated: string
}

export function useDocuments() {
  return useQuery<DocumentStat[]>({
    queryKey: ['documents'],
    queryFn: async () => {
      const { data } = await apiClient.get('/gestor/documents')
      return data
    },
  })
}

export function useUploadDocument() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (file: File) => {
      const form = new FormData()
      form.append('file', file)
      const { data } = await apiClient.post('/gestor/documents/upload', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['documents'] }),
  })
}

export function useDeleteDocument() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (path: string) =>
      apiClient.delete(`/vector/documents/${encodeURIComponent(path)}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['documents'] }),
  })
}
```

**`src/hooks/useUsers.ts`**

```typescript
import { useQuery } from '@tanstack/react-query'
import apiClient from '../api/client'

export function useUsers() {
  return useQuery({
    queryKey: ['gestor-users'],
    queryFn: async () => {
      const { data } = await apiClient.get('/gestor/users')
      return data
    },
  })
}
```

---

## 6. Página DocumentUpload

**`src/pages/DocumentUpload.tsx`**

```tsx
import { useState } from 'react'
import {
  Title, Stack, Text, Table, Badge, ActionIcon,
  Tooltip, Group, Paper, Progress,
} from '@mantine/core'
import { Dropzone, MIME_TYPES } from '@mantine/dropzone'
import { IconUpload, IconFile, IconTrash, IconX } from '@tabler/icons-react'
import { notifications } from '@mantine/notifications'
import { useDocuments, useUploadDocument, useDeleteDocument } from '../hooks/useDocuments'

export function DocumentUpload() {
  const { data: docs, isLoading } = useDocuments()
  const upload = useUploadDocument()
  const deleteDoc = useDeleteDocument()
  const [uploading, setUploading] = useState(false)

  const handleDrop = async (files: File[]) => {
    setUploading(true)
    for (const file of files) {
      try {
        await upload.mutateAsync(file)
        notifications.show({
          title: 'Upload concluído',
          message: `${file.name} ingerido com sucesso.`,
          color: 'green',
        })
      } catch {
        notifications.show({
          title: 'Erro no upload',
          message: `Falha ao processar ${file.name}.`,
          color: 'red',
        })
      }
    }
    setUploading(false)
  }

  const handleDelete = async (path: string) => {
    try {
      await deleteDoc.mutateAsync(path)
      notifications.show({ title: 'Removido', message: path, color: 'orange' })
    } catch {
      notifications.show({ title: 'Erro', message: 'Falha ao remover.', color: 'red' })
    }
  }

  return (
    <Stack>
      <Title order={2}>Base de Conhecimento</Title>

      <Dropzone
        onDrop={handleDrop}
        accept={[MIME_TYPES.pdf, 'application/msword',
                 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']}
        maxSize={20 * 1024 * 1024}
        loading={uploading}
      >
        <Group justify="center" gap="xl" mih={100}>
          <Dropzone.Accept><IconUpload size={48} color="blue" /></Dropzone.Accept>
          <Dropzone.Reject><IconX size={48} color="red" /></Dropzone.Reject>
          <Dropzone.Idle><IconFile size={48} color="gray" /></Dropzone.Idle>
          <Stack gap={4} align="center">
            <Text size="lg" fw={500}>Arraste PDFs ou DOCXs aqui</Text>
            <Text size="sm" c="dimmed">Máximo 20 MB por arquivo</Text>
          </Stack>
        </Group>
      </Dropzone>

      {uploading && <Progress value={100} animated />}

      <Paper withBorder>
        <Table highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Arquivo</Table.Th>
              <Table.Th>Chunks</Table.Th>
              <Table.Th>Última atualização</Table.Th>
              <Table.Th>Ações</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {docs?.map(d => (
              <Table.Tr key={d.source_path}>
                <Table.Td>
                  <Text size="sm" ff="monospace">{d.source_path.split('/').pop()}</Text>
                </Table.Td>
                <Table.Td>
                  <Badge variant="light">{d.chunk_count} chunks</Badge>
                </Table.Td>
                <Table.Td>
                  {new Date(d.last_updated).toLocaleDateString('pt-BR')}
                </Table.Td>
                <Table.Td>
                  <Tooltip label="Remover da base">
                    <ActionIcon
                      color="red" variant="subtle"
                      onClick={() => handleDelete(d.source_path)}
                      loading={deleteDoc.isPending}
                    >
                      <IconTrash size={16} />
                    </ActionIcon>
                  </Tooltip>
                </Table.Td>
              </Table.Tr>
            ))}
            {!isLoading && !docs?.length && (
              <Table.Tr>
                <Table.Td colSpan={4}>
                  <Text ta="center" c="dimmed" py="lg">Nenhum documento na base.</Text>
                </Table.Td>
              </Table.Tr>
            )}
          </Table.Tbody>
        </Table>
      </Paper>
    </Stack>
  )
}
```

---

## 7. Página UsageReport

**`src/pages/UsageReport.tsx`**

```tsx
import { Title, Stack, Table, Text, Loader, Center, Paper, Badge } from '@mantine/core'
import { useQuery } from '@tanstack/react-query'
import apiClient from '../api/client'

interface UsageReport {
  period: string
  total_queries: number
  unique_users: number
  avg_response_time_ms: number
  top_topics: string[]
}

export function UsageReport() {
  const { data, isLoading } = useQuery<UsageReport>({
    queryKey: ['usage-report'],
    queryFn: async () => {
      const { data } = await apiClient.get('/gestor/reports/usage')
      return data
    },
  })

  if (isLoading) return <Center><Loader /></Center>

  return (
    <Stack>
      <Title order={2}>Relatório de Uso</Title>
      <Paper withBorder p="lg" radius="md">
        <Stack>
          <Text><strong>Período:</strong> {data?.period}</Text>
          <Text><strong>Total de consultas:</strong> {data?.total_queries}</Text>
          <Text><strong>Usuários únicos:</strong> {data?.unique_users}</Text>
          <Text>
            <strong>Tempo médio de resposta:</strong> {data?.avg_response_time_ms} ms
          </Text>
          <Text fw={500}>Tópicos mais consultados:</Text>
          <Stack gap={4}>
            {data?.top_topics.map((t, i) => (
              <Badge key={i} variant="light" size="sm">{t}</Badge>
            ))}
          </Stack>
        </Stack>
      </Paper>
    </Stack>
  )
}
```

---

## 8. App.tsx

```tsx
import { BrowserRouter, Routes, Route, Navigate, Link } from 'react-router-dom'
import { MantineProvider, AppShell, NavLink, Title, Group, Button, Text } from '@mantine/core'
import { Notifications } from '@mantine/notifications'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAuth } from 'react-oidc-context'
import { IconFiles, IconChartBar } from '@tabler/icons-react'
import { AuthProvider } from './auth/AuthProvider'
import { TokenSync } from './auth/TokenSync'
import { DocumentUpload } from './pages/DocumentUpload'
import { UsageReport } from './pages/UsageReport'
import '@mantine/core/styles.css'
import '@mantine/notifications/styles.css'
import '@mantine/dropzone/styles.css'

const queryClient = new QueryClient()

function AppRoutes() {
  const auth = useAuth()
  if (auth.isLoading) return <Text p="md">Autenticando...</Text>
  if (!auth.isAuthenticated) { auth.signinRedirect(); return null }

  return (
    <>
      <TokenSync />
      <AppShell navbar={{ width: 220, breakpoint: 'sm' }} header={{ height: 56 }} padding="md">
        <AppShell.Header>
          <Group h="100%" px="md" justify="space-between">
            <Title order={4}>IntelliCare — Gestor</Title>
            <Button size="xs" variant="subtle" onClick={() => auth.signoutRedirect()}>Sair</Button>
          </Group>
        </AppShell.Header>
        <AppShell.Navbar p="sm">
          <NavLink component={Link} to="/"        label="Documentos" leftSection={<IconFiles size={16} />} />
          <NavLink component={Link} to="/reports" label="Relatórios" leftSection={<IconChartBar size={16} />} />
        </AppShell.Navbar>
        <AppShell.Main>
          <Routes>
            <Route path="/"        element={<DocumentUpload />} />
            <Route path="/reports" element={<UsageReport />} />
            <Route path="*"        element={<Navigate to="/" />} />
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
          <BrowserRouter basename="/gestor-ui">
            <AppRoutes />
          </BrowserRouter>
        </MantineProvider>
      </QueryClientProvider>
    </AuthProvider>
  )
}
```

---

## 9. Script de Build

**`tools/scripts/build_gestor_ui.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail
UI_DIR="$(git rev-parse --show-toplevel)/frontend/GestorUI"
OUT_DIR="$(git rev-parse --show-toplevel)/intellicare_core/static/gestor-ui"
cd "$UI_DIR"
npm ci
npm run build
echo "==> Artefato em: $OUT_DIR"
ls -lh "$OUT_DIR"
```

---

## 10. Keycloak — Client `gestor-ui`

```python
ensure_client(admin, realm="intellicare", client_id="gestor-ui", config={
    "publicClient": True,
    "redirectUris": ["http://localhost:5175/*", "http://localhost:8000/gestor-ui/*"],
    "webOrigins":   ["http://localhost:5175", "http://localhost:8000"],
    "standardFlowEnabled": True,
    "directAccessGrantsEnabled": False,
})
```

---

## 11. Portas de desenvolvimento

| UI | Porta dev | Base path |
|---|---|---|
| AdminUI | 5174 | `/admin-ui/` |
| GestorUI | 5175 | `/gestor-ui/` |
| ClinicoUI | 5173 | `/clinico-ui/` |

---

## 12. Checklist de Aceite Técnico

- [ ] `npm run build` sem erros TypeScript
- [ ] Login OIDC funciona com `client_id=gestor-ui`
- [ ] Apenas `TENANT_GESTOR` acessa (`403` para outros roles)
- [ ] Dropzone aceita PDF e DOCX, rejeita outros formatos
- [ ] Upload dispara ingestão e lista de documentos atualiza sem reload
- [ ] Deletar documento remove da lista imediatamente
- [ ] Relatório de uso exibe dados reais do backend
- [ ] Build em `intellicare_core/static/gestor-ui/`
- [ ] FastAPI serve `GET /gestor-ui/` com 200
