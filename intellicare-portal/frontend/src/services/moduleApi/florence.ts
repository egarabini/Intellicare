import { createApiClient, moduleUrls } from './base';

const florenceClient = createApiClient(moduleUrls.florence);

export interface FlorencePanel {
  id: string;
  labs: Array<{ id: string; name: string; loinc_code: string; unit: string }>;
}

export const florenceApi = {
  health: () => florenceClient.request<{ status: string; version: string }>('/api/v1/health'),
  info: () => florenceClient.request<{ name: string; version: string; capabilities: string[] }>('/api/v1/info'),
  panels: () => florenceClient.request<FlorencePanel[]>('/api/v1/panels'),
  labs: () => florenceClient.request<Array<{ id: string; name: string; normal_range: string }>>('/api/v1/labs'),
};
