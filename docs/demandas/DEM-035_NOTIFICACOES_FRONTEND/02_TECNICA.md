# DEM-035 — Notificações Frontend — Especificação Técnica

## 1. Dependências

Nenhuma biblioteca nova necessária. Todos os módulos já têm:
- `@mantine/core` ≥ 7 — `Indicator`, `Popover`, `ScrollArea`, `ActionIcon`, `Text`, `Stack`, `Badge`
- `@tabler/icons-react` — `IconBell`
- `react-oidc-context` — token de acesso disponível via `useAuth()`

---

## 2. Endpoints utilizados (DEM-026 — já existentes)

| Método | Path | Uso |
|--------|------|-----|
| `GET` | `/notifications/?limit=20` | Busca inicial da lista |
| `GET` | `/notifications/stream?token={access_token}` | SSE — novas notificações em tempo real |
| `PATCH` | `/notifications/{id}/read` | Marcar notificação como lida |

O endpoint SSE aceita o token via query param porque EventSource do browser não suporta headers customizados.

---

## 3. Arquivos a criar

### 3.1 Hook compartilhado — replicar em cada frontend

Cada frontend tem sua própria pasta `src/hooks/`. Criar `useNotifications.ts` em **cada um dos 4 frontends**:

```
frontend/AdminUI/src/hooks/useNotifications.ts
frontend/GestorUI/src/hooks/useNotifications.ts
frontend/ClinicoUI/src/hooks/useNotifications.ts
frontend/PacienteUI/src/hooks/useNotifications.ts
```

**Conteúdo de `useNotifications.ts`:**

```typescript
import { useEffect, useRef, useState, useCallback } from 'react'
import { useAuth } from 'react-oidc-context'
import api from '../api/client'  // instância axios com baseURL: '' já configurada

export interface AppNotification {
  id: string
  title: string
  message: string
  is_read: boolean
  created_at: string  // ISO 8601
  category?: string
}

export function useNotifications() {
  const auth = useAuth()
  const [notifications, setNotifications] = useState<AppNotification[]>([])
  const [available, setAvailable] = useState(true)  // false se backend retornar 404
  const retryRef = useRef(0)
  const esRef = useRef<EventSource | null>(null)

  const unreadCount = notifications.filter(n => !n.is_read).length

  // Busca inicial
  const fetchNotifications = useCallback(async () => {
    try {
      const { data } = await api.get<AppNotification[]>('/notifications/?limit=20')
      setNotifications(data)
    } catch (err: any) {
      if (err?.response?.status === 404) setAvailable(false)
    }
  }, [])

  // Marcar como lida
  const markRead = useCallback(async (id: string) => {
    try {
      await api.patch(`/notifications/${id}/read`)
      setNotifications(prev =>
        prev.map(n => (n.id === id ? { ...n, is_read: true } : n))
      )
    } catch {
      // silencioso
    }
  }, [])

  // SSE
  useEffect(() => {
    if (!available) return
    const token = auth.user?.access_token
    if (!token) return

    function connect() {
      const es = new EventSource(`/notifications/stream?token=${token}`)
      esRef.current = es

      es.onmessage = (event) => {
        try {
          const incoming: AppNotification = JSON.parse(event.data)
          setNotifications(prev => [incoming, ...prev].slice(0, 20))
          retryRef.current = 0
        } catch {
          // ignore parse errors
        }
      }

      es.onerror = () => {
        es.close()
        if (retryRef.current < 3) {
          retryRef.current++
          setTimeout(connect, 5_000)
        }
      }
    }

    fetchNotifications()
    connect()

    return () => {
      esRef.current?.close()
    }
  }, [auth.user?.access_token, available, fetchNotifications])

  return { notifications, unreadCount, markRead, available }
}
```

---

### 3.2 Componente `NotificationBell.tsx`

Criar em **cada um dos 4 frontends**:

```
frontend/AdminUI/src/components/NotificationBell.tsx
frontend/GestorUI/src/components/NotificationBell.tsx
frontend/ClinicoUI/src/components/NotificationBell.tsx
frontend/PacienteUI/src/components/NotificationBell.tsx
```

**Conteúdo de `NotificationBell.tsx`:**

