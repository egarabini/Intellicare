import { createApiClient, moduleUrls } from './base';

const grahameClient = createApiClient(moduleUrls.grahame);

export interface FhirBundle<T = Record<string, unknown>> {
  total: number;
  entry?: Array<{ fullUrl?: string; resource: T }>;
}

export const grahameApi = {
  health: () => grahameClient.request<{ status: string; version: string }>('/api/v1/health'),
  info: () => grahameClient.request<{ name: string; version: string; capabilities: string[] }>('/api/v1/info'),
  searchResources: <T = Record<string, unknown>>(resourceType: string, params?: Record<string, string>) =>
    grahameClient.request<FhirBundle<T>>(`/api/v1/${resourceType}`, { query: params }),
  getResource: <T = Record<string, unknown>>(resourceType: string, id: string) =>
    grahameClient.request<T>(`/api/v1/${resourceType}/${id}`),
};
