import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Suspense, lazy } from 'react';
import Layout from '@components/layout/Layout';
import { TenantProvider, useTenant, TenantSelectorPage } from './components/tenant';

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
  const { showSelector } = useTenant();

  // Se multi-org e tenant não selecionado → mostrar seletor
  if (showSelector) {
    return <TenantSelectorPage />;
  }

  return (
    <Layout>
      <Suspense fallback={<div className="flex h-screen items-center justify-center text-white">Carregando Módulos...</div>}>
        <Routes>
          {/* Core Demo Routes */}
          <Route path="/" element={<DemoDashboard />} />
          <Route path="/home" element={<Navigate to="/" replace />} />
          <Route path="/pierre" element={<PierreChat />} />
          <Route path="/hippocrates" element={<HippocratesPage />} />
          <Route path="/minerva" element={<MinervaOCR />} />
          <Route path="/oswaldo" element={<OswaldoPage />} />
          <Route path="/florence" element={<FlorencePage />} />
          <Route path="/geralda" element={<GeraldaPage />} />
          <Route path="/nise" element={<NisePage />} />
          <Route path="/zilda" element={<ZildaPage />} />
          <Route path="/wanda" element={<WandaPage />} />
          <Route path="/donabedian" element={<DonabedianPage />} />
          <Route path="/grahame" element={<GrahamePage />} />

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
  // Multi-tenancy desabilitado por padrão no dev
  // Habilitar com VITE_MULTI_TENANT=true
  const multiTenantEnabled = import.meta.env.VITE_MULTI_TENANT === 'true';

  return (
    <Router>
      <TenantProvider enabled={multiTenantEnabled}>
        <AppRoutes />
      </TenantProvider>
    </Router>
  );
}

export default App;

