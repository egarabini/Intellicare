import { useEffect } from 'react'
import { useAuth } from 'react-oidc-context'
import { MantineProvider, Center, Loader, Text, Stack } from '@mantine/core'
import { AuthProvider } from './auth/AuthProvider'
import { Unauthorized } from './pages/Unauthorized'
import '@mantine/core/styles.css'

// Mapeamento role → URL de destino
const ROLE_ROUTES: Record<string, string> = {
  PLATFORM_ADMIN: '/admin-ui/',
  TENANT_GESTOR:  '/gestor-ui/',
  CLINICO:        '/clinico-ui/',
}

function extractRoles(user: { profile: Record<string, unknown> } | null | undefined): string[] {
  if (!user) return []
  // Keycloak emite roles em realm_access.roles
  const realmAccess = user.profile['realm_access'] as { roles?: string[] } | undefined
  return realmAccess?.roles ?? []
}

function Router() {
  const auth = useAuth()

  useEffect(() => {
    // Não autenticado → inicia login imediatamente
    if (!auth.isLoading && !auth.isAuthenticated) {
      auth.signinRedirect()
    }
  }, [auth.isLoading, auth.isAuthenticated])

  // Carregando / aguardando redirecionamento para Keycloak
  if (auth.isLoading || !auth.isAuthenticated) {
    return (
      <Center h="100vh">
        <Stack align="center" gap="sm">
          <Loader size="lg" />
          <Text c="dimmed">Autenticando...</Text>
        </Stack>
      </Center>
    )
  }

  // Autenticado — determinar destino pelo role
  const roles = extractRoles(auth.user)
  const destination = Object.entries(ROLE_ROUTES).find(
    ([role]) => roles.includes(role)
  )?.[1]

  if (destination) {
    // Redireciona para a UI correta
    window.location.replace(destination)
    return (
      <Center h="100vh">
        <Stack align="center" gap="sm">
          <Loader size="lg" />
          <Text c="dimmed">Redirecionando...</Text>
        </Stack>
      </Center>
    )
  }

  // Nenhum role reconhecido
  return <Unauthorized onLogout={() => auth.signoutRedirect()} email={auth.user?.profile.email as string} />
}

export default function App() {
  return (
    <AuthProvider>
      <MantineProvider>
        <Router />
      </MantineProvider>
    </AuthProvider>
  )
}
