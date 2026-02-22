/**
 * Configuracao dos modulos IntelliCare conhecidos.
 * O portal faz discovery automatico consultando /api/v1/info de cada URL.
 */

export interface ModuleConfig {
  /** Identificador unico do modulo */
  id: string;
  /** URL base do modulo (ex: http://localhost:8001) */
  baseUrl: string;
  /** Slug para matching com catálogo de agentes */
  agentSlug?: string;
}

/** Modulos registrados — URLs podem ser sobrescritas via env */
export const MODULE_REGISTRY: ModuleConfig[] = [
  {
    id: 'intellicare-oswaldo',
    baseUrl: import.meta.env.VITE_OSWALDO_URL || 'http://localhost:8001',
    agentSlug: 'oswaldo',
  },
  {
    id: 'intellicare-florence',
    baseUrl: import.meta.env.VITE_FLORENCE_URL || 'http://localhost:8002',
    agentSlug: 'florence',
  },
  {
    id: 'intellicare-zilda',
    baseUrl: import.meta.env.VITE_ZILDA_URL || 'http://localhost:8003',
    agentSlug: 'zilda',
  },
  {
    id: 'intellicare-donabedian',
    baseUrl: import.meta.env.VITE_DONABEDIAN_URL || 'http://localhost:8004',
    agentSlug: 'donabedian',
  },
  {
    id: 'intellicare-comunicacao',
    baseUrl: import.meta.env.VITE_COMUNICACAO_URL || 'http://localhost:8005',
  },
];

/** Intervalo de polling para health check (ms) */
export const DISCOVERY_INTERVAL_MS = 30_000;
