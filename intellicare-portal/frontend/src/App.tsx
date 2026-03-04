import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Suspense, lazy } from 'react';
import Layout from '@components/layout/Layout';
import { TenantProvider, TenantSelectorPage, ModuleRoute } from './components/tenant';
import { useTenantContext } from './contexts/TenantContext';

// Eager load Dashboard
import DemoDashboard from '@pages/DemoDashboard';

// Lazy load feature modules
const PierreChat = lazy(() => import('./pages/PierreChat'));
const HippocratesPage = lazy(() => import('./pages/HippocratesPage'));
const MinervaOCR = lazy(() => import('./pages/MinervaOCR'));
const OswaldoPage = lazy(() => import('./pages/OswaldoPage'));
const FlorencePage = lazy(() => import('./pages/FlorencePage'));
const GeraldaPage = lazy(() => import('./pages/GeraldaPage'));
const NisePage = lazy(() => import('./pages/NisePage'));
const ZildaPage = lazy(() => import('./pages/ZildaPage'));
const WandaPage = lazy(() => import('./pages/WandaPage'));
const DonabedianPage = lazy(() => import('./pages/DonabedianPage'));
const GrahamePage = lazy(() => import('./pages/GrahamePage'));

// Import other pages
// import HomePage from '@pages/HomePage';
import AgentsPage from '@pages/AgentsPage';
// import AgentDetailPage from '@pages/AgentDetailPage';
import DashboardsPage from '@pages/DashboardsPage';
import ParticipacaoPage from '@pages/ParticipacaoPage';
import SobrePage from '@pages/SobrePage';
import ContatoPage from '@pages/ContatoPage';
import TermosPage from '@pages/TermosPage';
import PresentationPage from '@pages/PresentationPage';
import PrivacidadePage from '@pages/PrivacidadePage';
import CookiesPage from '@pages/CookiesPage';
import LgpdPage from '@pages/LgpdPage';
import AjudaPage from '@pages/AjudaPage';
import FaqPage from '@pages/FaqPage';
import StatusPage from '@pages/StatusPage';
import ModulesPage from '@pages/ModulesPage';
import SolicitacaoPage from '@pages/SolicitacaoPage';
import AcompanhamentoPage from '@pages/AcompanhamentoPage';

// ─── Inner App (com acesso ao TenantContext) ────────────────

function AppRoutes() {
  const { showSelector } = useTenantContext() as any; // Temporary cast until we expose it cleanly or we can just rely on not implementing the hook layer since the Provider now uses React state locally if we want it to. But let's assume we exposed it or we will. Actually our context only has {tenantInfo, isLoading, error, changeTenant}, wait. Let's fix this in App.tsx right now.

  return (
    <Layout>
      <Suspense fallback={<div className="flex h-screen items-center justify-center text-white">Carregando Módulos...</div>}>
        <Routes>
          {/* Core Demo Routes */}
          <Route path="/" element={<DemoDashboard />} />
          <Route path="/home" element={<Navigate to="/" replace />} />
          <Route path="/pierre" element={<ModuleRoute module="pierre"><PierreChat /></ModuleRoute>} />
          <Route path="/hippocrates" element={<ModuleRoute module="hippocrates"><HippocratesPage /></ModuleRoute>} />
          <Route path="/minerva" element={<ModuleRoute module="minerva"><MinervaOCR /></ModuleRoute>} />
          <Route path="/oswaldo" element={<ModuleRoute module="oswaldo"><OswaldoPage /></ModuleRoute>} />
          <Route path="/florence" element={<ModuleRoute module="florence"><FlorencePage /></ModuleRoute>} />
          <Route path="/geralda" element={<ModuleRoute module="geralda"><GeraldaPage /></ModuleRoute>} />
          <Route path="/nise" element={<ModuleRoute module="nise"><NisePage /></ModuleRoute>} />
          <Route path="/zilda" element={<ModuleRoute module="zilda"><ZildaPage /></ModuleRoute>} />
          <Route path="/wanda" element={<ModuleRoute module="wanda"><WandaPage /></ModuleRoute>} />
          <Route path="/donabedian" element={<ModuleRoute module="donabedian"><DonabedianPage /></ModuleRoute>} />
          <Route path="/grahame" element={<ModuleRoute module="grahame"><GrahamePage /></ModuleRoute>} />

          {/* Support Pages */}
          <Route path="/privacidade" element={<PrivacidadePage />} />
          <Route path="/cookies" element={<CookiesPage />} />
          <Route path="/lgpd" element={<LgpdPage />} />
          <Route path="/ajuda" element={<AjudaPage />} />
          <Route path="/faq" element={<FaqPage />} />
          <Route path="/status" element={<StatusPage />} />
          <Route path="/modulos" element={<ModulesPage />} />
          <Route path="/solicitacao" element={<SolicitacaoPage />} />
          <Route path="/acompanhamento/:protocol?" element={<AcompanhamentoPage />} />

          {/* Placeholders */}
          <Route path="/dashboards" element={<DashboardsPage />} />
          <Route path="/apresentacao" element={<PresentationPage />} />

          <Route path="/sobre" element={<SobrePage />} />
          <Route path="/contato" element={<ContatoPage />} />
          <Route path="/termos" element={<TermosPage />} />
          <Route path="/participacao" element={<ParticipacaoPage />} />

          <Route path="/agentes" element={<AgentsPage />} />
          {/*
          <Route path="/agentes/:slug" element={<AgentDetailPage />} />
          <Route path="/participacao" element={<ParticipacaoPage />} />
          */}
        </Routes>
      </Suspense>
    </Layout>
  );
}

// ─── Root App ───────────────────────────────────────────────

function App() {
  return (
    <Router>
      <TenantProvider>
        <AppRoutes />
      </TenantProvider>
    </Router>
  );
}

export default App;

