/**
 * Store Zustand para estado dos modulos IntelliCare.
 */

import { create } from 'zustand';
import { discoverModules, type DiscoveredModule } from '@services/moduleDiscovery';
import { DISCOVERY_INTERVAL_MS } from '@config/modules';

interface ModuleState {
  /** Modulos descobertos */
  modules: DiscoveredModule[];
  /** Carregamento em andamento */
  loading: boolean;
  /** Ultima vez que fez discovery */
  lastDiscovery: Date | null;
  /** Erro (se houver) */
  error: string | null;
  /** Timer ID do polling */
  _intervalId: ReturnType<typeof setInterval> | null;

  /** Executa discovery uma vez */
  discover: () => Promise<void>;
  /** Inicia polling periodico */
  startPolling: () => void;
  /** Para polling */
  stopPolling: () => void;
  /** Retorna modulo por ID */
  getModule: (id: string) => DiscoveredModule | undefined;
  /** Retorna modulo pelo slug do agente */
  getModuleBySlug: (slug: string) => DiscoveredModule | undefined;
  /** Verifica se uma capability existe em algum modulo */
  hasCapability: (capability: string) => boolean;
}

export const useModuleStore = create<ModuleState>((set, get) => ({
  modules: [],
  loading: false,
  lastDiscovery: null,
  error: null,
  _intervalId: null,

  discover: async () => {
    set({ loading: true, error: null });
    try {
      const modules = await discoverModules();
      set({ modules, lastDiscovery: new Date(), loading: false });
    } catch (err) {
      set({
        error: err instanceof Error ? err.message : 'Erro ao descobrir modulos',
        loading: false,
      });
    }
  },

  startPolling: () => {
    const { _intervalId, discover } = get();
    if (_intervalId) return; // ja rodando

    // Discovery imediato
    discover();

    const id = setInterval(() => {
      discover();
    }, DISCOVERY_INTERVAL_MS);

    set({ _intervalId: id });
  },

  stopPolling: () => {
    const { _intervalId } = get();
    if (_intervalId) {
      clearInterval(_intervalId);
      set({ _intervalId: null });
    }
  },

  getModule: (id: string) => {
    return get().modules.find((m) => m.config.id === id);
  },

  getModuleBySlug: (slug: string) => {
    return get().modules.find((m) => m.config.agentSlug === slug);
  },

  hasCapability: (capability: string) => {
    return get().modules.some((m) => m.info.capabilities.includes(capability));
  },
}));
