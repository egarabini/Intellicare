# DEM-015 — Frontend Clínico: Especificação Técnica

## 1. Estrutura de Arquivos

```
frontend/ClinicoUI/
├── package.json
├── tsconfig.json
├── vite.config.ts
├── index.html
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── auth/
│   │   └── AuthProvider.tsx
│   ├── api/
│   │   └── client.ts
│   ├── hooks/
│   │   ├── usePatients.ts
│   │   └── useEncounters.ts
│   ├── components/
│   │   └── SLMAssistant.tsx
│   └── pages/
│       ├── PatientList.tsx
│       └── EncounterView.tsx
tools/scripts/
└── build_clinico_ui.sh
```

---

## 2. package.json

```json
{
  "name": "clinico-ui",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev":   "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "@mantine/core":        "^7.10.0",
    "@mantine/hooks":       "^7.10.0",
    "@mantine/notifications": "^7.10.0",
    "@tanstack/react-query": "^5.40.0",
    "axios":                 "^1.7.0",
    "oidc-client-ts":        "^3.0.1",
    "react":                 "^18.3.0",
    "react-dom":             "^18.3.0",
    "react-oidc-context":    "^3.1.0",
    "react-router-dom":      "^6.23.0"
  },
  "devDependencies": {
    "@types/react":          "^18.3.0",
    "@types/react-dom":      "^18.3.0",
    "@vitejs/plugin-react":  "^4.3.0",
    "typescript":            "^5.4.0",
    "vite":                  "^5.3.0"
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
  base: '/clinico-ui/',
  build: {
    outDir: '../../intellicare_core/static/clinico-ui',
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '/cuidado':  'http://localhost:8000',
      '/gestor':   'http://localhost:8000',
      '/slm':      'http://localhost:8000',
      '/vector':   'http://localhost:8000',
      '/auth':     'http://localhost:8000',
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
  authority:              import.meta.env.VITE_KEYCLOAK_URL + '/realms/intellicare',
  client_id:              'clinico-ui',
  redirect_uri:           window.location.origin + '/clinico-ui/callback',
  post_logout_redirect_uri: window.location.origin + '/clinico-ui/',
  scope:                  'openid profile email',
  // Tokens ficam somente em memória — sem localStorage
  userStore: undefined,
  onSigninCallback: () => {
    window.history.replaceState({}, document.title, window.location.pathname)
  },
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  return <OidcAuthProvider {...oidcConfig}>{children}</OidcAuthProvider>
}
```

> **Segurança**: `userStore: undefined` força armazenamento em memória (padrão do `oidc-client-ts`
> quando nenhum store é injetado). Tokens não sobrevivem ao reload — comportamento intencional
> para ambientes clínicos.

---

## 5. Axios Client com Bearer Token

**`src/api/client.ts`**

```typescript
import axios, { InternalAxiosRequestConfig } from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '',
  timeout: 30_000,
})

// Token é injetado a partir do contexto OIDC via sessionStorage temporário
// O AuthProvider escreve o access_token em sessionStorage['oidc.access_token']
// apenas durante a sessão de aba (não persiste entre abas ou reloads).
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = sessionStorage.getItem('oidc.access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export default apiClient
```

**`src/auth/TokenSync.tsx`** — sincroniza token OIDC → sessionStorage:

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

## 6. Hooks TanStack Query

**`src/hooks/usePatients.ts`**

```typescript
import { useQuery } from '@tanstack/react-query'
import apiClient from '../api/client'

export interface Patient {
  id: number
  full_name: string
  birth_date: string
  cpf: string
  phone: string | null
}

export function usePatients(search: string) {
  return useQuery<Patient[]>({
    queryKey: ['patients', search],
    queryFn: async () => {
      const { data } = await apiClient.get('/cuidado/patients', {
        params: { q: search, limit: 20 },
      })
      return data
    },
    enabled: search.length >= 3,
    staleTime: 30_000,
  })
}
```

**`src/hooks/useEncounters.ts`**

