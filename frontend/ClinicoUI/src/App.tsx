import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { MantineProvider } from '@mantine/core'
import { Notifications } from '@mantine/notifications'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAuth } from 'react-oidc-context'
import { AuthProvider } from './auth/AuthProvider'
import { TokenSync } from './auth/TokenSync'
import { PatientList } from './pages/PatientList'
import { EncounterView } from './pages/EncounterView'
import { Dashboard } from './pages/Dashboard'
import { Agenda } from './pages/Agenda'
import { PatientProfile } from './pages/PatientProfile'
import { AIAssistant } from './pages/AIAssistant'
import { MyProfile } from './pages/MyProfile'
import { UnauthorizedPage } from './pages/UnauthorizedPage'
import { RoleGuard } from './auth/RoleGuard'
import { ClinicoShell } from './components/AppShell'

import '@mantine/core/styles.css'
import '@mantine/notifications/styles.css'

const queryClient = new QueryClient()

function AppRoutes() {
  return (
    <>
      <TokenSync />
      <RoleGuard>
        <ClinicoShell>
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/agenda" element={<Agenda />} />
            <Route path="/patients" element={<PatientList />} />
            <Route path="/patients/:id" element={<PatientProfile />} />
            <Route path="/patients/:patientId/encounter" element={<EncounterView />} />
            <Route path="/assistant" element={<AIAssistant />} />
            <Route path="/profile" element={<MyProfile />} />
            <Route path="/unauthorized" element={<UnauthorizedPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </ClinicoShell>
      </RoleGuard>
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
