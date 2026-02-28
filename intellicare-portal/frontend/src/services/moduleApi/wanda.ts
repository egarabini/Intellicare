import { createApiClient, moduleUrls } from './base';

const wandaClient = createApiClient(moduleUrls.wanda);

export interface WandaModuleStatus {
  name: string;
  base_url: string;
  version: string;
  description: string;
  capabilities: string[];
  status: 'online' | 'offline' | 'degraded';
  last_check?: string;
}

export interface WandaModulesResponse {
  success: boolean;
  data: {
    total: number;
    online: number;
    modules: WandaModuleStatus[];
  };
}

export interface WandaAlertQueueResponse {
  total: number;
  alerts: Array<Record<string, unknown>>;
}

export const wandaApi = {
  health: () => wandaClient.request<{ status: string; modules_online: number; version: string }>('/api/v1/health'),
  modules: () => wandaClient.request<WandaModulesResponse>('/api/v1/modules'),
  discoverModules: () => wandaClient.request<WandaModulesResponse>('/api/v1/modules/discover', { method: 'POST' }),
  alertQueue: (patientId?: string) =>
    wandaClient.request<WandaAlertQueueResponse>('/api/v1/alerts/queue', {
      query: { patient_id: patientId, limit: 20 },
    }),
  chat: (message: string, patientId?: string) =>
    wandaClient.request<{
      success: boolean;
      data: { response: string; modules_used: string[]; safety_warnings: string[] };
    }>('/api/v1/chat', {
      method: 'POST',
      body: { message, patient_id: patientId },
    }),
};
