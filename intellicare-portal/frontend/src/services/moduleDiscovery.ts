/**
 * Servico de descoberta de modulos IntelliCare.
 * Faz ping em /api/v1/info e /api/v1/health de cada modulo registrado.
 */

import { MODULE_REGISTRY, type ModuleConfig } from '@config/modules';

export interface ModuleInfo {
  name: string;
  version: string;
  description?: string;
  capabilities: string[];
  metadata?: Record<string, unknown>;
}

export interface ModuleHealth {
  status: 'healthy' | 'degraded' | 'offline';
  module_name?: string;
  version?: string;
}

export interface DiscoveredModule {
  config: ModuleConfig;
  info: ModuleInfo;
  health: ModuleHealth;
  online: boolean;
  discoveredAt: Date;
}

async function fetchWithTimeout(url: string, timeoutMs = 5000): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }
}

async function discoverOne(config: ModuleConfig): Promise<DiscoveredModule | null> {
  try {
    const [infoRes, healthRes] = await Promise.all([
      fetchWithTimeout(`${config.baseUrl}/api/v1/info`),
      fetchWithTimeout(`${config.baseUrl}/api/v1/health`),
    ]);

    if (!infoRes.ok) return null;

    const info: ModuleInfo = await infoRes.json();
    const health: ModuleHealth = healthRes.ok
      ? await healthRes.json()
      : { status: 'degraded' as const };

    return {
      config,
      info,
      health,
      online: health.status !== 'offline',
      discoveredAt: new Date(),
    };
  } catch {
    return null;
  }
}

/**
 * Descobre todos os modulos ativos no registro.
 * Retorna apenas os que responderam com sucesso.
 */
export async function discoverModules(
  registry: ModuleConfig[] = MODULE_REGISTRY,
): Promise<DiscoveredModule[]> {
  const results = await Promise.all(registry.map(discoverOne));
  return results.filter((m): m is DiscoveredModule => m !== null);
}

/**
 * Verifica a saude de um unico modulo.
 */
export async function checkModuleHealth(baseUrl: string): Promise<ModuleHealth> {
  try {
    const res = await fetchWithTimeout(`${baseUrl}/api/v1/health`);
    if (!res.ok) return { status: 'offline' };
    return await res.json();
  } catch {
    return { status: 'offline' };
  }
}
