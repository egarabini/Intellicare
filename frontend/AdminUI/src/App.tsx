import { BrowserRouter, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import {
  AppShell, Button, Group, Loader, MantineProvider,
  NavLink, Paper, Stack, Text, Title,
} from '@mantine/core'
import { Notifications, notifications } from '@mantine/notifications'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAuth } from 'react-oidc-context'
import {
  IconDashboard, IconBuilding, IconShield, IconLogout,
} from '@tabler/icons-react'

import { AuthProvider } from './auth/AuthProvider'
import { setToken } from './auth/tokenRef'
import { DashboardPage } from './pages/DashboardPage'
import { TenantDetail } from './pages/TenantDetail'
import { TenantForm } from './pages/TenantForm'
import { TenantList } from './pages/TenantList'
import { TenantUsers } from './pages/TenantUsers'
import { AuditLog } from './pages/AuditLog'

import '@mantine/core/styles.css'
import '@mantine/notifications/styles.css'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 30_000 } },
})

const NAV_ITEMS = [
  { path: '/',        label: 'Dashboard', icon: IconDashboard },
  { path: '/tenants', label: 'Tenants',   icon: IconBuilding  },
  { path: '/audit',   label: 'Auditoria', icon: IconShield    },
]

function Sidebar() {
  const location = useLocation()
  const navigate = useNavigate()
  const auth = useAuth()

  return (
    <AppShell.Navbar p="sm" style={{ display: 'flex', flexDirection: 'column' }}>
      <Stack gap={4} style={{ flex: 1 }}>
        {NAV_ITEMS.map(item => (
          <NavLink
            key={item.path}
            label={item.label}
            leftSection={<item.icon size={16} />}
            active={
              item.path === '/'
                ? location.pathname === '/'
                : location.pathname.startsWith(item.path)
            }
            onClick={() => navigate(item.path)}
          />
        ))}
      </Stack>
      <NavLink
        label="Sair"
        leftSection={<IconLogout size={16} />}
        color="red"
        onClick={() => auth.signoutRedirect()}
        mt="auto"
      />
    </AppShell.Navbar>
  )
}

function ForbiddenPage() {
  const auth = useAuth()
  return (
    <Stack align="center" justify="center" h="100vh">
      <Paper withBorder radius="lg" p="xl" maw={460}>
        <Stack gap="md">
          <Title order={2}>Acesso negado</Title>
          <Text c="dimmed">
            Esta interface é exclusiva para <code>PLATFORM_ADMIN</code>.
          </Text>
          <Button variant="light" onClick={() => auth.signoutRedirect()}>Sair</Button>
        </Stack>
      </Paper>
    </Stack>
  )
}

function AppRoutes() {
  const auth = useAuth()

  // ── Token síncrono: atualizado a cada render, antes de qualquer query ──
  setToken(auth.user?.access_token ?? null)

  const roles =
    (auth.user?.profile?.realm_access as { roles?: string[] } | undefined)
      ?.roles ?? []
  const isPlatformAdmin = roles.includes('PLATFORM_ADMIN')

  if (auth.isLoading) {
    return <Group justify="center" mt="xl"><Loader /></Group>
  }

  if (!auth.isAuthenticated) {
    void auth.signinRedirect()
    return null
  }

  if (!isPlatformAdmin) {
    notifications.show({
      title: 'Permissão insuficiente',
      message: 'Somente PLATFORM_ADMIN pode acessar o Admin UI.',
      color: 'red',
    })
    return <ForbiddenPage />
  }

  return (
    <AppShell
      header={{ height: 56 }}
      navbar={{ width: 200, breakpoint: 'sm' }}
      padding="lg"
    >
      <AppShell.Header>
        <Group h="100%" px="lg" justify="space-between">
          <Title order={4} c="blue">IntelliCare Admin</Title>
          <Text size="sm" c="dimmed">{auth.user?.profile?.email as string}</Text>
        </Group>
      </AppShell.Header>

      <Sidebar />

      <AppShell.Main>
        <Routes>
          <Route path="/"                    element={<DashboardPage />} />
          <Route path="/tenants"             element={<TenantList />} />
          <Route path="/tenants/new"         element={<TenantForm />} />
          <Route path="/tenants/:slug"       element={<TenantDetail />} />
          <Route path="/tenants/:slug/users" element={<TenantUsers />} />
          <Route path="/audit"               element={<AuditLog />} />
          <Route path="*"                    element={<Navigate to="/" replace />} />
        </Routes>
      </AppShell.Main>
    </AppShell>
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