```typescript
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import apiClient from '../api/client'

export interface Encounter {
  id: number
  patient_id: number
  status: 'open' | 'closed'
  started_at: string
  ended_at: string | null
}

export interface Note {
  id: number
  encounter_id: number
  content: string
  created_at: string
}

export function useEncounterHistory(patientId: number) {
  return useQuery<Encounter[]>({
    queryKey: ['encounters', patientId],
    queryFn: async () => {
      const { data } = await apiClient.get(`/cuidado/patients/${patientId}/encounters`)
      return data
    },
  })
}

export function useOpenEncounter() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (patientId: number) =>
      apiClient.post('/cuidado/encounters', { patient_id: patientId }).then(r => r.data),
    onSuccess: (_, patientId) => qc.invalidateQueries({ queryKey: ['encounters', patientId] }),
  })
}

export function useAddNote(encounterId: number) {
  return useMutation({
    mutationFn: (content: string) =>
      apiClient
        .post(`/cuidado/encounters/${encounterId}/notes`, { content })
        .then(r => r.data),
  })
}

export function useCloseEncounter() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ encounterId, patientId }: { encounterId: number; patientId: number }) =>
      apiClient.post(`/cuidado/encounters/${encounterId}/close`).then(r => r.data),
    onSuccess: (_, { patientId }) =>
      qc.invalidateQueries({ queryKey: ['encounters', patientId] }),
  })
}
```

---

## 7. Componente SLMAssistant (SSE Streaming)

**`src/components/SLMAssistant.tsx`**

```tsx
import { useState, useRef } from 'react'
import { Button, Paper, ScrollArea, Text, Textarea, Stack, Badge } from '@mantine/core'

interface Props {
  encounterContext?: string   // texto da nota SOAP atual para enriquecer o prompt
}

export function SLMAssistant({ encounterContext }: Props) {
  const [question, setQuestion]   = useState('')
  const [answer, setAnswer]       = useState('')
  const [streaming, setStreaming] = useState(false)
  const [error, setError]         = useState<string | null>(null)
  const abortRef                  = useRef<AbortController | null>(null)

  const handleAsk = async () => {
    if (!question.trim()) return
    setAnswer('')
    setError(null)
    setStreaming(true)

    abortRef.current = new AbortController()
    const token = sessionStorage.getItem('oidc.access_token') ?? ''

    try {
      const res = await fetch('/slm/ask', {
        method: 'POST',
        headers: {
          'Content-Type':  'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          question,
          context:  encounterContext ?? '',
          stream:   true,
        }),
        signal: abortRef.current.signal,
      })

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`)
      }

      const reader = res.body!.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const chunk = decoder.decode(value, { stream: true })
        // SSE format: "data: <token>\n\n"
        chunk.split('\n').forEach(line => {
          if (line.startsWith('data: ')) {
            const token = line.slice(6)
            if (token !== '[DONE]') setAnswer(prev => prev + token)
          }
        })
      }
    } catch (err: unknown) {
      if ((err as Error).name !== 'AbortError') {
        setError((err as Error).message)
      }
    } finally {
      setStreaming(false)
    }
  }

  const handleStop = () => {
    abortRef.current?.abort()
    setStreaming(false)
  }

  return (
    <Stack gap="sm">
      <Textarea
        label="Pergunta ao Assistente IA"
        placeholder="Ex: Sugestão de CID para hipertensão com nefropatia..."
        minRows={3}
        value={question}
        onChange={e => setQuestion(e.currentTarget.value)}
        disabled={streaming}
      />

      <Button
        onClick={streaming ? handleStop : handleAsk}
        color={streaming ? 'red' : 'blue'}
        disabled={!streaming && !question.trim()}
      >
        {streaming ? 'Parar' : 'Perguntar'}
      </Button>

      {error && <Text c="red" size="sm">{error}</Text>}

      {(answer || streaming) && (
        <Paper withBorder p="sm" radius="md">
          <Stack gap={4}>
            <Badge color={streaming ? 'yellow' : 'green'} variant="light" size="sm">
              {streaming ? 'Gerando...' : 'Concluído'}
            </Badge>
            <ScrollArea h={300}>
              <Text size="sm" style={{ whiteSpace: 'pre-wrap' }}>{answer}</Text>
            </ScrollArea>
          </Stack>
        </Paper>
      )}
    </Stack>
  )
}
```

---

## 8. Página EncounterView

**`src/pages/EncounterView.tsx`**

```tsx
import { useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Grid, Stack, Title, Button, Textarea, Badge,
  Group, Text, Divider, Alert,
} from '@mantine/core'
import { IconAlertCircle } from '@tabler/icons-react'
import { useEncounterHistory, useOpenEncounter, useAddNote, useCloseEncounter } from '../hooks/useEncounters'
import { SLMAssistant } from '../components/SLMAssistant'

