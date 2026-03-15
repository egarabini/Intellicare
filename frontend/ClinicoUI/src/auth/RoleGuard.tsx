import { useAuth } from 'react-oidc-context';
import { Navigate } from 'react-router-dom';

export function RoleGuard({ children }: { children: React.ReactNode }) {
  const auth = useAuth()
  if (auth.isLoading) return <div>Verificando permissões...</div>
  if (!auth.isAuthenticated) {
    auth.signinRedirect()
    return null
  }
  const roles: string[] = (auth.user?.profile?.realm_access as any)?.roles ?? []
  if (!roles.includes('CLINICO') && !roles.includes('PLATFORM_ADMIN')) {
    return <Navigate to="/unauthorized" replace />
  }
  return <>{children}</>
}