```tsx
import { useState } from 'react'
import {
  ActionIcon, Badge, Group, Indicator, Popover,
  ScrollArea, Stack, Text,
} from '@mantine/core'
import { IconBell } from '@tabler/icons-react'
import { useNotifications, AppNotification } from '../hooks/useNotifications'

function timeAgo(iso: string): string {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
  if (diff < 60) return 'agora'
  if (diff < 3600) return `há ${Math.floor(diff / 60)} min`
  if (diff < 86400) return `há ${Math.floor(diff / 3600)} h`
  return `há ${Math.floor(diff / 86400)} d`
}

function NotificationItem({
  notification,
  onRead,
}: {
  notification: AppNotification
  onRead: (id: string) => void
}) {
  return (
    <Stack
      gap={2}
      p="xs"
      style={{
        cursor: notification.is_read ? 'default' : 'pointer',
        borderRadius: 6,
        background: notification.is_read ? 'transparent' : 'var(--mantine-color-blue-0)',
        borderBottom: '1px solid var(--mantine-color-gray-2)',
      }}
      onClick={() => !notification.is_read && onRead(notification.id)}
    >
      <Group justify="space-between" gap={4}>
        <Text size="sm" fw={notification.is_read ? 400 : 600} lineClamp={1}>
          {notification.title}
        </Text>
        <Text size="xs" c="dimmed">{timeAgo(notification.created_at)}</Text>
      </Group>
      <Text size="xs" c="dimmed" lineClamp={2}>
        {notification.message}
      </Text>
    </Stack>
  )
}

export function NotificationBell() {
  const { notifications, unreadCount, markRead, available } = useNotifications()
  const [opened, setOpened] = useState(false)

  if (!available) return null

  const label = unreadCount >= 10 ? '9+' : String(unreadCount)

  return (
    <Popover
      opened={opened}
      onClose={() => setOpened(false)}
      position="bottom-end"
      shadow="md"
      width={320}
    >
      <Popover.Target>
        <Indicator
          label={label}
          size={16}
          color="red"
          disabled={unreadCount === 0}
          processing={unreadCount > 0}
        >
          <ActionIcon
            variant="subtle"
            color="gray"
            onClick={() => setOpened(o => !o)}
            aria-label="Notificações"
          >
            <IconBell size={20} />
          </ActionIcon>
        </Indicator>
      </Popover.Target>

      <Popover.Dropdown p={0}>
        <Group px="sm" py="xs" justify="space-between"
          style={{ borderBottom: '1px solid var(--mantine-color-gray-2)' }}>
          <Text size="sm" fw={600}>Notificações</Text>
          {unreadCount > 0 && (
            <Badge size="xs" color="blue">{unreadCount} não lidas</Badge>
          )}
        </Group>
        <ScrollArea.Autosize mah={360}>
          {notifications.length === 0 ? (
            <Text size="sm" c="dimmed" ta="center" py="md">
              Nenhuma notificação
            </Text>
          ) : (
            notifications.map(n => (
              <NotificationItem key={n.id} notification={n} onRead={markRead} />
            ))
          )}
        </ScrollArea.Autosize>
      </Popover.Dropdown>
    </Popover>
  )
}
```

---

## 4. Arquivos a modificar

### 4.1 AdminUI — `src/App.tsx`

**Alteração no `AppShell.Header`:**

```tsx
// Antes:
import { IconDashboard, IconBuilding, IconShield, IconLogout, IconServer, IconPackages, IconCash, IconUsers } from '@tabler/icons-react'

// Depois (acrescentar import):
import { NotificationBell } from './components/NotificationBell'

// Antes:
<AppShell.Header>
  <Group h="100%" px="lg" justify="space-between">
    <Title order={4} c="blue">IntelliCare Admin</Title>
    <Text size="sm" c="dimmed">{auth.user?.profile?.email as string}</Text>
  </Group>
</AppShell.Header>

// Depois:
<AppShell.Header>
  <Group h="100%" px="lg" justify="space-between">
    <Title order={4} c="blue">IntelliCare Admin</Title>
    <Group gap="sm">
      <NotificationBell />
      <Text size="sm" c="dimmed">{auth.user?.profile?.email as string}</Text>
    </Group>
  </Group>
</AppShell.Header>
```

---

### 4.2 GestorUI — `src/App.tsx`

**Alteração no `AppShell.Header` (Group do lado direito já existe):**

```tsx
// Acrescentar import:
import { NotificationBell } from './components/NotificationBell'

// Antes:
<Group gap="sm">
  <Text size="sm" c="dimmed">
    {auth.user?.profile.email as string | undefined}
  </Text>
  <Button size="xs" variant="subtle" onClick={() => auth.signoutRedirect()}>
    Sair
  </Button>
</Group>

// Depois:
<Group gap="sm">
  <NotificationBell />
  <Text size="sm" c="dimmed">
    {auth.user?.profile.email as string | undefined}
  </Text>
  <Button size="xs" variant="subtle" onClick={() => auth.signoutRedirect()}>
    Sair
  </Button>
</Group>
```

---

### 4.3 ClinicoUI — `src/components/AppShell.tsx`

O `ClinicoShell` atual **não tem AppShell.Header**. Adicionar header com height 56.