export function EncounterView() {
  const { patientId } = useParams<{ patientId: string }>()
  const pid = Number(patientId)

  const { data: encounters, isLoading } = useEncounterHistory(pid)
  const openEncounter   = useOpenEncounter()
  const addNote         = useAddNote(encounters?.find(e => e.status === 'open')?.id ?? 0)
  const closeEncounter  = useCloseEncounter()

  const [noteContent, setNoteContent] = useState('')

  const activeEncounter = encounters?.find(e => e.status === 'open')

  const handleAddNote = async () => {
    if (!activeEncounter || !noteContent.trim()) return
    await addNote.mutateAsync(noteContent)
    setNoteContent('')
  }

  const handleClose = async () => {
    if (!activeEncounter) return
    await closeEncounter.mutateAsync({ encounterId: activeEncounter.id, patientId: pid })
  }

  if (isLoading) return <Text>Carregando...</Text>

  return (
    <Grid gutter="md">
      {/* ── Painel Esquerdo: Encontro / Nota SOAP ── */}
      <Grid.Col span={8}>
        <Stack>
          <Group justify="space-between">
            <Title order={3}>Encontro Atual</Title>
            {activeEncounter ? (
              <Badge color="green">Aberto</Badge>
            ) : (
              <Badge color="gray">Nenhum Aberto</Badge>
            )}
          </Group>

          {!activeEncounter && (
            <Button
              onClick={() => openEncounter.mutate(pid)}
              loading={openEncounter.isPending}
            >
              Abrir Novo Encontro
            </Button>
          )}

          {activeEncounter && (
            <>
              <Textarea
                label="Nota SOAP"
                placeholder="S: (Subjetivo) O: (Objetivo) A: (Avaliação) P: (Plano)"
                minRows={8}
                value={noteContent}
                onChange={e => setNoteContent(e.currentTarget.value)}
              />
              <Group>
                <Button
                  onClick={handleAddNote}
                  loading={addNote.isPending}
                  disabled={!noteContent.trim()}
                >
                  Salvar Nota
                </Button>
                <Button
                  color="red"
                  variant="outline"
                  onClick={handleClose}
                  loading={closeEncounter.isPending}
                >
                  Fechar Encontro
                </Button>
              </Group>
            </>
          )}

          <Divider label="Histórico" labelPosition="left" />
          {encounters?.filter(e => e.status === 'closed').map(enc => (
            <Alert key={enc.id} icon={<IconAlertCircle />} color="gray" variant="light">
              Encontro #{enc.id} — Fechado em {new Date(enc.ended_at!).toLocaleDateString('pt-BR')}
            </Alert>
          ))}
        </Stack>
      </Grid.Col>

      {/* ── Painel Direito: Assistente SLM ── */}
      <Grid.Col span={4}>
        <Stack>
          <Title order={4}>Assistente IA</Title>
          <SLMAssistant encounterContext={noteContent} />
        </Stack>
      </Grid.Col>
    </Grid>
  )
}
```

---

## 9. Página PatientList

**`src/pages/PatientList.tsx`**

```tsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { TextInput, Table, Text, Stack, Title, Loader, Center } from '@mantine/core'
import { useDebouncedValue } from '@mantine/hooks'
import { usePatients } from '../hooks/usePatients'

