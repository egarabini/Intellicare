/**
 * Hook para acessar modulos IntelliCare com discovery automatico.
 * Inicia polling ao montar, para ao desmontar.
 */

import { useEffect } from 'react';
import { useModuleStore } from '@store/moduleStore';

/**
 * Hook principal de modulos — inicia discovery automaticamente.
 */
export function useModules() {
  const store = useModuleStore();

  useEffect(() => {
    store.startPolling();
    return () => store.stopPolling();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return {
    modules: store.modules,
    loading: store.loading,
    error: store.error,
    lastDiscovery: store.lastDiscovery,
    getModule: store.getModule,
    getModuleBySlug: store.getModuleBySlug,
    hasCapability: store.hasCapability,
    refresh: store.discover,
  };
}

/**
 * Hook simplificado que retorna apenas contagem de modulos online.
 */
export function useModuleCount() {
  const { modules, loading } = useModules();
  return {
    total: modules.length,
    healthy: modules.filter((m) => m.health.status === 'healthy').length,
    degraded: modules.filter((m) => m.health.status === 'degraded').length,
    loading,
  };
}