```tsx
// Acrescentar imports:
import { Title } from '@mantine/core'  // Title já pode estar ou não — confirmar
import { NotificationBell } from './NotificationBell'

// Antes:
return (
  <AppShell navbar={{ width: 220, breakpoint: 'sm' }} padding="md">
    <AppShell.Navbar p="xs">
      {/* ... navbar existente ... */}
    </AppShell.Navbar>
    <AppShell.Main>{children}</AppShell.Main>
  </AppShell>
)

// Depois:
return (
  <AppShell
    navbar={{ width: 220, breakpoint: 'sm' }}
    header={{ height: 56 }}
    padding="md"
  >
    <AppShell.Header>
      <Group h="100%" px="md" justify="space-between">
        <Title order={4} c="teal">IntelliCare Clínico</Title>
        <Group gap="sm">
          <NotificationBell />
          <Text size="sm" c="dimmed">{name as string}</Text>
        </Group>
      </Group>
    </AppShell.Header>
    <AppShell.Navbar p="xs">
      {/* navbar existente sem alteração */}
    </AppShell.Navbar>
    <AppShell.Main>{children}</AppShell.Main>
  </AppShell>
)
```

**Atenção:** `name` já está disponível como `const name = auth.user?.profile?.name ?? 'Clínico'` no componente atual. Adicionar `Text` ao import de `@mantine/core` se não estiver.

---

### 4.4 PacienteUI — `src/App.tsx`

**Alteração no `AppShell.Header`:**

```tsx
// Acrescentar import:
import { NotificationBell } from './components/NotificationBell'

// Antes:
<AppShell.Header>
  <Group h="100%" px="lg" justify="space-between">
    <Title order={4} c="teal">IntelliCare — Paciente</Title>
    <Text size="sm" c="dimmed">{auth.user?.profile?.email as string}</Text>
  </Group>
</AppShell.Header>

// Depois:
<AppShell.Header>
  <Group h="100%" px="lg" justify="space-between">
    <Title order={4} c="teal">IntelliCare — Paciente</Title>
    <Group gap="sm">
      <NotificationBell />
      <Text size="sm" c="dimmed">{auth.user?.profile?.email as string}</Text>
    </Group>
  </Group>
</AppShell.Header>
```

---

## 5. Arquivo `api/client` nos frontends

O hook usa `api` (instância axios). Cada frontend já tem esse arquivo. Confirmar path:

| Frontend | Path do cliente axios |
|----------|----------------------|
| AdminUI | `src/api/client.ts` ou `src/auth/apiClient.ts` |
| GestorUI | `src/api/client.ts` |
| ClinicoUI | `src/api/client.ts` |
| PacienteUI | `src/api/client.ts` |

Se o path for diferente, ajustar o import no `useNotifications.ts`. O cliente deve ter `baseURL: ''` e interceptor de token — padrão existente em todos os módulos.

---

## 6. Statics a gerar

Após as modificações, buildar os 4 frontends:

```bash
# Para cada frontend:
cd frontend/AdminUI && npm run build
cd frontend/GestorUI && npm run build
cd frontend/ClinicoUI && npm run build
cd frontend/PacienteUI && npm run build
```

Os builds atualizam os statics em:
```
packages/intellicare-core/intellicare_core/static/{admin,gestor,clinico,paciente}-ui/
```

---

## 7. Checklist de entrega

- [ ] `frontend/AdminUI/src/hooks/useNotifications.ts` criado
- [ ] `frontend/AdminUI/src/components/NotificationBell.tsx` criado
- [ ] `frontend/AdminUI/src/App.tsx` atualizado com `NotificationBell` no header
- [ ] `frontend/GestorUI/src/hooks/useNotifications.ts` criado
- [ ] `frontend/GestorUI/src/components/NotificationBell.tsx` criado
- [ ] `frontend/GestorUI/src/App.tsx` atualizado com `NotificationBell` no header
- [ ] `frontend/ClinicoUI/src/hooks/useNotifications.ts` criado
- [ ] `frontend/ClinicoUI/src/components/NotificationBell.tsx` criado
- [ ] `frontend/ClinicoUI/src/components/AppShell.tsx` atualizado com `AppShell.Header` + `NotificationBell`
- [ ] `frontend/PacienteUI/src/hooks/useNotifications.ts` criado
- [ ] `frontend/PacienteUI/src/components/NotificationBell.tsx` criado
- [ ] `frontend/PacienteUI/src/App.tsx` atualizado com `NotificationBell` no header
- [ ] Build AdminUI: ok (sem erros TypeScript)
- [ ] Build GestorUI: ok
- [ ] Build ClinicoUI: ok
- [ ] Build PacienteUI: ok
- [ ] Verificar no browser: badge aparece e incrementa ao receber notificação via POST `/notifications/`
- [ ] Verificar: clicar em notificação não lida → badge decrementa
- [ ] Verificar: se 404 retornado → sino não aparece (sem console errors)
