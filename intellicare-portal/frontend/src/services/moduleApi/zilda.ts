import { createApiClient, moduleUrls } from './base';

const zildaClient = createApiClient(moduleUrls.zilda);

export interface ZildaEstablishment {
  cnes_code: string;
  legal_name: string;
  fantasy_name: string;
  unit_type_description: string;
  city_name: string;
  state_code: string;
  city_code: string;
  active: boolean;
}

export const zildaApi = {
  health: () => zildaClient.request<{ status: string; version: string }>('/api/v1/health'),
  establishments: (params: { state_code?: string; city_code?: string; limit?: number }) =>
    zildaClient.request<ZildaEstablishment[]>('/api/v1/establishments', { query: params }),
  regionContext: (cityCode: string, stateCode?: string) =>
    zildaClient.request<Record<string, unknown>>(`/api/v1/region-context/${cityCode}`, {
      query: { state_code: stateCode },
    }),
};
