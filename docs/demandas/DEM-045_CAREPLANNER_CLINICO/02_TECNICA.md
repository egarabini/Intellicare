---
tipo: especificacao-tecnica
demanda: DEM-045
titulo: CarePlanner no ClinicoUI — lista de jornadas + detalhe read-only
---

# DEM-045 — Especificação Técnica

## Arquivos alterados/criados

| Arquivo | Tipo |
|---------|------|
| `frontend/ClinicoUI/src/hooks/useCareplanner.ts` | Novo |
| `frontend/ClinicoUI/src/pages/CareplannerPage.tsx` | Novo |
| `frontend/ClinicoUI/src/pages/CareplannerDetail.tsx` | Novo |
| `frontend/ClinicoUI/src/components/AppShell.tsx` | Modificar — NavLink + badge |
| `frontend/ClinicoUI/src/App.tsx` | Modificar — 2 novas rotas |
| `modules/careplanner/api/routes.py` | Modificar — adicionar CLINICO ao require_role dos GETs |
| `frontend/ClinicoUI/e2e/careplanner_clinico.spec.ts` | Novo (se e2e/ existir) |

---

## Bloco 1 — Backend: liberar CLINICO nos endpoints de leitura

Localizar em `modules/careplanner/api/routes.py` os endpoints:
- `GET /tasks` (listagem)
- `GET /tasks/{correlation_id}` (detalhe)
- `GET /consultations/video/{correlation_id}` (sessão de vídeo)

Verificar o `require_role` atual. Se for `require_role("GESTOR")`, alterar para:

```python
if not ctx.has_role("GESTOR") and not ctx.has_role("CLINICO"):
    raise api_error(403, "forbidden", "Role GESTOR ou CLINICO necessaria")
```

⚠️ Apenas os endpoints de **leitura** (GET). `POST /tasks`, `POST /journeys/trigger`,
`PATCH /tasks/.../close` permanecem exclusivos de GESTOR.

---

## Bloco 2 — `frontend/ClinicoUI/src/hooks/useCareplanner.ts`

```typescript
import { useQuery, useQueryClient } from '@tanstack/react-query'
import api from '../auth/api'  // ajustar caminho se diferente do GestorUI

export interface CareTask {
  correlation_id: string
  task_type: string
  status: string
  patient_ref: string
  clinico_ref: string | null
  created_at: string
  updated_at: string | null
  kestra_execution_id: string | null
}

export interface CareEvent {
  id: number
  event_type: string
  recorded_at: string
  payload: Record<string, unknown> | null
}

export interface CareTaskDetail {
  task: CareTask
  conversation: { phone_e164: string | null } | null
  events: CareEvent[]
}

export interface CareTaskList {
  items: CareTask[]
  total: number
  page: number
}

export function useCareplannerTasks(statusFilter?: string, page = 1) {
  return useQuery<CareTaskList>({
    queryKey: ['cp-tasks-clinico', statusFilter, page],
    queryFn: async () => {
      const params = new URLSearchParams({ page: String(page) })
      if (statusFilter) params.set('status', statusFilter)
      const res = await api.get(`/careplanner/tasks?${params}`)
      return res.data
    },
  })
}

export function useCareplannerTask(correlationId: string) {
  return useQuery<CareTaskDetail>({
    queryKey: ['cp-task-clinico', correlationId],
    queryFn: async () => {
      const res = await api.get(`/careplanner/tasks/${correlationId}`)
      return res.data
    },
    enabled: !!correlationId,
  })
}

export function useVideoSessionClinico(correlationId: string, enabled: boolean) {
  return useQuery({
    queryKey: ['cp-video-clinico', correlationId],
    queryFn: async () => {
      const res = await api.get(`/careplanner/consultations/video/${correlationId}`)
      return res.data as { clinico_url: string; patient_url: string; expired: boolean }
    },
    enabled,
  })
}
```

---

## Bloco 3 — `CareplannerPage.tsx`

