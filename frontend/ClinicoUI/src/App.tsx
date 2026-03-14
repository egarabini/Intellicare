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
        <Route path="/" element={<PatientList />} />
        <Route path="/encounter/:patientId" element={<EncounterView />} />
        <Route path="*" element={<Navigate to="/" />} />
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