export function PatientList() {
  const [search, setSearch] = useState('')
  const [debounced] = useDebouncedValue(search, 400)
  const { data, isLoading, isFetching } = usePatients(debounced)
  const navigate = useNavigate()

  return (
    <Stack>
      <Title order={2}>Pacientes</Title>
      <TextInput
        placeholder="Buscar por nome (mín. 3 caracteres)..."
        value={search}
        onChange={e => setSearch(e.currentTarget.value)}
        rightSection={isFetching ? <Loader size="xs" /> : null}
      />

      {isLoading && (
        <Center><Loader /></Center>
      )}

      {data && data.length === 0 && (
        <Text c="dimmed">Nenhum paciente encontrado.</Text>
      )}

      {data && data.length > 0 && (
        <Table highlightOnHover striped withTableBorder>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Nome</Table.Th>
              <Table.Th>Data Nasc.</Table.Th>
              <Table.Th>CPF</Table.Th>
              <Table.Th>Telefone</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {data.map(p => (
              <Table.Tr
                key={p.id}
                onClick={() => navigate(`/encounter/${p.id}`)}
                style={{ cursor: 'pointer' }}
              >
                <Table.Td>{p.full_name}</Table.Td>
                <Table.Td>{new Date(p.birth_date).toLocaleDateString('pt-BR')}</Table.Td>
                <Table.Td>{p.cpf}</Table.Td>
                <Table.Td>{p.phone ?? '—'}</Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      )}
    </Stack>
  )
}
```

---

## 10. App.tsx e main.tsx

**`src/App.tsx`**

```tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { MantineProvider } from '@mantine/core'
import { Notifications } from '@mantine/notifications'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAuth } from 'react-oidc-context'
import { AuthProvider } from './auth/AuthProvider'
import { TokenSync } from './auth/TokenSync'
import { PatientList } from './pages/PatientList'
import { EncounterView } from './pages/EncounterView'
import '@mantine/core/styles.css'
import '@mantine/notifications/styles.css'

const queryClient = new QueryClient()

function AppRoutes() {
  const auth = useAuth()
  if (auth.isLoading) return <div>Carregando...</div>
  if (!auth.isAuthenticated) {
    auth.signinRedirect()
    return null
  }
  return (
    <>
      <TokenSync />
      <Routes>
        <Route path="/"               element={<PatientList />} />
        <Route path="/encounter/:patientId" element={<EncounterView />} />
        <Route path="*"               element={<Navigate to="/" />} />
      </Routes>
    </>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <QueryClientProvider client={queryClient}>
        <MantineProvider>
          <Notifications />
          <BrowserRouter basename="/clinico-ui">
            <AppRoutes />
          </BrowserRouter>
        </MantineProvider>
      </QueryClientProvider>
    </AuthProvider>
  )
}
```

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

---

## 11. Script de Build

**`tools/scripts/build_clinico_ui.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail

UI_DIR="$(git rev-parse --show-toplevel)/frontend/ClinicoUI"
OUT_DIR="$(git rev-parse --show-toplevel)/intellicare_core/static/clinico-ui"

echo "==> Instalando dependências..."
cd "$UI_DIR"
npm ci

echo "==> Gerando build de produção..."
npm run build

echo "==> Artefato em: $OUT_DIR"
ls -lh "$OUT_DIR"
```

---

## 12. Mount no FastAPI

Em `intellicare_core/main.py`, adicionar:

```python
from fastapi.staticfiles import StaticFiles
import pathlib

STATIC_ROOT = pathlib.Path(__file__).parent / "static"

app.mount(
    "/clinico-ui",
    StaticFiles(directory=str(STATIC_ROOT / "clinico-ui"), html=True),
    name="clinico-ui",
)
```

---

## 13. Keycloak — Client `clinico-ui`

Adicionar em `tools/scripts/setup_keycloak.py`:

```python
ensure_client(admin, realm="intellicare", client_id="clinico-ui", config={
    "publicClient": True,
    "redirectUris": ["http://localhost:5173/*", "http://localhost:8000/clinico-ui/*"],
    "webOrigins": ["http://localhost:5173", "http://localhost:8000"],
    "standardFlowEnabled": True,
    "directAccessGrantsEnabled": False,
})
```

---

## 14. Variáveis de Ambiente (`.env.local`)

```
VITE_KEYCLOAK_URL=http://localhost:8080
VITE_API_BASE_URL=http://localhost:8000
```

---

## 15. Checklist de Aceite Técnico

- [ ] `npm run build` sem erros TypeScript
- [ ] Bundle total < 500 KB gzip (`vite build --report`)
- [ ] `react-oidc-context` redireciona para Keycloak ao acessar app sem sessão
- [ ] `sessionStorage` contém token após login; `localStorage` vazio
- [ ] Busca de pacientes dispara após 3 caracteres (debounce 400 ms)
- [ ] SSE streaming exibe tokens progressivamente — sem buffer completo
- [ ] Botão "Parar" cancela stream via `AbortController`
- [ ] Fechamento de encontro desativa textarea e botões
- [ ] Build copiado para `intellicare_core/static/clinico-ui/`
- [ ] FastAPI serve `GET /clinico-ui/` com status 200
