import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from '@components/layout/Layout';
import HomePage from '@pages/HomePage';
import AgentsPage from '@pages/AgentsPage';
import AgentDetailPage from '@pages/AgentDetailPage';
import DashboardsPage from '@pages/DashboardsPage';
import ParticipacaoPage from '@pages/ParticipacaoPage';
import SobrePage from '@pages/SobrePage';
import ContatoPage from '@pages/ContatoPage';
import TermosPage from '@pages/TermosPage';
import PrivacidadePage from '@pages/PrivacidadePage';
import CookiesPage from '@pages/CookiesPage';
import LgpdPage from '@pages/LgpdPage';
import AjudaPage from '@pages/AjudaPage';
import FaqPage from '@pages/FaqPage';
import StatusPage from '@pages/StatusPage';
import SolicitacaoPage from '@pages/SolicitacaoPage';
import AcompanhamentoPage from '@pages/AcompanhamentoPage';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/agentes" element={<AgentsPage />} />
          <Route path="/agentes/:slug" element={<AgentDetailPage />} />
          <Route path="/dashboards" element={<DashboardsPage />} />
          <Route path="/participacao" element={<ParticipacaoPage />} />
          <Route path="/sobre" element={<SobrePage />} />
          <Route path="/contato" element={<ContatoPage />} />
          <Route path="/termos" element={<TermosPage />} />
          <Route path="/privacidade" element={<PrivacidadePage />} />
          <Route path="/cookies" element={<CookiesPage />} />
          <Route path="/lgpd" element={<LgpdPage />} />
          <Route path="/ajuda" element={<AjudaPage />} />
          <Route path="/faq" element={<FaqPage />} />
          <Route path="/status" element={<StatusPage />} />
          <Route path="/solicitacao" element={<SolicitacaoPage />} />
          <Route path="/acompanhamento/:protocol?" element={<AcompanhamentoPage />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
