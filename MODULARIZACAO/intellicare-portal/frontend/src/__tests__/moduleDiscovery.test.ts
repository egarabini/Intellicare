import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { discoverModules, checkModuleHealth } from '../services/moduleDiscovery';
import type { ModuleConfig } from '../config/modules';

const FAKE_INFO = {
  name: 'intellicare-oswaldo',
  version: '1.0.0',
  description: 'Motor de doencas cronicas',
  capabilities: ['staging', 'alerts'],
};

const FAKE_HEALTH = {
  status: 'healthy' as const,
  module_name: 'intellicare-oswaldo',
  version: '1.0.0',
};

const mockRegistry: ModuleConfig[] = [
  { id: 'intellicare-oswaldo', baseUrl: 'http://localhost:8001', agentSlug: 'oswaldo' },
  { id: 'intellicare-florence', baseUrl: 'http://localhost:8002', agentSlug: 'florence' },
];

describe('discoverModules', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('returns discovered modules when APIs respond', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: vi.fn()
        .mockResolvedValueOnce(FAKE_INFO)
        .mockResolvedValueOnce(FAKE_HEALTH)
        .mockResolvedValueOnce({ ...FAKE_INFO, name: 'intellicare-florence' })
        .mockResolvedValueOnce({ ...FAKE_HEALTH, module_name: 'intellicare-florence' }),
    });
    vi.stubGlobal('fetch', mockFetch);

    const modules = await discoverModules(mockRegistry);
    expect(modules).toHaveLength(2);
    expect(modules[0].info.name).toBe('intellicare-oswaldo');
    expect(modules[0].online).toBe(true);
    expect(modules[0].config.agentSlug).toBe('oswaldo');
  });

  it('returns empty when all modules offline', async () => {
    const mockFetch = vi.fn().mockRejectedValue(new Error('Connection refused'));
    vi.stubGlobal('fetch', mockFetch);

    const modules = await discoverModules(mockRegistry);
    expect(modules).toHaveLength(0);
  });

  it('returns partial when some modules respond', async () => {
    let callCount = 0;
    const mockFetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('8001')) {
        return Promise.resolve({
          ok: true,
          json: () => {
            callCount++;
            return Promise.resolve(callCount <= 1 ? FAKE_INFO : FAKE_HEALTH);
          },
        });
      }
      return Promise.reject(new Error('Offline'));
    });
    vi.stubGlobal('fetch', mockFetch);

    const modules = await discoverModules(mockRegistry);
    expect(modules).toHaveLength(1);
    expect(modules[0].config.id).toBe('intellicare-oswaldo');
  });
});

describe('checkModuleHealth', () => {
  it('returns healthy when API responds', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(FAKE_HEALTH),
    });
    vi.stubGlobal('fetch', mockFetch);

    const health = await checkModuleHealth('http://localhost:8001');
    expect(health.status).toBe('healthy');
  });

  it('returns offline on error', async () => {
    const mockFetch = vi.fn().mockRejectedValue(new Error('Timeout'));
    vi.stubGlobal('fetch', mockFetch);

    const health = await checkModuleHealth('http://localhost:8001');
    expect(health.status).toBe('offline');
  });

  it('returns offline on non-ok response', async () => {
    const mockFetch = vi.fn().mockResolvedValue({ ok: false });
    vi.stubGlobal('fetch', mockFetch);

    const health = await checkModuleHealth('http://localhost:8001');
    expect(health.status).toBe('offline');
  });
});