```typescript
import { useState } from 'react'
import { Box, Title, Table, Badge, Group, Text, Switch,
         Loader, Center, Pagination } from '@mantine/core'
import { useNavigate } from 'react-router-dom'
import { useAuth } from 'react-oidc-context'
import { useCareplannerTasks } from '../hooks/useCareplanner'

const STATUS_COLOR: Record<string, string> = {
  CREATED: 'gray', DISPATCHED: 'blue', SENT: 'cyan',
  REPLIED: 'teal', CLOSED: 'green', FAILED: 'red', EXPIRED: 'orange',
}

export function CareplannerPage() {
  const [page, setPage] = useState(1)
  const [minhas, setMinhas] = useState(false)
  const navigate = useNavigate()
  const auth = useAuth()
  const myId = auth.user?.profile?.sub ?? ''

  const { data, isLoading } = useCareplannerTasks(undefined, page)

  const items = minhas
    ? (data?.items ?? []).filter(t => t.clinico_ref === myId)
    : (data?.items ?? [])

  if (isLoading) return <Center h="100%"><Loader /></Center>

  return (
    <Box>
      <Group mb="md" justify="space-between">
        <Title order={2}>Jornadas CarePlanner</Title>
        <Switch
          label="Minhas Jornadas"
          checked={minhas}
          onChange={e => { setMinhas(e.currentTarget.checked); setPage(1) }}
        />
      </Group>

      <Table striped highlightOnHover withTableBorder>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Paciente</Table.Th>
            <Table.Th>Tipo</Table.Th>
            <Table.Th>Status</Table.Th>
            <Table.Th>Atualizado em</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {items.map(task => (
            <Table.Tr
              key={task.correlation_id}
              style={{ cursor: 'pointer' }}
              onClick={() => navigate(`/careplanner/${task.correlation_id}`)}
            >
              <Table.Td>{task.patient_ref}</Table.Td>
              <Table.Td>{task.task_type}</Table.Td>
              <Table.Td>
                <Badge color={STATUS_COLOR[task.status] ?? 'gray'} variant="light">
                  {task.status}
                </Badge>
              </Table.Td>
              <Table.Td>
                <Text size="sm" c="dimmed">
                  {task.updated_at
                    ? new Date(task.updated_at).toLocaleString('pt-BR')
                    : '—'}
                </Text>
              </Table.Td>
            </Table.Tr>
          ))}
          {items.length === 0 && (
            <Table.Tr>
              <Table.Td colSpan={4}>
                <Text c="dimmed" ta="center" py="md">Nenhuma jornada encontrada.</Text>
              </Table.Td>
            </Table.Tr>
          )}
        </Table.Tbody>
      </Table>

      {data && data.total > 10 && (
        <Pagination
          mt="md"
          value={page}
          onChange={setPage}
          total={Math.ceil(data.total / 10)}
        />
      )}
    </Box>
  )
}
```

---

## Bloco 4 — `CareplannerDetail.tsx`

Idêntico à `CareplannerJourneyDetail.tsx` do GestorUI, mas:
- **Sem** botão "Encerrar Jornada"
- **Sem** botão "Criar Videoconsulta" (read-only)
- **Com** botão "Entrar na Videoconsulta" se sessão ativa existir
- Botão "Voltar" navega para `/careplanner`

```typescript
import { useCareplannerTask, useVideoSessionClinico } from '../hooks/useCareplanner'
// ... adaptar CareplannerJourneyDetail removendo mutações e botões de ação
```

---

## Bloco 5 — `AppShell.tsx`: NavLink Jornadas + badge REPLIED

```typescript
import { IconHeartbeat } from '@tabler/icons-react'
import { useCareplannerTasks } from '../hooks/useCareplanner'

// Dentro do ClinicoShell:
const { data: repliedData } = useCareplannerTasks('REPLIED')
const repliedCount = repliedData?.total ?? 0

// No array NAV_ITEMS (ou inline):
<NavLink
  label={
    <Group gap="xs" wrap="nowrap">
      <span>Jornadas</span>
      {repliedCount > 0 && (
        <Badge size="xs" color="red" circle>
          {repliedCount > 9 ? '9+' : repliedCount}
        </Badge>
      )}
    </Group>
  }
  leftSection={<IconHeartbeat size={18} />}
  active={location.pathname.startsWith('/careplanner')}
  onClick={() => navigate('/careplanner')}
  mb={4}
/>
```

---

## Bloco 6 — `App.tsx`: 2 novas rotas

```typescript
import { CareplannerPage } from './pages/CareplannerPage'
import { CareplannerDetail } from './pages/CareplannerDetail'

// Dentro de <Routes>:
<Route path="/careplanner" element={<CareplannerPage />} />
<Route path="/careplanner/:id" element={<CareplannerDetail />} />
```
