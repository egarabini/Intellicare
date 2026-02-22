import { motion } from 'framer-motion';
import { Activity, CheckCircle, AlertTriangle, XCircle, RefreshCw, Boxes } from 'lucide-react';
import { useModules } from '@hooks/useModules';
import { AGENTS, type Agent } from '../types/index';
import type { DiscoveredModule } from '@services/moduleDiscovery';

const statusConfig = {
  healthy: { icon: CheckCircle, color: 'text-green-500', bg: 'bg-green-100', label: 'Saudável' },
  degraded: { icon: AlertTriangle, color: 'text-yellow-500', bg: 'bg-yellow-100', label: 'Degradado' },
  offline: { icon: XCircle, color: 'text-red-500', bg: 'bg-red-100', label: 'Offline' },
};

function ModuleCard({ module }: { module: DiscoveredModule }) {
  const cfg = statusConfig[module.health.status];
  const StatusIcon = cfg.icon;

  // Encontra agente correspondente no catalogo
  const agent: Agent | undefined = AGENTS.find(
    (a) => a.slug === module.config.agentSlug,
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6"
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          {agent && (
            <span className="text-2xl">{agent.icon}</span>
          )}
          <div>
            <h3 className="font-bold text-neutral-900">
              {module.info.name}
            </h3>
            <p className="text-sm text-neutral-500">
              v{module.info.version}
            </p>
          </div>
        </div>
        <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${cfg.bg} ${cfg.color}`}>
          <StatusIcon className="w-3 h-3" />
          {cfg.label}
        </span>
      </div>

      {module.info.description && (
        <p className="text-sm text-neutral-600 mb-4">
          {module.info.description}
        </p>
      )}

      {module.info.capabilities.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {module.info.capabilities.map((cap) => (
            <span
              key={cap}
              className="inline-block px-2 py-0.5 bg-primary-50 text-primary-700 text-xs rounded-md"
            >
              {cap}
            </span>
          ))}
        </div>
      )}

      <div className="mt-4 pt-4 border-t border-neutral-100 text-xs text-neutral-400">
        {module.config.baseUrl}
      </div>
    </motion.div>
  );
}

export default function ModulesPage() {
  const { modules, loading, lastDiscovery, refresh } = useModules();

  const healthy = modules.filter((m) => m.health.status === 'healthy').length;
  const degraded = modules.filter((m) => m.health.status === 'degraded').length;

  return (
    <div className="min-h-screen bg-gradient-to-b from-neutral-50 to-white py-16">
      <div className="container max-w-5xl">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 rounded-full mb-4">
            <Boxes className="w-8 h-8 text-primary-600" />
          </div>
          <h1 className="text-4xl font-bold text-neutral-900 mb-4">
            Módulos Ativos
          </h1>
          <p className="text-lg text-neutral-600">
            Arquitetura LEGO — módulos independentes descobertos automaticamente
          </p>
        </motion.div>

        {/* Summary bar */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="flex items-center justify-between bg-white rounded-xl shadow-sm border border-neutral-200 p-6 mb-8"
        >
          <div className="flex items-center gap-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-neutral-900">{modules.length}</div>
              <div className="text-sm text-neutral-500">Módulos</div>
            </div>
            <div className="h-10 w-px bg-neutral-200" />
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600">{healthy}</div>
              <div className="text-sm text-neutral-500">Saudáveis</div>
            </div>
            {degraded > 0 && (
              <>
                <div className="h-10 w-px bg-neutral-200" />
                <div className="text-center">
                  <div className="text-3xl font-bold text-yellow-600">{degraded}</div>
                  <div className="text-sm text-neutral-500">Degradados</div>
                </div>
              </>
            )}
          </div>
          <button
            onClick={refresh}
            disabled={loading}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm text-neutral-600 hover:text-primary-600 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Atualizar
          </button>
        </motion.div>

        {/* Module grid */}
        {loading && modules.length === 0 ? (
          <div className="text-center py-20">
            <RefreshCw className="w-8 h-8 text-primary-400 animate-spin mx-auto mb-4" />
            <p className="text-neutral-500">Descobrindo módulos...</p>
          </div>
        ) : modules.length === 0 ? (
          <div className="text-center py-20 bg-white rounded-xl border border-neutral-200">
            <Activity className="w-12 h-12 text-neutral-300 mx-auto mb-4" />
            <p className="text-neutral-500 text-lg mb-2">Nenhum módulo ativo encontrado</p>
            <p className="text-neutral-400 text-sm">
              Verifique se os módulos estão rodando e acessíveis na rede
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {modules.map((mod) => (
              <ModuleCard key={mod.config.id} module={mod} />
            ))}
          </div>
        )}

        {lastDiscovery && (
          <p className="text-center text-xs text-neutral-400 mt-8">
            Última descoberta: {lastDiscovery.toLocaleTimeString('pt-BR')}
          </p>
        )}
      </div>
    </div>
  );
}
