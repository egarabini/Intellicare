import { createApiClient, moduleUrls } from './base';

const donabedianClient = createApiClient(moduleUrls.donabedian);

export interface DonabedianIndicator {
  id: string;
  name: string;
  code: string;
  target_value?: number;
}

export interface DonabedianDashboardOverview {
  period_start: string;
  period_end: string;
  overall_score: number;
  total_pillars: number;
  total_indicators: number;
  total_measurements: number;
  status_distribution: {
    green: number;
    yellow: number;
    red: number;
    total: number;
    green_percent: number;
    yellow_percent: number;
    red_percent: number;
  };
  triad_summaries: Array<{
    dimension: 'estrutura' | 'processo' | 'resultado';
    indicator_count: number;
    measurement_count: number;
    current_score: number;
  }>;
}

export const donabedianApi = {
  health: () => donabedianClient.request<{ status: string; module: string; version: string }>('/api/v1/health'),
  info: () => donabedianClient.request<{ name: string; version: string; description: string }>('/api/v1/info'),
  indicators: () =>
    donabedianClient.request<{ items?: DonabedianIndicator[]; total?: number } | DonabedianIndicator[]>(
      '/api/v1/indicators',
    ),
  dashboard: (periodDays = 30) =>
    donabedianClient.request<DonabedianDashboardOverview>('/api/v1/dashboard', {
      query: { period_days: periodDays },
    }),
};
