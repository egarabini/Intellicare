import { useState } from 'react';
import { motion } from 'framer-motion';
import { Activity, CheckCircle, AlertCircle, Clock, RefreshCw, Server, Database, Wifi } from 'lucide-react';

interface ServiceStatus {
  name: string;
  status: 'operational' | 'degraded' | 'outage' | 'maintenance';
  uptime: string;
  lastChecked: string;
}

interface Incident {
  id: string;
  title: string;
  status: 'investigating' | 'identified' | 'monitoring' | 'resolved';
  severity: 'critical' | 'major' | 'minor';
  date: string;
  description: string;
}

export default function StatusPage() {
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [isRefreshing, setIsRefreshing] = useState(false);

  const services: ServiceStatus[] = [
    { name: 'Plataforma Web', status: 'operational', uptime: '99.98%', lastChecked: 'há 1 minuto' },
    { name: 'API', status: 'operational', uptime: '99.95%', lastChecked: 'há 1 minuto' },
    { name: 'Agentes de IA', status: 'operational', uptime: '99.92%', lastChecked: 'há 2 minutos' },
    { name: 'Banco de Dados', status: 'operational', uptime: '99.99%', lastChecked: 'há 1 minuto' },
    { name: 'Autenticação', status: 'operational', uptime: '99.97%', lastChecked: 'há 1 minuto' },
    { name: 'Integrações FHIR', status: 'operational', uptime: '99.85%', lastChecked: 'há 3 minutos' },
  ];

  const incidents: Incident[] = [
    {
      id: 'INC-001',
      title: 'Atualização de sistema',
      status: 'resolved',
      severity: 'minor',
      date: '2025-01-15',
      description: 'Manutenção programada para atualização de componentes de segurança.',
    },
    {
      id: 'INC-002',
      title: 'Degradação de performance',
      status: 'resolved',
      severity: 'major',
      date: '2025-01-10',
      description: 'Aumento temporário no tempo de resposta da API. Resolvido em 45 minutos.',
    },
  ];

  const statusConfig = {
    operational: { icon: CheckCircle, color: 'text-green-500', bg: 'bg-green-100', label: 'Operacional' },
    degraded: { icon: AlertCircle, color: 'text-yellow-500', bg: 'bg-yellow-100', label: 'Degradado' },
    outage: { icon: AlertCircle, color: 'text-red-500', bg: 'bg-red-100', label: 'Indisponível' },
    maintenance: { icon: Clock, color: 'text-blue-500', bg: 'bg-blue-100', label: 'Manutenção' },
  };

  const severityConfig = {
    critical: { color: 'bg-red-500', label: 'Crítico' },
    major: { color: 'bg-orange-500', label: 'Maior' },
    minor: { color: 'bg-yellow-500', label: 'Menor' },
  };

  const incidentStatusConfig = {
    investigating: { color: 'text-red-600', label: 'Investigando' },
    identified: { color: 'text-orange-600', label: 'Identificado' },
    monitoring: { color: 'text-blue-600', label: 'Monitorando' },
    resolved: { color: 'text-green-600', label: 'Resolvido' },
  };

  const handleRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => {
      setLastUpdated(new Date());
      setIsRefreshing(false);
    }, 1000);
  };

  const allOperational = services.every((s) => s.status === 'operational');

  return (
    <div className="min-h-screen bg-gradient-to-b from-neutral-50 to-white py-16">
      <div className="container max-w-4xl">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 rounded-full mb-4">
            <Activity className="w-8 h-8 text-primary-600" />
          </div>
          <h1 className="text-4xl font-bold text-neutral-900 mb-4">
            Status dos Serviços
          </h1>
          <p className="text-lg text-neutral-600">
            Acompanhe o status em tempo real da IntelliCare
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className={`rounded-2xl p-8 mb-8 text-center ${
            allOperational
              ? 'bg-gradient-to-r from-green-500 to-green-600'
              : 'bg-gradient-to-r from-yellow-500 to-orange-500'
          } text-white`}
        >
          <div className="flex items-center justify-center gap-3 mb-2">
            {allOperational ? (
              <CheckCircle className="w-8 h-8" />
            ) : (
              <AlertCircle className="w-8 h-8" />
            )}
            <span className="text-2xl font-bold">
              {allOperational ? 'Todos os sistemas operacionais' : 'Alguns sistemas com problemas'}
            </span>
          </div>
          <p className="text-white/90">
            Última atualização: {lastUpdated.toLocaleTimeString('pt-BR')}
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6 mb-8"
        >
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-neutral-900">Status dos Serviços</h2>
            <button
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm text-neutral-600 hover:text-primary-600 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              Atualizar
            </button>
          </div>
          <div className="space-y-4">
            {services.map((service, index) => {
              const config = statusConfig[service.status];
              const Icon = config.icon;
              return (
                <motion.div
                  key={service.name}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3, delay: 0.4 + index * 0.05 }}
                  className="flex items-center justify-between p-4 bg-neutral-50 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 ${config.bg} rounded-lg flex items-center justify-center`}>
                      <Icon className={`w-5 h-5 ${config.color}`} />
                    </div>
                    <div>
                      <h3 className="font-medium text-neutral-900">{service.name}</h3>
                      <p className="text-sm text-neutral-500">
                        Uptime: {service.uptime}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium ${config.bg} ${config.color}`}>
                      {config.label}
                    </span>
                    <p className="text-xs text-neutral-400 mt-1">
                      {service.lastChecked}
                    </p>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.6 }}
            className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6 text-center"
          >
            <Server className="w-8 h-8 text-primary-600 mx-auto mb-2" />
            <div className="text-2xl font-bold text-neutral-900">99.9%</div>
            <div className="text-sm text-neutral-600">Uptime Médio</div>
          </motion.div>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.7 }}
            className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6 text-center"
          >
            <Database className="w-8 h-8 text-primary-600 mx-auto mb-2" />
            <div className="text-2xl font-bold text-neutral-900">{'&lt;100ms'}</div>
            <div className="text-sm text-neutral-600">Latência Média</div>
          </motion.div>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.8 }}
            className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6 text-center"
          >
            <Wifi className="w-8 h-8 text-primary-600 mx-auto mb-2" />
            <div className="text-2xl font-bold text-neutral-900">24/7</div>
            <div className="text-sm text-neutral-600">Monitoramento</div>
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.9 }}
          className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6"
        >
          <h2 className="text-xl font-bold text-neutral-900 mb-6">
            Histórico de Incidentes
          </h2>
          {incidents.length > 0 ? (
            <div className="space-y-4">
              {incidents.map((incident) => (
                <div
                  key={incident.id}
                  className="border-l-4 border-neutral-200 pl-4 py-2"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h3 className="font-medium text-neutral-900">
                        {incident.title}
                      </h3>
                      <p className="text-sm text-neutral-500">
                        {incident.id} • {new Date(incident.date).toLocaleDateString('pt-BR')}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${severityConfig[incident.severity].color}`} />
                      <span className="text-xs text-neutral-500">
                        {severityConfig[incident.severity].label}
                      </span>
                    </div>
                  </div>
                  <p className="text-sm text-neutral-600 mb-2">
                    {incident.description}
                  </p>
                  <span className={`text-xs font-medium ${incidentStatusConfig[incident.status].color}`}>
                    {incidentStatusConfig[incident.status].label}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-neutral-500 text-center py-8">
              Nenhum incidente registrado nos últimos 30 dias.
            </p>
          )}
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 1 }}
          className="mt-8 text-center text-sm text-neutral-500"
        >
          <p>
            Assine nossas notificações de status para receber alertas em tempo real.
            <a href="#" className="text-primary-600 hover:underline ml-1">
              Configurar alertas
            </a>
          </p>
        </motion.div>
      </div>
    </div>
  );
}
