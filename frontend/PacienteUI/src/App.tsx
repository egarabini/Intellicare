import { BrowserRouter, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import {
  AppShell, Button, Group, Loader, MantineProvider,
  NavLink, Paper, Stack, Text, Title,
} from '@mantine/core'
import { Notifications } from '@mantine/notifications'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAuth } from 'react-oidc-context'
import {
  IconDashboard, IconCalendar, IconHeartbeat,
  IconMessageCircle, IconClipboardHeart,
  IconUser, IconPhone, IconLogout,
} from '@tabler/icons-react'

import { AuthProvider } from './auth/AuthProvider'
import { setToken } from './auth/tokenRef'
import { PainelPage } from './pages/PainelPage'
import { AgendaPage } from './pages/AgendaPage'
import { HistoricoPage } from './pages/HistoricoPage'
import { JornadasPage } from './pages/JornadasPage'
import { ProgramasPage } from './pages/ProgramasPage'
import { CadastroPage } from './pages/CadastroPage'
import { ContatoPage } from './pages/ContatoPage'
import { NotificationBell } from './components/NotificationBell'

import '@mantine/core/styles.css'
import '@mantine/notifications/styles.css'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 30_000 } },
})

const NAV_ITEMS = [
  { path: '/',          label: 'Painel',      icon: IconDashboard },
  { path: '/agenda',    label: 'Agenda',      icon: IconCalendar },
  { path: '/jornadas',  label: 'Minhas Jornadas', icon: IconMessageCircle },
  { path: '/historico', label: 'Histórico Clínico', icon: IconClipboardHeart },
  { path: '/programas', label: 'Programas',   icon: IconHeartbeat },
  { path: '/cadastro',  label: 'Meus Dados',  icon: IconUser },
  { path: '/contato',   label: 'Contato',     icon: IconPhone },
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
            Esta interface é exclusiva para pacientes com role <code>PACIENTE</code>.
          </Text>
          <Button variant="light" onClick={() => auth.signoutRedirect()}>Sair</Button>
        </Stack>
      </Paper>
    </Stack>
  )
}

function AppRoutes() {
  const auth = useAuth()
  setToken(auth.user?.access_token ?? null)

  const roles =
    (auth.user?.profile?.realm_access as { roles?: string[] } | undefined)
      ?.roles ?? []
  const isPaciente = roles.includes('PACIENTE')

  if (auth.isLoading) {
    return <Group justify="center" mt="xl"><Loader /></Group>
  }

  if (!auth.isAuthenticated) {
    void auth.signinRedirect()
    return null
  }

  if (!isPaciente) {
    return <ForbiddenPage />
  }

  return (
    <AppShell
      header={{ height: 56 }}
      navbar={{ width: 220, breakpoint: 'sm' }}
      padding="lg"
    >
      <AppShell.Header>
        <Group h="100%" px="lg" justify="space-between">
          <Title order={4} c="teal">IntelliCare — Paciente</Title>
          <Group gap="sm">
            <NotificationBell />
            <Text size="sm" c="dimmed">{auth.user?.profile?.email as string}</Text>
            <Button
              variant="light"
              color="red"
              leftSection={<IconLogout size={16} />}
              onClick={() => auth.signoutRedirect()}
            >
              Sair
            </Button>
          </Group>
        </Group>
      </AppShell.Header>

      <Sidebar />

      <AppShell.Main>
        <Routes>
          <Route path="/"          element={<PainelPage />} />
          <Route path="/agenda"    element={<AgendaPage />} />
          <Route path="/jornadas"  element={<JornadasPage />} />
          <Route path="/historico" element={<HistoricoPage />} />
          <Route path="/programas" element={<ProgramasPage />} />
          <Route path="/cadastro"  element={<CadastroPage />} />
          <Route path="/contato"   element={<ContatoPage />} />
          <Route path="*"          element={<Navigate to="/" replace />} />
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
          <BrowserRouter basename="/paciente-ui">
            <AppRoutes />
          </BrowserRouter>
        </MantineProvider>
      </QueryClientProvider>
    </AuthProvider>
  )
}
