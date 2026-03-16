import { BrowserRouter, Link, Navigate, Route, Routes, NavLink } from 'react-router-dom'
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
  NavLink as MantineNavLink,
  ActionIcon,
} from '@mantine/core'
import { Notifications, notifications } from '@mantine/notifications'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAuth } from 'react-oidc-context'
import {
  IconDashboard,
  IconUsers,
  IconCalendarEvent,
  IconFileInvoice,
  IconDatabase,
  IconStethoscope,
  IconSettings,
  IconLogout,
  IconBuilding,
  IconUserShield,
} from '@tabler/icons-react'

import { AuthProvider } from './auth/AuthProvider'
import { setToken } from './auth/tokenRef'
import { Dashboard } from './pages/Dashboard'
import { PatientList } from './pages/PatientList'
import { PatientProfile } from './pages/PatientProfile'
import { AppointmentCalendar } from './pages/AppointmentCalendar'
import { InvoiceList } from './pages/InvoiceList'
import { RagDocuments } from './pages/RagDocuments'
import { ProgramList } from './pages/ProgramList'
import { ClinicianList } from './pages/ClinicianList'
import { TenantSettings } from './pages/TenantSettings'
import { UnitsPage } from './pages/UnitsPage'
import { UnitDetailPage } from './pages/UnitDetailPage'
import { TenantUsersPage } from './pages/TenantUsersPage'
import { RelatoriosPage } from './pages/RelatoriosPage'
import { NotificationBell } from './components/NotificationBell'

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

  // Token síncrono — antes de qualquer query disparar
  setToken(auth.user?.access_token ?? null)

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

  function NavLinks() {
    return (
      <>
        <MantineNavLink component={NavLink} to="/dashboard" label="Dashboard" leftSection={<IconDashboard size="1rem"/>} />
        <MantineNavLink component={NavLink} to="/patients" label="Pacientes" leftSection={<IconUsers size="1rem"/>} />
        <MantineNavLink component={NavLink} to="/appointments" label="Agenda" leftSection={<IconCalendarEvent size="1rem"/>} />
        <MantineNavLink component={NavLink} to="/financeiro" label="Faturamento" leftSection={<IconFileInvoice size="1rem"/>} />
        <MantineNavLink component={NavLink} to="/programas" label="Programas de Saúde" leftSection={<IconStethoscope size="1rem"/>} />
        <MantineNavLink component={NavLink} to="/rag" label="Base de Conhecimento" leftSection={<IconDatabase size="1rem"/>} />
        <MantineNavLink component={NavLink} to="/equipe" label="Equipe Clínica" leftSection={<IconStethoscope size="1rem"/>} />
        <MantineNavLink component={NavLink} to="/units" label="Unidades" leftSection={<IconBuilding size="1rem"/>} />
        <MantineNavLink component={NavLink} to="/tenant-users" label="Usuários" leftSection={<IconUserShield size="1rem"/>} />
        <MantineNavLink component={NavLink} to="/relatorios" label="Relatórios" leftSection={<IconStethoscope size="1rem"/>} />
        <MantineNavLink component={NavLink} to="/settings" label="Configurações" leftSection={<IconSettings size="1rem"/>} />
      </>
    );
  }

  return (
    <>
      <AppShell
        navbar={{ width: 220, breakpoint: 'sm' }}
        header={{ height: 56 }}
        padding="md"
      >
        <AppShell.Header>
          <Group h="100%" px="md" justify="space-between">
            <Title order={4}>IntelliCare — Gestor</Title>
            <Group gap="sm">
              <NotificationBell />
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
          <NavLinks />
        </AppShell.Navbar>
        <AppShell.Main>
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/patients" element={<PatientList />} />
            <Route path="/patients/:id" element={<PatientProfile />} />
            <Route path="/appointments" element={<AppointmentCalendar />} />
            <Route path="/financeiro" element={<InvoiceList />} />
            <Route path="/rag" element={<RagDocuments />} />
            <Route path="/programas" element={<ProgramList />} />
            <Route path="/equipe" element={<ClinicianList />} />
            <Route path="/units" element={<UnitsPage />} />
            <Route path="/units/:id" element={<UnitDetailPage />} />
            <Route path="/tenant-users" element={<TenantUsersPage />} />
            <Route path="/relatorios" element={<RelatoriosPage />} />
            <Route path="/settings" element={<TenantSettings />} />
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
