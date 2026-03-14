import { BrowserRouter, Link, Navigate, Route, Routes } from 'react-router-dom'
import {
  AppShell,
  Button,
  Group,
  Loader,
  MantineProvider,
  NavLink,
  Paper,
  Stack,
  Text,
  Title,
} from '@mantine/core'
import { Notifications, notifications } from '@mantine/notifications'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAuth } from 'react-oidc-context'
import {
  IconBuildingHospital,
  IconChartBar,
  IconDashboard,
  IconFiles,
  IconUsers,
} from '@tabler/icons-react'

import { AuthProvider } from './auth/AuthProvider'
import { TokenSync } from './auth/TokenSync'
import { Dashboard } from './pages/Dashboard'
import { DocumentUpload } from './pages/DocumentUpload'
import { ProfilePage } from './pages/ProfilePage'
import { UsageReport } from './pages/UsageReport'
import { UserList } from './pages/UserList'

import '@mantine/core/styles.css'
import '@mantine/notifications/styles.css'
import '@mantine/dropzone/styles.css'

const queryClient = new QueryClient()

function ForbiddenPage() {
  const auth = useAuth()

  return (
    <Stack align="center" justify="center" h="100%">
      <Paper withBorder radius="lg" p="xl" maw={460}>
        <Stack gap="md">
          <Title order={2}>Acesso negado</Title>
          <Text c="dimmed">
            Esta interface e exclusiva para usuarios com role <code>TENANT_GESTOR</code>.
          </Text>
          <Group justify="flex-end">
            <Button variant="light" onClick={() => auth.signoutRedirect()}>Sair</Button>
          </Group>
        </Stack>
      </Paper>
    </Stack>
  )
}

function AppRoutes() {
  const auth = useAuth()
  const roles = (auth.user?.profile.realm_access as { roles?: string[] } | undefined)?.roles ?? []
  const isGestor = roles.includes('TENANT_GESTOR')

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

  if (!isGestor) {
    notifications.show({
      title: 'Permissao insuficiente',
      message: 'Somente TENANT_GESTOR pode acessar o Gestor UI.',
      color: 'red',
    })
    return <ForbiddenPage />
  }

  return (
    <>
      <TokenSync />
      <AppShell
        navbar={{ width: 220, breakpoint: 'sm' }}
        header={{ height: 56 }}
        padding="md"
      >
        <AppShell.Header>
          <Group h="100%" px="md" justify="space-between">
            <Title order={4}>IntelliCare — Gestor</Title>
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
        <AppShell.Navbar p="sm">
          <NavLink component={Link} to="/" label="Dashboard" leftSection={<IconDashboard size={16} />} />
          <NavLink component={Link} to="/users" label="Usuarios" leftSection={<IconUsers size={16} />} />
          <NavLink component={Link} to="/documents" label="Documentos" leftSection={<IconFiles size={16} />} />
          <NavLink component={Link} to="/reports" label="Relatorios" leftSection={<IconChartBar size={16} />} />
          <NavLink component={Link} to="/profile" label="Perfil" leftSection={<IconBuildingHospital size={16} />} />
        </AppShell.Navbar>
        <AppShell.Main>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/users" element={<UserList />} />
            <Route path="/documents" element={<DocumentUpload />} />
            <Route path="/reports" element={<UsageReport />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="*" element={<Navigate to="/" />} />
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
