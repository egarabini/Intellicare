import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { useEffect, useState } from 'react';
import MainLayout from '@components/layout/MainLayout';
import Loading from '@components/common/Loading';
import DashboardHome from '@pages/DashboardHome';
import DiseaseDashboard from '@pages/DiseaseDashboard';
import TenantsPage from '@pages/TenantsPage';
import ConsolidadoPage from '@pages/ConsolidadoPage';
import SettingsPage from '@pages/SettingsPage';
import NotFound from '@pages/NotFound';
import { initKeycloak, getUserInfo } from '@services/keycloak';
import { useAuthStore } from '@store/authStore';

function App() {
  const { setUser, setAuthenticated, setLoading, loading } = useAuthStore();
  const [authError, setAuthError] = useState(false);

  useEffect(() => {
    const init = async () => {
      try {
        if (import.meta.env.DEV && import.meta.env.VITE_SKIP_AUTH === 'true') {
          setUser({
            id: 'admin-user',
            name: 'Administrador',
            email: 'admin@intellicare.ia.br',
            roles: ['PLATFORM_ADMIN'],
            tenantId: 'platform',
            tenantName: 'IntelliCare Platform',
          });
          setAuthenticated(true);
          setLoading(false);
          return;
        }

        const authenticated = await initKeycloak();
        if (authenticated) {
          const user = getUserInfo();
          if (user) {
            setUser({
              id: user.id,
              name: user.name,
              email: user.email,
              roles: user.roles,
              tenantId: user.tenantId,
              tenantName: user.tenantName,
            });
          }
          setAuthenticated(true);
        } else {
          setAuthError(true);
        }
      } catch {
        setAuthError(true);
      } finally {
        setLoading(false);
      }
    };
    init();
  }, [setUser, setAuthenticated, setLoading]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-surface">
        <Loading message="Autenticando..." />
      </div>
    );
  }

  if (authError) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-surface text-slate-500">
        <p className="text-xl font-semibold mb-2">Erro de Autenticação</p>
        <p className="text-sm mb-4">Não foi possível conectar ao servidor de autenticação.</p>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm font-medium"
        >
          Tentar novamente
        </button>
      </div>
    );
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route element={<MainLayout />}>
          <Route index element={<DashboardHome />} />
          <Route path="/doenca/:diseaseCode" element={<DiseaseDashboard />} />
          <Route path="/tenants" element={<TenantsPage />} />
          <Route path="/consolidado" element={<ConsolidadoPage />} />
          <Route path="/configuracoes" element={<SettingsPage />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
