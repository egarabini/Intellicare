import api from './api';
import { API_CONFIG } from '@config/api';
import type { DashboardFilters, DiseaseDashboardData, DiseaseCode } from '@/types/index';

const BASE = API_CONFIG.donabedianUrl;

/**
 * Donabedian Disease Dashboard API
 */
export const donabedianApi = {
  /** Fetch full disease dashboard data */
  async getDashboard(filters: DashboardFilters): Promise<DiseaseDashboardData> {
    const { data } = await api.get(`${BASE}/dashboard/disease/${filters.disease}`, {
      params: {
        period: filters.period,
        establishment: filters.establishment,
        region: filters.region,
        stage: filters.stage,
        status: filters.status,
        search: filters.search,
        page: filters.page,
        page_size: filters.pageSize,
      },
    });
    return data;
  },

  /** Fetch KPIs only */
  async getKPIs(disease: DiseaseCode, period: string) {
    const { data } = await api.get(`${BASE}/dashboard/disease/${disease}/kpis`, {
      params: { period },
    });
    return data;
  },

  /** Fetch trend data for a specific indicator */
  async getTrends(disease: DiseaseCode, period: string) {
    const { data } = await api.get(`${BASE}/dashboard/disease/${disease}/trends`, {
      params: { period },
    });
    return data;
  },

  /** Fetch stage distribution */
  async getStageDistribution(disease: DiseaseCode) {
    const { data } = await api.get(`${BASE}/dashboard/disease/${disease}/stages`);
    return data;
  },

  /** Fetch geographic data */
  async getGeoData(disease: DiseaseCode) {
    const { data } = await api.get(`${BASE}/dashboard/disease/${disease}/geo`);
    return data;
  },

  /** Fetch patient list with pagination + filters */
  async getPatients(filters: DashboardFilters) {
    const { data } = await api.get(`${BASE}/dashboard/disease/${filters.disease}/patients`, {
      params: {
        stage: filters.stage,
        status: filters.status,
        search: filters.search,
        page: filters.page,
        page_size: filters.pageSize,
      },
    });
    return data;
  },

  /** Health check */
  async health() {
    const { data } = await api.get(`${BASE}/health`);
    return data;
  },
};
