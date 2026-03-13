import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import {
  AppShell,
  Button,
  Group,
  Loader,
  MantineProvider,
  Paper,
  Stack,
  Text,
  Title,
} from '@mantine/core'
import { Notifications, notifications } from '@mantine/notifications'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAuth } from 'react-oidc-context'

import { AuthProvider } from './auth/AuthProvider'
import { TokenSync } from './auth/TokenSync'
import { DashboardPage } from './pages/DashboardPage'
import { TenantDetail } from './pages/TenantDetail'
import { TenantForm } from './pages/TenantForm'
import { TenantList } from './pages/TenantList'

import '@mantine/core/styles.css'
import '@mantine/notifications/styles.css'

const queryClient = new QueryClient()

function ForbiddenPage() {
  const auth = useAuth()

  return (
    <Stack align="center" justify="center" h="100%">
      <Paper withBorder radius="lg" p="xl" maw={460}>
        <Stack gap="md">
          <Title order={2}>Acesso negado</Title>
          <Text c="dimmed">
            Esta interface e exclusiva para usuarios com role <code>PLATFORM_ADMIN</code>.
          </Text>
          <Group justify="flex-end">
            <Button variant="light" onClick={() => auth.signoutRedirect()}>
              Sair
            </Button>
          </Group>
        </Stack>
      </Paper>
    </Stack>
  )
}

function AppRoutes() {
  const auth = useAuth()
  const roles = (auth.user?.profile.realm_access as { roles?: string[] } | undefined)?.roles ?? []
  const isPlatformAdmin = roles.includes('PLATFORM_ADMIN')

  if (auth.isLoading) {
    return (
      <Group justify="center" mt="xl">
        <Loader />
      </Group>
    )
  }

  if (!auth.isAuthenticated) {
    void auth.signinRedirect()
    return null
  }

  if (!isPlatformAdmin) {
    notifications.show({
      title: 'Permissao insuficiente',
      message: 'Somente PLATFORM_ADMIN pode acessar o Admin UI.',
      color: 'red',
    })
    return <ForbiddenPage />
  }

  return (
    <>
      <TokenSync />
      <AppShell header={{ height: 64 }} padding="lg">
        <AppShell.Header>
          <Group h="100%" px="lg" justify="space-between">
            <Title order={3}>IntelliCare Admin</Title>
            <Group gap="sm">
              <Text size="sm" c="dimmed">
                {auth.user?.profile.email as string | undefined}
              </Text>
              <Button size="xs" variant="subtle" onClick={() => auth.signoutRedirect()}>
                Sair
              </Button>
            </Group>
          </Group>
        </AppShell.Header>
        <AppShell.Main>
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/tenants" element={<TenantList />} />
            <Route path="/tenants/new" element={<TenantForm />} />
            <Route path="/tenants/:slug" element={<TenantDetail />} />
            <Route path="*" element={<Navigate to="/" replace />} />
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
